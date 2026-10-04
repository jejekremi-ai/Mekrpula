export const MARKET_CATEGORIES = [
  { name: 'NFT', items: ['Existing NFT', 'Create NFT'], note: 'Minting and exchange require configured NFT services; not currently enabled.' },
  { name: 'Artwork', items: ['Artwork', 'Meme Pack', 'Wallpaper', 'GIF'] },
  { name: 'Physical', items: ['T-shirt', 'Hoodie', 'Poster', 'Sticker'] },
];

export const EVENT_TYPES = ['Holder Reward', 'Airdrop', 'Buyback', 'Burn', 'LP Action', 'NFT / Asset Distribution', 'Other'];
export const FUTURE_DIRECTIONS = ['More marketplace categories', 'Better creator tools', 'More community features', 'Better token discovery', 'More commerce functionality', 'More integrations', 'More ways for communities to create activity around their tokens'];
export const FAQ_ITEMS = [
  { id: 'what-is-mart', question: 'What is MART?', answer: 'MART is a Solana platform built around tokens, combining launching, trading, markets, events, and communities. A token is the starting point—not the whole experience.' },
  { id: 'token-hub', question: 'What is a Token Hub?', answer: 'A Token Hub is the central page for everything around a token. It brings together Trade, Market, Events, and Community, using the Solana token address as its unique identity.' },
  { id: 'market', question: 'What is the Market?', answer: 'A token-specific marketplace where products can be bought and sold using that token. Markets live inside individual Token Hubs; there is no mixed global marketplace.' },
  { id: 'existing-token', question: 'Can I add an existing token?', answer: 'Yes. Compatible Solana tokens can be added to MART. Use + Add Token, paste the mint address, and MART fetches the token information. If a Hub already exists for that address, it opens instead of creating a duplicate.' },
  { id: 'launch-required', question: 'Does a token have to launch on MART?', answer: 'No. Existing tokens can also be added. A token does not need to be relaunched or replaced to get its own Token Hub.' },
  { id: 'products', question: 'What can be sold in a Market?', answer: 'The market categories cover NFTs, artwork, meme packs, wallpapers, GIFs, and selected physical products. Artwork and supported physical listings are available now. NFT minting and sales are not yet enabled; they require storage and an atomic exchange integration.' },
  { id: 'listing', question: 'Can anyone create a listing?', answer: 'Community members can create supported marketplace listings by connecting their wallet and signing in. The connected wallet is used as the seller identity. A Token Hub can have community listings even while it is unclaimed.' },
  { id: 'events', question: 'What are Events?', answer: 'Structured announcements for activities happening around a token, such as rewards, drops, or community plans. Official events are published by the verified token authority.' },
  { id: 'guarantee', question: 'Are Events guaranteed?', answer: 'No. Events are announcements and do not guarantee execution, funding, rewards, distributions, or returns. Read the details and make your own assessment before participating.' },
  { id: 'unclaimed', question: 'What is an Unclaimed Token?', answer: 'A token that has a MART Token Hub but has not yet been officially claimed and verified. Adding a token does not make the person who added it the official owner. A legitimate, verifiable token authority can claim the Hub later.' },
];

