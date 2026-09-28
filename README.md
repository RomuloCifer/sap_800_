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

## Rodar a Parte 1

Com a venv ativa e o SAP aberto no monitor da esquerda:

```powershell
python parts\parte1.py
```

1. Abre um formulário pedindo o **Batch number**
2. Contagem de 3 segundos (tempo para focar o SAP)
3. Executa a sequência (espera padrão **0,8 s** entre passos; passo 4 espera **3 s**)

Simulação sem clicar de verdade:

```powershell
python parts\parte1.py --dry-run
```

Abortar emergencialmente: leve o mouse ao **canto superior esquerdo** da tela principal (fail-safe do PyAutoGUI).

## Próximos passos

1. Validar a Parte 1 no SAP real
2. Mapear e implementar a Parte 2 (novo formulário + sequência)
