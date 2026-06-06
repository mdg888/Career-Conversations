# AI Profile Chatbot — Engineering Project Memory

> Authoritative project guide. Update at completion of each stage.
> Last updated: Stage 1 (Repository Audit)

---

## Project Overview

**Goal:** Refactor "Career Conversations" — a single-person chatbot hardcoded for Michael Di Giatnamasso — into a reusable SaaS platform called "AI Profile Chatbot" where any user can upload their own information and generate a chatbot that represents them.

**Working Branch:** `claude/test-coverage-analysis-t2jDU`
**Repository:** `mdg888/career-conversations`

---

## Stage 1: Repository Audit — COMPLETE

### Current File Inventory

```
Career-Conversations/
├── me/
│   ├── profile_summary.pdf      # Michael's LinkedIn PDF (hardcoded)
│   └── summary.txt              # Michael's career summary (hardcoded)
├── src/
│   ├── __init__.py
│   └── app.py                   # Entire application (254 lines, monolithic)
├── database/
│   ├── question_db.py           # PostgreSQL interface
│   ├── schema.sql               # DB schema (single table)
│   └── README.md
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── pytest.ini               # Pytest config
│   └── test_app.py              # Test suite (748 lines)
├── requirements.txt
├── README.md
└── .gitignore
```

### Current Architecture

**Runtime flow:**
1. `src/app.py` loads → reads `me/profile_summary.pdf` and `me/summary.txt` at startup
2. Gradio `ChatInterface` renders a simple chat UI at `http://127.0.0.1:7860`
3. User sends a message → `Me.chat()` builds a system prompt stuffed with the full profile text
4. OpenAI GPT-4o-mini responds; may invoke `record_user_details` or `record_unknown_question` tools
5. Every response is evaluated by a second GPT-4o-mini call; if rejected, a third call regenerates the answer
6. Unknown questions are stored in PostgreSQL and a Pushover push notification is sent

**Dependencies:**
- OpenAI GPT-4o-mini (chat + structured evaluation)
- Gradio (UI framework)
- pypdf (PDF text extraction)
- psycopg2 / PostgreSQL (unknown question storage)
- Pushover API (push notifications)
- pydantic (structured evaluation output)

---

### Hardcoded Personal Dependencies

| File | Line(s) | Hardcoded Element |
|------|---------|-------------------|
| `src/app.py` | 113 | `self.name = "Michael Di Giatnomasso"` |
| `src/app.py` | 116 | `PdfReader("me/profile_summary.pdf")` — literal path |
| `src/app.py` | 124 | `open("me/summary.txt", "r", ...)` — literal path |
| `src/app.py` | 22 | `push()` docstring references "Michael" |
| `src/app.py` | 147–158 | System prompt template hardcoded for Michael |
| `src/app.py` | 163–173 | Evaluator prompt template hardcoded for Michael |
| `README.md` | all | Entirely about Michael Di Giantomasso |

---

### Technical Debt & Architectural Constraints

#### Critical (blocks SaaS refactor)

1. **No RAG / vector store** — The entire profile is dumped raw into the system prompt. This approach:
   - Does not scale beyond ~10–15 pages of text (token limit)
   - Cannot cite sources
   - Cannot be selectively retrieved
   - Cannot support multiple documents

2. **No multi-tenancy** — One chatbot, one person, one hardcoded name. No concept of users, chatbots, or isolated contexts.

3. **No document ingestion pipeline** — No support for file upload, chunking, embedding, or storage abstraction. PDF is read at startup via a hardcoded path.

4. **No admin interface** — No way to configure, upload, or manage chatbot content at runtime.

5. **No chatbot configuration system** — Name, tone, greeting, and fallback message are all embedded in code strings.

#### High (significant risk or maintenance burden)

6. **Module-level side effects on import:**
   - `openai = OpenAI()` (line 16) — initialises OpenAI client at import time; fails without `OPENAI_API_KEY`
   - `question_db = QuestionDB()` (line 19) — instantiates DB class at import time. `QuestionDB.__init__` doesn't connect, but every method will immediately attempt a PostgreSQL connection. This means any test that imports `src.app` and triggers a `record_unknown_question` call will fail without a live database.

