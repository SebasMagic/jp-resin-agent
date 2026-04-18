# JP Resin — Agente Precalificador: Design Spec
**Date:** 2026-04-18  
**Status:** Approved

---

## 1. Resumen

Agente conversacional que recibe leads del ad funnel de JP Resin en GoHighLevel (GHL), calcula un engagement score automático, mueve el contacto en el pipeline según su clasificación y mantiene una conversación personalizada vía SMS, Instagram DM o Facebook Messenger para convertirlos en inscritos al bootcamp de epoxy.

---

## 2. Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Servidor / API | FastAPI (Python) |
| Agente IA | LangChain + DeepSeek (deepseek-chat) |
| Mensajería + CRM | GHL API (PIT token) |
| Calendario de clases | Google Sheets API |
| Hosting | Render |
| Memoria conversacional | LangChain ConversationBufferMemory (por contacto) |

**Credenciales:**
- GHL Location ID: `AWQqYSyxdYeqqhoLc0ef`
- GHL PIT Token: `pit-434e3525-02b4-4960-a9e2-fc3f58d4d0fb`
- Google Sheet: `https://docs.google.com/spreadsheets/d/1p0avMlP5xFm1nWj2CkYD0ream60Ot4ed7qdzdvskqmI`

---

## 3. Engagement Scoring (100 pts)

### Pesos por pregunta del form

| Pregunta | Respuesta | Puntos |
|---|---|---|
| **Investment readiness** (40 pts max) | I'm ready to commit and start ASAP | 40 |
| | Within the next 1-3 months | 25 |
| | In 3-6 months, still planning | 10 |
| | Just gathering info for now | 5 |
| **Main goal** (30 pts max) | Start my own epoxy business and go full-time | 30 |
| | Add epoxy services to my existing business | 25 |
| | Learn as a hobby or side hustle | 10 |
| | Just exploring options right now | 5 |
| **Experience** (10 pts max) | Yes, I do flooring/construction work now | 10 |
| | No, but I'm ready to learn and commit fully | 8 |
| | I've done some DIY projects at home | 6 |
| | No experience at all, just researching | 3 |
| **Location match** (20 pts max) | Estado del lead = estado de clase activa | 20 |
| | No coincide | 0 |

### Clasificación

| Score | Nivel | Pipeline Stage |
|---|---|---|
| 70–100 | 🔥 Hot Lead | `Hot Lead` |
| 40–69 | 🟡 Mid Lead | `Mid Lead` |
| 0–39 | 🧊 Cold Lead | `Cold Lead` |

---

## 4. Pipeline Stages en GHL

```
New Lead → score automático → Hot / Mid / Cold
                                    ↓
                          First Message enviado
                                    ↓
                          In Conversation (agente activo)
                                    ↓
               Call Scheduled / Enrolled / Not Interested
```

| Stage | Descripción |
|---|---|
| `New Lead` | Llega del form, sin score aún |
| `Hot Lead` | Score 70-100 |
| `Mid Lead` | Score 40-69 |
| `Cold Lead` | Score 0-39 |
| `In Conversation` | Agente activo en conversación |
| `Call Scheduled` | Lead agendó llamada con JP |
| `Enrolled` | Pagó e inscrito |
| `Not Interested` | Cerró conversación |

---

## 5. Tool Belt del Agente

| Tool | Acción |
|---|---|
| `score_lead` | Calcula el engagement score con los campos del form |
| `get_classes` | Lee Google Sheet y retorna clases activas (fecha, ciudad, estado, cupos) |
| `move_pipeline` | Mueve el contacto a un stage específico en GHL |
| `send_message` | Envía mensaje al lead vía SMS / Instagram / Facebook Messenger |
| `notify_jp` | Crea tarea en GHL asignada a JP para contacto inmediato |
| `send_payment_link` | Envía link de pago directo al lead |
| `send_calendar_link` | Envía link de calendario de JP para agendar llamada |
| `trigger_workflow` | Activa un workflow en GHL (nurture, follow-up, etc.) |

---

## 6. Flujo de Conversación por Lead Type

### 🔥 Hot Lead

**Primer mensaje** (usa datos del form + clase activa de Google Sheet):
> "Hey [Name]! Saw you're ready to go with epoxy flooring 🔥 We only have **[X] spots left** for our bootcamp in [Ciudad], [Estado] — [Fecha]. Would you like to jump on a quick call with JP personally, or are you ready to lock in your spot right now?"

**Respuesta "hablar con JP":**
→ Tool: `send_calendar_link` → Tool: `move_pipeline` → `Call Scheduled`

**Respuesta "reservar":**
→ Tool: `send_payment_link` → Tool: `move_pipeline` → `Enrolled`

**Sin respuesta en 4h:**
→ Tool: `send_message` (follow-up con más scarcity) → Tool: `trigger_workflow`

