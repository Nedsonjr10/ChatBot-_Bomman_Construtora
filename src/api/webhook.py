from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Any

from src.core.triage import Triage
from src.core.session import SessionManager
from src.core.replier import Replier

app = FastAPI(title="Bomman Construtora — Bot WhatsApp 🏗️")

triage  = Triage()
session = SessionManager()
replier = Replier()


class GatewayPayload(BaseModel):
    clientId:  str
    remoteJid: str
    pushName:  Optional[str] = None
    text:      str           = ""
    mediaType: Optional[str] = "text"
    fromMe:    Optional[bool] = False
    timestamp: Optional[Any] = None


@app.post("/webhook")
async def webhook(payload: GatewayPayload):
    print(f"[IN] [{payload.clientId}] {payload.remoteJid}: {payload.text!r}")

    if "@g.us" in payload.remoteJid:
        return {"status": "ignored", "reason": "group"}

    if not payload.text.strip() and not payload.fromMe:
        return {"status": "ignored", "reason": "empty"}

    phone    = payload.remoteJid.split("@")[0]
    intent   = None
    entities = {}

    if not payload.fromMe:
        intent   = triage.detect_intent(payload.text)
        entities = triage.extract_entities(payload.text)
        print(f"   [TRIAGE] intent={intent} | entities={entities}")

    result = session.update_session(
        client_id    = payload.clientId,
        phone        = phone,
        message      = payload.text,
        intent       = intent,
        entities     = entities,
        contact_name = payload.pushName,
        media_type   = payload.mediaType,
        from_me      = payload.fromMe,
    )

    if not result:
        return {"status": "processed", "note": "no reply needed"}

    reply = result.get("reply_message")
    if reply:
        replier.send_text(payload.clientId, payload.remoteJid, reply)
        print(f"   [OUT] → {payload.remoteJid}: {reply[:80]}...")

    return {"status": "processed", "session_state": result.get("status")}


@app.get("/health")
def health():
    return {"status": "ok", "bot": "Bomman Construtora 🏗️"}