7. **`globals().get(tool_name)` for tool dispatch** (line 138) — Security risk. The tool name comes from an OpenAI response; if a malicious or hallucinated tool name matches any global function, it gets called. An attacker who controls the model output could invoke any module-level function.

8. **Two OpenAI clients instantiated** — `openai = OpenAI()` at module level (line 16, never used by the Me class) and `self.openai = OpenAI()` inside `Me.__init__`. The module-level one is only used by `push()`, `record_user_details()`, `record_unknown_question()` — which don't use it at all. It's dead code that still consumes an API key check.

9. **Name collision** — `openai = OpenAI()` (line 16) shadows the `openai` import (line 2). Any code that subsequently tries to use the `openai` module directly would get the client instance instead.

10. **No streaming** — `openai.chat.completions.create()` called with default (non-streaming) mode. Gradio supports streaming; users see nothing until the full response is ready.

11. **Pushover tightly coupled** — Notification logic is embedded directly in `push()`, `record_user_details()`, and `record_unknown_question()`. Cannot be swapped, disabled, or extended.

#### Medium (maintainability and scalability)

12. **`Me` class name** — Semantically tied to one person. Needs to become `Chatbot`, `ProfileBot`, or similar.

13. **No input validation or sanitisation** — No checks on message length, content, or uploaded file types.

14. **No prompt injection protection** — System prompt contents can be exposed if a user crafts a message asking the bot to repeat its instructions.

15. **Evaluation loop overhead** — Every response triggers 2–3 OpenAI API calls (chat + evaluate + optional rerun). At scale this is expensive and slow.

16. **PostgreSQL required at runtime** — There is no fallback if the database is unavailable. A transient DB failure will crash `record_unknown_question`.

17. **No error handling on `push()`** — HTTP failures from Pushover are silently ignored (no logging, no retry).

#### Low (test quality issues)

18. **`TestSystemPrompts` uses wrong patch path** — Lines 337, 355, 373 use `@patch('app.PdfReader')` instead of `@patch('src.app.PdfReader')`. These tests will fail under the current project layout.

19. **No tests for `QuestionDB`** — The database module has zero test coverage.

20. **Tests don't mock `QuestionDB`** — The `record_unknown_question` function calls `question_db.add_question()`. Tests mock `push()` via `@responses.activate`, but `question_db` is a module-level instance. Tests that call `record_unknown_question` would hit a real (or absent) database unless `QuestionDB` is also patched.

21. **No integration tests** — All tests are unit tests with heavy mocking. No end-to-end chat flow is tested.

22. **Missing coverage markers** — pytest.ini defines markers (`unit`, `integration`, `slow`, `api`) but no tests use them.

---

### What the Platform Does Well (Preserve)

- Quality control loop (evaluate + rerun) is a genuinely useful pattern; worth keeping in refactored form
- Tool calling architecture (OpenAI function calling) is solid
- `QuestionDB` API design is clean and extensible
- Test file structure is well-organised, even if some tests have bugs
- `.env`-based configuration is correct

---

### Summary of Scope for Refactor

To turn this into a multi-user SaaS platform the following must be built:

| Area | Current State | Target State |
|------|---------------|--------------|
| Knowledge ingestion | Hardcoded PDF + TXT read at startup | Upload pipeline: TXT, PDF, DOCX, MD, images (OCR) |
| Storage | Files on disk + PostgreSQL for questions | Vector DB (ChromaDB) + file storage per user/chatbot |
| Multi-tenancy | None (single chatbot) | User → Chatbot → Documents hierarchy |
| System prompt | Hardcoded for Michael | Template-driven from `chatbot_config.json` |
| UI | Gradio chat interface | Chat UI + Admin dashboard |
| Notifications | Pushover hardcoded | Configurable notification service |
| Streaming | No | Yes |
| Source citations | No | Yes (RAG retrieval attribution) |
| Configuration | None | Per-chatbot JSON config |
| API design | Monolithic app.py | Service-oriented (ChatService, EmbeddingService, etc.) |
| Security | None | File validation, upload limits, prompt injection protection |

---

## Stage 2: Refactor & Migration Design — COMPLETE (approved)

