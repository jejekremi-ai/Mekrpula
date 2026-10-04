# MART

## Original problem statement
Build MART, “A market built around every token.” Pump.fun remains the launch/trading infrastructure; MART is an ecosystem layer. Flow: MART Launch → Pump.fun → canonical Solana token mint → automatically create Token Hub → Trade | Market | Events | Community. Landing copy: “Launch on Pump.fun. Build your market on MART.” Primary Launch Token and Explore MART CTAs. Clean modern crypto-native terminal + marketplace + community, strong wordmark, restrained gradients, strong typography and product imagery.

Add existing Solana tokens by mint address; retrieve name/symbol/logo/decimals/on-chain identity and market data, open existing Hub on duplicates. Each token has its own token-denominated market (no global market). Categories NFT Existing/Create, Artwork/Meme Pack/Wallpaper/GIF, Physical T-shirt/Hoodie/Poster/Sticker. Seller wallet automatically connected, not typed. Listings image/name/type/description/price/quantity. Actual transfers must be wallet-signed and verified on-chain; no custodial funds or unnecessary contracts.

Externally added tokens are unclaimed; adding is not ownership. Verify metadata authority before claims and privileged changes. Official events are announcements only, title/image/type/description, no funding/proof fields. Types Holder Reward, Airdrop, Buyback, Burn, LP Action, NFT / Asset Distribution, Treasury Distribution, Other. Hub ticker links to events. Global Events has Live/Coming Soon/Past. Token communities have text/images/replies/likes. Wallet shows balances, NFTs, listings, purchases, events, created tokens. NFT mint/storage must be seller-funded and exchange atomic through standard infrastructure, no unauthorized backend transfer.

### User choices
- Solana mainnet, real user-signed transactions and fees.
- Public services first; identify any features requiring credentials.
- Complete first version across all sections, live blockchain where supported.
- “Tambahkan gambar contoh yg keren gitu di landing page nya” — cool sample imagery on landing.

## Architecture
React 19 + existing shadcn/Radix + custom Outfit/IBM Plex dark emerald visual system, React Router, sonner. FastAPI modules, Motor/MongoDB database. Env-based public Solana RPC, DexScreener, PumpPortal local transaction provider. No wallet private keys ever sent to backend. Signed single-use nonce authentication and expiring hashed sessions. Media is validated/re-encoded JPG in MongoDB, served through API. Pump launch metadata immutable API document hosted by MART (not decentralized permanent storage).

## Implemented
- Responsive illustrated landing with curated stock digital art/merch concept cards; imagery is inspiration, never fake purchasable inventory.
- Explore search by address/name/symbol, sort, verified filter, grid/list, canonical token cards. Four explicitly pinned real mints (Fartcoin, BONK, WIF, POPCAT) fetched from chain + DexScreener; never ticker-based identity.
- Add Token validates actual mint program/type; unique DB index + duplicate-open behavior.
- Token Hub market default, chart iframe/trading redirects to Pump.fun, real market snapshot, recent mint activity with Solscan links; no fabricated price history.
- Phantom/Solflare injected wallet connection and signature verification, account change cleanup.
- Non-NFT artwork/physical listing creation, image upload, removal, isolated per-token pricing with exact base units. Token-2022 market sales gated pending extension validation.
- Standard SPL-token noncustodial checkout, buyer fee payer + idempotent seller ATA + TransferChecked + unique order memo. User signs, server only relays exact stored transaction. Reservation prevents oversell; buyer can release after transaction expiry. Finalized on-chain message hash verification, signature uniqueness, private delivery details, seller fulfillment notes, My Purchases/My Sales recovery.
- PumpPortal local create transaction + locally generated mint keypair, user-signed launch; exact message verified at relay and finalization. Automatic Hub only after confirmed mint. No actual paid launch performed by agent.
- Authority-based claim and management endpoints/UI, official events creation/status, global filters, event detail, moving real-event ticker.
- Community text/image posts, atomic like toggle, replies; persisted MongoDB data.
- Wallet token balances across standard/2022 programs, SOL, listings/purchases/sales/events/created tokens.

## Explicit availability limits
- NFT minting, durable NFT storage, indexed discovery and atomic NFT exchange are not enabled: need a DAS/storage provider and configured audited standard exchange. UI explains requirements; never simulate NFT ownership/transfer success.
- Public RPC/indexer is rate limited; errors surfaced, no fake success. Charts can be unavailable; external chart link remains.
- Paid mainnet launch/payment execution needs a real user wallet approval and has not been executed in testing.
- No authentication mocks or fake financial metrics in runtime application.

## Prioritized backlog
P0: No known blockers in tested off-chain flows. Funded mainnet launch/payment and real installed-extension UAT remain unexecuted; never treat isolated fixture tests as proof of an executed mainnet transaction.
P1: Dedicated reliable RPC/DAS, decentralized persistent metadata uploader, standard configured atomic NFT marketplace and seller-funded minting. Controlled user-approved tiny mainnet launch and checkout validation.
P2: Marketplace fulfillment/dispute policies, moderation/reporting, notifications, creator analytics, stricter distributed rate limiting.

