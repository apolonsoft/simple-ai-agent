# Lesson 06: What Actually Blocks the Event Loop

**Pattern:** An `async def` function runs on a single thread shared by *every* request on that worker. Any code that doesn't `await` — CPU work, synchronous I/O, slow object construction — freezes all of them until it finishes. "It's inside an async function" says nothing about whether it's non-blocking.

**Applies to:** Task 08 (Argon2, tools, boto3), Task 17 (bounded reads), Task 19 (MCP discovery)

---

## 1. The bugs in this repo

| Code | Kind | Approximate blocking time |
|---|---|---|
| `password_hash.verify(...)` in `authenticate` | CPU (Argon2 is *designed* to be slow) | tens of ms per call |
| `password_hash.hash(...)` in register / reset / change | CPU | tens of ms |
| `execute_tool("search_web", ...)` → sync `TavilyClient` | Network I/O | 0.5–3 s |
| `execute_tool("create_pdf", ...)` → fpdf | CPU + disk | 10–500 ms |
| `boto3.client("s3", ...)` per request | CPU (loads service JSON models) | ~10–50 ms |

`AGENT.md` describes `security.py` as "Non-blocking". It isn't. Documentation is a claim, not a guarantee.

## 2. Mental model: cooperative scheduling
The event loop runs one coroutine at a time until it hits an `await` on something not ready yet, then switches. Picture 40 SSE streams each emitting a token every 30 ms. One 60 ms Argon2 call means *every* stream stalls for 60 ms. The users see stutter. Under a login burst (10 logins per IP per minute is allowed), the stutter becomes continuous.

```
Thread: [stream A][stream B][argon2 ██████████████][stream A][stream B] ...
                              ↑ every other coroutine waits here
```

### What does NOT block
`await` on asyncpg, redis.asyncio, httpx.AsyncClient, `asyncio.sleep`, and anything else built on non-blocking sockets.

### What DOES block, even in `async def`
- Any sync library that does I/O: `requests`, `boto3`, `smtplib` (correctly offloaded in `EmailService`), sync `TavilyClient`, `open().read()` on big files.
- CPU work: hashing, PDF generation, image processing, large `json.dumps`, regex on huge strings.
- "Construction" that hides work: `boto3.client(...)`, compiling big regexes, loading models.

## 3. The fix options

| Option | When | Note |
|---|---|---|
| `await asyncio.to_thread(fn, *args)` | Sync I/O; C extensions that release the GIL | Default threadpool is shared and bounded; don't flood it |
| Native async library | Long-term for I/O | e.g. `aioboto3`, async Tavily client |
| `ProcessPoolExecutor` | Pure-Python CPU-heavy work | The GIL makes threads useless for pure-Python CPU |
| Plain `def` route | Whole handler is sync | FastAPI runs it in the threadpool automatically |
| Do it once | Expensive setup | Module-level lazy singleton (boto3 client, MCP tool list) |

Argon2 via `argon2-cffi` is C code. Offloading it to a thread keeps the loop responsive. Whether it releases the GIL during hashing decides whether you also get *parallel* hashing. Measure it rather than assume.

## 4. Per-request setup cost is a hidden blocker
```python
def get_user_controller(db = Depends(get_db)) -> UserController:
    return UserController(UserService(db))   # → StorageService() → boto3.client(...)
```
Dependency factories run on every request. Here, `GET /users/me`, which never touches S3, builds an S3 client every time. Ask of every constructor in a dependency: *"what does this do, and does it need to happen per request?"*

The MCP client has the same smell in another form: opening SSE sessions to every MCP server on every chat message just to *list tools* that change only on deploy. Cache it with a TTL (Task 19).

## 5. How to detect blocking
- `PYTHONASYNCIODEBUG=1` plus `loop.slow_callback_duration = 0.05` logs every callback that blocks longer than 50 ms, with a traceback.
- `py-spy dump --pid <uvicorn>` during a load test shows what the loop thread is doing.
- A **loop lag** metric: a background task that sleeps 100 ms and measures how late it wakes up. Export it to your metrics system.
- `make benchmark` while running a login loop in parallel; watch p99 chunk latency.

---

## Exercises
1. Which of these block the loop? (a) `await redis.get(k)` (b) `json.loads(10_MB_string)` (c) `await file.read()` on a `SpooledTemporaryFile` (d) `hashlib.sha256(token).hexdigest()` (e) `settings.SECRET_KEY`
2. Why is `EmailService.send_password_reset_email` already correct, even though it uses `smtplib`?
3. If you wrap Argon2 in `asyncio.to_thread`, what new limit do you hit under a login flood, and is that better or worse than blocking the loop?
4. `execute_tool` is synchronous, but `mcp_client.call_tool` is async. Why does the in-process path even exist, and when does it run in production?
5. Where else in this codebase is something constructed per request that could be constructed once?

---

## Mentor Notes
1. (a) No. (b) **Yes**: CPU proportional to size, around 50 ms or more for 10 MB. (c) Starlette's `UploadFile.read` runs the sync file read in a threadpool, so the loop is fine, *but* the whole content lands in memory, which is Task 17's problem. (d) Technically yes, but microseconds for a 43-character token: irrelevant. (e) No. Judgment matters: don't offload microsecond work, because thread hops cost more than that.
2. It uses `await asyncio.to_thread(self._send_smtp_sync, msg)`. The sync library runs in a worker thread. This file shows the right pattern, so copy it.
3. The default threadpool has a bounded number of workers, around `min(32, cpu_count + 4)` for `asyncio.to_thread`. A login flood queues hashing jobs, so *logins* get slow, but streams keep flowing. That's strictly better: the slowness is isolated to the expensive endpoint, and the rate limiter caps it. For heavy production loads, a dedicated executor caps hashing concurrency explicitly.
4. `AVAILABLE_TOOLS` is the original in-process registry, kept as a fallback when a tool isn't advertised by MCP, which includes the case where the MCP server is down. So in production it runs exactly when something else is already wrong. That's also when you can least afford a blocked loop.
5. `httpx.AsyncClient` per LLM call (`GeminiProvider`, `OllamaProvider`) means a new TLS handshake for every message; a shared client gives connection reuse. Also `get_llm_provider()` per stream (cheap, fine) and `EmailService()` per `AuthController` (cheap, fine). Only the first is worth fixing.

## Review Checklist
- [ ] Any sync I/O or CPU work > ~5 ms inside `async def`?
- [ ] Any expensive object constructed in a per-request dependency?
- [ ] Any "discover/list" call on the hot path that could be cached?
- [ ] Does the service export a loop-lag metric?
