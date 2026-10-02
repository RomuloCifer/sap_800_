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

### Tesseract OCR (obrigatório para validação de valor)

A checagem de **Total Value** (prints na tela) usa OCR via `pytesseract`.
Além do `pip install`, é preciso instalar o **motor Tesseract** no Windows:

```powershell
winget install UB-Mannheim.TesseractOCR
```

Depois do install, **feche e abra** o PowerShell (para atualizar o PATH) e confira:

```powershell
tesseract --version
```

Se o comando não for encontrado, o bot ainda tenta o caminho padrão
`C:\Program Files\Tesseract-OCR\tesseract.exe` (instalação via winget).
Se mesmo assim falhar, adicione essa pasta ao PATH ou reinicie o PC.

Sem o Tesseract, o bot ainda tenta ler o valor via clipboard (fallback),
mas o OCR é o caminho recomendado.

Se a execução de scripts estiver bloqueada:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Rodar o fluxo (máquina já mapeada ou a de referência)

Coloque a planilha em `entrada/lancamentos.xlsx` (colunas **Batch** e **Total Value**).

```powershell
python main.py
```

O bot lê os batches da planilha, pede só o tempo de espera, e no fim compara
Total Value da planilha com os dois prints da tela (OCR).

Planilha em outro caminho:

```powershell
python main.py --planilha "C:\caminho\lancamentos.xlsx"
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
| `Pillow` / `mss` / `opencv-python` | Tela / screenshots |
| `pytesseract` | OCR (requer **Tesseract** no sistema — ver setup acima) |
| `pyperclip` | Área de transferência |
