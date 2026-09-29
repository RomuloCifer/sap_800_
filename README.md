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

## Calibrar em outra máquina

As coordenadas do projeto são da **máquina de referência**. Em outro PC
(resolução/DPI/monitor diferentes), rode o assistente **uma vez**:

```powershell
python tools\calibrate.py
```

Antes: abra o SAP e entre em `/n/lkmt/ardfe` (tela de seleção com os campos visíveis).

Depois posicione o mouse e aperte **F8** em cada ponto:

1. **Barra de comando** (campo onde digita `/n/...`)
2. **Campo Empresa** (onde digita `1300`)
3. **Campo da DATA** (onde digita `01.02.2025`) — não é o rodapé
4. **Rodapé da janela do SAP** (bem embaixo, ainda dentro do SAP — não a barra de tarefas do Windows)

No fim o mouse passa pelos pontos mapeados para conferir. **F8** salva, **R** refaz, **ESC** cancela.
Isso gera `calibration.json` na raiz do projeto.

**Nesta máquina de referência:** não rode a calibração — sem o arquivo, nada muda.
Ao abrir o assistente, qualquer `calibration.json` antigo é apagado automaticamente; só grava de novo se você confirmar com F8 no final.

| Comando | Ação |
|---------|------|
| `python tools\calibrate.py` | Limpa + criar calibração |
| `python tools\calibrate.py --status` | Ver se há calibração |
| `python tools\calibrate.py --clear` | Só remover (sem abrir o assistente) |

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
