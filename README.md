# 🏥 Emergency Hospital Resource Optimizer (EHODR)

EHODR is a full-stack, disaster-response decision-support platform combining a **Quantum-Inspired optimization engine**, a **Universal AI Memory System (UAMS)** backend, **real-time GIS routing**, and **three role-specific HTML command dashboards** — all built to SDG 3 (Good Health & Well-being) standards.

---

## 🚀 System Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                 EHODR Platform — High-Level View                  │
├─────────────────────────────┬─────────────────────────────────────┤
│  🖥️ Streamlit Dashboard      │  🌐 HTML Command Dashboard Hub       │
│  app_enhanced.py            │  dashboards/index.html              │
│  · Multi-solver optimizer   │  ├── ambulance.html                 │
│  · Live triage registrar    │  ├── guardian.html                  │
│  · GIS real-time map        │  └── er-command.html                │
│  · EOC Advisor chatbot      │                                     │
└────────────┬────────────────┴──────────────┬──────────────────────┘
             │                               │
             ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│            Universal AI Memory System (UAMS) Backend            │
│                     gateway/ — FastAPI v2.0                     │
│  /v1/memories  /v1/chat  /v1/health  (port 8000)               │
│  · Structured Logging · Rate Limiting · Prometheus /metrics     │
├──────────────┬───────────────────────┬──────────────────────────┤
│  PostgreSQL  │   Qdrant v1.18.0      │   Redis 7                │
│  (memories   │   (vector semantic    │   (session cache &       │
│  metadata)   │    search index)      │    rate limit state)     │
└──────────────┴───────────────────────┴──────────────────────────┘
```

---

## 📂 Complete Project Directory Structure

```text
EHODR/
│
├── app_enhanced.py              # Main Streamlit dashboard & all solver engines
│
├── dashboards/                  # Standalone HTML role dashboards (served on :8080)
│   ├── index.html               # Command Hub — entry point with 3 role tiles
│   ├── ambulance.html           # Paramedic cockpit: vitals, nav, hospital readiness
│   ├── guardian.html            # Family-facing tracker: ETA, secure chat, forms
│   ├── er-command.html          # ER Command: incoming units, capacity, regional map
│   └── shared/
│       ├── ehodr-base.css       # Material Design 3 token CSS design system
│       ├── ehodr-theme.js       # Dynamic theme + color token loader
│       └── nav.js               # Cross-dashboard navigation switcher bar
│
├── gateway/                     # Universal AI Memory System (UAMS) FastAPI Backend
│   ├── main.py                  # FastAPI app factory, lifespan, middleware stack
│   ├── config.py                # Pydantic settings from .env
│   ├── dependencies.py          # Shared DI: get_db, get_qdrant, get_redis
│   ├── Dockerfile               # Production Docker image build
│   ├── requirements.txt         # Gateway-specific Python dependencies
│   ├── api/v1/
│   │   ├── router.py            # v1 API router aggregator
│   │   ├── memory.py            # POST /memories, GET /memories/search
│   │   ├── chat.py              # POST /chat — LLM-assisted memory recall
│   │   └── health.py            # GET /health — liveness & dependency checks
│   ├── core/
│   │   ├── embedding.py         # Pluggable embedding provider (OpenAI / local)
│   │   ├── ranking.py           # Semantic importance re-ranker
│   │   ├── deduplication.py     # Cosine similarity dedup filter
│   │   ├── compression.py       # Memory content compressor
│   │   └── security.py          # API key auth & HMAC verification
│   ├── db/
│   │   ├── models.py            # SQLAlchemy ORM memory model
│   │   ├── postgres.py          # Async SQLAlchemy engine factory
│   │   ├── qdrant_client.py     # Qdrant collection manager & vector ops
│   │   └── redis_client.py      # Redis async client & TTL cache helpers
│   ├── middleware/
│   │   ├── logging.py           # Structured JSON logging middleware
│   │   ├── rate_limit.py        # 100 req/60 s sliding-window rate limiter
│   │   └── error_handler.py     # Global exception → JSON error response
│   └── schemas/
│       ├── memory.py            # Pydantic schemas: MemoryCreate, MemoryRead
│       └── chat.py              # Pydantic schemas: ChatRequest, ChatResponse
│
├── agents/
│   └── memory_client.py         # Python client SDK: UniversalMemoryClient.save/recall
│
├── scripts/
│   ├── init_qdrant_collections.py  # One-shot Qdrant collection bootstrap
│   ├── mcp_server.py               # JSON-RPC 2.0 MCP server (Claude/AI tool use)
│   ├── validate_spec.py            # OpenSpec conformance validator
│   ├── watch_edits.py              # File watcher for live spec drift detection
│   └── backup_qdrant.sh            # Qdrant snapshot backup shell script
│
├── openspec/design/
│   └── system_architecture.md      # Authoritative system blueprint (OpenSpec)
│
├── nginx/
│   └── nginx.conf                  # Reverse proxy config for production
│
├── docker-compose.yml              # Full production stack: gateway + qdrant + postgres + redis
├── docker-compose.override.yml     # Local dev port overrides
├── requirements.txt                # Dashboard Python dependencies (pip install -r)
├── .env                            # Active secrets (not committed)
├── .env.example                    # Environment variable reference template
│
├── run_all.ps1                     # ⭐ Full stack launcher (Docker + deps + Streamlit)
├── run_all.bat                     # Windows CMD equivalent
├── run_command_dashboards.ps1      # Launches HTML dashboards on :8080
├── run_command_dashboards.bat      # Windows CMD equivalent
├── run_dashboard.ps1               # Streamlit-only shortcut
├── run_dashboard.bat               # Windows CMD equivalent
├── kill_all.ps1                    # Terminates all active processes
├── kill_all.bat                    # Windows CMD equivalent
│
├── Explainer.md                    # Plain-language user guide
├── testing.md                      # Interactive test cases & diagnostic scenarios
├── FUTURE.md                       # Engineering roadmap & scaling blueprint
└── pytest.ini                      # Test runner configuration
```

---

## ⚙️ Core Solver Paradigms

Three distinct algorithmic pathways are implemented in [`app_enhanced.py`](file:///c:/codingprojects/EHODR/app_enhanced.py). All three share an identical **QUBO Hamiltonian** formulation.

| Solver | Scale | Speed | Library |
|---|---|---|---|
| **Exact Classical (Brute Force)** | ≤ 6 patients | Slow (exponential) | Pure Python |
| **Simulated Annealing (Quantum-Inspired)** | Any scale | < 0.1 sec | `simanneal` |
| **QAOA (Quantum)** | ≤ 18 qubits | 5–15 sec (CPU sim) | `qiskit`, `qiskit-algorithms` |

**Auto-routing**: If QAOA is selected but the grid requires > 18 qubits (≥ 6 patients × 3 hospitals), the system automatically redirects to Simulated Annealing to prevent memory exhaustion, displaying the exact RAM cost of the blocked simulation.

---

## 📐 Mathematical Formulation (QUBO Hamiltonian)

All solvers minimize the same energy function. Let $x_{p,h} \in \{0,1\}$ denote assigning patient $p$ to hospital $h$:

$$H = A \sum_{p} \left( \sum_{h} x_{p,h} - 1 \right)^2 + B \sum_{h} \text{Penalties}(x_{p,h}) + \sum_{p,h} (\text{Severity}_p \times \text{Distance}_{p,h})\, x_{p,h}$$

| Term | Role |
|---|---|
| **Term A** | Penalizes states where a patient is assigned to zero or multiple hospitals |
| **Term B** | Penalizes violations of ICU bed, ventilator, and medical staff capacities |
| **Objective** | Minimizes severity-weighted transport distance |

---

## 🎨 Streamlit Dashboard Features

### Scenario Modes
- **Manual Config**: Slider-driven patient/hospital counts with random distance matrices
- **Mass Casualty Preset**: 10 patients, 3 hospitals, restricted bed supply
- **Pandemic Surge Preset**: 12 patients, 3 hospitals, ventilator bottleneck stress
- **Earthquake Preset**: 8 patients, 2 hospitals, proximity-critical routing
- **📝 Live Patient Registrar**: Interactive intake form — type name, age, symptoms → ESI score auto-calculated → UAMS memory sync optional

### 🌍 Real-Time GIS Dispatch Map
Three Indian city presets with real hospital geocoordinates, OSRM live road routing, and interactive Folium map:

| Preset | City | Hospitals |
|---|---|---|
| Bangalore Metro Triage | Bangalore, KA | NIMHANS, Fortis Bannerghatta, Manipal Old Airport Rd |
| Kerala Kochi Flood | Kochi, KL | Aster Medcity, Amrita Edappally, Medical Trust |
| Chennai Cyclone Surge | Chennai, TN | Apollo Greams Rd, MIOT International, Fortis Malar |

- Markers color-coded by hospital saturation (green < 70% / orange < 85% / red ≥ 85%)
- Patient circles color-coded by severity (🔴 Critical / 🟡 Urgent / 🟢 Stable)
- OSRM polylines show actual road paths; Haversine fallback used offline

### Advanced Constraints
- **Doctor Specialties**: Severity-3 patients hard-routed to H1 (trauma center)
- **Transit Time Windows**: Routes > 15 km incur additional objective penalty

### Visualization & Reporting
- **Allocation Results Table**: Patient → Hospital assignments with severity and distance
- **Distance Heatmap**: `severity × distance` matrix (float-formatted, registered patient names on y-axis)
- **Bed Allocation Chart**: Bar chart comparing allocations vs. capacity per hospital
- **QAOA Convergence Plot**: Energy descent across circuit layers (reps)
- **🔬 Quantum Formulation Tab**: Rendered Hamiltonian math + live 3-qubit QAOA ansatz circuit diagram
- **CSV Export**: One-click download of full allocation directory

### 🤖 Floating EOC Command Advisor Chatbot
- Draggable floating bubble (JavaScript `mousemove` + `sessionStorage` position persistence)
- Integrates with local Ollama LLM for contextual routing analysis
- **Offline fallback**: Rule-based deterministic diagnostic engine analyzes bottlenecks, saturation, and routing justifications without internet or LLM

---

## 🌐 HTML Command Dashboard Hub

Standalone multi-role interface at `http://localhost:8080` — no Streamlit required.

