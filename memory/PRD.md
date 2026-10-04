# MART — Compute Credits & Running Token Agents

## CURRENT SCOPE — 2026-10-04 (supersedes all configuration-only historical sections below)

### Original problem statement
"Clone repo ini https://github.com/apartemen178-hash/Mrktpuls semuanya, lalu Tahapan selanjutnya adalah:
Menambahkan saldo operasional per token dengan rincian penggunaan dan batas biaya yang jelas (Kredit Compute)
Menambahkan satu pekerjaan riset manual dengan model pilihan kreator sebelum mengaktifkan pekerjaan terjadwal (Jalankan Agent)
Menambahkan perkiraan biaya berdasarkan model dan frekuensi kerja yang akan dijalankan sebelum kreator mengisi kredit agent (Estimasi Anggaran)
Buat agent berjalan juga untuk yg sudab ada di token hub buat agent berjalan dengan activity log event dll sesuai tokennya, oiyaa hapus konsep treasurynya"

### Explicit user choices
- Follow the existing repo model catalog.
- Use Emergent universal LLM key for REAL research.
- Internal testing credits only, no real-money payments.
- Remove treasury UI and flows; preserve historical data.

### Personas and core requirements
- Token creators: keep original selected model and private instructions; operate official agent through existing signed-wallet permission checks.
- Holders/visitors: read per-token research reports, credit usage, public activity, market and events.
- Existing unclaimed/unconfigured hubs: explicit bounded community-test research agent, NOT an official creator agent or ownership claim. Default Sonnet fixed; public visitors cannot edit its model.
- Preserve MART identity, integrated overview (no separate agent navigation), full original Launch/Trade/Market/Events/Community/Wallet app.
- Complete one successful manual research job with CURRENT model before scheduling; no token trading, private key access or automatic official event publication.

### Architecture decisions
- Full public main repo source imported into /app; workspace Git and protected environment URLs preserved. Git contains source, not the original deployment's database. Canonical FARTCOIN/BONK/WIF/POPCAT hubs are populated from existing original seed routine using real Solana/DexScreener data.
- React/FastAPI/Motor/Mongo retained. Additive compute_catalog/store/runner/routes/cron modules; existing core wallet authentication unchanged.
- Mongo compute_accounts keyed uniquely by token stores integer micro-credits, one active run lock, embedded ledger and events. Atomic reserve + compare-and-set settlement prevents negative balances/double charging. Run records separate and bounded; prompts/private instructions omitted from every public response and unset after completion/failure.
- Real streaming LlmChat SDK. UI polls persisted progress (not a scheduler). Provider usage supplies input/output totals including reported reasoning; unknown/missing usage fails without charging internal credits. Per-run cap 1,800 output tokens, 24,000 prompt bytes, 150s execution timeout. Truncated reports are visibly marked as partial, never auto-continued at extra cost.
- Internal versioned tariff `internal-test-v1`: measured usage produces CR charge. Not a provider invoice or redeemable currency. Estimator uses 2,500 input/800 output tokens and selected frequency over 30 days; tooling currently costs 0 CR. No external payment integration.
- Limits: initial 20 CR/run, 50 CR/day; 5 attempts/token/UTC day; global default40/day from env; up to100 CR/topup and1000 CR total token funding. Run/day settings bounded. Failed/interrupted runs release internal reservation and pause schedule (external provider may nevertheless incur real key usage).
- Single platform cron `.emergent/crons.yml`, every15min, /api/cron/research. Constant-time bearer secret, validated envelope, unique delivery ID, immediate2xx ack and background dispatch. Mongo per-schedule due claim and job idempotency; ownership rechecked;7day trial expiry. No APScheduler/custom infinite loop.
- Creator mode verifies existing agent.updated_by and source; external-authority sources recheck live authority. Community mode enabled by server COMPUTE_TEST_MODE only if no owner/profile. Schedules cannot continue as community if later claimed.
- Source Object Storage, market/chart and wallet endpoints retained. New environment config restored in ignored backend/.env; protected variables not changed; no secret in tracked files.