---

### 🟡 Mid Lead

**Primer mensaje personalizado por timeline del form:**

| Su respuesta al form | Mensaje |
|---|---|
| Within 1-3 months | "Hey [Name]! You mentioned you're aiming to start within the next few months — what's the one thing that needs to fall into place for you to pull the trigger?" |
| In 3-6 months | "Hey [Name]! You're planning for later this year — is it more about timing, the investment, or just wanting to learn more first?" |
| Just gathering info | "Hey [Name]! No rush at all — what's the biggest question you have about epoxy flooring as a business?" |

**Intención detectada → workflow activado:**

| Señal | Acción |
|---|---|
| Menciona dinero / ROI | `trigger_workflow`: enviar testimonios de ingresos |
| Pregunta sobre la clase | `trigger_workflow`: enviar programa + video del bootcamp |
| Dice que está listo | `notify_jp` + `move_pipeline` → `Hot Lead` |
| Sin respuesta 24h | `trigger_workflow`: follow-up automático |

---

### 🧊 Cold Lead

**Primer mensaje:**
> "Hey [Name]! Thanks for your interest in epoxy flooring. What's the biggest question you have about getting started as a pro?"

**Estrategia:** Secuencia educativa larga. El agente no presiona. Responde dudas, comparte info del negocio de epoxy. Si el lead muestra interés real → re-score y mover a Mid o Hot.

---

## 7. Scarcity — Regla Global

El agente **siempre** menciona escasez cuando hay una clase próxima relevante para el lead:
- Cupos disponibles (dato del Google Sheet)
- Fecha límite de registro
- "JP personally trains every student"

---

## 8. Memoria Conversacional

Cada contacto tiene su propia instancia de `ConversationBufferMemory` en LangChain, inicializada con:
- Nombre, email, teléfono, estado
- Respuestas del form original
- Score calculado
- Stage actual en GHL
- Clase de interés (match por estado)

La memoria se identifica por `contact_id` de GHL y se persiste en un store en disco o base de datos ligera (SQLite en Render).

---

## 9. Flujo de Datos

```
1. Lead llena form en el ad (Facebook/Instagram)
2. GHL recibe lead → dispara webhook POST a FastAPI /webhook/ghl
3. FastAPI parsea: nombre, email, teléfono, estado, respuestas del form
4. Agent Tool get_classes() → lee Google Sheet → retorna clases activas
5. Agent Tool score_lead() → calcula score 0-100
6. Agent Tool move_pipeline() → mueve contacto a Hot/Mid/Cold en GHL
7. Agent Tool send_message() → envía primer mensaje personalizado
8. Lead responde → GHL webhook → FastAPI /webhook/reply
9. LangChain carga memoria del contacto (por contact_id)
10. DeepSeek genera respuesta → decide tools a ejecutar
11. Ciclo continúa hasta: Enrolled / Call Scheduled / Not Interested
```

---

## 10. Endpoints FastAPI

| Endpoint | Método | Descripción |
|---|---|---|
| `/webhook/new-lead` | POST | Recibe nuevo lead del form de GHL |
| `/webhook/reply` | POST | Recibe respuesta de un lead en conversación |
| `/health` | GET | Health check para Render |

---

## 11. Estructura del Proyecto

```
jp-resin-agent/
├── main.py                  # FastAPI app + endpoints
├── agent/
│   ├── agent.py             # LangChain agent setup
│   ├── tools.py             # Tool Belt (score, pipeline, messages, etc.)
│   ├── memory.py            # Conversation memory manager
│   └── prompts.py           # System prompts por lead type
├── services/
│   ├── ghl.py               # GHL API client
│   └── sheets.py            # Google Sheets API client
├── models/
│   └── lead.py              # Pydantic models
├── config.py                # Variables de entorno
├── requirements.txt
└── render.yaml              # Config de deploy en Render
```

---

## 12. Variables de Entorno

```
GHL_PIT_TOKEN=pit-434e3525-02b4-4960-a9e2-fc3f58d4d0fb
GHL_LOCATION_ID=AWQqYSyxdYeqqhoLc0ef
DEEPSEEK_API_KEY=...
GOOGLE_SHEETS_ID=1p0avMlP5xFm1nWj2CkYD0ream60Ot4ed7qdzdvskqmI
GOOGLE_SERVICE_ACCOUNT_JSON=...
```

---

## 13. Clase Activa Actual

| Campo | Valor |
|---|---|
| Nombre | Launch Your Flooring Career: 4-Day Hands-On Epoxy Bootcamp |
| Fechas | Abril 27-30, 2026 |
| Ciudad | Atlanta |
| Estado | Georgia |
| Precio | $2,500 |
| Incluye | JP Academy Cert, Lifetime Online Access, Private Group, Material Discounts, CoLab Partnership |