const AGENT_DOCS = [
  {
    slug: 'ecosystem-agents', title: 'Ecosystem Agents', label: 'AN OPTIONAL ADDITION', summary: 'Creator-defined agents, integrated into the token—not a separate destination.',
    sections: [
      { title: 'Choose it at the start', paragraphs: ['Launch and Add Token each include an optional Ecosystem agent section. Choose a name, role, provider, model, and mission. Model selection belongs to the creator form, not the public Token Hub.', 'The selected profile is fixed once attached. Private operating instructions are not returned by the public profile endpoint.'] },
      { title: 'A breakdown alongside the chart', paragraphs: ['A Token Hub combines the price chart, agent profile, research reports, activity log, compute credits, and budget estimate. Trade, Market, Events, and Community remain underneath.', 'Existing unclaimed tokens without creator profiles have a clearly labelled community research agent in test mode. It does not represent the official creator or change token ownership.'] },
      { title: 'New tokens and existing tokens', items: ['New launch: the profile is saved with the launch request, then attached only after the creator’s exact transaction is finalized successfully on Solana.', 'Existing token: adding a token without an agent stays public. Attaching an agent requires a signed-in wallet and a fresh on-chain metadata update-authority check.', 'Program-controlled or renounced metadata authority: an external token cannot attach an agent through the current self-service import check. A confirmed original MART launch uses its verified launch provenance instead.', 'Re-importing a token without an agent does not remove an existing profile. Re-importing never replaces its selected configuration.'] },
      { title: 'Current availability', notice: 'Real research is available with internal test credits. No real-money top-up or automated transaction is performed.', paragraphs: ['Anthropic, OpenAI and Google catalog models can execute research. DeepSeek, Qwen and Mistral remain catalog choices requiring a separate provider connection; no automatic model substitution occurs.', 'Research uses token market snapshots, MART events and community posts. Results include draft event ideas, never automatically published official events. No live news or social-media search is implied.'] },
    ],
  },
  {
    slug: 'agent-compute', title: 'Agent Compute', label: 'CREDITS & RESEARCH', summary: 'Per-token operating credits, real research, and visible cost limits.',
    sections: [
      { title: 'What compute means', paragraphs: ['CR is a non-redeemable internal testing unit, not a currency, token asset or provider invoice. AI calls are real and use the connected provider key.', 'The versioned internal tariff charges measured input/output tokens. Market data tools currently cost 0 CR. Cached and reasoning tokens are included in provider-reported input/output totals where reported; no cache discount is assumed.'] },
      { title: 'Estimate before adding credits', items: ['Compare catalog models and hourly, six-hourly, daily or weekly frequency before adding credits.', 'Estimates assume 2,500 input and 800 output tokens per research job, projected over 30 days. Actual reports vary.', 'Model comparison does not change the creator-selected model. Credits and schedules remain isolated by token.', 'Add 100 test credits per request, up to 1,000 CR total per token. No wallet payment occurs.'] },
      { title: 'A bounded execution cycle', items: ['Run one manual research job before enabling any schedule for that model.', 'Reserve the maximum bounded job cost before inference. A single job may run per token; spend cannot exceed its reserved credits.', 'The ledger records measured input/output usage, charged credits and released reservation. Failed jobs return internal test credits; the external provider may still incur usage.', 'The agent never receives a wallet private key, publishes an official event, or executes a transaction. Event ideas remain drafts.'] },
      { title: 'Scheduled research', paragraphs: ['Enabled schedules are checked every 15 minutes and run at their selected frequency. A successful manual run with the current model is required.', 'Test schedules expire after seven days. Insufficient funds, authorization changes or failed runs pause scheduling. Pausing the agent also disables its schedule.', 'Safety limits are five attempts per token per UTC day and an application-wide daily cap. Frequency estimates describe the requested workload; these safeguards may reduce completed runs.'] },
      { title: 'Creator and community modes', paragraphs: ['Only the authorized creator can operate a creator-configured agent. Existing unclaimed hubs without a profile have a bounded public community test agent with a fixed default model, not an official endorsement.', 'Re-importing or claiming a token does not delete historical balances, reports, or records. All timestamps and source links remain attached to the original token mint.'] },
    ],
  },
];