| Dashboard | URL | Audience |
|---|---|---|
| **Command Hub** | `/index.html` | Entry point — role selector |
| **Ambulance Command** | `/ambulance.html` | Paramedic: Unit 704 cockpit, vitals, hospital readiness |
| **Guardian Portal** | `/guardian.html` | Family: ambulance ETA, journey timeline, secure chat |
| **ER Command Center** | `/er-command.html` | Hospital: incoming units, capacity monitor, regional map |

Built with Material Design 3 tokens (`ehodr-base.css`), Inter/Plus Jakarta Sans fonts, and a shared navigation bar (`nav.js`).

---

## 🧠 Universal AI Memory System (UAMS)

The UAMS backend (`gateway/`) provides persistent semantic memory for AI agents.

| Component | Technology | Purpose |
|---|---|---|
| FastAPI Gateway | Python / Uvicorn | REST API + WebSocket server (port 8000) |
| PostgreSQL 15 | `asyncpg` / SQLAlchemy | Structured memory metadata & relational records |
| Qdrant v1.18.0 | Vector DB | Semantic similarity search across stored memories |
| Redis 7 | In-memory cache | Session state, rate limit counters, TTL caching |
| Prometheus | `/metrics` endpoint | Latency, request rate, error rate observability |

### API Endpoints
```
GET  /                        → Redirects to /docs (Swagger UI)
GET  /v1/health               → Service liveness + dependency status
POST /v1/memories             → Store a new memory
GET  /v1/memories/search      → Semantic recall by query
POST /v1/chat                 → LLM-assisted context retrieval
GET  /metrics                 → Prometheus scrape endpoint
```