### Implemented — 2026-10-04
- Per-token credit balance, reserved credits, actual spending ledger, input/output token counts, returned reservation, daily progress, run count, limit editing and pause/resume.
- Real manual research with selected model, token-specific market snapshot, current MART events, community posts and listing counts; persisted Markdown report, source links, event drafts and report download.
- Existing hubs operate in clearly labelled community research test mode without altering official creator profile/ownership.
- Activity event lifecycle: credit/queued/observe/research/proposal/completed/failed/schedule/paused. Results and usage tabs in integrated hub.
- Model/frequency estimator before credit topup. Comparing does NOT change agent configuration. Hourly/6-hourly/daily/weekly schedule toggle gated by current-model successful manual run, next due display, changed-frequency apply button.
- All seven supported catalog models verified REAL: Sonnet4.5, Opus4.5, Haiku4.5, GPT5.2, GPT5mini, Gemini3FlashPreview, Gemini2.5Pro. Anthropic catalog IDs map to same-version dated provider IDs (not different models).
- DeepSeek R1/Qwen3/Mistral catalog entries retained as explicitly unavailable without separate provider connection. No silent model fallback.
- Removed all rendered treasury panels, allocations from Launch/AddToken, treasury event creation category and outdated public docs/copy. Legacy allocation documents are NOT deleted or mutated; old event category maps to Other on read. New profile writes exclude allocation.
- Original MART design preserved; responsive new control panels, budget band, activity timeline, and report/limits modals.

### Verification and resolved findings — 2026-10-04
- Production frontend build passes. Main-agent screenshots desktop1920x800/mobile390x844 zero horizontal overflow; live chart candles render.
- Real FARTCOIN manual report `2787f87fe66e416123434522dd25a387` and scheduled reports completed, ledger funded=balance+reserved+spent, actual provider usage recorded. Test schedules left disabled.
- iteration7:11passed/1owner-fixture skip. Mobile test incorrectly selected CSS id despite existing data-testid; added matching DOM id/htmlFor and retested. Its secret-commit concern was disproven by empty git ls-files/log for .env and git check-ignore.
- iteration8:7supplemental tests covered actual model calls, ephemeral-owner auth401/403/owner success, immutable model, token isolation, exact concurrency guard, no public private instructions, stale single-refund, scheduler ownership drift and mobile selectors. Five models passed initially; Gemini ChatError traced to unsupported thinking parameter.
- Gemini fix: remove Anthropic-style thinking object, preserve max_tokens1800. iteration9 full app regression confirms both Gemini completed, positive usage, exact tariff charge and ledger invariant;2/2 passed. Gemini2.5Pro can hit output cap, now UI explicitly warns report is partial rather than silently presenting full report.
- Test fixtures were isolated disposable mints/ephemeral wallets and cleaned. No mainnet payment/launch/trade submitted. Old historical suites requiring AI OFF/treasury are superseded.
- Final build successful (only inherited upstream Solana/superstruct missing-source-map warnings). Final screenshot `compute-final-desktop.jpeg`; partial-report warning verified at both exact viewports with TEST-ONLY browser response override of finish_reason (no DB/runtime mocks), zero overflow. No active schedules or orphan TEST_ONLY hubs remain.

### Prioritized backlog / next tasks
- P0: none outstanding in agreed compute/research scope; all7runtime models and critical credit/schedule/auth flows verified.
- P1: no deferred requested core feature. Real-money credits intentionally excluded per user choice; unsupported3provider connectors require separate future authorization.
- P2 optional visible enhancements: creator approval of AI event draft into official event; compare research reports over time; low-credit in-app notifications.
- Operational boundaries: trial credits,5attempt/token/day,40app/day; schedules off until manual success and explicit toggle, expire after7days. Research is grounded in available snapshots/MART data, NOT live news/social search. Provider-capped partial report is labelled.

