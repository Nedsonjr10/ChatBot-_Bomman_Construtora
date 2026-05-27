import re
from unidecode import unidecode

ONTOLOGY = {
    "intents": {
        "GREETING":   ["oi", "ola", "bom dia", "boa tarde", "boa noite", "menu", "inicio", "comecar", "start"],
        "CONSTRUIR":  ["construir", "construcao", "casa do zero", "obra nova", "quero construir", "1"],
        "REFORMAR":   ["reforma", "reformar", "ajuste", "ajustes", "renovar", "quero reformar", "2"],
        "FORNECEDOR": ["fornecedor", "fornecimento", "catalogo", "portfolio", "parceria", "material", "3"],
        "ATENDENTE":  ["atendente", "humano", "pessoa", "falar com alguem", "quero falar", "4"],
    },
    "entities": {
        "TIPO_SERVICO": {
            "CASA_ZERO": ["casa do zero", "zero", "obra nova", "terreno", "construcao do zero", "nova construcao"],
            "REFORMA":   ["reforma", "reformar", "ajuste", "banheiro", "cozinha", "fachada", "quarto", "sala"],
        }
    }
}


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unidecode(text).lower()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return " ".join(text.split())


class Triage:
    def __init__(self):
        self.ontology = ONTOLOGY

    def detect_intent(self, text: str) -> str:
        normalized = normalize_text(text)
        for intent, keywords in self.ontology["intents"].items():
            for kw in keywords:
                pattern = rf"\b{re.escape(normalize_text(kw))}\b"
                if re.search(pattern, normalized):
                    return intent
        return None

    def extract_entities(self, text: str) -> dict:
        normalized = normalize_text(text)
        found = {}
        for entity_type, mapping in self.ontology["entities"].items():
            for entity_id, keywords in mapping.items():
                for kw in keywords:
                    if normalize_text(kw) in normalized:
                        found[entity_type] = entity_id
        return found
