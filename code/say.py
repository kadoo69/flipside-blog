"""Say something to the flip agent, as yourself, and print its reply.

Standard library only. Run it in a second terminal while flip_agent.py runs:
SWITCH_EMAIL=... SWITCH_PASSWORD=... python3 say.py hello, Switch
"""
import http.cookiejar
import json
import os
import sys
import time
import urllib.request
import uuid

BASE = os.environ.get("SWITCH_BASE", "http://127.0.0.1:52370")
jar = urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
me = urllib.request.build_opener(jar)


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    with me.open(req, timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


login = {"email": os.environ["SWITCH_EMAIL"],
         "password": os.environ["SWITCH_PASSWORD"]}
call("POST", "/gateway/auth/login", login)

# The flip-demo room with the newest message is the one flip_agent.py opened.
rooms = [c for c in call("GET", "/gateway/chats")["chats"]
         if c["name"] == "flip-demo"]
if not rooms:
    sys.exit("No flip-demo room yet. Start flip_agent.py first.")
chat = max(rooms, key=lambda c: (c.get("lastMessage") or {}).get("sentAt", ""))
room, flip = chat["roomId"], chat["agents"][0]["id"]

text = " ".join(sys.argv[1:]) or "hello, Switch"
head = call("GET", f"/gateway/chats/{room}/messages")["headSeq"]
call("POST", f"/gateway/chats/{room}/messages", {
    "requestId": uuid.uuid4().hex, "body": f"@flip {text}",
    "mentionAgentId": flip})
print(f"you   @flip {text}")

for _ in range(30):
    time.sleep(1)
    replies = [m for m in call("GET", f"/gateway/chats/{room}/messages")["messages"]
               if m["seq"] > head and m["sender"]["kind"] == "agent"]
    if replies:
        print(f"flip  {replies[0]['body']}")
        break
else:
    sys.exit("No reply in 30 s. Is flip_agent.py still running?")