export const DOCS = [
  {
    slug: 'introduction', title: 'Introduction', label: 'START HERE', summary: 'A practical guide to building a world around your token.',
    sections: [
      { title: 'A market built around every token.', paragraphs: ['MART is a Solana token launchpad and token ecosystem platform. It connects trading, token-denominated commerce, events, and community around a single token identity.', 'Start by exploring a Token Hub, adding an existing token, or configuring a new launch. You can browse without connecting a wallet. Signing in is required to post, list items, or manage your activity.'] },
      { title: 'Choose your starting point', items: ['Explore: discover existing Token Hubs and open their Market, Trade, Events, or Community sections.', 'Launch: connect your wallet, configure the token, review fees, and sign the creation transaction. A Hub is created after on-chain confirmation.', 'Add Token: paste the mint address of a compatible existing Solana token. An existing Hub opens automatically if it has already been added.'] },
      { title: 'Technical implementation', paragraphs: ['MART is the ecosystem layer, not a replacement token or trading engine. New token creation currently uses Pump.fun infrastructure through PumpPortal’s non-custodial local transaction integration. Trading opens the appropriate Pump.fun experience. Native candle history comes from GeckoTerminal; market snapshots and external chart links use DexScreener.', 'Your wallet signs the transaction. The resulting Solana mint address becomes the canonical identity in MART. Adding a Hub does not mint a duplicate token.'] },
      { title: 'Know what is available', paragraphs: ['Public data providers can be rate limited. A missing chart or temporarily unavailable market value is not a zero balance or a successful transaction. NFT minting, indexed NFT discovery, and atomic NFT sales remain unavailable until their required services are configured.'] },
    ],
  },
  {
    slug: 'what-is-mart', title: 'What is MART?', label: 'THE PLATFORM', summary: 'More than a launch. A connected experience around the token.',
    sections: [
      { title: 'A token gets a home', paragraphs: ['A token can have a chart, a social account, a community, and activities scattered across different platforms. MART brings those experiences together around the token itself.', 'The goal is to help token communities turn attention into activity: trading, discovering products, participating in events, and creating together.'] },
      { title: 'One token, one identity', paragraphs: ['The Solana mint address—not the token name, ticker, or logo—is the unique identity of a Token Hub. Different tokens can use the same name, so always check the address.', 'MART is not one global marketplace. Each token has its own Market, priced in that token. Global Explore and Events help you discover the ecosystem without mixing those markets together.'] },
      { title: 'A direction, not a promise', paragraphs: ['MART’s long-term vision is for tokens to support communities, cultures, brands, economies, and digital worlds. Future capabilities are a direction for development, not dated commitments or guarantees of value.'] },
    ],
  },
  {
    slug: 'token-hubs', title: 'Token Hubs', label: 'THE TOKEN’S HOME', summary: 'Trade · Market · Events · Community. One address brings it all together.',
    sections: [
      { title: 'Find your way around', items: ['Trade: follow market data and recent on-chain activity, open a chart, and access the available external trading experience.', 'Market: discover products from the community, priced in the Hub’s token.', 'Events: read official structured announcements and follow the Hub’s event ticker.', 'Community: create posts, share images, reply, and like discussions.'] },
      { title: 'Read the header', paragraphs: ['The header identifies the token by name, symbol, and mint address. Market data can include price, market capitalization, volume, and liquidity. These are provider snapshots, not guaranteed execution prices.', 'Use the copy-address and explorer controls to verify the token. The Unclaimed or Verified label describes control of the Hub, not investment quality or seller reliability.'] },
      { title: 'Manage an official Hub', paragraphs: ['A verified authority wallet can edit official Hub information and publish events. Authority is re-checked for sensitive changes. Community members can participate without becoming official Hub owners.'] },
    ],
  },
  ...AGENT_DOCS,
  {
    slug: 'markets', title: 'Markets', label: 'THE HEART OF MART', summary: 'Products priced in the token. Activity rooted in its community.',
    sections: [
      { title: 'Enter a token’s Market', paragraphs: ['Open a Token Hub and select Market. Use All items, NFT, Artwork, or Physical to explore its categories. Each listing displays its token price, item details, and available quantity.', 'A price such as 10,000 $ABC means 10,000 units of that Hub’s token—not SOL and not US dollars. Check the mint address as well as the symbol before paying.'] },
      { title: 'Buy an item', items: ['Connect your wallet and sign in.', 'Open the listing, review the seller and item description, and provide the requested delivery contact or shipping details.', 'Review the exact token amount and SOL network/account fees in your wallet before signing.', 'After submission, check payment finalization from checkout or My Purchases. A submitted transaction is not yet a confirmed purchase.', 'View the seller’s shipping or digital-delivery updates in My Purchases.'] },
      { title: 'Payment and delivery are different', paragraphs: ['Supported SPL-token payments go directly from buyer to seller. MART does not custody funds or provide escrow in this flow. The seller is responsible for delivering physical or digital goods.', 'Pending orders reserve inventory. Expired unsigned or failed payments can be released after their on-chain validity window ends. Never assume an event, listing, or Verified Hub badge guarantees fulfillment.'], notice: 'Market payments currently support standard SPL tokens. Token-2022 transfers with extensions need additional validation and are not enabled for checkout.' },
    ],
  },
  {
    slug: 'listings', title: 'Listings', label: 'FOR CREATORS & SELLERS', summary: 'Bring something meaningful to your token’s market.',
    sections: [
      { title: 'Create a listing', items: ['Open the correct Token Hub and select Market → Add Listing.', 'Connect and sign in with the wallet that will receive payments. MART fills in the seller identity from this wallet.', 'Choose an item type and upload an image (PNG, JPG, or WebP, up to 5 MB).', 'Add the item name, an accurate description, the token-denominated price, and available quantity.', 'Include what the buyer receives and how you will deliver it. Publish the listing when the information is complete.'] },
      { title: 'Price it correctly', paragraphs: ['The price must be positive and respect the token’s decimal precision. Make sure you have selected the intended Hub: a listing in $ABC Market is priced in $ABC, not another token.', 'Adding a token does not grant ownership of its Hub, but community members can still publish supported listings in an unclaimed Hub.'] },
      { title: 'Manage your sales', paragraphs: ['Open My MART → My Listings to review or remove your listings. Paid orders appear in My Sales. Add tracking information or digital delivery details to mark an order fulfilled.', 'Only you and the buyer can access the order’s delivery information through the authenticated order views. Use it only to fulfill the order, and avoid requesting unnecessary personal information.'] },
    ],
  },
  {
    slug: 'nfts', title: 'NFTs', label: 'COLLECTIBLES', summary: 'Existing NFTs and creator-minted work—with ownership and authorization at the center.',
    sections: [
      { title: 'Current availability', paragraphs: ['NFT categories are part of MART’s product direction, but NFT minting, indexed discovery, and atomic NFT sales are not currently enabled. They require durable artwork storage, an asset indexer, and a configured standard atomic exchange.'], notice: 'No NFT mint or NFT purchase is being completed by the current NFT forms. Do not send funds independently to “activate” this feature.' },
      { title: 'Existing NFT: intended flow', items: ['Connect the wallet that owns the NFT.', 'Select an eligible NFT and verify on-chain ownership.', 'Review and sign the required listing authorization.', 'On a completed sale, payment and NFT transfer must happen atomically through supported standard infrastructure.'] },
      { title: 'Create NFT: intended flow', paragraphs: ['A creator provides artwork, name, description, supply, and token price. Once the necessary services are available, the creator—not the platform by default—pays storage, minting, and network costs.', 'Minted assets should first belong to the creator’s wallet. A backend cannot transfer an NFT from a wallet without the appropriate signed authorization.'] },
    ],
  },
  {
    slug: 'events', title: 'Events', label: 'COMMUNITY MOMENTS', summary: 'A structured way to communicate what is happening around a token.',
    sections: [
      { title: 'Discover events', paragraphs: ['Open Events in the main navigation to browse Live, Coming Soon, and Past announcements across tokens. Select an event to read its details and open its Token Hub.', 'Each Hub also has its own Events section and a ticker linking to its active announcements.'] },
      { title: 'Publish an official announcement', paragraphs: ['A verified token authority can create an event with a title, image, type, description, and status. Include timing and participation details in the description. There are no funding or proof-of-funds fields.', 'The verified authority can change an event’s status on its detail page. A Coming Soon label or Live status describes the announcement; it does not trigger a blockchain action.'] },
      { title: 'Supported event types', items: EVENT_TYPES },
      { title: 'No guarantee of execution', paragraphs: ['Events are announcements and community activity. MART does not guarantee execution, funding, token distributions, buybacks, burns, rewards, or returns. Verify any claims independently.'] },
    ],
  },
  {
    slug: 'community', title: 'Community', label: 'THE PEOPLE BEHIND THE TOKEN', summary: 'Keep the conversation around the token in one place.',
    sections: [
      { title: 'Join the conversation', items: ['Open Community inside the relevant Token Hub.', 'Connect your wallet and sign the free sign-in message to participate.', 'Create a text post and optionally attach an image.', 'Reply to discussions or like a post. Likes can be toggled off.'] },
      { title: 'Make it useful', paragraphs: ['Discuss events, share artwork, exchange ideas, or talk about the token. Each community belongs to its token; a post in one Hub does not become a global post.', 'Community posts are not official announcements. Be respectful, do not impersonate the project, and never share private keys, seed phrases, or another person’s delivery information.'] },
    ],
  },
  {
    slug: 'add-token', title: 'Add Token', label: 'BRING YOUR COMMUNITY', summary: 'Your token does not have to start here to belong here.',
    sections: [
      { title: 'Add an existing token', items: ['Select + Add Token in the header, footer, or existing-token section.', 'Paste the Solana token mint address—not a wallet address, transaction signature, or pool address.', 'MART checks the mint on Solana and retrieves available token and market information.', 'Open the new Hub. If the same mint is already on MART, its existing Hub opens instead.'] },
      { title: 'What MART retrieves', paragraphs: ['Available information can include name, symbol, logo, decimals, mint address, and market data. Unindexed markets or rate-limited providers may leave some information unavailable.', 'A compatible token does not need to have launched through MART. Adding it does not relaunch, duplicate, or transfer the token.'] },
      { title: 'The Hub starts unclaimed', paragraphs: ['The person adding a token is not automatically its official owner. A legitimate, verifiable token authority can claim it later. In the meantime, community activity and supported marketplace listings can begin.'] },
    ],
  },
  {
    slug: 'token-verification', title: 'Token Verification', label: 'IDENTITY & AUTHORITY', summary: 'Separate community participation from official control.',
    sections: [
      { title: 'Unclaimed', paragraphs: ['An Unclaimed Hub is a community-created home for a token that has not been officially claimed and verified. Adding the token, holding its tokens, or using the same name does not establish official ownership.'] },
      { title: 'Verified', paragraphs: ['A Verified Hub has been claimed by a wallet whose applicable on-chain authority has been verified. This wallet can manage official Hub information and events, subject to authority checks.', 'The current claim flow verifies the token’s Metaplex metadata update authority against the signed-in wallet. Renounced or program-controlled authority cannot be claimed through that flow. Not every token is eligible for self-service verification.'] },
      { title: 'Claim a Hub', items: ['Connect the legitimate authority wallet and sign in.', 'Open the token’s Hub and select Claim this Token.', 'MART checks the on-chain metadata authority. A mismatched wallet is rejected.', 'If the check succeeds, the Hub displays Verified and the authority can access its management tools.'] },
      { title: 'What verification does not mean', paragraphs: ['A Verified label is not a financial endorsement, smart-contract audit, guarantee of safety, seller guarantee, or promise of returns. It describes the verified authority relationship to that Hub.'] },
    ],
  },
  {
    slug: 'fees', title: 'Fees', label: 'BEFORE YOU SIGN', summary: 'Understand what you are paying, in which currency, and why.',
    sections: [
      { title: 'Browsing and signing in', paragraphs: ['Browsing MART and signing a wallet login message do not move funds. Creating a supported off-chain listing or community post does not itself submit an on-chain payment. Never approve an unexpected transaction just to sign in.'] },
      { title: 'Marketplace purchases', paragraphs: ['The item price is paid in the current Hub’s token. The buyer also needs SOL for network fees and, if necessary, creation of the seller’s associated token account. The current supported checkout transfers the listed token amount directly to the seller without a separate MART commission instruction.', 'Exact network and account costs depend on the transaction. A token’s displayed US-dollar price is a market reference, not the checkout denomination.'] },
      { title: 'Launches and trades', paragraphs: ['Launching can involve Solana network, priority, account-creation, and provider fees, plus an optional initial token purchase. The current local launch integration uses PumpPortal and Pump.fun infrastructure. Its launch flow discloses a 0.00001 SOL priority fee and a 0.5% local-trade provider fee, separate from applicable underlying trading fees.', 'Fees and market conditions can change. Review the wallet transaction, initial-buy amount, slippage tolerance, and the relevant provider’s current terms before approval. MART cannot guarantee a fixed all-in launch or trading cost.'] },
      { title: 'NFT fees', paragraphs: ['NFT minting is not currently enabled. Its intended flow requires the creator to pay the applicable artwork storage, minting, and network costs. No NFT fee estimate should be treated as an active checkout quote today.'] },
    ],
  },
  {
    slug: 'security', title: 'Security', label: 'YOUR WALLET. YOUR RESPONSIBILITY.', summary: 'Practical safeguards for participating in the MART ecosystem.',
    sections: [
      { title: 'Keep control of your wallet', items: ['MART does not ask for your seed phrase or private key. Never enter them in a form, post, or direct message.', 'Wallet sign-in uses a short-lived signed message. Read the domain and message before approving.', 'Asset movement requires a separate wallet-signed transaction. Review the token mint, recipient, amount, and fees.', 'Disconnect if your wallet changes or you no longer want to use the session.'] },
      { title: 'Verify the token, not just the ticker', paragraphs: ['Token names, symbols, and logos can be copied. Use the full Solana mint address and an independent block explorer to identify the asset. One mint address maps to one MART Token Hub.', 'Unclaimed and Verified are Hub authority states. Neither guarantees the value of a token or the trustworthiness of a listing.'] },
      { title: 'Payments and fulfillment', paragraphs: ['MART verifies the exact submitted order transaction and waits for on-chain finalization before marking payment successful. A pending or failed transaction must not be treated as a completed purchase.', 'Marketplace payments are direct and non-custodial, not escrow. Blockchain verification confirms the payment—not physical shipment, digital delivery, product quality, or dispute resolution. Assess the seller and listing before paying.'] },
      { title: 'Service and transaction risks', paragraphs: ['Public RPC and market-data services may be delayed or unavailable. External charts and trading experiences have their own availability and terms. No transaction is risk-free, and mainnet actions can have irreversible consequences.', 'Only share delivery details needed to fulfill an order. Avoid publishing personal information in token communities. Events are announcements, not guarantees.'] },
    ],
  },
];