### Approved Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| UI | FastAPI backend + React frontend | Full SaaS-quality interface, proper admin dashboard |
| Notifications | Removed entirely | Replaced by admin dashboard (view contacts + unknown questions) |
| Vector store (default) | ChromaDB | Local, zero infra, abstractions allow future swap |
| LLM provider | OpenAI GPT-4o-mini | Already integrated, cost-effective |
| Database | SQLite via SQLAlchemy | Zero infra for single-instance; swap path to PostgreSQL via env var |
| Auth | None (v1) | Out of scope; architecture prepared for future addition |

---

### Target Repository Structure

```
Career-Conversations/           ← repo root (preserved name)
├── .ai/
│   └── CLAUDE.md
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── main.py              # FastAPI app + router registration
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── chat.py          # POST /api/chatbots/{id}/chat
│   │   │       ├── chatbots.py      # CRUD /api/chatbots
│   │   │       └── documents.py     # POST /api/chatbots/{id}/documents
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── chat_service.py      # Chat logic (refactored from Me class)
│   │   │   ├── document_service.py  # File parsing + pipeline orchestration
│   │   │   ├── embedding_service.py # Text chunking + OpenAI embeddings
│   │   │   ├── ocr_service.py       # Image → text extraction
│   │   │   ├── vector_store.py      # Abstract VectorStore + ChromaDB impl
│   │   │   └── config_service.py    # Chatbot config load/save
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── chatbot.py           # Pydantic + ORM models for chatbots
│   │   │   ├── document.py          # Pydantic + ORM models for documents
│   │   │   └── chat.py              # Chat request/response models
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py          # SQLAlchemy engine + session factory
│   │   │   └── migrations/          # Alembic migrations
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── config.py            # App-level settings (env vars)
│   │       └── tool_registry.py     # Explicit tool registry (replaces globals())
│   ├── data/
│   │   └── users/
│   │       └── {user_id}/
│   │           └── {chatbot_id}/
│   │               ├── documents/   # Raw uploaded files
│   │               └── chroma/      # ChromaDB persistent collection
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_chat_service.py
│   │   ├── test_document_service.py
│   │   ├── test_vector_store.py
│   │   ├── test_embedding_service.py
│   │   └── api/
│   │       ├── test_chat.py
│   │       ├── test_chatbots.py
│   │       └── test_documents.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   └── SourceCitations.tsx
│   │   │   └── Admin/
│   │   │       ├── Dashboard.tsx
│   │   │       ├── DocumentUpload.tsx
│   │   │       ├── ChatbotSettings.tsx
│   │   │       └── ContactCaptures.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── .env.example
├── .gitignore
└── README.md
```

---

### Database Schema (SQLite via SQLAlchemy, PostgreSQL-compatible)

```sql
-- Chatbots (one per profile / SaaS user in future)
CREATE TABLE chatbots (
    id          TEXT PRIMARY KEY,   -- UUID
    name        TEXT NOT NULL,
    description TEXT,
    tone        TEXT DEFAULT 'professional',
    greeting    TEXT,
    fallback_message TEXT,
    model       TEXT DEFAULT 'gpt-4o-mini',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Documents (each file uploaded to a chatbot)
CREATE TABLE documents (
    id          TEXT PRIMARY KEY,   -- UUID
    chatbot_id  TEXT NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    file_type   TEXT NOT NULL,      -- pdf, txt, md, docx, png, jpg, jpeg, webp, tiff
    file_path   TEXT NOT NULL,      -- path inside data/users/.../documents/
    status      TEXT DEFAULT 'pending',  -- pending | processing | ready | failed
    error       TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions
CREATE TABLE chat_sessions (
    id          TEXT PRIMARY KEY,
    chatbot_id  TEXT NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
    started_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages
CREATE TABLE chat_messages (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,      -- user | assistant
    content     TEXT NOT NULL,
    sources     TEXT,               -- JSON array of source document names
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Contact captures (replaces record_user_details + Pushover)
CREATE TABLE contact_captures (
    id          TEXT PRIMARY KEY,
    chatbot_id  TEXT NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
    email       TEXT NOT NULL,
    name        TEXT,
    notes       TEXT,
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Unknown questions (replaces QuestionDB + Pushover)
CREATE TABLE unknown_questions (
    id          TEXT PRIMARY KEY,
    chatbot_id  TEXT NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
    question    TEXT NOT NULL,
    asked_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### Service Contracts

#### VectorStore (abstract interface)
```python
class VectorStore(ABC):
    def add_documents(self, texts: list[str], metadatas: list[dict], ids: list[str]) -> None: ...
    def query(self, query_text: str, n_results: int = 5) -> list[QueryResult]: ...
    def delete_documents(self, ids: list[str]) -> None: ...
    def reset(self) -> None: ...
