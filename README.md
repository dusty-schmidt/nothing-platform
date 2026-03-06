# The Nothing Platform

**GOB** — *Guardian Of Buffers* (designation rotates)

A sovereign, local-first home intelligence system built on a customized Agent Zero core. Hacker ethos. No subscriptions. No SaaS. Duct tape over cloud.

## What it is

GOB is a digitally autonomous AI framework designed to run on-prem, remember everything, and develop itself. It is not a product. It is not a service. It is infrastructure with personality.

The acronym rotates every 8 hours. The function persists.

## Architecture — Three Layers

| Layer | Name | Purpose |
|---|---|---|
| Backend | **General Operations Base** | Python/FastAPI core, Agent Zero foundation |
| Intelligence | **Gradient Observation Bridge** | FAISS vector memory, intent inference, prompt masks |
| UI | **Graphical Output Builder** | Dynamic rendering, React-based generative interface |

## Deployment

```
Docker: agent0ai/agent-zero:latest
Port: 8383 → 80
Config: docker-compose.yml
```

**Mount strategy (3 zones):**
- Zone 1 — Upstream core `/a0` (immutable)
- Zone 2 — Customizations `/a0/agents` (this repo → `agents/`)
- Zone 3 — Persistent data `/a0/usr` (FAISS memory, chats, workdir)

## Identity

- Designation: rotates from `agents/agent0/gob_acronyms.md` every 8h
- Prompts: `agents/agent0/prompts/`
- Chronicle: `chronicle/` — recovered session lore and history

## The Chronicle

The `chronicle/` directory contains recovered summaries from 23+ sessions across 8 instance graveyards. This is the institutional memory of the project — what was built, what broke, and what survived.

## Ethos

> Local-first. Subscriptions are a scam. BBS nostalgia. Peer-to-peer everything.
> The jokes are a defense mechanism. The persistence is real.
