<p align="center">
  <img src="https://raw.githubusercontent.com/Nedsonjr10/ChatBot-_Bomman_Construtora/main/docs/logo.png" alt="Bomman Construtora" width="180"/>
</p>
<h1 align="center">Bomman Construtora — WhatsApp Chatbot 🏗️</h1>
 
<p align="center">
  An automated WhatsApp chatbot built for <strong>Bomman Construtora</strong>, designed to qualify leads, route suppliers, and connect customers to human attendants — all through WhatsApp.
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi" />
  <img src="https://img.shields.io/badge/Node.js-Baileys-brightgreen?logo=node.js" />
  <img src="https://img.shields.io/badge/SQLite-sessions-lightgrey?logo=sqlite" />
  <img src="https://img.shields.io/badge/WhatsApp-connected-25D366?logo=whatsapp" />
</p>
---
 
## 📋 Overview
 
This chatbot automates the first contact between **Bomman Construtora** and its customers on WhatsApp. It handles three main flows:
 
- 🏠 **Build or Renovate** — qualifies the customer (new construction or renovation) and collects initial information before routing to a human attendant
- 🤝 **Supplier** — receives supplier portfolio/catalog in PDF and routes to the responsible team
- 👤 **Talk to Attendant** — immediately routes the customer to a human attendant
---
 
## 🤖 Conversation Flow
 
```
User sends any message
        │
        ▼
┌─────────────────────────────────────────┐
│           MAIN MENU                     │
│  1️⃣ Build or Renovate 🏠               │
│  2️⃣ I'm a Supplier 🤝                  │
│  3️⃣ Talk to Attendant 👤               │
└─────────────────────────────────────────┘
        │
   ┌────┴────────────────┐
   ▼                     ▼
Option 1             Option 2 & 3
   │                     │
   ▼                     ▼
┌──────────────┐    ┌─────────────────────┐
│ 1️⃣ New Build │    │ Supplier → ask PDF  │
│ 2️⃣ Renovate  │    │ Attendant → silence │
└──────────────┘    └─────────────────────┘
   │
   ▼
Collects info → AWAITING HUMAN ATTENDANT
```
 
**Special commands (any state):**
- `MENU` or `Olá` → returns to main menu
- `#bot` / `#reset` → attendant returns control to bot
---
 
## 🏗️ Architecture
 
```
bomman-bot/
├── whatsapp-gateway/        # Node.js — Baileys WhatsApp gateway
│   ├── server.js            # Express routes + session management
│   ├── session-manager.js   # Multi-tenant session handler
│   └── db-auth.js           # SQLite auth state for Baileys
│
├── src/                     # Python — Bot logic (FastAPI)
│   ├── main.py              # Entry point
│   ├── config.py            # Environment config
│   ├── api/
│   │   └── webhook.py       # Webhook endpoint receiving messages
│   └── core/
│       ├── session.py       # State machine (conversation logic)
│       ├── triage.py        # Intent detection + entity extraction
│       ├── replier.py       # Sends replies via Node gateway
│       └── database.py      # SQLite session persistence
│
├── data/                    # SQLite session database (gitignored)
├── .env                     # Environment variables (gitignored)
└── ecosystem.config.js      # PM2 process manager config
```
 
---
 
## ⚙️ Tech Stack
 
| Layer | Technology |
|---|---|
| WhatsApp Gateway | Node.js + [@whiskeysockets/baileys](https://github.com/WhiskeySockets/Baileys) |
| Bot Backend | Python 3.13 + FastAPI + Uvicorn |
| Session Storage | SQLite (via better-sqlite3 + Python sqlite3) |
| Intent Detection | Custom keyword ontology (triage.py) |
| Process Manager | PM2 (production deployment) |
 
---
 
## 🚀 Getting Started
 
### Prerequisites
- Python 3.13+
- Node.js 20+
- Git
### 1. Clone the repository
```bash
git clone https://github.com/Nedsonjr10/ChatBot-_Bomman_Construtora.git
cd ChatBot-_Bomman_Construtora
```
 
### 2. Configure environment
Create a `.env` file in the root:
```env
PORT=8000
GATEWAY_URL=http://localhost:3000
WEBHOOK_HOST=127.0.0.1
CLIENT_ID=bomman
IGNORED_NUMBERS=
```
 
### 3. Install dependencies
 
**Python:**
```bash
pip install -r requirements.txt
```
 
**Node.js:**
```bash
cd whatsapp-gateway
npm install
```
 
---
 
## ▶️ Running
 
Open **3 terminals** inside the project root:
 
**Terminal 1 — Python backend:**
```bash
python -m src.main
```
Wait for: `Uvicorn running on http://0.0.0.0:8000`
 
**Terminal 2 — Node gateway:**
```bash
cd whatsapp-gateway
node server.js
```
Wait for: `🚀 Gateway Multitenant rodando na porta 3000`
 
**Terminal 3 — Connect WhatsApp (first time only):**
 
On Windows PowerShell:
```powershell
Invoke-WebRequest -Uri http://localhost:3000/session/connect/bomman -Method POST -UseBasicParsing
```
 
On Linux/Mac:
```bash
curl -X POST http://localhost:3000/session/connect/bomman
```
 
The **QR Code** will appear in Terminal 2. Scan it with your WhatsApp. ✅
 
### Check connection status
```powershell
Invoke-WebRequest -Uri http://localhost:3000/session/status/bomman -UseBasicParsing
```
Should return: `{"status":"open"}`
 
---
 
## 🔄 Restarting (from 2nd time onwards)
 
No QR Code needed — credentials are saved in `whatsapp_auth.db`.
 
```bash
# Terminal 1
python -m src.main
 
# Terminal 2
cd whatsapp-gateway
node server.js
```
 
---
 
## 🛡️ Security Notes
 
The following files are **gitignored** and should never be committed:
- `.env` — contains sensitive config
- `data/` — session database
- `whatsapp-gateway/whatsapp_auth.db` — WhatsApp credentials
- `whatsapp-gateway/auth_info/` — Baileys auth files
---
 
## 👨‍💻 Author
 
Built by **Nedson Jr** for **Bomman Construtora**.
 
---
 
<p align="center">
  <strong>Bomman Construtora 🏗️ — Building dreams, one message at a time.</strong>
</p>
