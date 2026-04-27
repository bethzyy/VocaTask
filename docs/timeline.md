# VocaTask — Timeline Estimate

> All estimates based on AI-assisted development (Claude Code).

---

## 1. Current Status

| Module | Status | Completed |
|--------|--------|-----------|
| Voice recording + upload | ✅ Done | 2026-04-22 |
| ASR transcription (ZhipuAI GLM-ASR-2512) | ✅ Done | 2026-04-22 |
| Task routing (GLM-4-flash function calling + keyword fallback) | ✅ Done | 2026-04-22 |
| Long-form transcription queue (background worker + ffmpeg segmentation) | ✅ Done | 2026-04-22 |
| Browser UI (recording, results display, status polling) | ✅ Done | 2026-04-22 |
| Mock org data (10 people, 5 departments, hardcoded) | ✅ Done | 2026-04-22 |
| Save routed tasks to SQLite (routing_history table) | ✅ Done | 2026-04-24 |
| Task history view in UI (/api/history endpoint) | ✅ Done | 2026-04-24 |
| CRM task management UI (crm_server.py + web/crm/) | ✅ Done | 2026-04-26 |
| Image attachments + Vision AI (GLM-4V-Flash) | ✅ Done | 2026-04-26 |
| AI task analysis (ai_router.py, Anthropic-compatible endpoint) | ✅ Done | 2026-04-26 |
| HTTPS mobile testing (Flask ssl_context="adhoc") | ✅ Done | 2026-04-26 |
| Data consistency fix (AI worker no longer overwrites routing) | ✅ Done | 2026-04-26 |

### 2.5 Requirements Gap Analysis (vs. requirements.md)

> Expert review conducted 2026-04-26 — three-perspective analysis: Architecture, Features, Production/DevOps.

#### Critical Gaps

| Gap | Description | Impact | Effort (with CC) |
|-----|-------------|--------|-------------------|
| Speaker diarization | requirements.md specifies multi-speaker identification; current ASR (GLM-ASR-2512) outputs single speaker | Cannot distinguish who said what in meetings | 1-2 weeks research + integration |
| Authentication & authorization | No user auth exists — CRM and API endpoints are fully open | Anyone on the network can read/write/delete tasks | 3-5 days |
| Concurrency capacity | Flask `debug=True` + SQLite cannot handle production load (50+ users) | Data corruption / errors under concurrent writes | 3-5 days (PostgreSQL migration) |

#### Major Gaps

| Gap | Description | Impact | Effort (with CC) |
|-----|-------------|--------|-------------------|
| SQLite → PostgreSQL | requirements.md implies persistent relational DB; SQLite lacks concurrent write safety | Data integrity under load | 3-4 days |
| Notification system | requirements.md specifies notification workflow; not implemented | Task assignees not notified of new assignments | 3-5 days |
| Offline mode | requirements.md mentions offline capability; browser-based frontend requires constant network | Unusable in field with poor connectivity | 5-7 days (Capacitor) or 7-10 days (React Native) |
| Long transcription 90-min | requirements.md targets 90-min recordings; current chunked pipeline untested at that scale | May fail on very long recordings | 1-2 days testing + fixes |
| User confirmation flow | requirements.md describes task confirmation before routing; current flow auto-routes | User cannot review/edit AI interpretation | 2-3 days |

#### Minor Gaps

| Gap | Description | Impact | Effort (with CC) |
|-----|-------------|--------|-------------------|
| Dynamic org structure | Organization data is hardcoded; no CRUD API for departments/people | Requires code change to update org chart | 2-3 days |
| Gemma fallback model | requirements.md mentions Gemma as fallback; only GLM models used | No fallback if ZhipuAI is down | 1 day (switch API key/model) |
| Custom analyzers | No plugin system for custom task analysis | Cannot extend analysis without code changes | 3-5 days |
| Performance monitoring | No metrics/logging for response times or error rates | Cannot measure system health | 1-2 days |
| API rate limiting | No rate limiting on endpoints | Vulnerable to abuse | 0.5 day |
| File upload security | No file type/size validation on image uploads | Potential security risk | 0.5 day |

---

## 2. PoC Timeline

### 2.1 Option 1: Browser Only — Already Functional + 2-4 Hours Polish

The core task delegation pipeline is already working. Only minor polish needed before demo.

| Task | Time | Status |
|------|------|--------|
| Save routed tasks to a simple list (in-memory or SQLite, no full CRM) | 1h | ✅ Done 2026-04-24 |
| Add task history view in UI (list of past routed tasks) | 1h | ✅ Done 2026-04-24 |
| Test with real voice input in browser, fix any issues | 1-2h | ⏳ In Progress |

Test on real phone: Flask runs with `ssl_context="adhoc"` (self-signed HTTPS). Open `https://<server-ip>:8010` in phone browser → tap "Advanced" → "Proceed" → microphone works. No registration needed, Android only (iOS Safari does not allow getUserMedia with self-signed certs).

#### Local Mobile Testing Options

| Tool | Setup | Android | iOS | Best for |
|------|-------|---------|-----|----------|
| Flask self-signed cert (`ssl_context="adhoc"`) | 1 line code change | ✅ (tap "Proceed") | ❌ | Quick local testing |
| ngrok tunnel | npm install + account registration | ✅ | ✅ | Testing from outside LAN |
| Cloudflare Tunnel | `cloudflared` install | ✅ | ✅ | PoC demo (free, no registration) |