---
# HISTORICAL SOURCE DOCUMENTATION (not current scope)

## LATEST CORRECTION — 2026-10-04 (supersedes the old Agent Studio design below)
User: "Lu salah bro ... penempatan agent itu bukan jadi sub menu di token hub, tapi jadi breakdown dengan chart dll ... semua di tentukan oleh kreator pas isi form token launch ... add token yg bukan launch di mart, juga ada form pilihan agent ... masukan fitur agent itu di landing page ... jangan gunakan kata kata seperti mind".

User confirmed: agent OPTIONAL in both Launch/Add Token. Additional request: after finishing, propose compute system so agents can operate like AgencyPad. Previous no-live-AI scope still applies.

### Corrected requirements and implementation
- Removed standalone agent page and all agent tabs/sub-tabs/public model editing. Legacy `/token/:mint/agent` redirects to the canonical token page.
- Main token page now integrates three columns: profile/activity, live DexScreener chart and trade links, compute/treasury. Original four ecosystem tabs remain below the overview. No extra agent tab.
- No configured agent means an honest empty state, not a default pseudo-agent. Public profile excludes private operating instructions. No browser draft is ever displayed as a token's real profile.
- Shared optional AgentCreatorFields inside Launch and a full Add Token form/page. Both default off; inline provider/model options, persona, mission, private instructions, capabilities, creativity and proposed allocation.
- Launch form accessible before wallet sign-in; upload/submission still require wallet. Existing Pump.fun transaction construction/signing/confirmation retained. Private agent snapshot saved at prepare; attached only after exact successful finalized transaction verification. No agent details leaked in public token metadata.
- No-agent imports remain public; imports with agent require signed wallet session and fresh Metaplex update-authority check BEFORE agent writes. Reimports never delete or replace an existing configured agent. Attachment idempotent under unique token index.
- Finalized original MART launch provenance is sufficient for its own chosen profile attachment; it does NOT claim that program-controlled metadata authority belongs to the creator. External renounced/program-controlled tokens need a different future verification path; current import fails closed.
- Landing now explains optional creator-configured agents and links to Launch/Add Token. MART branding retained; forbidden copied term removed from app copy.
- Added `/docs/ecosystem-agents`, `/docs/agent-compute` and `/app/memory/COMPUTE_PROPOSAL.md`. Compute roadmap only: hosted APIs + separate per-token usage ledger + creator topups first + bounded jobs + deterministic financial policy, no actual runtime/fee custody activated.
- Shared schema `/app/backend/agent_schema.py`; new attachment service in `agents.py`; creator snapshots integrated into `hubs.py` and `launch.py`. Auth core and transactions/send unchanged.
- Production build and initial external APIs passed. Desktop/mobile screenshots of Hub/forms/landing: zero overflow. New comprehensive correction tests pending.
- Found original DexScreener embed returns "No data here". Replaced integrated embed with real native candlestick+volume chart (lightweight-charts v5) backed by keyless GeckoTerminal OHLCV; four intervals, manual refresh, 60s Mongo cache, coalesced upstream access, explicit error/backoff, correct USD/mint orientation, public attribution. Kept DexScreener snapshot and external chart links. 160 real candles verified externally. Fixed chart locale to en-US because browser reports invalid en-US@posix.

### Current backlog
- P0: none outstanding in agreed correction scope; comprehensive verification completed below.
- P1 requested next: choose and implement actual compute funding/runtime only after user approves next phase/integrations.
- P2 optional enhancement: compute budget estimator; public run receipts and creator pause controls in live-runtime phase.

