import requests
from src.config import GATEWAY_URL


class Replier:
    def send_text(self, client_id: str, remote_jid: str, text: str):
        url = f"{GATEWAY_URL}/send-message/{client_id}"
        payload = {"number": remote_jid, "text": text}
        try:
            response = requests.post(url, json=payload, timeout=20)
            if response.status_code == 200:
                print(f"[REPLIER] [{client_id}] ✅ Enviado para {remote_jid}")
            else:
                print(f"[REPLIER] [{client_id}] ❌ Erro {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[REPLIER] [{client_id}] ❌ Falha ao enviar: {e}")