> **Current setup**: Flask self-signed cert — already configured in `server.py`.
>
> These are **testing tools**, not product solutions. For shipping a real mobile app, see [Capacitor](#31-decision-1-client--browser-vs-capacitor-vs-react-native).

### 2.2 Option 2: Deploy to Cloud + Real Device Testing — 2-3 Days

Take the working prototype, deploy to a cloud server, and test on real phones over 4G/5G.

| Task | Time |
|------|------|
| Polish tasks (same as Option 1) | 2-4h |
| Provision cloud server (Alibaba Cloud / Tencent Cloud) | 1h |
| Deploy backend to cloud + configure nginx | 2h |
| HTTPS setup (Let's Encrypt) | 30min |
| Replace mock org data with real employee list | 1h |
| Test on real Android phone over 4G/5G | 1h |
| Test on real iPhone over 4G/5G | 1h |
| Fix mobile-specific issues (mic permission, browser compat, audio format) | 2-4h |
| Bug fixes and stability testing | 2-3h |

### 2.3 Option 3: Capacitor APP on Real Device — 2-3 Days *(Recommended)*

Wrap the existing web frontend in a native shell using Capacitor. Reuses all current HTML/CSS/JS code.

| Task | Time |
|------|------|
| All tasks from Option 2 (deploy backend) | 1 day |
| Capacitor project init + config | 2-3h |
| Replace getUserMedia with Capacitor native microphone plugin (~30 lines JS) | 2-3h |
| Configure API base URL for server address | 1h |
| Test on real Android device (USB debug) | 2-3h |
| Test on real iPhone (TestFlight, requires Mac) | 2-3h |
| Fix device-specific issues | 1 day |

### 2.4 Option 4: React Native App on Real Device — 4-6 Days *(Alternative)*

Rewrite the frontend in React/TypeScript as a fully native app. **Choose this only if** the app will have complex UI interactions, animations, or features beyond what a WebView can handle. For most cases, Capacitor (Option 3) is sufficient.

| Task | Time |
|------|------|
| All tasks from Option 2 (deploy backend) | 1 day |
| React Native project setup + voice recording module | 1-2 days |
| API integration (connect app to deployed backend) | 1 day |
| Test on real Android device (USB debug) | 2-3h |
| Test on real iPhone (TestFlight) | 2-3h |
| Fix device-specific issues (permissions, audio codecs, background recording) | 1-2 days |

### 2.5 PoC Deliverables

- Working app: record voice → AI transcribes → routes to person/department → shows result
- Long-form recording → queued → transcribed → stored
- Task history: list of all routed tasks
- Employee list with responsibilities driving AI routing
- Tested on real mobile device

### 2.6 What's NOT in PoC (deferred to production)

| Item | Gap Level | Notes |
|------|-----------|-------|
| User authentication | 🔴 Critical | No auth — all API endpoints are open |
| Speaker diarization | 🔴 Critical | Single-speaker ASR only; cannot identify who said what |
| SQLite → PostgreSQL migration | 🟠 Major | SQLite insufficient for production concurrency |
| Notification system | 🟠 Major | Assignees not notified of new tasks |
| User confirmation before routing | 🟠 Major | Auto-routes without user review |
| Offline mode | 🟠 Major | Requires constant network connection |
| Push notifications | 🟠 Major | No push capability in browser; needs Capacitor |
| Dynamic org structure (CRUD API) | 🟡 Minor | Currently hardcoded in org_structure.py |
| CRM management UI for departments | ✅ Done | CRM task view done; org CRUD deferred |
| Photo attachments | ✅ Done | Vision AI + image upload working |

### 2.7 How Task Delegation Works

The system uses an employee list with responsibilities to match tasks to the right person:

1. **Employee list** defined in `core/org_structure.py` — each person has name, department, title, and responsibilities
2. **Voice input** → ASR transcribes → text sent to GLM-4-flash
3. **AI routing** — GLM receives the org structure as context, uses function calling to pick the best assignee based on task content and employee responsibilities
4. **Fallback** — if AI unavailable, keyword matching against responsibilities (e.g. "equipment" → equipment department)
5. **Result** — task description + assigned person + department + priority + reason displayed in UI

**To customize for client**: replace the mock data in `core/org_structure.py` with real employee names and responsibilities. No code changes needed, just data.

---

## 3. Production Timeline

> Going to production requires **two independent decisions**. Make each one separately, then combine them to find your scenario and timeline.
>
> | | Decision 1: Client (what runs on the phone) | Decision 2: Server (where the backend lives) |
> |--|--|--|
> | Options | Browser (done) / Capacitor APP (+1-2 days) / React Native APP (+1-2 weeks) | VPS Cloud / Company On-Premise |
> | These are independent — choosing a native app does NOT change where your server lives. |

---

### 3.1 Decision 1: Client — Browser vs. Capacitor vs. React Native

> **Upgrade path**: Browser (works fine → keep using it) → Capacitor (need an APP, don't want to rewrite) → React Native (APP complexity exceeds WebView capability).

| | Browser (Current) | Capacitor APP *(Recommended)* | React Native APP |
|--|-------------------|------------------|------------------|
| Access | Open URL in phone browser — works on any network (WiFi / 4G/5G) once server has a public address | Install APP (APK / IPA) — feels like a native app | Install from App Store / Google Play |
| Voice recording | Web MediaRecorder API (requires HTTPS on real devices) | Native microphone access (no HTTPS restriction) | Native microphone access |
| Push notifications | No | Yes (Capacitor plugins) | Yes (Firebase / APNs) |
| Offline support | **Not supported** — requires network connection to reach server | Yes (Capacitor plugins) | Full (local queue + sync) |
| Frontend changes | None | ~30 lines (microphone module) | Full rewrite in React/TypeScript |
| Development time | Already done | +1-2 days | +1-2 weeks |
| Native feel | Browser experience | Same as browser, but in an APP shell | Truly native rendering |
| App Store review | Not needed | 3-7 days review time | 3-7 days review time |
| Skill requirement | None extra | None extra (same HTML/JS/CSS) | TypeScript + React Native |
| **When to choose** | PoC, internal use, simplest deployment | Need an APP but want to reuse existing frontend | APP has complex UI, animations, or exceeds WebView performance |

**If choosing Capacitor — development tasks:**

| Task | Time |
|------|------|
| Capacitor project init + config | 2-3h |
| Replace getUserMedia with Capacitor microphone plugin (~30 lines) | 2-3h |
| API base URL config | 1h |
| Testing on real devices (Android + iOS) | 1-2 days |
| App Store / Google Play submission and review | 3-7 days (waiting) |
| **Total** | **+1-2 days active dev + 1 week review** |

**If choosing React Native — development tasks:**

| Task | Time |
|------|------|
| React Native project setup + voice recording module | 2-3 days |
| API integration (connect to existing backend) | 1-2 days |
| Offline queue (record without network, sync later) | 1-2 days |
| Push notification setup (Firebase for Android, APNs for iOS) | 1 day |
| Testing on real devices (Android + iOS) | 1-2 days |
| App Store / Google Play submission and review | 3-7 days (waiting) |
| **Total** | **+1-2 weeks active dev + 1 week review** |

### 3.2 Decision 2: Server Hosting — Where to Deploy

**System architecture** — the server is the central hub; phone and CRM computer are both browser clients:

```
                    ┌─────────────────────────────┐
                    │  Server (fixed address)      │
                    │  server.py      port 8010    │
                    │  crm_server.py  port 8011    │
                    │  SQLite database             │
                    └────────────┬────────────────┘
                                 │
               ┌─────────────────┴──────────────────┐
               ▼                                     ▼
  📱 Phone (browser client)             💻 Computer (CRM browser)
  Records audio → uploads task          Views & manages tasks
  Works on any network (WiFi / 4G/5G)   Opens CRM dashboard
```

> **Important**: The server must NOT run on the phone. The phone is a browser client only. Phones on 4G/5G have no public IP (carrier-grade NAT) — they cannot be reached from outside.

**Three deployment options:**

| | Option A: VPS Cloud Server | Option B: Company Server + Cloudflare Tunnel | Option C: Company Server + IT Setup |
|--|---|---|---|
| **Phase** | Production | **PoC / Demo only** | Production |
| **Cost** | 60–200 CNY/month | Free | No extra cost |
| **Setup time** | 3–4 hours | 30 min | 3–5 days |
| **Data location** | Cloud (outside company) | Company server | Company server |
| **Data via 3rd party** | No | Yes (Cloudflare, encrypted) | No |
| **IT involvement** | No | No | Yes |
| **HTTPS** | Manual (Let's Encrypt) | Automatic | Manual (internal CA) |
| **Recommended for** | Production, non-sensitive data | PoC demos & testing | Sensitive data / compliance |

> Option B (Cloudflare Tunnel) is a **PoC shortcut only** — it uses the company server as the host but routes traffic through Cloudflare's network. For production, choose Option A or C.

**Option A setup: VPS Cloud Server (3–4 hours)**

| Task | Time |
|------|------|
| Provision server (Alibaba Cloud / Tencent Cloud) | 1h |
| Install Python, PostgreSQL, nginx | 1–2h |
| Deploy backend code, configure systemd service | 1h |
| HTTPS setup (Let's Encrypt) | 30min |
| DNS configuration | 30min |
| Smoke test + verify from mobile | 1h |

**Option B setup: Cloudflare Tunnel (30 min, run on company server)**

```bash
curl -L -o cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

cloudflared tunnel --url http://localhost:8010  # → phone uses this HTTPS URL
cloudflared tunnel --url http://localhost:8011  # → computer uses this HTTPS URL for CRM
```

No firewall changes needed. Cloudflare provides HTTPS automatically.

**Option C setup: Company Server + IT Network (3–5 days)**

| Task | Time |
|------|------|
| Coordinate with client IT (server access, OS, network) | 1 day |
| Install Python, PostgreSQL, nginx on internal server | 1 day |
| Firewall / port configuration for mobile access | 1 day |
| VPN or reverse proxy setup (for 4G/5G access from field) | 1–2 days |
| Internal SSL cert or self-signed | 1h |
| Smoke test from inside and outside network | 1h |

**Decision guide:**

| Your situation | Use this option |
|----------------|----------------|
| Need a quick demo / PoC on real device | **Option B** — free, 30 min, no IT needed |
| Going to production, data is not sensitive | **Option A** — stable, fully controlled, low cost |
| Going to production, data must stay on company premises | **Option C** — data never leaves company network |

---

### 3.3 Your Scenario = Decision 1 × Decision 2

Pick one from each decision — the intersection is your timeline:

| | **Browser** (Decision 1, already done) | **Capacitor APP** (Decision 1, +1-2 days) | **React Native APP** (Decision 1, +1-2 weeks) |
|--|--|--|--|
| **PoC Demo** — Company server + CF Tunnel (Option B) | 30 min setup | 1-2 days | — *(overkill for PoC)* |
| **Production** — VPS Cloud Server (Option A) | **3–4 weeks** | **3–4 weeks + 1-2 days + review** | **4–5 weeks + App Store review** |
| **Production** — Company Server + IT (Option C) | **3–4 weeks** | **3–4 weeks + 1-2 days + review** | **5–6 weeks + App Store review** |

> All three columns share the same backend work (Weeks 1–3). The client-side development stacks on top. Capacitor's 1-2 days can overlap with backend work, so it may not extend the overall timeline.

---

**Detailed timelines by scenario:**

**Scenario A: Cloud Server + Browser Access** *(Option A × Browser)*

| Phase | Time | Tasks |
|-------|------|-------|
| Week 1 | 5 days | Backend hardening, error handling, audio format compatibility |
| Week 2 | 5 days | Task lifecycle, auth, notifications, task dashboard |
| Week 3 | 3-5 days | Cloud deploy, PostgreSQL migration, testing |
| Week 4 (optional) | 5 days | CRM integration, photo attachments |
| **Total** | **3-4 weeks** | |

**Scenario B: Cloud Server + Capacitor APP** *(Option A × Capacitor)*

| Phase | Time | Tasks |
|-------|------|-------|
| Weeks 1-3 | Same as Scenario A | Backend + deploy |
| Week 3-4 | 1-2 days | Capacitor packaging + device testing |
| Week 4 | 3-7 days | App Store / Google Play review (waiting) |
| **Total** | **3-4 weeks + review** | (Capacitor work overlaps with backend) |

**Scenario C: Cloud Server + React Native APP** *(Option A × React Native)*

| Phase | Time | Tasks |
|-------|------|-------|
| Weeks 1-3 | Same as Scenario A | Backend + deploy |
| Week 4 | 5 days | React Native app development |
| Week 5 | 5 days | Offline queue, push notifications, device testing |
| Week 6 | 3-7 days | App Store / Google Play review (waiting) |
| **Total** | **4-5 weeks + review** | |

**Scenario D: On-Premise + Browser Access** *(Option C × Browser)*

| Phase | Time | Tasks |
|-------|------|-------|
| Weeks 1-2 | Same as Scenario A | Backend development |
| Week 3 | 3-5 days | On-premise deployment + IT coordination |
| Week 4 (optional) | 5 days | CRM integration, photo attachments |
| **Total** | **3-4 weeks** | (but may slip if IT coordination slow) |

**Scenario E: On-Premise + Capacitor APP** *(Option C × Capacitor)*

| Phase | Time | Tasks |
|-------|------|-------|
| Weeks 1-3 | Same as Scenario D | Backend + on-premise deploy |
| Week 3-4 | 1-2 days | Capacitor packaging + device testing |
| Week 4 | 3-7 days | App Store review |
| **Total** | **3-4 weeks + review** | |

**Scenario F: On-Premise + React Native APP** *(Option C × React Native)*

| Phase | Time | Tasks |
|-------|------|-------|
| Weeks 1-2 | Same as Scenario A | Backend development |
| Week 3 | 3-5 days | On-premise deployment |
| Week 4-5 | 10 days | React Native app + offline + push |
| Week 6 | 3-7 days | App Store review |
| **Total** | **5-6 weeks + review** | |

### 3.4 Technical Risk Assessment

> Risk ratings reviewed by three-expert panel (2026-04-26). All estimates assume Claude Code assistance.

#### 🔴 Critical Risks

| Risk | Probability | Mitigation | Skill Required |
|------|-------------|------------|---------------|
| **Security breach** — no auth, Flask `debug=True` exposes interactive debugger (RCE risk), CORS wide open | High (if exposed to internet) | Auth middleware + `debug=False` + gunicorn/waitress in production | ★★☆☆☆ CC writes middleware |
| **ZhipuAI single point of failure** — ASR + routing + vision all depend on one provider; ASR failure = total system paralysis | Medium | Add backup ASR provider (iFlytek / Alibaba); keyword fallback covers routing only | ★★☆☆☆ config + adapter pattern |

#### 🟠 Major Risks

| Risk | Probability | Mitigation | Skill Required |
|------|-------------|------------|---------------|
| **SQLite concurrency** — WAL mode works for <10 users; two Flask processes share one DB file | Medium | Migrate to PostgreSQL before 10+ concurrent users | ★★☆☆☆ CC handles migration |
| **Speaker diarization** — no mature open-source Chinese solution; requirements.md specifies it | High | Evaluate FunASR / pyannote / commercial API; **only needed for multi-person meetings, NOT for single-speaker task reports** | ★★★★☆ signal processing |
| **Audio format incompatibility** — iOS Safari records m4a (AAC); Android records WebM/OGG | Medium | ffmpeg server-side conversion + real-device testing | ★★☆☆☆ CC writes conversion |
| **GLM-4-flash routing accuracy** — lightweight model may struggle with dialects, jargon, cross-department tasks | Medium | Build 50-case test set; upgrade to GLM-4 if accuracy < 85% | ★★☆☆☆ prompt engineering |
| **Factory network instability** — WiFi dead zones in steel structures, 4G blind spots | Medium-high | Capacitor offline recording + background sync; browser retry logic | ★★☆☆☆ |
| **Disk space unlimited growth** — audio + images + WAV conversions never cleaned up; 90-min WAV ≈ 1.7 GB | High | Auto-cleanup policy; object storage migration | ★☆☆☆☆ CC writes cleanup |
| **Long transcription segment quality** — 25s fixed chunks cut words mid-sentence; lose cross-segment context | Medium | Overlapping segments; post-processing merge; test at 90-min scale | ★★☆☆☆ |
| **Customer expectation gap** — requirements.md describes production-grade system (RN + Claude + Gemma + PostgreSQL); PoC delivers browser + SQLite + GLM | Medium-high | Align PoC acceptance criteria with customer before demo | Communication skill |
| **Optimistic time estimates** — "Claude Code assisted" assumes developer familiarity; Phase 1 packs 5 subsystems into 1 week | Medium-high | 30% buffer per phase; spike high-risk items early | Project management |

#### 🟡 Medium Risks

| Risk | Probability | Mitigation | Skill Required |
|------|-------------|------------|---------------|
| **Scope creep** — requirements.md has 13 gaps vs implementation; customer may demand all | High | Freeze per-phase scope with explicit acceptance criteria | Process discipline |
| **LLM function calling format drift** — GLM model updates may change JSON output structure | Medium | Strict schema validation on model responses (not just json.loads) | ★★☆☆☆ |
| **API cost overrun** — 50 users × 5 tasks/day = 7500 ASR calls/month; 90-min recording = 216 calls | Medium | Daily/monthly API caps; usage dashboard in CRM | ★☆☆☆☆ config |
| **Single developer dependency** — bus factor = 1 | Low | Onboarding guide for handoff; standardize non-obvious patterns (e.g. Anthropic-compatible endpoint) | Documentation |

### 3.5 Production Roadmap (Phased)

> Based on expert analysis, the recommended path from current PoC to production:

**Phase 1 — Security & Infrastructure (Week 1)**

| Task | Time | Dependencies |
|------|------|-------------|
| Add JWT authentication middleware | 2 days | — |
| API rate limiting + input validation | 1 day | — |
| SQLite → PostgreSQL migration | 1 day | PostgreSQL installed |
| File upload security (type/size checks) | 0.5 day | — |
| Basic logging & health checks | 0.5 day | — |

**Phase 2 — Core Production Features (Weeks 2-3)**

| Task | Time | Dependencies |
|------|------|-------------|
| Notification system (email / in-app) | 3-5 days | Auth system |
| User confirmation flow (review before route) | 2-3 days | — |
| Dynamic org structure CRUD API | 2-3 days | PostgreSQL |
| Long transcription stress test (90-min) | 1-2 days | — |
| Task lifecycle improvements | 2 days | — |

**Phase 3 — Advanced Features (Weeks 3-4)**

| Task | Time | Dependencies |
|------|------|-------------|
| Speaker diarization research & prototype | 5-10 days | External API or model |
| Capacitor packaging (if APP needed) | 1-2 days | Phase 1 complete |
| Offline mode (Capacitor plugin) | 3-5 days | Capacitor |
| Performance monitoring dashboard | 1-2 days | Logging from Phase 1 |

**Phase 4 — Scale & Polish (Week 5)**

| Task | Time | Dependencies |
|------|------|-------------|
| Load testing (50+ concurrent users) | 1-2 days | PostgreSQL |
| Nginx + systemd production config | 1 day | — |
| Real-device testing (Android + iOS) | 1-2 days | Server deployed |
| Documentation & ops runbook | 1 day | — |

**Total: 4-5 weeks** (aligns with Production A/B estimates in Section 3.3)

### 3.6 Technical Verification Checklist

> Every item below must be individually tested and confirmed. If all items pass, the project has no remaining technical feasibility risk.
>
> Status: ✅ Verified | ⏳ Partially verified | ❌ Not verified

#### Voice Processing Pipeline

| # | What to Verify | How | Pass Criteria | If Fails | Status |
|---|---------------|-----|---------------|----------|--------|
| V1 | ASR accuracy under factory noise | 20 industrial-term test clips in 3 environments (quiet / workshop / outdoor) | Key info accuracy ≥ 90%, WER ≤ 15% | Must switch ASR or add noise reduction | ⏳ |
| V2 | iOS Safari recording → ASR pipeline | iPhone Safari recording → check MIME → ffmpeg to WAV → ASR transcribe | iOS audio → ffmpeg → ASR success | iOS must use Capacitor native mic | ❌ |
| V3 | 90-min long transcription end-to-end | Submit 90-min audio to `/api/queue`; monitor segment success, total time, memory, disk | Complete within 30 min, no crash, no lost segments | Must limit duration or change chunking strategy | ❌ |
| V4 | Speaker diarization for Chinese | 2-person 5-min dialogue; test FunASR / pyannote / iFlytek / Alibaba API | DER ≤ 20%, distinguish 3-5 speakers | Multi-person meeting scenario not feasible with open-source; budget for commercial API | ❌ |

#### AI Model Capability

| # | What to Verify | How | Pass Criteria | If Fails | Status |
|---|---------------|-----|---------------|----------|--------|
| A1 | GLM-4-flash routing accuracy | 50 test cases: direct name / department hint / cross-dept / safety urgent / with image | Overall ≥ 85%, name recognition ≥ 95%, safety = 100% high priority | Upgrade to GLM-4 (non-flash) | ⏳ |
| A2 | Function calling JSON stability | 100 consecutive calls with `tool_choice`; check json.loads success + required fields | JSON parse success ≥ 98% | Add stricter prompt + schema validation | ⏳ |
| A3 | Vision model image description quality | 20 factory photos; evaluate if descriptions capture key info | Key info extraction ≥ 80% | Refine prompt or upgrade vision model | ⏳ |

#### Mobile Compatibility

| # | What to Verify | How | Pass Criteria | If Fails | Status |
|---|---------------|-----|---------------|----------|--------|
| M1 | Android Chrome HTTPS + microphone | Self-signed cert on Flask; open in Android Chrome | Microphone access works after "Proceed" | ✅ Done | ✅ |
| M2 | iOS Safari HTTPS + microphone | Self-signed cert or Cloudflare Tunnel on iPhone Safari | Microphone access works | iOS browser route blocked; must use Capacitor or Cloudflare Tunnel | ❌ |
| M3 | Background / lock-screen recording | Start recording in browser → switch app → lock screen → check if MediaRecorder continues | Recording continues for ≥ 5 min in background | Long transcription requires Capacitor native plugin | ❌ |
| M4 | Weak network upload reliability | Throttle network to 2G / intermittent; upload 5 MB audio file | Upload succeeds with retry logic within 3 attempts | Must add chunked upload + resume | ❌ |
| M5 | Capacitor wrapper feasibility | Copy `web/` into Capacitor project; test recording + API calls | Zero code changes needed in WebView | Minor JS adjustments for native mic plugin | ❌ |

#### Concurrency & Stability

| # | What to Verify | How | Pass Criteria | If Fails | Status |
|---|---------------|-----|---------------|----------|--------|
| S1 | SQLite 10+ concurrent writes | Spawn 10-20 parallel POST requests to `/api/transcribe-and-route` | All succeed, no `database is locked` errors | Must migrate to PostgreSQL immediately | ❌ |
| S2 | 24-hour continuous operation | Run both servers for 24h; submit 1 task every 5 min; monitor memory/CPU | Memory stable (no leak), no crash | Fix memory leak or add process restart | ❌ |
| S3 | Large file upload (50 MB audio) | Upload max-size audio via mobile browser | Upload succeeds, processed correctly | Increase timeout or add chunked upload | ❌ |

#### External Dependencies

| # | What to Verify | How | Pass Criteria | If Fails | Status |
|---|---------------|-----|---------------|----------|--------|
| E1 | ZhipuAI API rate limits | Send 50 rapid sequential requests; observe throttling behavior | No hard block within normal usage pattern | Must implement request queuing + backoff | ⏳ |
| E2 | ZhipuAI Anthropic-compatible endpoint stability | 100 calls over 24h to `open.bigmodel.cn/api/anthropic` | Success rate ≥ 99% | Switch to native ZhipuAI SDK | ⏳ |
| E3 | PostgreSQL migration compatibility | Run current SQL schema + all queries against PostgreSQL | All CRUD operations work identically | Must adapt SQL dialect differences | ❌ |
| E4 | Cloudflare Tunnel PoC demo | Start tunnel on dev machine; access from external 4G phone | Both services (8010, 8011) accessible via HTTPS | Must use VPS or other tunnel solution | ❌ |

#### Summary: Verification Gate

> **Project is technically feasible when all items above are ✅ Verified.**
>
> Current status: 1/19 verified (5%). The remaining 18 items represent 2-3 weeks of focused verification work.
>
> **Priority order**: V1 (ASR accuracy) → M1/M2 (device mic) → S1 (concurrency) → A1 (routing) → V3 (90-min) → remaining items.

---

## 4. Developer Skill Requirements

> All estimates assume AI-assisted development with **Claude Code**. Skill ratings reflect the effective requirement *after* Claude Code assistance — not what you'd need coding from scratch.

### 4.1 Core Skills (Browser + Python path — current PoC through Production A/C)

| Skill | <span style="color:#1a73e8">Required Level</span> | Notes |
|-------|-----------------|-------|
| Python (Flask, asyncio) | ★★★☆☆ | Claude Code writes boilerplate and APIs; you need to read and debug |
| SQLite / PostgreSQL | ★★☆☆☆ | Claude Code generates schema and queries; you define data model |
| ZhipuAI API integration | ★★☆☆☆ | Claude Code knows API patterns; you supply keys and test output |
| Vanilla JavaScript (fetch, MediaRecorder) | ★★☆☆☆ | Claude Code writes recording and polling logic |
| Linux server / nginx / systemd | ★★☆☆☆ | Claude Code writes config files; you run commands and troubleshoot |
| ffmpeg (audio conversion, segmentation) | ★☆☆☆☆ | Claude Code handles almost all ffmpeg commands |

**If Capacitor is chosen (Decision 1):** no additional skills required — uses existing HTML/CSS/JS code. Only basic npm commands needed. Capacitor development ★★★★★ (→ ★☆☆☆☆ with CC).

**If React Native is chosen (Decision 1):** add TypeScript ★★★★★ (→ ★★★☆☆ with CC), React Native ★★★★★ (→ ★★★☆☆ with CC), App Store submission ★★★☆☆ (CC cannot help — fully human)

---

### 4.2 Gap Analysis by Background

| Your Background | Main Gaps | Ramp-up Time (with Claude Code) |
|----------------|-----------|--------------------------------|
| Python developer | JavaScript/MediaRecorder, nginx/systemd | 2-3 days |
| Web frontend developer | Python/Flask, Linux server, database | 1 week |
| React/React Native developer | Python backend, ffmpeg, Linux | 1 week |
| No programming background | Python + web + server from scratch | 2-3 months |

#### 5.2.1 Adjustment: Developer Lacks Web / Backend / Deployment Experience

If the developer has general coding skills but **no prior experience** in web frontend, backend, or server deployment, add the following on top of the estimates above:

| Missing Experience | What Claude Code Still Can't Cover | Extra Time |
|-------------------|------------------------------------|-----------|
| Web frontend (JS, browser APIs, DevTools) | Cross-device debugging, MediaRecorder quirks | +3-5 days |
| Backend (Flask, HTTP, virtual environments) | Understanding errors when request/response flow breaks | +3-5 days |
| Server deployment (Linux, nginx, systemd, SSL, firewall) | SSH setup, 502 troubleshooting, certificate install, Cloudflare Tunnel account | +1-2 weeks |
| **Browser path total** | | **+2-3 weeks** |
| App Store submission (React Native path only) | Developer account approval, provisioning profiles, screenshots, review wait + likely 1st rejection | +2-3 weeks |
| **React Native path total** | | **+4-6 weeks** |

> Deployment is the steepest gap — even experienced developers spend days here. Plan for it explicitly.

**Compared to React Native path**: The browser-based PoC is significantly more accessible for Python developers — no TypeScript, no Xcode/Android Studio, no App Store review cycle.

---

### 4.3 Hard Challenges — What Claude Code Can and Cannot Fix

| Challenge | Difficulty | Claude Code Help | Why CC Can't Fully Solve It |
|-----------|-----------|-----------------|----------------------------|
| HTTPS on mobile (getUserMedia blocked over HTTP) | 🔴 High | ★★★☆☆ | Production: domain + Let's Encrypt or Cloudflare Tunnel. Local testing: Flask `ssl_context="adhoc"` works on Android (1 line change). |
| Audio format compatibility across phones | 🔴 High | ★★★☆☆ | CC writes conversion code, but real-phone testing to find edge cases is irreplaceable |
| Routing accuracy (GLM-4-flash edge cases) | 🟠 Medium | ★★★★☆ | CC helps tune prompts; you must supply real voice test data |
| Cross-network deployment (nginx, firewall, public IP) | 🟠 Medium | ★★★★☆ | CC writes nginx config and explains steps; IT cooperation or VPS account still needed |
| Concurrent database access under load | 🟡 Low-medium | ★★★★★ | CC handles WAL mode config and query safety fully |
| ffmpeg segmentation for long audio | 🟡 Low-medium | ★★★★★ | CC handles ffmpeg commands end-to-end |

---

## 5. Summary

| Phase | Time | What You Get |
|-------|------|-------------|
| **PoC 1** (browser only) | Done + 2-4h polish | Working demo in browser |
| **PoC 2** (cloud + real device) | 2-3 days | Deployed, tested on real phone via browser |
| **PoC 3** (Capacitor APP on device) | 2-3 days | Capacitor APP installed on real phone *(recommended)* |
| **PoC 4** (React Native APP on device) | 4-6 days | Native APP installed on real phone (alternative) |
| **Production A** (cloud + browser) | 3-4 weeks | Deployed cloud system, auth, notifications |
| **Production B** (cloud + Capacitor) | 3-4 weeks + review | Same as A + Capacitor mobile APP |
| **Production C** (cloud + React Native) | 4-5 weeks + review | Same as A + React Native mobile APP |
| **Production D** (on-premise + browser) | 3-4 weeks | Deployed on internal server |
| **Production E** (on-premise + Capacitor) | 3-4 weeks + review | Same as D + Capacitor mobile APP |
| **Production F** (on-premise + React Native) | 5-6 weeks + review | Same as D + React Native mobile APP |

**Recommendation**: PoC 2 for fastest real-device validation. PoC 3 (Capacitor) when APP form factor is needed. Production A for fastest go-live. Production B when APP is required.

---

---

# VocaTask — 时间评估

> 所有时间估算基于 AI 辅助开发（Claude Code）。

---

## 1. 当前进度

| 模块 | 状态 | 完成时间 |
|------|------|---------|
| 语音录制 + 上传 | ✅ 已完成 | 2026-04-22 |
| ASR 转录（智谱 GLM-ASR-2512） | ✅ 已完成 | 2026-04-22 |
| 任务路由（GLM-4-flash 函数调用 + 关键词 fallback） | ✅ 已完成 | 2026-04-22 |
| 长篇转录队列（后台 Worker + ffmpeg 分片） | ✅ 已完成 | 2026-04-22 |
| 浏览器 UI（录音、结果展示、状态轮询） | ✅ 已完成 | 2026-04-22 |
| 模拟组织数据（10 人、5 部门，硬编码） | ✅ 已完成 | 2026-04-22 |
| 路由结果存入 SQLite（routing_history 表） | ✅ 已完成 | 2026-04-24 |
| 任务历史记录界面（/api/history 接口） | ✅ 已完成 | 2026-04-24 |
| CRM 任务管理界面（crm_server.py + web/crm/） | ✅ 已完成 | 2026-04-26 |
| 图片附件 + 视觉 AI（GLM-4V-Flash） | ✅ 已完成 | 2026-04-26 |
| AI 任务分析（ai_router.py，Anthropic 兼容接口） | ✅ 已完成 | 2026-04-26 |
| HTTPS 移动端测试（Flask ssl_context="adhoc"） | ✅ 已完成 | 2026-04-26 |
| 数据一致性修复（AI Worker 不再覆盖主路由结果） | ✅ 已完成 | 2026-04-26 |

### 1.5 需求差距分析（对比 requirements.md）

> 专家评审于 2026-04-26 — 从架构、功能、生产/DevOps 三个维度分析。

#### 关键差距

| 差距 | 说明 | 影响 | 工作量（CC 辅助） |
|------|------|------|-------------------|
| 说话人识别 | requirements.md 要求多人说话识别；当前 ASR（GLM-ASR-2512）仅输出单说话人 | 无法区分会议中谁说了什么 | 1-2 周调研 + 集成 |
| 用户认证与授权 | 无用户认证 — CRM 和 API 端点完全开放 | 网络上任何人可读/写/删除任务 | 3-5 天 |
| 并发承载能力 | Flask `debug=True` + SQLite 无法支撑生产负载（50+ 用户） | 并发写入导致数据损坏/错误 | 3-5 天（迁移 PostgreSQL） |

#### 重要差距

| 差距 | 说明 | 影响 | 工作量（CC 辅助） |
|------|------|------|-------------------|
| SQLite → PostgreSQL | requirements.md 隐含持久化关系型数据库；SQLite 缺乏并发写入安全 | 负载下数据完整性风险 | 3-4 天 |
| 通知系统 | requirements.md 指定通知流程；未实现 | 任务受理人无法收到新任务通知 | 3-5 天 |
| 离线模式 | requirements.md 提及离线能力；浏览器前端需持续联网 | 网络差的现场无法使用 | 5-7 天（Capacitor）或 7-10 天（React Native） |
| 长篇转录 90 分钟 | requirements.md 目标 90 分钟录音；当前分片管道未在该规模测试 | 超长录音可能失败 | 1-2 天测试 + 修复 |
| 用户确认流程 | requirements.md 描述路由前确认步骤；当前自动路由 | 用户无法审核/编辑 AI 解读结果 | 2-3 天 |

#### 次要差距

| 差距 | 说明 | 影响 | 工作量（CC 辅助） |
|------|------|------|-------------------|
| 动态组织架构 | 组织数据硬编码；无部门/人员增删改查 API | 更新组织架构需改代码 | 2-3 天 |
| Gemma 备用模型 | requirements.md 提及 Gemma 作为备用；仅使用 GLM 模型 | 智谱 API 宕机无后备 | 1 天（切换 API key/模型） |
| 自定义分析器 | 无自定义任务分析插件系统 | 无法在不改代码情况下扩展分析 | 3-5 天 |
| 性能监控 | 无响应时间/错误率指标和日志 | 无法衡量系统健康状态 | 1-2 天 |
| API 限流 | 端点无速率限制 | 易被滥用 | 0.5 天 |
| 文件上传安全 | 图片上传无文件类型/大小验证 | 潜在安全风险 | 0.5 天 |

---

## 2. PoC 时间

### 2.1 方案一：仅浏览器 — 已完成 + 2-4 小时打磨

任务委派核心流程已经跑通，只需微调即可用于演示。

| 任务 | 时间 | 状态 |
|------|------|------|
| 将路由结果保存为简单列表（内存或 SQLite，不做完整 CRM） | 1h | ✅ 已完成 2026-04-24 |
| 添加任务历史记录界面（展示过去路由过的任务） | 1h | ✅ 已完成 2026-04-24 |
| 用真实语音输入测试，修复问题 | 1-2h | ⏳ 进行中 |

手机测试：Flask 使用 `ssl_context="adhoc"`（自签 HTTPS）启动。手机浏览器打开 `https://<服务器IP>:8010` → 点"高级"→"继续前往" → 麦克风可用。无需注册，仅支持 Android（iOS Safari 不允许自签证书使用麦克风）。

#### 本地移动测试方案对比

| 工具 | 配置 | Android | iOS | 适用场景 |
|------|------|---------|-----|----------|
| Flask 自签证书（`ssl_context="adhoc"`） | 改一行代码 | ✅（点"继续前往"） | ❌ | 快速本地测试 |
| ngrok 隧道 | npm 安装 + 注册账号 | ✅ | ✅ | 从外网测试 |
| Cloudflare Tunnel | 安装 `cloudflared` | ✅ | ✅ | PoC 演示（免费，无需注册） |

> **当前配置**：Flask 自签证书 — 已在 `server.py` 中配置。
>
> 这些是**测试工具**，不是产品方案。正式发布移动应用请参考 [Capacitor 方案](#21-决策一客户端--浏览器-vs-capacitor-vs-react-native)。

### 2.2 方案二：部署到云端 + 真机测试 — 2-3 天

把跑通的原型部署到云服务器，用真手机在 4G/5G 下测试。

| 任务 | 时间 |
|------|------|
| 打磨任务（同方案一） | 2-4h |
| 购买云服务器（阿里云/腾讯云） | 1h |
| 部署后端到云 + 配置 nginx | 2h |
| HTTPS 配置（Let's Encrypt） | 30min |
| 将模拟数据替换为真实员工列表 | 1h |
| Android 真机 4G/5G 测试 | 1h |
| iPhone 真机 4G/5G 测试 | 1h |
| 修复移动端问题（麦克风权限、浏览器兼容、音频格式） | 2-4h |
| Bug 修复 + 稳定性测试 | 2-3h |

### 2.3 方案三：Capacitor APP 真机安装 — 2-3 天 *（推荐）*

用 Capacitor 把现有 Web 前端包进原生壳，复用全部 HTML/CSS/JS 代码。

| 任务 | 时间 |
|------|------|
| 方案二全部任务（部署后端） | 1 天 |
| Capacitor 项目初始化 + 配置 | 2-3h |
| 替换 getUserMedia 为 Capacitor 原生麦克风插件（约 30 行 JS） | 2-3h |
| 配置 API 基础地址 | 1h |
| Android 真机测试（USB 调试） | 2-3h |
| iPhone 真机测试（TestFlight，需要 Mac） | 2-3h |
| 修复设备问题 | 1 天 |

### 2.4 方案四：React Native App 真机安装 — 4-6 天 *（备选）*

用 React/TypeScript 重写前端为原生 App。**仅在** APP 将有复杂 UI 交互、动画或超出 WebView 能力的功能时选择。大多数场景下 Capacitor（方案三）已足够。

| 任务 | 时间 |
|------|------|
| 方案二全部任务（部署后端） | 1 天 |
| React Native 项目搭建 + 语音录制模块 | 1-2 天 |
| API 对接（App 连接已部署的后端） | 1 天 |
| Android 真机测试（USB 调试） | 2-3h |
| iPhone 真机测试（TestFlight） | 2-3h |
| 修复设备问题（权限、音频编解码、后台录音） | 1-2 天 |

### 2.5 PoC 交付物

- 可运行应用：录音 → AI 转录 → 路由到人员/部门 → 展示结果
- 长篇录音 → 排队 → 转录 → 存储
- 任务历史记录列表
- 员工职责列表驱动 AI 路由
- 真机上测试通过

### 2.6 PoC 不包含（推迟到生产版）

| 项目 | 差距等级 | 说明 |
|------|---------|------|
| 用户认证 | 🔴 关键 | 无认证 — 所有 API 端点开放 |
| 说话人识别 | 🔴 关键 | 仅单说话人 ASR；无法识别谁说了什么 |
| SQLite → PostgreSQL 迁移 | 🟠 重要 | SQLite 无法支撑生产并发 |
| 通知系统 | 🟠 重要 | 受理人收不到新任务通知 |
| 路由前用户确认 | 🟠 重要 | 自动路由，无用户审核环节 |
| 离线模式 | 🟠 重要 | 需持续联网 |
| 推送通知 | 🟠 重要 | 浏览器无推送能力；需 Capacitor |
| 动态组织架构（CRUD API） | 🟡 次要 | 当前硬编码在 org_structure.py |
| CRM 管理界面（部门管理） | ✅ 已完成 | CRM 任务视图已完成；组织架构 CRUD 推迟 |
| 照片附件 | ✅ 已完成 | 视觉 AI + 图片上传已工作 |

### 2.7 任务委派逻辑

系统通过员工及其职责列表来智能匹配任务：

1. **员工列表** 定义在 `core/org_structure.py` — 每人有姓名、部门、职位、职责范围
2. **语音输入** → ASR 转录 → 文本发送给 GLM-4-flash
3. **AI 路由** — GLM 接收组织架构作为上下文，通过函数调用根据任务内容和员工职责选择最合适的委派人
4. **Fallback** — AI 不可用时，按职责关键词匹配（如"设备"→设备部门）
5. **结果** — 任务描述 + 委派人 + 部门 + 优先级 + 理由，展示在界面

**为客户定制**：将 `core/org_structure.py` 中的模拟数据替换为真实员工姓名和职责即可，无需改代码，只改数据。

---

## 3. 生产版时间

> 生产版规划需要做**两个独立的决策**，分别确定后组合，即可得出对应的方案和时间表。
>
> | | 决策一：客户端（手机上用什么） | 决策二：服务器（后端跑在哪里） |
> |--|--|--|
> | 选项 | 浏览器（已完成）/ Capacitor APP（+1-2天）/ React Native APP（+1-2周开发） | VPS 云服务器 / 公司内网 |
> | 说明 | 这两个决策**相互独立**——选原生 App 不影响服务器放在哪里。 | |

---

### 3.1 决策一：客户端 — 浏览器 vs Capacitor vs React Native

> **升级路径**：浏览器（够用就一直用）→ Capacitor（需要 APP 形态，不想重写前端）→ React Native（APP 复杂度超出 WebView 能力）。

| | 浏览器访问（当前方案） | Capacitor APP *（推荐）* | React Native 原生 App |
|--|---------------------|----------------------|----------------------|
| 访问方式 | 手机浏览器打开网址，服务器部署后支持任意网络（WiFi / 4G/5G） | 安装 APP（APK / IPA），像原生 App 一样使用 | 安装 App（App Store / Google Play） |
| 语音录制 | Web MediaRecorder API（真机需 HTTPS） | 原生麦克风（无 HTTPS 限制） | 原生麦克风接口 |
| 推送通知 | 不支持 | 支持（Capacitor 插件） | 支持（Firebase / APNs） |
| 离线使用 | **不支持**（需联网才能连接服务器提交任务） | 支持（Capacitor 插件） | 完整支持（本地排队 + 恢复后同步） |
| 前端改动 | 无 | 约 30 行（录音模块） | 全部重写（React/TypeScript） |
| 开发时间 | 已完成 | +1-2 天 | +1-2 周 |
| 原生体验 | 浏览器体验 | 与浏览器相同，但在 APP 壳中 | 真正的原生渲染 |
| 应用商店审核 | 不需要 | 3-7 天审核周期 | 3-7 天审核周期 |
| 技能要求 | 无额外要求 | 无额外要求（同样的 HTML/JS/CSS） | TypeScript + React Native |
| **何时选择** | PoC、内部使用、最简部署 | 需要 APP 但想复用现有前端 | APP 复杂、需要丝滑原生体验 |

**如果选择 Capacitor — 开发任务：**

| 任务 | 时间 |
|------|------|
| Capacitor 项目初始化 + 配置 | 2-3h |
| 替换 getUserMedia 为 Capacitor 麦克风插件（约 30 行） | 2-3h |
| API 基础地址配置 | 1h |
| 真机测试（Android + iOS） | 1-2 天 |
| App Store / Google Play 提交审核 | 3-7 天（等待） |
| **合计** | **+1-2 天开发 + 1 周审核** |

**如果选择 React Native — 开发任务：**

| 任务 | 时间 |
|------|------|
| React Native 项目搭建 + 语音录制模块 | 2-3 天 |
| API 对接（连接现有后端） | 1-2 天 |
| 离线队列（无网络时录音，恢复后同步） | 1-2 天 |
| 推送通知（Android 用 Firebase，iOS 用 APNs） | 1 天 |
| 真机测试（Android + iOS） | 1-2 天 |
| App Store / Google Play 提交审核 | 3-7 天（等待） |
| **合计** | **+1-2 周开发 + 1 周审核** |

### 3.2 决策二：服务器托管 — 部署在哪里

**系统架构** — 服务器是中心节点，手机和电脑都是浏览器客户端：

```
                    ┌─────────────────────────────┐
                    │  服务器（固定地址）            │
                    │  server.py      端口 8010    │
                    │  crm_server.py  端口 8011    │
                    │  SQLite 数据库               │
                    └────────────┬────────────────┘
                                 │
               ┌─────────────────┴──────────────────┐
               ▼                                     ▼
  📱 手机（浏览器客户端）                  💻 电脑（CRM 浏览器）
  录音 → 上传任务                         查看和管理任务
  支持任意网络（WiFi / 4G/5G）            打开 CRM 看板
```

> **重要**：服务器不能跑在手机上。手机只是浏览器客户端。手机在 4G/5G 下没有公网 IP（运营商级 NAT），无法被外部直接连接。

**三种部署方案：**

| | 方案 A：VPS 云服务器 | 方案 B：公司服务器 + Cloudflare Tunnel | 方案 C：公司服务器 + IT 正式开通 |
|--|---|---|---|
| **适用阶段** | 生产 | **仅 PoC / 演示** | 生产 |
| **费用** | 60–200 元/月 | 免费 | 无额外费用 |
| **搭建时间** | 3–4 小时 | 30 分钟 | 3–5 天 |
| **数据位置** | 云端（公司外） | 公司服务器 | 公司服务器 |
| **数据经过第三方** | 否 | 是（Cloudflare，传输加密） | 否 |
| **需要找 IT** | 否 | 否 | 是 |
| **HTTPS** | 手动配置（Let's Encrypt） | 自动 | 手动配置（内部 CA） |
| **推荐场景** | 生产，数据不敏感 | PoC 演示、测试 | 生产，数据合规要求高 |

> 方案 B（Cloudflare Tunnel）是 **PoC 快捷方式**：服务器仍在公司，但流量经 Cloudflare 中转。正式生产请选方案 A 或 C。

**方案 A 搭建步骤（3–4 小时）**

| 任务 | 时间 |
|------|------|
| 购买服务器（阿里云/腾讯云） | 1h |
| 安装 Python、PostgreSQL、nginx | 1–2h |
| 部署后端代码，配置 systemd 服务 | 1h |
| HTTPS 配置（Let's Encrypt） | 30min |
| DNS 域名配置 | 30min |
| 冒烟测试 + 手机访问验证 | 1h |

**方案 B 搭建步骤（30 分钟，在公司服务器上执行）**

```bash
curl -L -o cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

cloudflared tunnel --url http://localhost:8010  # → 手机用此 HTTPS 地址发任务
cloudflared tunnel --url http://localhost:8011  # → 电脑用此 HTTPS 地址打开 CRM
```

无需改防火墙，Cloudflare 自动提供 HTTPS。

**方案 C 搭建步骤（3–5 天）**

| 任务 | 时间 |
|------|------|
| 与客户 IT 协调（服务器访问、操作系统、网络） | 1 天 |
| 内网服务器安装 Python、PostgreSQL、nginx | 1 天 |
| 防火墙/端口配置（让手机能访问） | 1 天 |
| VPN 或反向代理搭建（让外场 4G/5G 能访问） | 1–2 天 |
| 内部 SSL 证书或自签名 | 1h |
| 内网 + 外网冒烟测试 | 1h |

**决策指南：**

| 你的情况 | 选这个方案 |
|---------|----------|
| 需要快速演示 / PoC 真机测试 | **方案 B** — 免费、30 分钟、无需找 IT |
| 正式上线，数据不涉及敏感信息 | **方案 A** — 稳定、可控、成本低 |
| 正式上线，数据必须留在公司内部 | **方案 C** — 数据不离开公司网络 |

---

### 3.3 你的方案 = 决策一 × 决策二

从两个决策各选一个，交叉点即为你的方案和时间：

| | **浏览器**（决策一，已完成） | **Capacitor APP**（决策一，+1-2天） | **React Native APP**（决策一，+1-2周） |
|--|--|--|--|
| **PoC 演示** — 公司服务器 + CF Tunnel（方案 B） | 30 分钟配置 | 1-2 天 | —（PoC 阶段无需重写前端） |
| **生产版** — VPS 云服务器（方案 A） | **3–4 周** | **3–4 周 + 1-2 天 + 审核** | **4–5 周 + 应用商店审核** |
| **生产版** — 公司内网 + IT（方案 C） | **3–4 周** | **3–4 周 + 1-2 天 + 审核** | **5–6 周 + 应用商店审核** |

> 三列共享相同的后端工作（第 1-3 周），客户端开发叠加在后端之上。Capacitor 的 1-2 天可与后端工作并行，不一定延长整体周期。

---

**各场景详细时间表：**

**场景 A：云服务器 + 浏览器访问** *（方案 A × 浏览器）*

| 阶段 | 时间 | 任务 |
|------|------|------|
| 第1周 | 5 天 | 后端加固、错误处理、音频格式兼容 |
| 第2周 | 5 天 | 任务生命周期、认证、通知、任务看板 |
| 第3周 | 3-5 天 | 云部署、PostgreSQL 迁移、测试 |
| 第4周（可选） | 5 天 | CRM 集成、照片附件 |
| **合计** | **3-4 周** | |

**场景 B：云服务器 + Capacitor APP** *（方案 A × Capacitor）*

| 阶段 | 时间 | 任务 |
|------|------|------|
| 第1-3周 | 同场景 A | 后端 + 部署 |
| 第3-4周 | 1-2 天 | Capacitor 打包 + 真机测试 |
| 第4周 | 3-7 天 | App Store / Google Play 审核（等待） |
| **合计** | **3-4 周 + 审核** | （Capacitor 工作可与后端并行） |

**场景 C：云服务器 + React Native App** *（方案 A × React Native）*

| 阶段 | 时间 | 任务 |
|------|------|------|
| 第1-3周 | 同场景 A | 后端 + 部署 |
| 第4周 | 5 天 | React Native App 开发 |
| 第5周 | 5 天 | 离线队列、推送通知、真机测试 |
| 第6周 | 3-7 天 | App Store / Google Play 审核（等待） |
| **合计** | **4-5 周 + 审核** | |

**场景 D：公司内网 + 浏览器访问** *（方案 C × 浏览器）*

| 阶段 | 时间 | 任务 |
|------|------|------|
| 第1-2周 | 同场景 A | 后端开发 |
| 第3周 | 3-5 天 | 内网部署 + IT 协调 |
| 第4周（可选） | 5 天 | CRM 集成、照片附件 |
| **合计** | **3-4 周** | （但 IT 协调慢的话可能延期） |

**场景 E：公司内网 + Capacitor APP** *（方案 C × Capacitor）*

| 阶段 | 时间 | 任务 |
|------|------|------|
| 第1-3周 | 同场景 D | 后端 + 内网部署 |
| 第3-4周 | 1-2 天 | Capacitor 打包 + 真机测试 |
| 第4周 | 3-7 天 | App Store 审核 |
| **合计** | **3-4 周 + 审核** | |

**场景 F：公司内网 + React Native App** *（方案 C × React Native）*

| 阶段 | 时间 | 任务 |
|------|------|------|
| 第1-2周 | 同场景 A | 后端开发 |
| 第3周 | 3-5 天 | 内网部署 |
| 第4-5周 | 10 天 | React Native App + 离线 + 推送 |
| 第6周 | 3-7 天 | App Store 审核 |
| **合计** | **5-6 周 + 审核** | |

### 3.4 技术风险评估

> 风险评级经三人专家团队评审（2026-04-26）。所有估算假设使用 Claude Code 辅助。

#### 🔴 关键风险

| 风险 | 概率 | 缓解措施 | 所需技能 |
|------|------|----------|---------|
| **安全漏洞** — 无认证 + Flask `debug=True` 暴露交互式调试器（RCE 风险）+ CORS 全开 | 高（暴露公网时） | 认证中间件 + `debug=False` + 生产用 gunicorn/waitress | ★★☆☆☆ CC 编写中间件 |
| **智谱 API 单点故障** — ASR + 路由 + 图片三层全绑智谱；ASR 失败 = 系统完全瘫痪 | 中 | 增加备用 ASR 供应商（讯飞/阿里）；关键词兜底仅覆盖路由 | ★★☆☆☆ 配置 + 适配器模式 |

#### 🟠 重要风险

| 风险 | 概率 | 缓解措施 | 所需技能 |
|------|------|----------|---------|
| **SQLite 并发** — WAL 模式 <10 用户可用；两个 Flask 进程共享一个 DB 文件 | 中 | 10+ 并发用户前迁移 PostgreSQL | ★★☆☆☆ CC 处理迁移 |
| **说话人识别** — 无成熟中文开源方案；requirements.md 要求 | 高 | 评估 FunASR / pyannote / 商业 API；**仅多人会议场景需要，单人任务上报不需要** | ★★★★☆ 信号处理 |
| **音频格式不兼容** — iOS Safari 录 m4a（AAC）；Android 录 WebM/OGG | 中 | ffmpeg 服务端转换 + 真机测试 | ★★☆☆☆ CC 编写转换 |
| **GLM-4-flash 路由准确率** — 轻量模型面对方言、术语、跨部门任务可能不准确 | 中 | 建立 50 条测试集；准确率 <85% 时升级到 GLM-4 | ★★☆☆☆ 提示工程 |
| **工厂网络不稳定** — 钢结构 WiFi 死角、4G 盲区 | 中高 | Capacitor 离线录音 + 后台同步；浏览器加重试逻辑 | ★★☆☆☆ |
| **磁盘空间无限增长** — 音频 + 图片 + WAV 转换无清理机制；90 分钟 WAV ≈ 1.7 GB | 高 | 自动清理策略；对象存储迁移 | ★☆☆☆☆ CC 编写清理 |
| **长篇转录分片质量** — 25 秒固定切割会切断词语、丢失跨段上下文 | 中 | 重叠分片；后处理合并；90 分钟级别实测 | ★★☆☆☆ |
| **客户期望落差** — requirements.md 描述生产级系统（RN + Claude + Gemma + PostgreSQL）；PoC 交付的是浏览器 + SQLite + GLM | 中高 | PoC 演示前与客户对齐验收标准 | 沟通能力 |
| **时间估算偏乐观** — "CC 辅助"假设开发者熟悉技术栈；阶段 1 含 5 个子系统仅 1 周 | 中高 | 每阶段预留 30% 缓冲；高风险项提前做技术验证 | 项目管理 |

#### 🟡 中等风险

| 风险 | 概率 | 缓解措施 | 所需技能 |
|------|------|----------|---------|
| **需求蔓延** — requirements.md 与实现有 13 项差距；客户可能要求全部补齐 | 高 | 每阶段冻结范围并明确验收标准 | 流程纪律 |
| **LLM 函数调用格式漂移** — GLM 模型更新可能改变 JSON 输出结构 | 中 | 对模型返回做严格 Schema 验证（非仅 json.loads） | ★★☆☆☆ |
| **API 费用失控** — 50 用户 × 5 任务/天 = 7500 次 ASR/月；90 分钟 = 216 次调用 | 中 | 每日/每月 API 调用上限；CRM 用量统计 | ★☆☆☆☆ 配置 |
| **单一开发者依赖** — 巴士因子 = 1 | 低 | 补充接手文档；标准化非标准用法说明 | 文档能力 |

### 3.5 生产路线图（分阶段）

> 基于专家分析，从当前 PoC 到生产的推荐路径：

**阶段 1 — 安全与基础设施（第 1 周）**

| 任务 | 时间 | 前置条件 |
|------|------|---------|
| 添加 JWT 认证中间件 | 2 天 | — |
| API 限流 + 输入验证 | 1 天 | — |
| SQLite → PostgreSQL 迁移 | 1 天 | 已安装 PostgreSQL |
| 文件上传安全（类型/大小检查） | 0.5 天 | — |
| 基础日志与健康检查 | 0.5 天 | — |

**阶段 2 — 核心生产功能（第 2-3 周）**

| 任务 | 时间 | 前置条件 |
|------|------|---------|
| 通知系统（邮件/站内信） | 3-5 天 | 认证系统 |
| 用户确认流程（路由前审核） | 2-3 天 | — |
| 动态组织架构 CRUD API | 2-3 天 | PostgreSQL |
| 长篇转录压力测试（90 分钟） | 1-2 天 | — |
| 任务生命周期改进 | 2 天 | — |

**阶段 3 — 高级功能（第 3-4 周）**

| 任务 | 时间 | 前置条件 |
|------|------|---------|
| 说话人识别调研与原型 | 5-10 天 | 外部 API 或模型 |
| Capacitor 打包（如需 APP） | 1-2 天 | 阶段 1 完成 |
| 离线模式（Capacitor 插件） | 3-5 天 | Capacitor |
| 性能监控仪表盘 | 1-2 天 | 阶段 1 日志 |

**阶段 4 — 规模化与打磨（第 5 周）**

| 任务 | 时间 | 前置条件 |
|------|------|---------|
| 负载测试（50+ 并发用户） | 1-2 天 | PostgreSQL |
| Nginx + systemd 生产配置 | 1 天 | — |
| 真机测试（Android + iOS） | 1-2 天 | 服务器已部署 |
| 文档与运维手册 | 1 天 | — |

**总计：4-5 周**（与 Section 3.3 中生产版 A/B 估算一致）

### 3.6 技术验证清单

> 以下每一项必须独立测试并确认通过。如果全部通过，项目无剩余技术可行性风险。
>
> 状态：✅ 已验证 | ⏳ 部分验证 | ❌ 未验证

#### 语音处理链路

| # | 验证内容 | 方法 | 通过标准 | 不通过的影响 | 状态 |
|---|---------|------|---------|------------|------|
| V1 | ASR 工业噪声识别准确率 | 20 条工业术语测试语音，三种环境（安静/车间/户外）对比人工听写 | 关键信息准确率 ≥ 90%，WER ≤ 15% | 必须换 ASR 或加降噪 | ⏳ |
| V2 | iOS Safari 录音 → ASR 全链路 | iPhone Safari 录音 → 检查 MIME → ffmpeg 转 WAV → ASR 转录 | iOS 音频 → ffmpeg → ASR 成功 | iOS 必须走 Capacitor 原生录音 | ❌ |
| V3 | 90 分钟长篇转录端到端 | 提交 90 分钟音频到 `/api/queue`；监控分片成功率、总耗时、内存、磁盘 | 30 分钟内完成，无崩溃无丢片 | 需限制时长或换分片策略 | ❌ |
| V4 | 中文说话人分离 | 双人 5 分钟对话；分别测试 FunASR / pyannote / 讯飞 / 阿里 | DER ≤ 20%，能区分 3-5 人 | 多人会议场景无开源方案可行；预算商业 API | ❌ |

#### AI 模型能力

| # | 验证内容 | 方法 | 通过标准 | 不通过的影响 | 状态 |
|---|---------|------|---------|------------|------|
| A1 | GLM-4-flash 路由准确率 | 50 条测试用例：人名直呼/部门暗示/跨部门/安全紧急/含图片 | 整体 ≥ 85%，人名识别 ≥ 95%，安全任务 100% 标高 | 升级到 GLM-4（非 flash） | ⏳ |
| A2 | 函数调用 JSON 稳定性 | 100 次连续 `tool_choice` 调用；检查 json.loads 成功率 + 必填字段 | JSON 解析成功率 ≥ 98% | 加强提示 + Schema 验证 | ⏳ |
| A3 | 视觉模型图片描述质量 | 20 张工厂照片；评估描述是否抓住关键信息 | 关键信息提取 ≥ 80% | 优化提示或升级视觉模型 | ⏳ |

#### 移动端兼容性

| # | 验证内容 | 方法 | 通过标准 | 不通过的影响 | 状态 |
|---|---------|------|---------|------------|------|
| M1 | Android Chrome HTTPS + 麦克风 | Flask 自签证书；Android Chrome 打开 | 点"继续前往"后麦克风可用 | ✅ 已通过 | ✅ |
| M2 | iOS Safari HTTPS + 麦克风 | 自签证书或 Cloudflare Tunnel 在 iPhone Safari 打开 | 麦克风可用 | iOS 浏览器方案不可行；必须用 Capacitor 或 Cloudflare Tunnel | ❌ |
| M3 | 后台/锁屏录音 | 浏览器开始录音 → 切换 App → 锁屏 → 检查 MediaRecorder 是否继续 | 后台继续录音 ≥ 5 分钟 | 长篇转录需 Capacitor 原生插件 | ❌ |
| M4 | 弱网上传可靠性 | 限速至 2G / 间歇断网；上传 5 MB 音频文件 | 3 次重试内上传成功 | 必须加分片上传 + 断点续传 | ❌ |
| M5 | Capacitor 包装可行性 | 将 `web/` 复制到 Capacitor 项目；测试录音 + API 调用 | WebView 内零改动可用 | 原生麦克风插件需微调 JS | ❌ |

#### 并发与稳定性

| # | 验证内容 | 方法 | 通过标准 | 不通过的影响 | 状态 |
|---|---------|------|---------|------------|------|
| S1 | SQLite 10+ 并发写入 | 10-20 个并行 POST 到 `/api/transcribe-and-route` | 全部成功，无 `database is locked` 错误 | 必须立即迁移 PostgreSQL | ❌ |
| S2 | 24 小时持续运行 | 两个服务跑 24 小时；每 5 分钟提交 1 条任务；监控内存/CPU | 内存稳定（无泄漏），无崩溃 | 修复内存泄漏或添加进程自动重启 | ❌ |
| S3 | 大文件上传（50 MB 音频） | 通过手机浏览器上传最大尺寸音频 | 上传成功，处理正确 | 增加超时或加分片上传 | ❌ |

#### 外部依赖

| # | 验证内容 | 方法 | 通过标准 | 不通过的影响 | 状态 |
|---|---------|------|---------|------------|------|
| E1 | 智谱 API 限流行为 | 50 次快速连续请求；观察限流响应 | 正常使用范围内无硬性阻断 | 必须实现请求排队 + 退避 | ⏳ |
| E2 | 智谱 Anthropic 兼容接口稳定性 | 24 小时内 100 次调用 `open.bigmodel.cn/api/anthropic` | 成功率 ≥ 99% | 切换到智谱原生 SDK | ⏳ |
| E3 | PostgreSQL 迁移兼容性 | 在 PostgreSQL 上运行当前 SQL schema + 所有查询 | 所有 CRUD 操作与 SQLite 行为一致 | 需适配 SQL 方言差异 | ❌ |
| E4 | Cloudflare Tunnel PoC 演示 | 在开发机启动隧道；外部 4G 手机访问 | 两个服务（8010、8011）均可通过 HTTPS 访问 | 需改用 VPS 或其他隧道方案 | ❌ |

#### 总结：验证门控

> **当以上所有项目均为 ✅ 已验证时，项目在技术上完全可行。**
>
> 当前进度：1/19 已验证（5%）。剩余 18 项代表 2-3 周的集中验证工作。
>
> **优先顺序**：V1（ASR 准确率）→ M1/M2（设备麦克风）→ S1（并发）→ A1（路由）→ V3（90 分钟）→ 其余项目。

---

## 4. 开发者技能要求

> 以下所有评估均假设使用 **Claude Code** 辅助开发。技能评级反映的是 AI 辅助后的实际门槛，而非从零手写代码所需的水平。

### 4.1 核心技能（浏览器 + Python 路线 — 当前 PoC 到生产版 A/C）

| 技能 | <span style="color:#1a73e8">所需水平</span> | 备注 |
|------|-----------------|------|
| Python（Flask、asyncio） | ★★★☆☆ | Claude Code 写脚手架和 API；你需要能读懂和调试 |
| SQLite / PostgreSQL | ★★☆☆☆ | Claude Code 生成建表和查询语句；你定义数据模型 |
| ZhipuAI API 集成 | ★★☆☆☆ | Claude Code 熟悉 API 用法；你提供密钥并验证输出 |
| 原生 JavaScript（fetch、MediaRecorder） | ★★☆☆☆ | Claude Code 写录音和轮询逻辑 |
| Linux 服务器 / nginx / systemd | ★★☆☆☆ | Claude Code 写配置文件；你执行命令并排查问题 |
| ffmpeg（音频转换、分段） | ★☆☆☆☆ | Claude Code 几乎全包 ffmpeg 命令构建 |

**若选择 Capacitor（决策一）：** 无额外技能要求 — 使用现有 HTML/CSS/JS 前端代码，仅需基础 npm 命令操作。Capacitor 开发 ★★★★★（→ CC 后 ★☆☆☆☆）。

**若选择 React Native（决策一）：** TypeScript ★★★★★（→ CC 后 ★★★☆☆）、React Native ★★★★★（→ CC 后 ★★★☆☆）、应用商店提交 ★★★☆☆（CC 无法代劳，纯人工）

---

### 4.2 不同背景的差距分析

| 你的背景 | 主要差距 | 上手时间（基于 Claude Code 辅助） |
|---------|---------|--------------------------------|
| Python 开发者 | JavaScript/MediaRecorder、nginx/systemd | 2-3 天 |
| Web 前端开发者 | Python/Flask、Linux 服务器、数据库 | 1 周 |
| React/React Native 开发者 | Python 后端、ffmpeg、Linux | 1 周 |
| 无编程基础 | Python + Web + 服务器从零学起 | 2-3 个月 |

#### 4.2.1 附加说明：开发人员缺乏前端 / 后端 / 部署经验

如果开发人员有一定编程基础，但**从未接触过**前端 Web、后端服务或服务器部署，需在上述时间基础上额外增加：

| 缺乏的经验 | Claude Code 仍无法覆盖的部分 | 额外时间 |
|-----------|---------------------------|---------|
| 前端（JS、浏览器 API、DevTools） | 跨设备调试、MediaRecorder 兼容问题 | +3-5 天 |
| 后端（Flask、HTTP、虚拟环境） | 请求/响应流出错时看不懂报错 | +3-5 天 |
| 服务器部署（Linux、nginx、systemd、SSL、防火墙） | SSH 配置、502 排查、证书安装、Cloudflare Tunnel 账号注册 | +1-2 周 |
| **浏览器路线合计** | | **+2-3 周** |
| App 上线（仅 React Native 路线） | 开发者账号申请、描述文件、截图规范、审核等待 + 首次基本被拒 | +2-3 周 |
| **React Native 路线合计** | | **+4-6 周** |

> 部署是最陡的学习曲线——即使有经验的开发者也可能在这里卡好几天，务必在排期中预留充裕时间。

**与 React Native 路线对比**：浏览器方案对 Python 开发者门槛显著更低——无需 TypeScript、无需 Xcode/Android Studio、无需应用商店审核周期。

---

### 4.3 硬性挑战 — Claude Code 能解决多少

| 挑战 | 难度 | CC 辅助能力 | 为什么 CC 无法完全解决 |
|------|------|-----------|---------------------|
| 手机端 HTTPS 要求（HTTP 下 getUserMedia 被阻断） | 🔴 高 | ★★★☆☆ | 生产：域名 + Let's Encrypt 或 Cloudflare Tunnel。本地测试：Flask `ssl_context="adhoc"` 可在 Android 上使用（改一行代码）。 |
| 跨机型音频格式兼容（iOS 录 m4a，Android 录 WebM） | 🔴 高 | ★★★☆☆ | CC 能写转换代码，但边缘情况必须用真机测试才能发现 |
| 路由准确率调优（GLM-4-flash 边缘情况） | 🟠 中 | ★★★★☆ | CC 辅助调整 prompt；真实语音测试数据必须人工提供 |
| 跨网络部署（nginx、防火墙、公网 IP） | 🟠 中 | ★★★★☆ | CC 写 nginx 配置并解释步骤；VPS 账号或 IT 配合仍需人工 |
| 高并发下的数据库访问 | 🟡 中低 | ★★★★★ | CC 全包 WAL 模式配置和查询安全处理 |
| 长音频 ffmpeg 分段 | 🟡 中低 | ★★★★★ | CC 端到端处理 ffmpeg 命令，基本无需人工介入 |

---

## 5. 总结

| 阶段 | 时间 | 交付内容 |
|------|------|---------|
| **PoC 1**（仅浏览器） | 已完成 + 2-4h 打磨 | 浏览器中可运行演示 |
| **PoC 2**（云端 + 真机） | 2-3 天 | 部署到云端，真机浏览器测试通过 |
| **PoC 3**（Capacitor APP 真机） | 2-3 天 | Capacitor APP 安装到真机测试 *（推荐）* |
| **PoC 4**（React Native APP 真机） | 4-6 天 | 原生 APP 安装到真机测试（备选） |
| **生产版 A**（云 + 浏览器） | 3-4 周 | 云端部署，认证、通知 |
| **生产版 B**（云 + Capacitor） | 3-4 周 + 审核 | 同 A + Capacitor 移动 APP |
| **生产版 C**（云 + React Native） | 4-5 周 + 审核 | 同 A + React Native 移动 APP |
| **生产版 D**（内网 + 浏览器） | 3-4 周 | 内网服务器部署 |
| **生产版 E**（内网 + Capacitor） | 3-4 周 + 审核 | 同 D + Capacitor 移动 APP |
| **生产版 F**（内网 + React Native） | 5-6 周 + 审核 | 同 D + React Native 移动 APP |

**建议**：PoC 用方案 2 最快在真机上验证。需要 APP 形态时用方案 3（Capacitor）。生产版用场景 A 最快上线，需要 APP 时用场景 B（Capacitor）。

---

## 6. 时间线变更记录

> 每次需求变更、技术约束或业务决策导致时间线调整时，在此追加一条记录。
> 格式：触发原因 → 具体调整 → 影响阶段。

---

*（暂无记录，以下为格式示例）*

### 6.1 2026-04-26 — 多项架构改进与移动端适配

**触发**: 手机端测试需求 + 数据一致性问题

**调整**:
- 全部 AI 模型统一使用智谱（claude_router.py → ai_router.py，Anthropic 兼容接口）
- 快速任务界面改为聊天式 UI（消息气泡、对话式交互）
- 新增 HTTPS 移动端测试支持（Flask `ssl_context="adhoc"`）
- 修复前端路由结果展示不完整（keyword_fallback 补全字段 + 前端 fallback）
- 修复数据不一致问题（AI Worker 不再覆盖主路由结果，路由只执行一次）
- 前端 UI 优化（录音按钮右侧放附件、合并相机按钮）
- CRM 用户下拉框显示部门和职位信息
- 客户端方案增加 Capacitor 选项（推荐），React Native 降为备选
- CRM 和图片附件模块标记为已完成

**影响阶段**: PoC 阶段实质性完成，移动端 HTTPS 问题已解决。PoC 1（仅浏览器）和 PoC 2（云端真机）可直接推进。

### 6.2 2026-04-26 — 三人专家团队需求差距审查

**触发**: 对 requirements.md 与当前实现进行系统性差距分析

**发现**:
- **关键差距** (3项): 说话人识别完全缺失、无用户认证、SQLite 并发不足
- **重要差距** (5项): 数据库迁移、通知系统、离线模式、长音频90分钟、用户确认流程
- **次要差距** (5项): 动态组织架构、备用模型、自定义分析器、性能监控、API 限流
- **#1 技术瓶颈**: 说话人分离（Speaker Diarization）— 无成熟开源方案匹配需求质量
- **#2 安全风险**: 无认证 + 开放 API — 任何联网者可读写删除任务

**决策**:
- 将差距分析和技术风险评估正式纳入 timeline.md
- 说话人识别作为独立技术预研项，不阻塞其他生产工作
- 生产路线图分4个阶段：安全基础设施 → 核心功能 → 高级功能 → 规模化

**影响阶段**: 生产版排期确认 4-5 周，与现有估算一致。关键路径在 Phase 3（说话人识别）。

### 6.3 2026-04-26 — 三人专家团队二次评审（技术风险 + 验证清单）

**触发**: 对首次风险评估进行独立交叉验证，并建立技术可行性验证门控

**发现**:
- **说话人识别降级**：从🔴关键降为🟠重要 — 工厂上报场景为单人说话，仅多人会议场景需要
- **智谱 API 依赖升级**：从🟠重要升为🔴关键 — ASR+路由+视觉三层全绑智谱，宕机=系统瘫痪
- **新增 9 项风险**：Flask debug RCE、磁盘增长、路由准确率、工厂网络、长转录分片质量、客户期望落差、时间估算偏乐观、LLM 格式漂移、API 费用失控
- **技术验证清单**：19 项独立验证点，全部通过则项目无技术可行性风险
- **当前验证进度**：1/19（5%），预计 2-3 周集中验证

**决策**:
- 安全漏洞（无认证 + debug=True）确认为 #1 关键风险
- 说话人识别不阻塞核心流程，作为 Phase 3 独立预研
- 每阶段预留 30% 时间缓冲

**影响阶段**: 风险数量从 6 项增至 15 项，但关键风险从 2 项减为 2 项（安全 + API 依赖），整体风险画像更准确。验证清单提供了明确的技术攻关路径图。

---

## Appendix: Mobile Testing Tool Guide / 移动测试工具指南

These tools serve different purposes at different stages — they are NOT alternatives to each other.

这些工具服务于不同阶段的不同目的——它们之间不是互为替代的关系。

| Stage / 阶段 | Tool / 工具 | Purpose / 目的 | Duration / 时效 |
|-------|------|---------|----------|
| **Development / 开发** | Flask self-signed cert (`ssl_context="adhoc"`) | Test microphone on Android via LAN | Temporary (adhoc cert per session) |
| **PoC Demo / 演示** | Cloudflare Tunnel (`cloudflared`) | Show to stakeholders from any network | Temporary (session-based URL) |
| **Production / 生产** | Capacitor APP | Ship as real mobile app (APK/IPA) | Permanent |

**Key distinction / 核心区别**:
- Self-signed cert and Cloudflare Tunnel are **testing tools** — they solve the HTTPS problem temporarily for development and demo.
- Capacitor is the **product solution** — it bypasses the HTTPS problem entirely by running as a native app.
- React Native is an **alternative product solution** — only needed if the app outgrows WebView capabilities.