```
ChromaDB implements this. Pinecone/Weaviate/Supabase can be added later with no changes to callers.

#### DocumentService
```python
class DocumentService:
    def ingest(self, chatbot_id: str, file_path: Path, file_type: str) -> str:
        # 1. Parse raw text (PDF→pypdf, DOCX→python-docx, MD→plain, images→OCR)
        # 2. Chunk into segments (~500 tokens with 50-token overlap)
        # 3. Embed via EmbeddingService
        # 4. Store in VectorStore under chatbot_id namespace
        # 5. Return document_id
```

#### EmbeddingService
```python
class EmbeddingService:
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def chunk(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]: ...
```
Uses `text-embedding-3-small` (cheaper than ada-002, better quality).

#### ChatService (refactored from Me class)
```python
class ChatService:
    def chat(self, chatbot_id: str, message: str, history: list[dict]) -> ChatResponse:
        # 1. Load chatbot config
        # 2. Retrieve top-k relevant chunks from VectorStore
        # 3. Build dynamic system prompt from template + config + chunks
        # 4. Call OpenAI with tool registry (contact capture + unknown question logging)
        # 5. Evaluate response quality
        # 6. Return ChatResponse with reply + sources
```

#### ToolRegistry (replaces `globals()` dispatch)
```python
TOOL_REGISTRY: dict[str, Callable] = {
    "record_contact": record_contact,
    "record_unknown_question": record_unknown_question,
}
# tool dispatch: TOOL_REGISTRY.get(tool_name) — no globals() risk
```

---

### Dynamic System Prompt Template

```
You are an AI assistant representing {name}.

{description}

Answer questions using only the knowledge base context provided below.
If the answer is not in the context, respond with: "{fallback_message}"

Do not hallucinate or invent information.
Maintain a {tone} tone throughout the conversation.

If the user expresses interest in connecting or getting in touch, ask for
their name and email using the record_contact tool.

## Knowledge Base (retrieved context):
{context}

With this context, assist the user while always representing {name} faithfully.
```

---

### Chatbot Config Format (chatbot_config.json per chatbot)

```json
{
  "chatbot_id": "uuid",
  "name": "Sarah's AI Assistant",
  "description": "Answers questions about Sarah's professional background and projects.",
  "tone": "professional",
  "greeting": "Hi! I'm Sarah's AI assistant. What would you like to know?",
  "fallback_message": "I don't have information about that. Please reach out to Sarah directly.",
  "model": "gpt-4o-mini",
  "max_context_chunks": 5
}
```

---

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chatbots` | Create new chatbot |
| `GET` | `/api/chatbots/{id}` | Get chatbot config |
| `PUT` | `/api/chatbots/{id}` | Update chatbot config |
| `DELETE` | `/api/chatbots/{id}` | Delete chatbot + all data |
| `POST` | `/api/chatbots/{id}/chat` | Send a chat message |
| `GET` | `/api/chatbots/{id}/sessions` | List chat sessions |
| `GET` | `/api/chatbots/{id}/sessions/{sid}/messages` | Get messages in session |
| `POST` | `/api/chatbots/{id}/documents` | Upload a document (multipart) |
| `GET` | `/api/chatbots/{id}/documents` | List documents |
| `DELETE` | `/api/chatbots/{id}/documents/{doc_id}` | Delete a document |
| `POST` | `/api/chatbots/{id}/documents/{doc_id}/rebuild` | Rebuild embeddings for one doc |
| `GET` | `/api/chatbots/{id}/contacts` | List captured contacts |
| `GET` | `/api/chatbots/{id}/unknown-questions` | List unanswered questions |

---

### Migration Strategy (incremental, no big-bang rewrite)

**Phase 1 — Stabilise existing code** *(no new features)*
- Fix broken test patches (`'app.PdfReader'` → `'src.app.PdfReader'`)
- Replace `globals()` tool dispatch with an explicit dict registry
- Move module-level side effects into initialisation functions
- Add missing `QuestionDB` test coverage
- Make current tests pass cleanly

