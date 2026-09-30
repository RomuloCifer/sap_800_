# SAP 800 — automação de cliques / preenchimento

Projeto para automatizar sequências repetitivas de clique e digitação
(ex.: lançamentos no SAP).

## Usar em outra máquina?

Leia o guia: **[COMO_MAPEAR.md](COMO_MAPEAR.md)**  
(passo a passo simples: instalar → mapear com F8 → usar o bot)

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

## Rodar o fluxo (máquina já mapeada ou a de referência)

```powershell
python main.py
```

Emergência: **F10** para a qualquer momento.

Só uma parte:

```powershell
python parts\parte1.py
python parts\parte2.py
```

## Para quem mantém o projeto (máquina de referência)

### Documentar nomes dos cliques

```powershell
python main.py --documentar
```

Gera/atualiza `mapa_passos.json` (por parte). Antes de cada clique: nome + obs.

### Capturar coordenadas

```powershell
python tools\mouse_coords.py
```

| Atalho | Ação |
|--------|------|
| **F8** | Copia `X, Y` |
| **F9** | Anota em `tools\coordenadas.txt` |
| **ESC** | Sai |

## Dependências

| Pacote | Uso |
|--------|-----|
| `pyautogui` | Clique, digitação |
| `pynput` / `keyboard` / `mouse` | Input |
| `Pillow` / `mss` / `opencv-python` | Tela |
| `pytesseract` | OCR (opcional; precisa do Tesseract) |
| `pyperclip` | Área de transferência |