### Correction verification completed — 2026-10-04
- `/app/test_reports/iteration_5.json`: 13/13 correction backend tests passed; UI Launch/Add Token optional form, integrated chart, native chart interval/refresh, no Agent submenu, legacy route redirect, landing/docs and entry points passed.
- Iteration5 flagged a literal `/token/FARTCOIN` test URL due shorthand in my test brief. Actual user/source contract is mint-only canonical identity. `/token/9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump` works; no ticker alias should be added. Iteration6 explicitly resolves this false positive.
- `/app/test_reports/iteration_6.json`: 10/10 additional executed isolated backend tests passed: private launch snapshot, exclusion from metadata, finalized exact-hash confirm gating, original creator provenance, idempotent attachment, rejected failed/unfinalized/wrong-wallet/wrong-hash cases, authority-only import, immutable conflict, no-agent non-destructive import, public private-field exclusion.
- Configured-profile browser rendering (60-character unbroken name and long mission) tested at 1920x800 and 390x844 using TEST-ONLY response interception, leaving real price chart untouched. No runtime mock or permanent profile fixture created. This is presentation coverage, not a claim of executing a real mainnet launch.
- Real native chart rendered candles/volume; mobile evidence `/app/test_reports/iteration5-native-chart-mobile-390x844.jpeg`. Desktop and mobile no horizontal overflow. Main-agent inspected mobile evidence and desktop candlesticks.
- Production build successful; only inherited upstream source-map warnings. No mainnet transaction submitted; authorized launch/authority-success paths use isolated fixtures. Real anonymous imports, rejected non-authority imports, public token/profile data and OHLCV exercised through external preview.
- Latest test reports list no outstanding app bugs. Old Agent Studio tests reflect superseded UX and are historical, not current acceptance criteria.
- Runtime AI, credits billing, scheduler, agent financial actions remain intentionally OFF. Current work is correction/configuration + requested compute proposal.

---
## Historical first implementation (SUPERSEDED by latest correction above)

## Original problem statement
Bro gue mau lu clone github repo ini semuanya https://market-pulse-2620.preview.emergentagent.com/
Lalu gue mau lu menambahkan konsep agent kaya https://www.agencypad.fun/ di token hubnya dan pilihan model ai nya breakdown token hubnya kaya gini https://www.agencypad.fun/coin/H7TuvDxEKygh27zGfGcjKG8JGWgrbyKpPtvJEpGosfas
Tapi jangan hilangkan konsep utama di github repo ini https://market-pulse-2620.preview.emergentagent.com/launch
Fitur agent yang seperti https://www.agencypad.fun/ hanya sebagai tambahan fitur saja

## Explicit user choices
- Source repo: https://github.com/banyakinaja13-prog/Mrkepulse
- First phase: agent presentation, profiles, model choices, token-hub breakdown.
- No real AI integration; focus on additional feature and appearance.
- Keep original MART and its launch concept. Do not replace it with AgencyPad.

## Personas
- Visitors/holders explore token markets, community and agent profiles.
- Creators configure an agent persona and allocation draft.
- Verified on-chain token authorities can publish a public profile.

## Core requirements (static)
- Import entire app source and preserve original routes, branding, components, launch, wallet, commerce, events and community.
- Add optional `/token/:address/agent`; retain Market as original default Hub tab.
- Agent identity, role, mission, provider/model selection, capabilities, treasury/allocation and activity breakdown.
- Clear separation of browser-local drafts, published profiles, live market data and inactive AI/treasury functions.
- Responsive desktop/mobile and no autonomous fund movements.

## Architecture decisions
- Imported public main branch commit `1642d3a2f9ba590e8261027399f124081cf651c3`; preserved existing environment/dependency management; source PRD saved separately.
- React 19, React Router, existing shadcn/Radix, original dark emerald MART design. New isolated `agent.css` and agent components.
- FastAPI/Motor/MongoDB with additive `agents.py`. No LLM SDK calls or agent task scheduling.
- Public GET model catalog and agent profile; POST validation; authority-gated PATCH publication. Pydantic validation and response models; Mongo `_id` excluded. Unique agents.token index.
- Browser-local draft per token; real local save history. Published configuration history stored in MongoDB. Never manufacture operational agent activity or balances.
- Existing wallet signature authentication reused unchanged. Publication validates claimed_by and fresh on-chain authority, fail-closed.
- Existing image upload contract preserved; new files use Emergent Object Storage and only metadata in MongoDB. Legacy image reads remain compatible.
- All API addresses from existing environment; public Solana RPC, DexScreener, PumpPortal infrastructure preserved.