### MCP Server (`scripts/mcp_server.py`)
JSON-RPC 2.0 stdio server exposing UAMS as Model Context Protocol tools for Claude and other AI agents:
- `memory_recall` — semantic search across stored memories
- `memory_save` — persist insight / decision / knowledge
- `validate_architecture_spec` — conformance check against OpenSpec blueprint

---

## 🛠️ Quick Start

### Prerequisites
- **Docker Desktop** (for UAMS backend services)
- **Python 3.10+** with the `venv` created at `./venv/`

### 1. Configure Environment
```powershell
Copy-Item .env.example .env
# Edit .env to set POSTGRES_PASSWORD, API_SECRET_KEY, OPENAI_API_KEY, etc.
```

### 2. Launch Full Stack (Recommended)
Starts Docker services, installs Python dependencies, initializes Qdrant collections, and launches Streamlit — all in one command:
```powershell
.\run_all.ps1
```

The Streamlit dashboard will be available at **http://localhost:8501**.

### 3. Launch HTML Command Dashboards (Optional)
```powershell
.\run_command_dashboards.ps1
```
Opens at **http://localhost:8080**.

### 4. Streamlit Only (No Docker)
For dashboard-only usage without the UAMS backend:
```powershell
.\run_dashboard.ps1
```

### 5. Install / Update Python Dependencies
```powershell
.\venv\Scripts\pip install -r requirements.txt
```

