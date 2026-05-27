import re
import time
from unidecode import unidecode
from src.core import database
from src.config import IGNORED_NUMBERS, TEST_PREFIX

SESSION_TIMEOUT = 900    # 15 min — fluxo automático
HUMAN_TIMEOUT   = 7200   # 2h    — modo humano

RESET_WORDS = [
    "oi", "ola", "menu", "inicio", "comecar",
    "bom dia", "boa tarde", "boa noite", "start"
]


def normalize(text: str) -> str:
    if not text:
        return ""
    text = unidecode(text).lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return " ".join(text.split())


class SessionManager:
    def __init__(self):
        database.init_db()
        database.prune_old_sessions(120)

    # ─────────────────────────────────────────────────────────────
    # Carrega ou cria sessão
    # ─────────────────────────────────────────────────────────────
    def get_session(self, client_id: str, phone: str) -> dict:
        session = database.get_session(client_id, phone)
        if not session:
            session = {
                "client_id":        client_id,
                "phone":            phone,
                "status":           "MENU",
                "data":             {},
                "history":          [],
                "last_updated":     0,
                "interaction_count": 0,
            }
        return session

    # ─────────────────────────────────────────────────────────────
    # Ponto de entrada principal
    # ─────────────────────────────────────────────────────────────
    def update_session(self, client_id: str, phone: str, message: str,
                       intent: str, entities: dict,
                       contact_name: str = None, media_type: str = "text",
                       from_me: bool = False):

        # Números bloqueados
        if phone in IGNORED_NUMBERS:
            if not message.startswith(TEST_PREFIX):
                print(f"[SESSION] Ignorando número bloqueado: {phone}")
                return None
            message = message[len(TEST_PREFIX):].strip() or "oi"

        session = self.get_session(client_id, phone)

        # Mensagem enviada pelo atendente → silêncio e marca handoff
        if from_me:
            session["status"]       = "AGUARDANDO_HUMANO"
            session["last_updated"] = time.time()
            database.save_session(client_id, phone, session)
            return None

        # Mensagem vazia
        if not message or not message.strip():
            return None

        msg_norm = normalize(message)
        now      = time.time()
        status   = session.get("status", "MENU")
        last_ts  = session.get("last_updated", 0)

        # ── TIMEOUT ──────────────────────────────────────────────
        timeout = HUMAN_TIMEOUT if status == "AGUARDANDO_HUMANO" else SESSION_TIMEOUT
        if last_ts > 0 and (now - last_ts) > timeout:
            print(f"[SESSION] Timeout para {phone}. Resetando.")
            session["status"] = "MENU"
            session["data"]   = {}
            status            = "MENU"

        session["last_updated"] = now
        session["history"].append({
            "ts": now, "role": "user",
            "msg": message, "intent": intent
        })

        # ── RESET GLOBAL ─────────────────────────────────────────
        is_reset = (
            intent == "GREETING" or
            any(w in msg_norm for w in RESET_WORDS) or
            message.strip().lower() in ["menu", "início", "inicio"]
        )
        if is_reset and status not in ("MENU", "AGUARDANDO_ESCOLHA"):
            session["status"] = "MENU"
            session["data"]   = {}
            status            = "MENU"

        # ── COMANDO ADMIN ─────────────────────────────────────────
        if message.strip().lower() in ["#bot", "#reset", "#voltar"]:
            session["status"] = "MENU"
            session["data"]   = {}
            database.save_session(client_id, phone, session)
            return {
                "status":        "MENU",
                "reply_message": "🤖 Controle retornado ao bot. Digite *Olá* para começar.",
                "action":        "ADMIN_RESET"
            }

        # ── HANDLER DE GRATIDÃO (global, exceto modo humano) ─────
        gratitude = [
            "obrigado", "obrigada", "obg", "valeu", "grato",
            "grata", "brigado", "brigada", "joia", "ok", "certo"
        ]
        if status != "AGUARDANDO_HUMANO" and \
           any(w in msg_norm for w in gratitude) and len(message) < 25:
            database.save_session(client_id, phone, session)
            return {
                "status":        status,
                "reply_message": "Disponha! 😊 Se precisar de algo mais é só chamar.",
                "action":        "ACK"
            }

        reply = None

        # ══════════════════════════════════════════════════════════
        # ESTADO: MENU  →  envia boas-vindas
        # ══════════════════════════════════════════════════════════
        if status == "MENU":
            session["status"] = "AGUARDANDO_ESCOLHA"
            reply = (
                "Olá! Tudo bem? 🏗️\n\n"
                "Somos da *Bomman Construtora*, especialistas em realizar o sonho "
                "da sua construção ou reforma!\n\n"
                "Como podemos te ajudar hoje?\n\n"
                "1️⃣ Construir ou Reformar 🏠\n"
                "2️⃣ Sou Fornecedor 🤝\n"
                "3️⃣ Falar com Atendente 👤"
            )

        # ══════════════════════════════════════════════════════════
        # ESTADO: AGUARDANDO_ESCOLHA  →  1ª camada
        # ══════════════════════════════════════════════════════════
        elif status == "AGUARDANDO_ESCOLHA":
            raw = message.strip()

            if raw == "1":
                session["status"] = "CONSTRUIR_OU_REFORMAR"
                reply = (
                    "Excelente escolha! 🌟\n\n"
                    "A Bomman tem a solução perfeita para você.\n"
                    "O que você deseja fazer?\n\n"
                    "1️⃣ Casa do Zero 🏗️\n"
                    "2️⃣ Reforma / Ajustes 🛠️\n\n"
                    "_(Digite MENU para voltar ao início)_"
                )

            elif raw == "2":
                session["status"] = "AGUARDANDO_HUMANO"
                reply = (
                    "Olá! Que bom ter seu contato! 🤝\n\n"
                    "Para darmos continuidade, pedimos que envie aqui o seu *catálogo ou portfólio em PDF* com os produtos/serviços que você fornece.\n\n"
                    "Assim que recebermos, um de nossos responsáveis irá analisar e entrar em contato com você em breve! 😊\n\n"
                    "_(Digite MENU para voltar ao início)_"
                )

            elif raw == "3":
                session["status"] = "AGUARDANDO_HUMANO"
                reply = (
                    "👤 Perfeito! Um de nossos atendentes irá falar com você em breve.\n\n"
                    "⏰ *Horário de atendimento:*\n"
                    "Segunda a Sexta: 8h às 18h\n"
                    "Sábado: 8h às 12h\n\n"
                    "Aguarde, logo te atendemos! 😊\n\n"
                    "_(Digite MENU para voltar ao início)_"
                )

            else:
                opc_construir = (
                    intent in ("CONSTRUIR", "REFORMAR") or
                    any(w in msg_norm for w in [
                        "construir", "reformar", "reforma", "obra", "casa"
                    ])
                )
                opc_fornecedor = (
                    intent == "FORNECEDOR" or
                    any(w in msg_norm for w in [
                        "fornecedor", "catalogo", "parceria"
                    ])
                )
                opc_atendente = (
                    intent == "ATENDENTE" or
                    any(w in msg_norm for w in [
                        "atendente", "humano", "falar"
                    ])
                )

                if opc_construir:
                    session["status"] = "CONSTRUIR_OU_REFORMAR"
                    reply = (
                        "Excelente escolha! 🌟\n\n"
                        "A Bomman tem a solução perfeita para você.\n"
                        "O que você deseja fazer?\n\n"
                        "1️⃣ Casa do Zero 🏗️\n"
                        "2️⃣ Reforma / Ajustes 🛠️\n\n"
                        "_(Digite MENU para voltar ao início)_"
                    )
                elif opc_fornecedor:
                    session["status"] = "AGUARDANDO_HUMANO"
                    reply = (
                        "Olá! Que bom ter seu contato! 🤝\n\n"
                        "Para darmos continuidade, pedimos que envie aqui o seu *catálogo ou portfólio em PDF* com os produtos/serviços que você fornece.\n\n"
                        "Assim que recebermos, um de nossos responsáveis irá analisar e entrar em contato com você em breve! 😊\n\n"
                        "_(Digite MENU para voltar ao início)_"
                    )
                elif opc_atendente:
                    session["status"] = "AGUARDANDO_HUMANO"
                    reply = (
                        "👤 Perfeito! Um de nossos atendentes irá falar com você em breve.\n\n"
                        "⏰ *Horário de atendimento:*\n"
                        "Segunda a Sexta: 8h às 18h\n"
                        "Sábado: 8h às 12h\n\n"
                        "Aguarde, logo te atendemos! 😊\n\n"
                        "_(Digite MENU para voltar ao início)_"
                    )
                else:
                    # Fallback — repete o menu
                    reply = (
                        "Não entendi sua mensagem. 😕\n\n"
                        "Por favor, escolha uma das opções abaixo:\n\n"
                        "1️⃣ Construir ou Reformar 🏠\n"
                        "2️⃣ Sou Fornecedor 🤝\n"
                        "3️⃣ Falar com Atendente 👤\n\n"
                        "_(Digite o número ou MENU para recomeçar)_"
                    )

        # ══════════════════════════════════════════════════════════
        # ESTADO: CONSTRUIR_OU_REFORMAR  →  2ª camada
        # ══════════════════════════════════════════════════════════
        elif status == "CONSTRUIR_OU_REFORMAR":
            raw = message.strip()

            opc_zero = (
                raw == "1" or
                any(w in msg_norm for w in [
                    "zero", "construir", "obra nova", "terreno", "nova"
                ])
            )
            opc_reforma = (
                raw == "2" or
                any(w in msg_norm for w in [
                    "reforma", "reformar", "ajuste", "ajustes", "renovar"
                ])
            )

            if opc_zero:
                session["status"] = "AGUARDANDO_HUMANO"
                reply = (
                    "Incrível! Vamos construir a casa dos seus sonhos! 🏗️\n\n"
                    "Para que nosso time possa te atender melhor, nos conte:\n\n"
                    "• Você já possui um *terreno*?\n"
                    "• Já tem algum *projeto arquitetônico* ou precisa de indicação?\n"
                    "• Em qual *cidade / bairro* pretende construir?\n\n"
                    "Pode mandar tudo aqui! Assim que recebermos, um *atendente da Bomman* já vai falar com você. 😊\n\n"
                    "_(Digite MENU para voltar ao início)_"
                )

            elif opc_reforma:
                session["status"] = "AGUARDANDO_HUMANO"
                reply = (
                    "Ótimo! Vamos deixar tudo ainda mais bonito e funcional! 🛠️\n\n"
                    "Para que nosso time possa te atender melhor, nos conte:\n\n"
                    "• O que pretende *reformar*? (ex: banheiro, cozinha, fachada, toda a casa...)\n"
                    "• Qual a *localidade* do imóvel? (cidade / bairro)\n"
                    "• Tem alguma ideia de *prazo* para início?\n\n"
                    "Pode mandar tudo aqui! Assim que recebermos, um *atendente da Bomman* já vai falar com você. 💪\n\n"
                    "_(Digite MENU para voltar ao início)_"
                )

            else:
                reply = (
                    "Por favor, escolha uma opção:\n\n"
                    "1️⃣ Casa do Zero 🏗️\n"
                    "2️⃣ Reforma / Ajustes 🛠️\n\n"
                    "_(Digite MENU para voltar ao início)_"
                )

        # ══════════════════════════════════════════════════════════
        # ESTADO: AGUARDANDO_HUMANO  →  silêncio
        # ══════════════════════════════════════════════════════════
        elif status == "AGUARDANDO_HUMANO":
            if is_reset:
                # Usuário pediu menu explicitamente → reativa o bot
                session["status"] = "AGUARDANDO_ESCOLHA"
                session["data"]   = {}
                reply = (
                    "Olá! 👋 Voltando ao menu principal.\n\n"
                    "Como podemos te ajudar?\n\n"
                    "1️⃣ Construir ou Reformar 🏠\n"
                    "2️⃣ Sou Fornecedor 🤝\n"
                    "3️⃣ Falar com Atendente 👤"
                )
            else:
                reply = None  # Silêncio total enquanto humano atende

        # ── Fallback geral ────────────────────────────────────────
        else:
            session["status"] = "MENU"
            session["data"]   = {}
            reply = "Digite *MENU* ou *Olá* para começar. 😊"

        database.save_session(client_id, phone, session)

        return {
            "status":        session["status"],
            "reply_message": reply,
            "action":        session["status"],
        }
