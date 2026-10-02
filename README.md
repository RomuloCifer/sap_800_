# SAP 800 — automação de cliques / preenchimento

Automatiza lançamentos repetitivos no SAP (cliques, digitação, validação de valor).

**Qual caminho seguir?**

| Situação | Vá para |
|----------|---------|
| Máquina já mapeada ou a de referência | [1. Setup](#1-setup) → [2. Rodar](#2-rodar) |
| PC novo / outra resolução | [1. Setup](#1-setup) → [3. Mapear uma vez](#3-mapear-uma-vez) → [2. Rodar](#2-rodar) |

Arquivos importantes:

- `mapa_passos.json` — vem com o projeto (nomes dos cliques). **Não apague.**
- `pontos_local.json` — gerado na **sua** máquina com `--mapear`. Não versionar / não compartilhar.

Emergência: **F10** para a automação a qualquer momento.

---

## 1. Setup

```powershell
cd "caminho\para\sap_800"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se scripts estiverem bloqueados:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Sempre que reabrir o PowerShell nesta pasta:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Tesseract (OCR do Total Value)

```powershell
winget install UB-Mannheim.TesseractOCR
```

Feche e abra o PowerShell, depois confira com `tesseract --version`.  
Se não achar o comando, o bot tenta `C:\Program Files\Tesseract-OCR\tesseract.exe`. Sem Tesseract ainda há fallback via clipboard.

---

## 2. Rodar

Coloque a planilha em `entrada/lancamentos.xlsx` (colunas **Batch** e **Total Value**).

```powershell
python main.py
```

O bot lê os batches, pede o tempo de espera e no fim compara o Total Value da planilha com os prints da tela (OCR).

Planilha em outro caminho:

```powershell
python main.py --planilha "C:\caminho\lancamentos.xlsx"
```

Só uma parte:

```powershell
python parts\parte1.py
python parts\parte2.py
```

---

## 3. Mapear uma vez

Em PC novo (ou depois de mudar monitor / resolução / zoom do Windows), os cliques precisam ser ensinados **uma vez**. O mapeamento **roda o fluxo de verdade no SAP** — use um caso de teste.

### Antes

- SAP aberto no monitor que você vai usar
- Mesma escala do Windows do dia a dia (100%, 125%, etc.)
- Dados do formulário em mãos (Batch, material, etc.)

### Como mapear

```powershell
python main.py --mapear
```

Em cada passo: leia o nome/obs → mova o mouse (não clique) → **F8**.  
O bot grava em `pontos_local.json` e executa o clique.

| Situação | Comando |
|----------|---------|
| Primeira vez / refazer tudo | `python main.py --mapear` |
| Continuar depois de erro / F10 | `python main.py --mapear-resto` |
| Refazer só uma parte | `python parts\parte2.py --mapear` |
| Uso no dia a dia (já mapeado) | `python main.py` |

Ordem das partes: `parte1` → `apos_parte1` → `dados_tela` → `parte2` → `parte3` → `parte4`.

| Problema | O que fazer |
|----------|-------------|
| Clique no lugar errado | Refaça a parte com `--mapear`; leia a obs |
| Mudou monitor / resolução / zoom | `--mapear` de novo |
| Quer zerar esta máquina | Apague `pontos_local.json` e rode `--mapear` |

Não rode `--documentar` neste PC — isso é só de quem mantém o catálogo.

---

## 4. Manutenção (máquina de referência)

Documentar nomes/obs dos cliques (atualiza `mapa_passos.json` — **commitar**):

```powershell
python main.py --documentar
```

Capturar coordenadas na tela:

```powershell
python tools\mouse_coords.py
```

| Atalho | Ação |
|--------|------|
| **F8** | Copia `X, Y` |
| **F9** | Anota em `tools\coordenadas.txt` |
| **ESC** | Sai |

---

## Dependências

| Pacote | Uso |
|--------|-----|
| `pyautogui` | Clique, digitação |
| `pynput` / `keyboard` / `mouse` | Input |
| `Pillow` / `mss` / `opencv-python` | Tela / screenshots |
| `pytesseract` | OCR (requer Tesseract no sistema) |
| `pyperclip` | Área de transferência |