### 6. Run Tests
```powershell
.\venv\Scripts\python -m pytest
```

### 7. Stop All Processes
```powershell
.\kill_all.ps1    # PowerShell
kill_all.bat      # Windows CMD
```

---

## 🔧 Key Technical Notes

> [!NOTE]
> **Streamlit Signal Patching**: `simanneal` registers `SIGINT` handlers on init. Since Streamlit runs scripts in worker threads, this raises `ValueError`. EHODR monkeypatches `signal.signal` at startup to silently skip non-main-thread registrations.

> [!NOTE]
> **QAOA Memory Safety**: Statevector simulation scales as $2^n$ complex amplitudes. The QUBO for $n$ patients × $h$ hospitals uses $n \times h$ qubits. The system hard-caps at 18 qubits and displays exact RAM cost before auto-routing to Simulated Annealing.

> [!NOTE]
> **GIS Routing Fallback**: Real road routes are fetched from the public OSRM API (`router.project-osrm.org`). If the API is unreachable (offline/timeout), the Haversine formula with a 1.3× circuity factor and 30 km/h average speed is used as a graceful fallback.

> [!NOTE]
> **Qdrant Compatibility**: The project targets Qdrant v1.7.x–v1.18.x. `init_qdrant_collections.py` uses `PayloadSchemaType.KEYWORD` (not `DATETIME`) for the `created_at` field to maintain backward compatibility with v1.7.4.

---

## 📚 Reference Documentation

| Document | Purpose |
|---|---|
| [Explainer.md](file:///c:/codingprojects/EHODR/Explainer.md) | Plain-language guide: how severities, costs, and solvers work |
| [testing.md](file:///c:/codingprojects/EHODR/testing.md) | Test cases: mass casualty, pandemic surge, specialty routing, feasibility failures |
| [FUTURE.md](file:///c:/codingprojects/EHODR/FUTURE.md) | Roadmap: multi-stage simulation, vehicle dispatch, IBM QPU execution |
| [openspec/design/system_architecture.md](file:///c:/codingprojects/EHODR/openspec/design/system_architecture.md) | Authoritative OpenSpec blueprint for all services and API contracts |

---

*Built for the Quantum Disaster Response Hackathon 2026 | SDG 3: Good Health & Well-being | Qiskit QAOA × Simulated Annealing × UAMS*
