# Usability improvements (Problem 9)

Four improvements, two on the front end and two on the agent/backend. Each one is live in the running app; where to see it is listed under each.

## Front end

### 1. Search, category filters, sort and "in stock only" on the Products page
**What I added:**
- A sticky toolbar on `/products` with a text search (name, type, description, colors).
- Category chips with counts (Hoodies 27, Crewnecks 30, Tees 26, Quarter-zips 11, Jackets & fleece 8).
- A sort menu (featured, price ↑, price ↓, A–Z) and an "In stock only" toggle.
- A live "Showing N of 102" count and a "Clear filters" empty state.
- Filters are kept in the URL (`/products?category=Hoodies&sort=price-asc`), so they survive refresh/back and the footer and home-page category tiles can deep-link into them.

**Why it helps:** 102 products in one grid is a lot of scrolling. A shopper who just wants "a hoodie under $50 that's actually available" now gets there in two clicks instead of scanning every card, and fewer shoppers bounce before finding something they like.

*See it:* Products page toolbar; Home → "Shop by category" tiles.

### 2. Context-aware quick replies + "Ask Dan about this" button
**What I added:**
- One-tap suggestion chips above the chat input that change with the page. On a product page they're "Is this in stock in M?", "What colors does this come in?" and "Show me something similar". Elsewhere they're "What hoodies do you have?", "Navy crewnecks under $60" and "Any Harvard–Yale gear?".
- The product page has an **Ask Dan about this** button that opens the chat with the question pre-filled. If the shopper has selected a size, it becomes "Is the … in stock in size M?".

**Why it helps:** most shoppers don't know what a chatbot can do and won't type a question from scratch. The chips show what Dan is good at and make asking a single tap, so more shoppers get a stock answer instead of guessing and leaving.

*See it:* open the chat on any page; product page → "Ask Dan about this".

## Agent / backend

### 3. New agent tool: `find_in_stock_alternatives`
**What I added:** when a size is sold out, the agent calls this tool. It finds up to 3 products in the same category that **are in stock in that size**, ranked by shared colors and closeness in price, each with a short reason ("also a crewneck, also navy, $58"). The results show up as cards in the chat and in the "Dan's picks" shelf.

**Why it helps:** "Sorry, sold out" is a dead end, and a lost sale. Pointing the shopper to a similar item they can buy right now keeps the sale, and it's honest because the stock comes straight from the database.

*See it:* on Baseball Left Chest Crewneck, ask "Do you have this in XS?" (screenshot `app_check_images/usability_alternatives.png`).

### 4. Cost & abuse guard (rate limit, input caps, loop limits, filtered-prompt handling)
**What I added:**
- **Per-shopper rate limit:** 12 messages per minute per logged-in user, or per IP for guests. After that the API returns a friendly 429 ("give me a few seconds") *before* any model call.
- **Input caps:** messages are limited to 1–1000 characters, and guest history to 40 turns. Only the last 12 turns are sent to the model.
- **Loop limits:** each turn is capped at 6 model requests and 8 tool calls; if the cap is hit, the shopper gets "could you ask in a simpler way" instead of an error.
- **Safe failure on blocked prompts:** if the model provider's content filter blocks a message (e.g. a jailbreak attempt), the shopper gets a polite in-scope reply instead of a crash, and the event is logged in the audit trail as `content_filter`.

**Why it helps:**
- **The business:** someone spamming the bot, or a runaway tool loop, can't run up the API bill. Every model call costs money, and this caps spend per shopper.
- **Shoppers:** the bot stays fast, and they never see a raw server error.

*See it:* send 13 messages within a minute (the 13th gets "Whoa, that's a lot of messages!"); `output/audit_trail.json` shows `usage` per turn and `stop_reason` values.
