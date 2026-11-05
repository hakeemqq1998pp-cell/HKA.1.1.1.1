"""Loopback-only Chrome UI for the local OMEGA AI CORE."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .core import ask, recent_messages, status, OmegaAIError

HOST = "127.0.0.1"
PORT = 8765
MAX_BODY = 16_384

PAGE = r"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09070d">
<title>OMEGA AI CORE</title>
<style>
:root{color-scheme:dark;--bg:#09070d;--panel:#120d19;--line:#54236f;--red:#ff3030;--purple:#c084fc;--muted:#a99ab4}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#24102d 0,#09070d 55%);color:#f5eafa;font-family:system-ui,"Noto Sans Arabic",sans-serif;min-height:100vh}
main{max-width:850px;margin:auto;padding:18px;display:flex;flex-direction:column;min-height:100vh}
header{border:1px solid var(--line);background:#100b17eF;border-radius:18px;padding:16px;margin-bottom:14px}
h1{margin:0;color:var(--red);font-size:clamp(22px,5vw,32px);letter-spacing:.04em}header p{margin:7px 0 0;color:var(--purple);font-size:13px}
#status{color:var(--muted);font-size:12px;margin-top:10px}
#chat{flex:1;min-height:45vh;border:1px solid var(--line);border-radius:18px;background:#0d0912;padding:14px;overflow:auto}
.msg{max-width:92%;white-space:pre-wrap;overflow-wrap:anywhere;padding:12px 14px;border-radius:14px;margin:10px 0;line-height:1.7}
.user{background:#25122e;border:1px solid #713b8e;margin-right:auto;color:#fff}
.ai{background:#17101e;border:1px solid #493052;margin-left:auto;color:#f5eafa}
small{display:block;color:var(--purple);font-size:11px;margin-bottom:4px}
form{display:flex;gap:9px;margin-top:12px}textarea{flex:1;resize:vertical;min-height:54px;max-height:160px;background:#120d19;color:#fff;border:1px solid var(--line);border-radius:13px;padding:12px;font:inherit;outline:none}
textarea:focus{border-color:var(--purple)}button{background:#641b76;color:white;border:1px solid #a34ac2;border-radius:13px;padding:0 20px;font:inherit;font-weight:700}button:disabled{opacity:.5}
footer{text-align:center;color:var(--muted);font-size:11px;padding:12px}
</style>
</head>
<body><main>
<header><h1>THE SPIDER OMEGA</h1><p>OMEGA AI CORE · LOCAL MODEL INTERFACE</p><div id="status">جارٍ فحص المحرك المحلي...</div></header>
<section id="chat" aria-live="polite"><div class="msg ai"><small>OMEGA AI CORE</small>مرحباً. اكتب رسالتك لبدء المحادثة مع النموذج المحلي.</div></section>
<form id="form"><textarea id="prompt" placeholder="اكتب رسالتك هنا..." required></textarea><button id="send">إرسال</button></form>
<footer>اتصال محلي على هذا الهاتف · 127.0.0.1 · لا توجد واجهة لتنفيذ أوامر النظام</footer>
</main>
<script>
const chat=document.getElementById('chat'),form=document.getElementById('form'),promptBox=document.getElementById('prompt'),send=document.getElementById('send'),statusBox=document.getElementById('status');
function addMessage(role,text){const box=document.createElement('div');box.className='msg '+(role==='user'?'user':'ai');const label=document.createElement('small');label.textContent=role==='user'?'أنت':'OMEGA AI CORE';const body=document.createElement('div');body.textContent=text;box.append(label,body);chat.appendChild(box);chat.scrollTop=chat.scrollHeight;}
async function loadStatus(){try{const r=await fetch('/api/status');const d=await r.json();statusBox.textContent='المحرك: '+d.engine+' · النموذج: '+d.model+' · '+d.endpoint;}catch(e){statusBox.textContent='تعذر قراءة حالة المحرك';}}
form.addEventListener('submit',async e=>{e.preventDefault();const text=promptBox.value.trim();if(!text)return;addMessage('user',text);promptBox.value='';send.disabled=true;send.textContent='...';try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:text})});const d=await r.json();if(!r.ok)throw new Error(d.error||'فشل الطلب');addMessage('assistant',d.answer);}catch(err){addMessage('assistant','خطأ: '+err.message);}finally{send.disabled=false;send.textContent='إرسال';promptBox.focus();}});
loadStatus();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/api/status":
            data = json.dumps(status(), ensure_ascii=False).encode("utf-8")
            self._send(200, data, "application/json; charset=utf-8")
        elif path == "/api/history":
            data = json.dumps(recent_messages(20), ensure_ascii=False).encode("utf-8")
            self._send(200, data, "application/json; charset=utf-8")
        else:
            self._send(404, b'{"error":"Not found"}', "application/json")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/chat":
            self._send(404, b'{"error":"Not found"}', "application/json")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > MAX_BODY:
                raise ValueError("حجم الطلب غير صالح")
            body = json.loads(self.rfile.read(size).decode("utf-8"))
            prompt = body.get("prompt", "")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("اكتب رسالة أولاً")
            answer = ask(prompt)
            data = json.dumps({"answer": answer}, ensure_ascii=False).encode("utf-8")
            self._send(200, data, "application/json; charset=utf-8")
        except (ValueError, json.JSONDecodeError) as exc:
            data = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
            self._send(400, data, "application/json; charset=utf-8")
        except OmegaAIError as exc:
            data = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
            self._send(503, data, "application/json; charset=utf-8")

    def log_message(self, fmt: str, *args) -> None:
        print("[OMEGA UI] " + (fmt % args))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("OMEGA AI CORE UI is running.")
    print(f"Open Chrome: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping OMEGA UI...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
