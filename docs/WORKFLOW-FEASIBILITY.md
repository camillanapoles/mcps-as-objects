# 🧪 Como saber se um novo workflow é POSSÍVEL ou NÃO

> Guia prático: antes de criar um workflow, faça estas perguntas.

---

## 1. O Teste Rápido (3 Perguntas)

Antes de criar qualquer workflow, responda:

```
┌────────────────────────────────────────────────────────────┐
│  PERGUNTA 1                                              │
│                                                          │
│  O workflow precisa de um PROCESSO VIVO que fique        │
│  escutando/esperando conexão depois de rodar?            │
│                                                          │
│  Ex: servidor HTTP, MCP server stdio, WebSocket,         │
│      fila de mensagens, banco aceitando conexão          │
│                                                          │
│  ┌─── SIM → ❌ IMPOSSÍVEL                                │
│  │         (runner morre no fim do job)                  │
│  │                                                      │
│  └─── NÃO → vá para Pergunta 2                          │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│  PERGUNTA 2                                              │
│                                                          │
│  O workflow precisa de interação HUMANA em tempo real?    │
│                                                          │
│  Ex: input() no terminal, CLI interativa,               │
│      confirmação, chat, debugger (pdb)                   │
│                                                          │
│  ┌─── SIM → ❌ IMPOSSÍVEL                                │
│  │         (workflow é headless)                         │
│  │                                                      │
│  └─── NÃO → vá para Pergunta 3                          │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│  PERGUNTA 3                                              │
│                                                          │
│  O workflow precisa de algo que SÓ EXISTE na             │
│  máquina LOCAL (não no runner)?                          │
│                                                          │
│  Ex: GPU, USB, câmera, VPN interna, disco local,        │
│      arquivos do seu PC, dispositivo Bluetooth          │
│                                                          │
│  ┌─── SIM → ❌ IMPOSSÍVEL (a menos que self-hosted)      │
│  │                                                      │
│  └─── NÃO → ✅ POSSÍVEL!                                │
│            (veja a árvore de decisão abaixo)             │
└────────────────────────────────────────────────────────────┘
```

---

## 2. Árvore de Decisão Detalhada

```
NOVA IDEIA DE WORKFLOW
│
├─ Precisa de processo VIVO?
│  ├─ Servidor HTTP/WS escutando → ❌
│  ├─ MCP server stdio (pi-agent) → ❌
│  ├─ Banco esperando conexão → ❌
│  └─ Não → ↓
│
├─ Precisa de interação HUMANA?
│  ├─ input() / pdb / breakpoint → ❌
│  ├─ CLI interativa → ❌
│  ├─ Chat com usuário → ❌
│  └─ Não → ↓
│
├─ Precisa de recurso LOCAL?
│  ├─ GPU / CUDA → ❌
│  ├─ USB / Bluetooth / câmera → ❌
│  ├─ Arquivos do seu PC → ❌
│  ├─ VPN interna / banco on-premise → ❌ (self-hosted contorna)
│  └─ Não → ↓
│
├─ Tempo estimado de execução?
│  ├─ >6 horas → ❌ (hard limit)
│  ├─ 1min ~ 6h → ✅ POSSÍVEL
│  ├─ <1min mas aceita delay de 30s boot → ✅ POSSÍVEL
│  └─ <1min e precisa de resposta rápida → ⚠️ Melhor fazer LOCAL
│
├─ Depende de OS específico?
│  ├─ Windows → ❌ (runner pago)
│  ├─ macOS → ❌ (runner pago)
│  ├─ Android → ❌ (self-hosted)
│  └─ Linux Ubuntu → ✅ POSSÍVEL
│
└─ Resultado: ✅ ou ❌
```

---

## 3. Exemplos Concretos

### ✅ POSSÍVEIS (exemplos reais do projeto)

| Workflow | O que faz | Por que é possível |
|----------|-----------|-------------------|
| `mcp-runtime.yml` | Executa MCPs em batch | Batch, sem processo vivo, sem interação |
| `mcp-single.yml` | Executa 1 MCP específico | Idem, recebe input via `workflow_dispatch` |
| `mcp-validate.yml` | Valida manifestos contra schema | CI puro, <30s, sem estado |
| `mcp-verify.yml` | 15 checks de conformidade | CI puro, <30s, autônomo |
| `mcp-cache.yml` | Reconstrói snapshot | Schedule, batch, sem interação |
| Build wheel (`android-wheel.yml`) | Cross-compila Rust p/ Android | Batch pesado, <5min, Ubuntu tem Rust |

### ❌ IMPOSSÍVEIS (exemplos didáticos)

Cada exemplo abaixo **NÃO funciona** em GitHub Actions. Entenda por quê.

---

#### ❌ Exemplo 1: "Chat MCP via workflow"

```yaml
# ── .github/workflows/chat-mcp.yml ──
# IDEIA: usuário pergunta algo, MCP responde em tempo real
on:
  workflow_dispatch:
    inputs:
      pergunta:
        description: 'Pergunta do usuário'
        required: true

jobs:
  responder:
    runs-on: ubuntu-22.04
    steps:
      - name: Iniciar MCP server para o pi-agent
        run: |
          python -m mcp server.py  # ← Aguarda stdin do pi
          # NUNCA vai funcionar: o pi não consegue se conectar
          # no runner. Não há IP, não há stdio compartilhado.
```

❌ **Motivo**: MCP server precisa de **processo vivo** com `pi` conectado via stdio. Workflow é **headless** e morre.

✅ **Alternativa**: Rodar `server.py` **localmente** — o pi se conecta direto.

---

#### ❌ Exemplo 2: "App Web com formulário"