## Next tasks
Later connect NFT providers and configure audited exchange. Validate a user-approved low-value launch and checkout, including real browser-extension transaction signing, before accepting high-value commerce.

## Verification results
- `/app/test_reports/iteration_1.json`: 20/20 live API regression tests passed, unsigned desktop/mobile navigation passed.
- `/app/test_reports/iteration_2.json`: 15/15 isolated payment/launch/authority fixture tests passed. RPC and authority responses substituted only in test fixtures, not the running app.
- Final self-check completed signed browser login (ephemeral unfunded injected wallet, actual server nonce signature verification), upload/publish/remove listing, post/like/reply, every wallet tab, disconnect. No on-chain transaction signed or submitted by tests.
- Resolved unique modal test-ID collisions, double-submit button guard, community reply drafts disappearing during refresh, Sonner mobile overflow, dialog animation overflow, and cramped mobile wallet header.
- Request-driven expired-order reconciliation releases unsigned/failed expired reservations once and verifies exact finalized payments, without background loops or scheduled tasks.
- Final screenshots at 1920x800 and 390x844: zero horizontal overflow in home, Hub, community, wallet, listing dialog including long text. `/app/mart-wallet-final-mobile.jpg`, `/app/mart-dialog-final-mobile.jpg`, desktop equivalents.
- `yarn build` passes. Remaining warnings are missing source maps in upstream Solana/superstruct dependencies (not application build errors).
- Test listing/post/media artifacts removed; four canonical token Hubs retained. Public preview briefly slept during long agent tests, then recovered; final public browser checks passed.

## Content expansion — preserve existing MART (current request)

### User requirements and explicit clarification
- DO NOT redesign/rebuild the existing website. Preserve original style, layout, components, navigation, animations, existing sections, and behavior. Add comprehensive product information rather than simplifying the landing page.
- User explicitly approved replacing ONLY the hero sample-art collage with a tilted Token Hub preview like the two attached screenshots. Keep hero headline, structure, buttons, and surrounding styling unchanged.
- User approved updating existing landing copy to MART-focused wording. Pump.fun is no longer in landing body/meta; relevant new documentation explains it as technical implementation detail. Existing operational launch/trade flows are unchanged.
- Social labels X, Discord, Telegram must have no links; do not invent profiles.
- Add About MART; Our Vision; Our Mission; How MART Works (Launch, Token Hub, Build, Grow); Token Hub explanation; token-denominated Market explanation and all categories; eight event types and non-guarantee disclaimer; community capabilities; existing-token flow; Unclaimed/Verified; Why MART; future directions without dates/promises; ten FAQ entries; twelve Docs topics; expanded Product/Resources/Social footer.

### Implementation boundaries
- No backend, original `App.css`, original `index.css`, wallet signing, marketplace, event, or community feature changes.
- Small targeted integration edits only in `Home.jsx`, `Shell.jsx`, `App.js` and page metadata.
- New isolated `content.css` styles reuse the current visual system and apply only to the new sections/preview/docs/footer additions.
- Hero illustration now shows a Token Hub, four miniature ecosystem tabs, digital artwork/merch concepts, and functional Explore/Hub links. It explicitly labels products as illustrative, not live listings.
- All original featured token cards, original category imagery sections, original quick ecosystem flow, and original final CTA retained.
- Reusable informational components in `src/components/information/`; shared FAQ/categories/events/docs data in `src/content/mart.js`.
- `/docs` and `/docs/:topic` provide Introduction, What is MART?, Token Hubs, Markets, Listings, NFTs, Events, Community, Add Token, Token Verification, Fees, Security. Desktop topic sidebar, mobile topic chooser, in-guide anchors, previous/next guides, and graceful missing-topic page.
- Footer expanded without removing the original brand/link row. Market and Community links go to explanatory landing anchors, never a global marketplace route. Social names are noninteractive text.
- Add Token buttons in new sections/footer/docs reuse the existing header modal through a small browser event; no duplicate submit logic or token identities.
- Hash-aware scrolling supports cross-route and repeated same-anchor clicks while retaining existing scroll behavior for normal search/filter query changes.
- Copy preserves real feature limits: NFT minting/exchange is not currently enabled; event announcements do not guarantee execution; Verified does not imply investment safety; payments are direct, not escrow.

### Content verification
- `/app/test_reports/iteration_3.json`: all content/routes/footer/Add Token/FAQ/responsive checks passed except repeated same-hash scrolling. That issue was fixed and independently retested.
- Final self-check: About, Markets, Community, FAQ anchors clicked twice each at both desktop 1920×800 and mobile 390×844; all re-scrolled correctly (16 successful checks). Repeated Docs section anchors, cross-route Docs→FAQ, and reuse of the original Add Token modal also passed.
- Home and Docs screenshots at both required widths: no horizontal overflow. Expanded footer, market example, About, FAQ, and the hero preview visually checked.
- `yarn build` passes with only pre-existing upstream Solana/superstruct source-map warnings.
- No new credentials, integrations, paid transactions, sample listings, or database seed records created for this content update.

### Optional content follow-up
- Add illustrated onboarding walkthroughs for creators and sellers if requested; retain the existing visual system.