## Implemented — 2026-10-04
- Full source imported (135 files); original home, Explore, Launch, Trade, Market, Events, Community, Wallet, Docs retained.
- Added Agent tab, compact Hub discovery strip, overview/configuration/activity views.
- Profile persona presets, editable mission/instructions, strategy posture/creativity controls, seven capability toggles.
- Searchable model picker: 10 catalog entries across Anthropic, OpenAI, Google, DeepSeek, Qwen, Mistral. Catalog-only, no real provider integration.
- Proposed five-part treasury allocation with 100% validation, unlinked balances shown as unavailable, real marketplace/event/post counts.
- Save/reload/reset local drafts; public publish confirmation and authority gating; actual configuration activity history.
- Backend validation: bounded inputs, supported model IDs/capabilities, total allocation, explicit execution_enabled=false.
- Image upload migrated to object storage while keeping source API paths.
- Production build passed with only pre-existing upstream Solana/superstruct source-map warnings. Desktop 1920x800/mobile 390x844 screenshots: zero horizontal overflow.

## Availability boundaries
- AI intentionally off, no connected model providers, no chat/generation or autonomous actions.
- Allocation is a proposal, not funded treasury accounting. No simulated balance or trading returns.
- Browser drafts are private to the browser, not cross-device/server-synced. Verified authority required for public profile storage.
- NFT minting/trading remains unavailable as in source. Paid mainnet launch/checkout and actual extension approval are not executed during tests.
- Public RPC/indexer may rate limit. Source handling remains intact.

## Prioritized backlog
- P0: none outstanding in agreed agent-configuration scope.
- P1: no additional required features beyond agreed first phase.
- P2 optional: export/import agent configurations; shareable agent profile card; side-by-side model comparison.
- Live AI and treasury automation intentionally outside requested scope, not pending setup.

## Verification — 2026-10-04
- Testing report `/app/test_reports/iteration_4.json`: 22/22 backend tests passed. New suite `/app/backend/tests/test_agent_storage_regression.py`.
- Verified real catalog/default profile APIs, validation rejections, unauthenticated/non-authority gates, off-chain signed challenge/replay rejection, object storage upload/download and metadata-only database records.
- Authority-success and failure logic verified in ISOLATED fixtures only; no mainnet metadata changed and no real authority-owned profile published during tests.
- Browser tests passed model/provider filtering, no-results, draft save/reload/isolation, reset confirmation, invalid allocations, persona/config fields, actual configuration history, publish/connect flow, and source-page regression checks.
- Follow-up self-test completed real backend off-chain authentication using a browser-injected ephemeral Ed25519 wallet. Connected non-authority publication was blocked, publish action absent. This resolves the test agent's remaining UI coverage gap. No transaction signed or sent.
- Source `Launch.jsx` is byte-identical to imported original. Its connected-wallet launch form also verified at desktop/mobile without submitting a transaction.
- Explore sort already has `data-testid="explore-sort"` via the shared Choice component. Follow-up browser verified the trigger and `explore-sort-market-cap` option work; report suggestion required no code change.
- Tested all required viewports at exact 1920x800 and 390x844; final model modal, config form, long-text profile, overview, home and connected-wallet launch had zero horizontal overflow.
- DexScreener iframe may emit a third-party analytics CORS warning; preserved original chart integration and existing external chart link. MART market data and core flows were unaffected.
- No production runtime mock API. Agent is deliberately configuration-only, not fake AI. No permanent test accounts or public profile seed data added.

## Next tasks
Await user feedback on this additive Agent Studio. Optional next additions: shareable profile card, configuration export/import, model comparison. Keep live AI and treasury automation out of scope unless explicitly requested.