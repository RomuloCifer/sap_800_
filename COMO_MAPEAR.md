# Como usar este bot em outra máquina

Este guia é para **você** que vai rodar o bot num PC diferente do que foi
programado. As telas têm tamanhos/resoluções diferentes, então os cliques
precisam ser “ensinados” uma vez na **sua** tela.

Depois disso, o uso normal é só `python main.py`.

---

## O que você vai fazer (resumo)

1. Instalar o projeto  
2. Abrir o SAP  
3. Rodar o modo **mapear** (o bot pergunta cada clique)  
4. Em cada passo: ler o nome → colocar o mouse no lugar → apertar **F8**  
5. Quando terminar, usar o bot normalmente  

O mapeamento **roda o fluxo de verdade no SAP** (faz lançamento).  
Use um caso de teste ou um lançamento que você já ia fazer.

---

## 1. Preparar o projeto (só na primeira vez)

1. Receba a pasta do projeto (com o arquivo `mapa_passos.json` dentro).  
2. Abra o **PowerShell** nessa pasta.  
3. Rode:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se aparecer erro de política de scripts:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois, sempre que abrir o PowerShell de novo nesta pasta:

```powershell
.\.venv\Scripts\Activate.ps1
```

(Você deve ver `(.venv)` no início da linha.)

---

## 2. Antes de mapear

- Deixe o **SAP aberto** e no monitor que você vai usar  
- Use a **mesma escala do Windows** que for usar no dia a dia (100%, 125%, etc.)  
- Não mude a resolução no meio do caminho  
- Tenha em mãos os dados do formulário (Batch, material, etc.) — o bot vai pedir  

---

## 3. Mapear os cliques (uma vez)

Com a venv ativa:

```powershell
python main.py --mapear
```

### Em cada clique

1. Aparece uma janela com o **nome do campo** (ex.: `batch`, `botao check`)  
   e às vezes uma **obs** (dica importante — leia!)  
2. **Não clique** no SAP ainda  
3. Só **mova o mouse** até o lugar certo na tela  
4. Aperte **F8**  
5. O bot confirma, grava a posição e **ele mesmo** clica / digita  

Teclas úteis:

| Tecla | O que faz |
|-------|-----------|
| **F8** | Confirma a posição do mouse e continua |
| **F10** | Para tudo (emergência) |

O resultado fica no arquivo `pontos_local.json` (só na sua máquina).

---

## 4. Se der erro no meio

As partes já mapeadas **não se perdem**.

**Continuar de onde parou** (não apaga o que já gravou):

```powershell
python main.py --mapear-resto
```

**Refazer só uma parte** (apaga só essa parte e mapeia de novo):

```powershell
python parts\parte1.py --mapear
python parts\parte2.py --mapear
python parts\parte3.py --mapear
python parts\parte4.py --mapear
```

Ordem das partes no fluxo completo:

1. `parte1`  
2. `apos_parte1` (cópias de Issuer / Invoice / Issue date)  
3. `parte2`  
4. `parte3`  
5. `parte4`  

---

## 5. Depois de mapear — uso normal

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

Não precisa mais do `--mapear`. O bot usa o `pontos_local.json` sozinho.

Só uma parte:

```powershell
python parts\parte1.py
```

---

## Problemas comuns

**O clique cai no lugar errado**  
Refaça só essa parte com `--mapear`. Leia a **obs** do passo — muitas vezes diz
para não clicar no cantinho esquerdo do campo.

**Pareceu no meio e perdi o progresso?**  
Não perdeu. Use `--mapear-resto`.

**Mudei de monitor / resolução / zoom do Windows**  
Precisa mapear de novo (`--mapear`).

**Quero voltar ao zero nesta máquina**  
Apague o arquivo `pontos_local.json` e rode `--mapear` outra vez.

**F10 por acidente**  
O bot para. Rode de novo com `--mapear-resto`.

---

## O que NÃO fazer

- Não rode `--documentar` (isso é só para quem criou o catálogo de nomes)  
- Não apague o `mapa_passos.json`  
- Não compartilhe / não versione o `pontos_local.json` (é da sua tela)  

---

## Resumo dos comandos

| Situação | Comando |
|----------|---------|
| Primeira vez / refazer tudo | `python main.py --mapear` |
| Continuar depois de erro | `python main.py --mapear-resto` |
| Refazer só a parte 2 | `python parts\parte2.py --mapear` |
| Usar o bot no dia a dia | `python main.py` |
| Parar o bot | **F10** |
