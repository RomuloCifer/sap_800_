"""
Captura automática na tela dos dados das Partes 3 e 4
(material, description, cfop, quantidade, price, protocol, etc.).

Substitui o formulário manual após a Parte 1 no fluxo completo.
"""

from __future__ import annotations

from automation.capture import (
    click_point,
    click_select_all_copy,
    drag_copy,
    drag_only,
)
from automation.forms import validate_random_no
from automation.utils import clean_value, normalize_cfop_prefix


def capture_part34_fields(dry_run=False):
    # type: (bool) -> tuple
    """
    Executa a sequência de cliques/seleções e devolve (doc_data, part4_data).

    doc_data: material, quantidade, price, description, cfop (sem /AA)
    part4_data: protocol_no, proc_date, proc_time, random_no, digit
    """
    print("\n--- Capturando dados das Partes 3/4 na tela ---\n")

    # 1 — Clique
    click_point(-1699, 330, label="dados 3/4 — clique inicial", dry_run=dry_run)

    # 2 — Material
    material = drag_copy(
        -1651, 479, -1785, 477, label="MATERIAL", dry_run=dry_run
    )

    # 3 — Description (Ctrl+A + copiar — texto longo)
    description = click_select_all_copy(
        -1542, 478, label="DESCRIPTION", dry_run=dry_run
    )

    # 4 — CFOP + lógica 5→1 / 6→2 (sem /AA aqui)
    cfop_raw = drag_copy(-1296, 481, -1326, 480, label="CFOP", dry_run=dry_run)
    cfop = normalize_cfop_prefix(cfop_raw)
    print("CFOP ajustado: {!r} → {!r}".format(clean_value(cfop_raw), cfop))

    # 5 — Quantidade
    quantidade = drag_copy(
        -682, 480, -584, 480, label="QUANTIDADE", dry_run=dry_run
    )

    # 6 — Barra de rolagem horizontal (só arrastar)
    drag_only(
        -1457, 917, -1075, 917,
        label="barra rolagem horizontal",
        dry_run=dry_run,
    )

    # 7 — Price
    price = drag_copy(-793, 481, -684, 479, label="PRICE", dry_run=dry_run)

    # 8–10 — Navegação
    click_point(-1757, 121, label="dados 3/4 — clique 8", dry_run=dry_run)
    click_point(
        -1724, 319,
        label="dados 3/4 — clique 9",
        dry_run=dry_run,
        wait_after=0.8,
        wiggle_x=4,
    )
    click_point(
        -1589, 391,
        label="dados 3/4 — clique 10",
        dry_run=dry_run,
        wait_after=1.5,
    )

    # 11–15 — Protocol / datas / random / digit
    protocol_no = drag_copy(
        -1257, 520, -1341, 522, label="PROTOCOL NO", dry_run=dry_run
    )
    proc_date = drag_copy(
        -1195, 520, -1252, 521, label="PROC DATE", dry_run=dry_run
    )
    proc_time = drag_copy(
        -1142, 521, -1189, 521, label="PROC TIME", dry_run=dry_run
    )
    # Random (8) + digit (1) vêm juntos — 9 dígitos; o último é o DIGIT
    random_digit = clean_value(
        drag_copy(-1174, 450, -1132, 450, label="RANDOM NO + DIGIT", dry_run=dry_run)
    )
    digits_only = "".join(ch for ch in random_digit if ch.isdigit())
    if dry_run:
        random_no, digit = "12345678", "9"
    elif len(digits_only) >= 9:
        random_no, digit = digits_only[:8], digits_only[8]
    elif len(digits_only) == 8:
        # fallback raro: só veio o random
        raise RuntimeError(
            "Esperava 9 dígitos (RANDOM + DIGIT), veio 8: {!r}. "
            "Ajuste a seleção na tela.".format(random_digit)
        )
    else:
        raise RuntimeError(
            "Não foi possível separar RANDOM NO e DIGIT a partir de {!r} "
            "(preciso de 9 dígitos).".format(random_digit)
        )
    print("RANDOM NO: {!r}  DIGIT: {!r}".format(random_no, digit))

    # 16 — Clique final + espera 3s
    click_point(
        -1014, 222,
        label="dados 3/4 — clique final",
        dry_run=dry_run,
        wait_after=3.0,
    )

    err = validate_random_no(random_no)
    if err and not dry_run:
        raise RuntimeError("RANDOM NO inválido após captura: {}".format(err))

    doc_data = {
        "material": clean_value(material),
        "quantidade": clean_value(quantidade),
        "price": clean_value(price),
        "description": clean_value(description),
        "cfop": clean_value(cfop),
    }
    part4_data = {
        "protocol_no": clean_value(protocol_no),
        "proc_date": clean_value(proc_date),
        "proc_time": clean_value(proc_time),
        "random_no": random_no,
        "digit": digit,
    }

    print("\nDados capturados da tela:")
    for k, v in doc_data.items():
        print("  {}: {!r}".format(k, v))
    for k, v in part4_data.items():
        print("  {}: {!r}".format(k, v))

    return doc_data, part4_data