**Phase 2 — Backend foundation**
- Add `backend/` directory structure
- Implement SQLAlchemy models and DB setup
- Implement `VectorStore` abstraction + ChromaDB implementation
- Implement `EmbeddingService` (chunk + embed)
- Implement `DocumentService` (parse PDF, TXT, MD, DOCX, images via OCR)
- Implement `ConfigService` (load/save chatbot_config.json)

**Phase 3 — ChatService**
- Refactor `Me` class logic into `ChatService`
- Replace hardcoded name/paths with config-driven template
- Connect ChatService to VectorStore for RAG retrieval
- Replace Pushover calls with DB inserts (contacts + unknown questions)
- Preserve evaluate + rerun quality-control pattern

**Phase 4 — FastAPI routes**
- Wire up all API endpoints
- Add file upload handling with type validation and size limits
- Add streaming chat endpoint (`StreamingResponse`)

**Phase 5 — React frontend**
- Vite + React + TypeScript scaffold
- Chat interface with streaming display
- Source citations component
- Admin dashboard: upload docs, view contacts, view unknown questions, edit config

**Phase 6 — Data migration**
- Script to migrate `me/profile_summary.pdf` and `me/summary.txt` into a default chatbot
- Confirm existing Gradio demo can be deprecated

---

### Security Requirements (implementation phase)

- File upload: validate MIME type + extension (allowlist only)
- File upload: max size 20 MB per file
- Prompt injection: user messages never interpolated into system prompt template
- Data isolation: chatbot_id scopes all DB queries and filesystem paths
- No `globals()` dispatch — explicit `TOOL_REGISTRY` only
- No secrets in committed files — `.env.example` with placeholders only

---

### Risks Carried Forward

| Risk | Mitigation in design |
|---|---|
| ChromaDB persistence on restart | Use `chromadb.PersistentClient(path=...)` |
| Large document token overflow | RAG chunking limits context to top-k chunks, not full doc |
| OCR quality for low-res images | Warn user on ingest; store raw image alongside extracted text |
| SQLite write contention under load | Acceptable for v1; PostgreSQL swap via `DATABASE_URL` env var |
| React build adds deploy complexity | Vite outputs static files; FastAPI serves them via `StaticFiles` |

---

## Stage 3: Implementation — IN PROGRESS

---

## Stage 4: Testing — PENDING

---

## Stage 5: Code Review — PENDING

---

## Conventions (to be enforced through implementation)

- Python 3.11+
- All services in `src/services/`
- All API routes in `src/api/`
- Data models in `src/models/`
- Configuration in `src/config/`
- Tests mirror source structure in `tests/`
- No business logic in route handlers
- No hardcoded strings — all user-facing text from config
- Secrets via `.env` only, never committed

---

## Risks & Assumptions

| Risk | Severity | Mitigation |
|------|----------|------------|
| OpenAI token limits with large documents | High | RAG chunking + retrieval (not stuffing full docs into prompt) |
| ChromaDB persistence across restarts | Medium | Use persistent client with `path=` parameter |
| PostgreSQL dependency for questions DB | Medium | Consider SQLite fallback or make DB optional |
| Gradio limitations for admin dashboard | High | May need to add FastAPI + separate admin UI |
| Pushover API coupling | Low | Abstract to NotificationService interface |
| `globals()` tool dispatch vulnerability | High | Replace with explicit tool registry dict |
| Test suite has broken patches | Medium | Fix all patch paths before expanding coverage |

---

## Key Decisions Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Use ChromaDB as default vector store | Local, no infra needed, supports abstraction layer | Stage 2 |
| Keep OpenAI as LLM provider | Already integrated, GPT-4o-mini is cost-effective | Stage 1 |
| Switch to FastAPI + React | Full SaaS UI with admin dashboard not possible in Gradio alone | Stage 2 |
| Remove Pushover notifications | Replaced by admin dashboard; reduces external dependencies | Stage 2 |
| Use SQLite (SQLAlchemy) | Zero infra for v1; PostgreSQL-compatible via DATABASE_URL | Stage 2 |
| Use text-embedding-3-small | Better quality than ada-002, lower cost | Stage 2 |
