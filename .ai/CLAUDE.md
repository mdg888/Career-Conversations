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

## Stage 2: Refactor & Migration Design — PENDING

*Will be documented here after Stage 1 review and approval.*

---

## Stage 3: Implementation — PENDING

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
| Keep Gradio for chat UI | Low friction, already working | Stage 2 |
| Add FastAPI for admin API | Gradio alone cannot support admin dashboard | Stage 2 |
