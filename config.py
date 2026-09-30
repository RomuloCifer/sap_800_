"""
Configurações de tempo da automação.

Os valores padrão abaixo são usados quando uma parte roda sozinha.
Quando o usuário informa o tempo de espera no formulário da Parte 1,
apply_user_wait() reescreve todos os tempos longos de uma vez.
As esperas curtas entre cliques (~1s) ficam no runner e não são afetadas.
"""

# Valores padrão (usados se a parte rodar sozinha sem o formulário inicial)
COUNTDOWN_START = 5
COUNTDOWN_BETWEEN_PARTS = 2
COUNTDOWN_AFTER_ISSUER = 3
COUNTDOWN_PART3 = 6
COUNTDOWN_PART3_SOLO = 7

WAIT_AFTER_OPEN_SAP = 4.0
WAIT_AFTER_EXECUTE = 3.0
WAIT_BETWEEN_DROPDOWN = 1.5  # Parte 2: intervalo entre os 2 cliques do passo 6
WAIT_AFTER_PART1 = 5.0  # após Parte 1, antes de copiar ISSUER/INVOICE na tela
WAIT_BETWEEN_PART3_PART4 = 5.0  # antes da Parte 4

def apply_user_wait(seconds):
    # type: (float) -> float
    """
    Define o tempo de espera do usuário para todas as esperas longas.
    Ex.: 10 → 10 segundos; 1 → 1 segundo.
    """
    global USER_WAIT
    global COUNTDOWN_START, COUNTDOWN_BETWEEN_PARTS, COUNTDOWN_AFTER_ISSUER
    global COUNTDOWN_PART3, COUNTDOWN_PART3_SOLO
    global WAIT_AFTER_OPEN_SAP, WAIT_AFTER_EXECUTE, WAIT_BETWEEN_DROPDOWN

    s = float(seconds)
    if s <= 0:
        raise ValueError("Tempo de espera deve ser maior que zero.")

    USER_WAIT = s
    WAIT_AFTER_OPEN_SAP = s
    WAIT_AFTER_EXECUTE = s
    WAIT_BETWEEN_DROPDOWN = s

    # Contagens usam segundos inteiros (mínimo 1)
    c = max(1, int(round(s)))
    COUNTDOWN_START = c
    COUNTDOWN_BETWEEN_PARTS = c
    COUNTDOWN_AFTER_ISSUER = c
    COUNTDOWN_PART3 = c
    COUNTDOWN_PART3_SOLO = c

    print("Tempo de espera definido: {}s (esperas longas + contagens)".format(s))
    return s


def parse_wait(text):
    # type: (str) -> float
    """Aceita '10', '1.5' ou '1,5'."""
    cleaned = text.strip().replace(",", ".")
    return float(cleaned)
