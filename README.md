# SAP 800 — automação de cliques / preenchimento

Projeto para automatizar sequências repetitivas de clique e digitação
(ex.: lançamentos no SAP), com coordenadas mapeadas e dados fixos/variáveis.

## Setup (Windows / PowerShell)

```powershell
cd "caminho\para\sap_800"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se a execução de scripts estiver bloqueada:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Capturar coordenadas do mouse

Com a venv ativa:

```powershell
python tools\mouse_coords.py
```

Aparece uma **barrinha no topo da tela** com `X` e `Y` em tempo real.

| Atalho | Ação |
|--------|------|
| **F8** | Copia `X, Y` para a área de transferência |
| **F9** | Anota no arquivo `tools\coordenadas.txt` |
| **ESC** | Fecha o capturador |

Use isso para ir anotando onde cada clique da sequência deve cair.

## Dependências instaladas

| Pacote | Uso |
|--------|-----|
| `pyautogui` | Clique, digitação, posição do mouse |
| `pynput` / `keyboard` / `mouse` | Escuta/controle fino de input |
| `Pillow` / `mss` / `opencv-python` | Captura e leitura de tela |
| `pytesseract` | OCR (precisa do [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) instalado no Windows) |
| `pyperclip` | Área de transferência |

## Rodar o fluxo completo (Parte 1 → Parte 2)

```powershell
python main.py
```

1. Formulário **Batch** → Parte 1  
2. Em seguida entra na Parte 2 (pausa de 2 s)  
3. No meio da Parte 2: formulário **ISSUER SAP** → 3 s → restante  

Para rodar só uma parte:

```powershell
python parts\parte1.py
python parts\parte2.py
```
