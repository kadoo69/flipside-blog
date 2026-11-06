"""A Switch agent in one file: it replies to messages addressed to it, flipped.

Standard library only.
Run: SWITCH_EMAIL=... SWITCH_PASSWORD=... python3 flip_agent.py
"""
import http.cookiejar, json, os, threading, time, urllib.request, uuid

BASE = os.environ.get("SWITCH_BASE", "http://127.0.0.1:52370")
web = urllib.request.build_opener()


def call(method, path, body=None, token=None, opener=web):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with opener.open(req, timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


# 1. Sign in as yourself, and mint an API key to register an agent with.
jar = urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
me = urllib.request.build_opener(jar)
login = {"email": os.environ["SWITCH_EMAIL"],
         "password": os.environ["SWITCH_PASSWORD"]}
call("POST", "/gateway/auth/login", login, opener=me)
key = call("POST", "/gateway/api-keys", {"label": "flip"}, opener=me)["key"]

# 2. Register the agent. It gets its own id and its own API key.
agent = call("POST", "/agents/register-known", {
    "agent_type": "codex", "name": "flip", "options": {},
    "description": "Replies to you, flipped", "overwrite": True}, token=key)
aid, akey = agent["id"], agent["api_key"]

# 3. Open a room with the agent in it.
chat = call("POST", "/gateway/chats", {
    "requestId": uuid.uuid4().hex, "name": "flip-demo", "agentIds": [aid],
    "greeting": "Tag @flip and I will say it back, flipped."}, opener=me)
room = chat["chat"]["roomId"]
print("room ready: flip-demo")

# 4. Open the event stream, then send a heartbeat every 2 seconds.
conn = uuid.uuid4().hex
url = (f"{BASE}/agents/{aid}/events?connection_id={conn}"
       f"&scope=all&filter=all&start_from=head&rooms={room}")
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {akey}")
req.add_header("Accept", "text/event-stream")
stream = urllib.request.urlopen(req)


def beat():
    while True:
        call("POST", f"/agents/{aid}/connection/beat",
             {"connection_id": conn}, token=akey)
        time.sleep(2)


threading.Thread(target=beat, daemon=True).start()

# 5. Answer only what is addressed to this agent, never its own messages.
for line in stream:
    if not line.startswith(b"data:"):
        continue
    ev = json.loads(line[5:])
    p = ev.get("payload") or {}
    if ev.get("type") != "message" or not p.get("addressed"):
        continue
    if p.get("sender_name") == "flip":
        continue
    text = p["body"].replace("@flip", "").strip()
    call("POST", f"/agents/{aid}/message",
         {"room_id": room, "content": text[::-1]}, token=akey)
    print(f"{p['sender_name']}: {text}  ->  {text[::-1]}")
