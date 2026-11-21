# Lesson 09: Trusting Infrastructure — Headers, Proxies and Config

**Pattern:** Some inputs *look* like infrastructure (proxy headers, environment defaults, URLs to third-party APIs) and get trusted as if they came from your own systems. Any header can be set by any client, a default value is a production value until proven otherwise, and a URL is something that gets logged.

**Applies to:** Task 09 (X-Forwarded-For), Task 10 (SECRET_KEY), Task 21 (Gemini key in URL)

---

## 1. The bugs in this repo

```python
# apps/api/app/core/rate_limiter.py
forwarded = request.headers.get("X-Forwarded-For")
if forwarded:
    client_ip = forwarded.split(",")[0].strip()   # first entry = whatever the client typed
```

```python
# apps/api/app/core/config.py
SECRET_KEY: str = "CHANGE_THIS_TO_A_SUPER_SECRET_RANDOM_KEY_IN_PRODUCTION"
```

```python
# apps/api/app/providers/gemini_provider.py
url = f"...:streamGenerateContent?alt=sse&key={self.api_key}"
```

## 2. X-Forwarded-For: who wrote each entry?
A request through one proxy arrives as:
```
X-Forwarded-For: <whatever the client sent>, <client IP as seen by proxy>
```
Proxies **append**. The leftmost entry is attacker-controlled; only the entries added by *your own* proxies can be trusted. The rate limiter takes the leftmost, so sending `X-Forwarded-For: 1.2.3.<n>` with a new `n` each request gives a fresh rate-limit bucket every time: unlimited login attempts.

### The correct division of labor
The ASGI server already knows how to do this safely:
```bash
uvicorn app.main:app --proxy-headers --forwarded-allow-ips="10.0.0.5"
```
uvicorn rewrites `request.client.host` from the header **only** when the TCP peer is a listed proxy. Application code then uses `request.client.host` and never parses the header. Never set `--forwarded-allow-ips="*"` on a port the internet can reach directly.

To configure this correctly you need to know your topology: how many proxies, which IPs, and whether the edge proxy overwrites or appends. That's why the spec lists it as an open question.

## 3. Secure defaults: fail fast on dangerous config
A default `SECRET_KEY` means a forgotten env var in production lets anyone mint valid JWTs for any user ID. The app shouldn't *start* in that state:

```python
@model_validator(mode="after")
def _require_strong_secret(self):
    if self.ENVIRONMENT not in {"development", "development_debug", "test"} and (
        self.SECRET_KEY == _DEFAULT_SECRET_KEY or len(self.SECRET_KEY) < 32
    ):
        raise ValueError("SECRET_KEY must be set ...")
    return self
```
General rule: **the dangerous configuration must be the one that requires effort**. Dev convenience defaults are fine only if production refuses to boot with them. The same thinking applies to `S3_ACCESS_KEY="any"`, `CORS_ORIGINS`, and `ENVIRONMENT` defaulting to `development`. That last one is subtle: if production forgets `ENVIRONMENT`, the guard thinks it's dev. Consider requiring `ENVIRONMENT` explicitly in deployed environments.

## 4. Secrets in URLs
Query strings are logged by default: httpx at INFO ("HTTP Request: POST https://...?key=AIza..."), proxies, APM tools, and exception messages that include the URL. Google's API accepts `x-goog-api-key` as a header, so use it. The same principle covers JWTs in `?token=` (Lesson 07).

## 5. CORS: what's actually right here
For contrast, here's something that's **fine**:
```python
allow_origins=settings.CORS_ORIGINS,   # explicit list
allow_credentials=True,
allow_methods=["*"], allow_headers=["*"],
```
- Explicit origins plus credentials is the correct pairing. Browsers forbid `*` with credentials anyway.
- Auth uses `Authorization: Bearer` from `localStorage`, not cookies, so CSRF via CORS isn't the main risk. XSS is, which is why the markdown pipe's sanitization matters.
- Wildcard methods and headers are acceptable with a tight origin list.

Knowing what *not* to flag is as important as knowing what to flag.

---

## Exercises
1. Your production setup is Cloudflare → nginx → uvicorn. What should `--forwarded-allow-ips` be, and which hop's view of the client IP do you want?
2. Besides rate limiting, where else would a spoofable client IP cause harm in a typical app?
3. The `SECRET_KEY` guard trusts `ENVIRONMENT`. Design a guard that doesn't depend on someone remembering to set it.
4. Is HS256 with a strong secret acceptable here, or should you move to RS256/EdDSA? What would change your answer?
5. Find another default in `config.py` that's dangerous in production, and say how you'd guard it.

---

## Mentor Notes
1. uvicorn's peer is nginx, so `--forwarded-allow-ips=<nginx IP>`. nginx should itself trust only Cloudflare's published ranges (`set_real_ip_from` + `real_ip_header CF-Connecting-IP`) and forward a clean `X-Forwarded-For`. You want Cloudflare's view: the real client. Every hop must trust only the hop before it.
2. Audit logs ("login from IP X"), geo-blocking, IP allowlists for admin panels, fraud scoring, and "new device" notifications. Anything that makes a security decision on IP.
3. Invert it: require an explicit `ENVIRONMENT` with no default, *or* refuse the default key unless `ALLOW_INSECURE_DEV_DEFAULTS=true` is set. Developers opt into insecurity, and production can't fall into it by omission.
4. HS256 is fine when **one service** both issues and verifies tokens. Move to asymmetric keys when other services need to *verify* tokens without being able to *mint* them (microservices, third parties), or when you want key rotation through a JWKS endpoint.
5. `S3_ACCESS_KEY="any"` / `S3_SECRET_KEY="any"`: harmless with SeaweedFS in dev, but dangerous if production S3 accepts it, which is unlikely. More real: `FRONTEND_RESET_URL="http://localhost:4200/..."`. In production, forgetting it sends reset links pointing to localhost, which is broken but safe. Forgetting to change it to **https** would leak reset tokens over plaintext. Guard: require an `https://` scheme outside dev.

## Review Checklist
- [ ] Does any code parse `X-Forwarded-*` headers directly?
- [ ] Will the app refuse to start in production with any dev default for secrets?
- [ ] Are any API keys or tokens placed in URLs?
- [ ] Is CORS an explicit origin list?