```yaml
# ── .github/workflows/web-app.yml ──
# IDEIA: workflow sobe um servidor web e usuário acessa
on: workflow_dispatch

jobs:
  server:
    runs-on: ubuntu-22.04
    steps:
      - run: uvicorn app:app --host 0.0.0.0 --port 8080
        # Runner não tem IP público → ninguém acessa
        # Job morre em 6h de qualquer forma
```

❌ **Motivo**: Runner **não aceita conexões de entrada**. Sem DNS, sem IP público.

✅ **Alternativa**: Hospedar em VM/Container fixo, ou usar serviço como Render, Fly.io.

---

#### ❌ Exemplo 3: "Processar vídeo com GPU"

```yaml
# ── .github/workflows/video-gpu.yml ──
# IDEIA: workflow usa GPU para processar vídeo com CUDA
jobs:
  processar:
    runs-on: ubuntu-22.04
    steps:
      - run: nvidia-smi
        # → command not found
      - run: ffmpeg -hwaccel cuda -i video.mp4 ...
        # → ffmpeg até funciona, mas sem aceleração GPU
```

❌ **Motivo**: Runners hosted **não têm GPU**. 

✅ **Alternativa**: Self-hosted runner com GPU, ou serviço de nuvem (RunPod, Lambda Labs).

---

#### ❌ Exemplo 4: "Acessar arquivos do meu PC"

```yaml
# ── .github/workflows/acessar-local.yml ──
# IDEIA: workflow lê arquivos do computador do usuário
jobs:
  ler:
    runs-on: ubuntu-22.04
    steps:
      - run: cat ~/meus-documentos/importante.txt
        # → arquivo não existe (runner é outro computador)
```

❌ **Motivo**: Runner é uma máquina **diferente** — não tem seus arquivos.

✅ **Alternativa**: Fazer upload do arquivo como artifact, ou usar `workflow_dispatch` com input.

---

#### ❌ Exemplo 5: "Digitar senha interativamente"

```yaml
# ── .github/workflows/login.yml ──
# IDEIA: workflow pede senha ao usuário
jobs:
  login:
    runs-on: ubuntu-22.04
    steps:
      - run: |
          echo "Digite sua senha:"
          read -s SENHA  # ← TRAVA AQUI
          echo "Senha: $SENHA"
```

❌ **Motivo**: Workflow não tem **stdin interativo**. O `read` trava até timeout.

✅ **Alternativa**: Usar `GitHub Secrets` ou `workflow_dispatch` com input (mas secreto).

---

#### ❌ Exemplo 6: "Pipeline que dura 8 horas"

```yaml
# ── .github/workflows/treinamento-ia.yml ──
# IDEIA: workflow treina modelo de ML por 8 horas
jobs:
  treinar:
    runs-on: ubuntu-22.04
    steps:
      - run: python treinar.py  # → 8 horas de treinamento
        # → Job é morto às 6 horas
```

❌ **Motivo**: Hard limit de **6 horas**. O job é terminado.

✅ **Alternativa**: Dividir em checkpoints + múltiplos jobs, ou rodar em VM dedicada.

---

#### ❌ Exemplo 7: "Scanner de rede interna"

```yaml
# ── .github/workflows/scan-rede.yml ──
# IDEIA: workflow escaneia dispositivos na rede da empresa
jobs:
  scan:
    runs-on: ubuntu-22.04
    steps:
      - run: nmap -sn 192.168.0.0/24
        # → Não acessa a rede da empresa
        # → Só vê a rede do datacenter da Microsoft
```

❌ **Motivo**: Runner está na **rede do GitHub**, não na sua rede local/VPN.

✅ **Alternativa**: Self-hosted runner dentro da rede, ou API local.

---

#### ❌ Exemplo 8: "Servidor de fila (WebSocket)"

```yaml
# ── .github/workflows/fila.yml ──
# IDEIA: workflow mantém WebSocket aberto para mensagens
jobs:
  fila:
    runs-on: ubuntu-22.04
    steps:
      - run: python -m websockets server.py
        # → WebSocket aberto enquanto job roda
        # → Ninguém consegue conectar (sem IP público)
        # → Job morre em 6h
```

❌ **Motivo**: Sem ingress + sem long-running.

✅ **Alternativa**: Serviço de fila externo (Redis, RabbitMQ, SQS).

---

## 4. Checklist Rápido Para Qualquer Ideia

```
Antes de criar um workflow, marque:
─────────────────────────────────────
□ O workflow termina sozinho? (sem processo vivo)
□ Não precisa de input humano durante execução?
□ Só precisa do que já está no checkout + internet?
□ Cabe em <6 horas?
□ Roda em Ubuntu amd64?
□ Não precisa de GPU/USB/hardware específico?
□ Não precisa receber conexão de fora?
□ Não precisa de arquivos da minha máquina?

Se TODOS ✅ → POSSÍVEL
Se algum ❌  → Analise alternativa abaixo
              - Self-hosted runner
              - API local
              - Serviço externo
              - Dividir em etapas
```

---

## 5. Estratégias Para Contornar Limitações

| Limitação | Contorno |
|-----------|----------|
| Precisa de processo vivo | RODAR LOCAL (`server.py`, API) |
| Precisa de GPU | Self-hosted runner com GPU |
| Precisa de rede interna | Self-hosted runner na rede |
| Precisa de >6h | Dividir em jobs com checkpoint |
| Precisa de Windows | Usar `act` local ou self-hosted |
| Precisa de resposta rápida | API local (:8712) + workflow para parte pesada |
| Precisa de arquivos locais | Upload como input/artifact |
| Precisa de Android/iOS | Build cross-compilado + teste local |
