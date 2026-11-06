"use strict";
// The parity gate executes this exact script under Node WebCrypto.
globalThis.FlipsideVerify = (() => {
  const meta = ["v", "session", "step", "chunk", "role", "tools", "files", "mentions", "cmd", "ok"];
  const leafKeys = [...meta, "text"];
  // Python re.match's '$' accepts one final LF. Preserve the existing CLI contract.
  const hex64 = /^[0-9a-f]{64}\n?$/;
  const encoder = new TextEncoder();
  const decoder = new TextDecoder("utf-8", {fatal: true, ignoreBOM: true});
  const object = x => x !== null && typeof x === "object" && !Array.isArray(x);
  const integer = x => typeof x === "bigint" && x >= 0n;
  const keysAre = (x, keys) => object(x) && Object.keys(x).length === keys.length && keys.every(k => Object.hasOwn(x, k));

  // JSON.parse rounds large integers and conflates 1 with 1.0. Preserve integer
  // tokens as BigInt; float tokens stay Number and cannot pass integer metadata.
  function parse(text) {
    let p = 0;
    const ws = () => { while (/[\x20\t\r\n]/.test(text[p] || "x")) p++; };
    function value() {
      ws();
      if (text[p] === '"') {
        const m = /^"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"/.exec(text.slice(p));
        if (!m) throw Error("Invalid JSON string");
        p += m[0].length;
        return JSON.parse(m[0]);
      }
      if (text[p] === "[" || text[p] === "{") {
        const array = text[p++] === "[", end = array ? "]" : "}";
        const out = array ? [] : Object.create(null);
        ws();
        if (text[p] === end) { p++; return out; }
        while (true) {
          if (array) out.push(value());
          else {
            ws();
            if (text[p] !== '"') throw Error("JSON object key must be a string");
            const key = value();
            ws();
            if (text[p++] !== ":") throw Error("Expected colon");
            out[key] = value();
          }
          ws();
          if (text[p] === end) { p++; return out; }
          if (text[p++] !== ",") throw Error("Expected comma");
        }
      }
      for (const [word, result] of [["true", true], ["false", false], ["null", null],
        ["NaN", NaN], ["Infinity", Infinity], ["-Infinity", -Infinity]]) {
        if (text.startsWith(word, p)) { p += word.length; return result; }
      }
      const m = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(text.slice(p));
      if (!m) throw Error("Invalid JSON value");
      p += m[0].length;
      return /[.eE]/.test(m[0]) ? Number(m[0]) : BigInt(m[0]);
    }
    const result = value();
    ws();
    if (p !== text.length) throw Error("Unexpected data after JSON value");
    return result;
  }

  function canonical(x) {
    if (typeof x === "bigint") return x.toString();
    if (typeof x === "number") throw Error("Floats are not canonical metadata");
    if (typeof x === "string") {
      // TextEncoder silently replaces lone surrogates; never hash replacement bytes.
      for (const c of x) {
        const n = c.codePointAt(0);
        if (n >= 0xd800 && n <= 0xdfff) throw Error("Unpaired Unicode surrogate");
      }
      return JSON.stringify(x);
    }
    if (x === null || typeof x === "boolean") return JSON.stringify(x);
    if (Array.isArray(x)) return "[" + x.map(canonical).join(",") + "]";
    return "{" + Object.keys(x).sort().map(k => JSON.stringify(k) + ":" + canonical(x[k])).join(",") + "}";
  }

  function validMeta(x) {
    return x.v === 1n && ["session", "step", "chunk"].every(k => integer(x[k])) &&
      ["user", "assistant", "tool_result"].includes(x.role) &&
      ["tools", "files", "mentions"].every(k => Array.isArray(x[k]) && x[k].every(s => typeof s === "string")) &&
      (x.cmd === null || ["test", "lint", "build", "other"].includes(x.cmd)) &&
      (x.ok === null || typeof x.ok === "boolean");
  }

  function shape(d) {
    if (!object(d) || !["v", "commit", "i", "n", "salt", "leaf", "proof"].every(k => Object.hasOwn(d, k))) return false;
    if (d.v !== 1n || typeof d.commit !== "string" || !/^[0-9a-f]{40}\n?$/.test(d.commit) ||
      !integer(d.i) || !integer(d.n) || typeof d.salt !== "string" || !hex64.test(d.salt) ||
      !Array.isArray(d.proof) || !d.proof.every(p => typeof p === "string" && hex64.test(p)) ||
      !keysAre(d.leaf, leafKeys) || typeof d.leaf.text !== "string" || !validMeta(d.leaf)) return false;
    try { canonical(d.leaf); return true; } catch { return false; }
  }

  const hex = bytes => Array.from(bytes, b => b.toString(16).padStart(2, "0")).join("");
  const unhex = s => Uint8Array.from(s.match(/../g), x => parseInt(x, 16));
  async function hash(...parts) {
    const data = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
    let offset = 0;
    for (const p of parts) { data.set(p, offset); offset += p.length; }
    return new Uint8Array(await globalThis.crypto.subtle.digest("SHA-256", data));
  }

  function proofLength(i, n) {
    let length = 0;
    while (n > 1n) {
      let k = 1n;
      while (k * 2n < n) k *= 2n;
      if (i < k) n = k;
      else { i -= k; n -= k; }
      length++;
    }
    return length;
  }

  async function rootFromProof(i, n, leaf, proof) {
    let fn = i, sn = n - 1n, root = leaf;
    for (const sibling of proof) {
      if (sn === 0n) return null;
      const p = unhex(sibling);
      if ((fn & 1n) || fn === sn) {
        root = await hash(new Uint8Array([1]), p, root);
        if (!(fn & 1n)) while (!(fn & 1n) && fn !== 0n) { fn >>= 1n; sn >>= 1n; }
      } else root = await hash(new Uint8Array([1]), root, p);
      fn >>= 1n;
      sn >>= 1n;
    }
    return sn === 0n ? hex(root) : null;
  }

  async function verify(disclosure, manifestBytes, record) {
    const result = (code, detail) => ({code, detail});
    let d;
    try { d = parse(disclosure); }
    catch { return result("INPUT_ERROR", "Disclosure is not JSON. The CLI treats unreadable JSON as a usage error."); }
    if (!shape(d)) return result("BAD_DISCLOSURE", "Disclosure fields or metadata are malformed.");
    const t = /^(?:Flipside-Seal: )?v1 root=([0-9a-f]{64}) n=([1-9][0-9]*) manifest=([0-9a-f]{64})$/.exec(record.trim());
    if (!t) return result("INPUT_ERROR", "Supply a v1 Flipside-Seal record with root, n and manifest hash. Git checks require flip verify.");
    if (!globalThis.crypto?.subtle) return result("INPUT_ERROR", "WebCrypto unavailable. Open as a local file or use localhost, or run flip verify.");
    if (hex(await hash(manifestBytes)) !== t[3]) return result("MANIFEST_HASH", "Manifest SHA-256 differs from the supplied record.");
    let entries;
    try {
      entries = parse(decoder.decode(manifestBytes));
      if (!Array.isArray(entries) || !entries.length || !entries.every((e, i) =>
        keysAre(e, ["i", ...meta]) && e.i === BigInt(i) && validMeta(e))) throw Error("Malformed manifest");
      const encoded = encoder.encode(canonical(entries));
      if (encoded.length !== manifestBytes.length || !encoded.every((b, i) => b === manifestBytes[i])) throw Error("Noncanonical manifest");
    } catch { return result("MANIFEST_HASH", "Manifest is malformed or is not exact canonical UTF-8 JSON."); }
    if (d.i < BigInt(entries.length) && meta.some(k => canonical(entries[Number(d.i)][k]) !== canonical(d.leaf[k])))
      return result("MANIFEST_MISMATCH", "Leaf metadata differs from the public manifest entry.");
    if (d.i >= d.n || d.n !== BigInt(t[2]) || d.proof.length !== proofLength(d.i, d.n))
      return result("BAD_SIZE", "Leaf index, tree size or proof length is inconsistent.");
    const leaf = await hash(new Uint8Array([0]), unhex(d.salt), encoder.encode(canonical(d.leaf)));
    if (await rootFromProof(d.i, d.n, leaf, d.proof) !== t[1])
      return result("PROOF_FAIL", "Disclosed bytes do not hash up to the supplied root.");
    return {...result("OK", `Leaf ${d.i}, session ${d.leaf.session}, step ${d.leaf.step}, chunk ${d.leaf.chunk} matches supplied seal ${t[1].slice(0, 7)}.`), text: d.leaf.text};
  }
  return Object.freeze({verify});
})();
