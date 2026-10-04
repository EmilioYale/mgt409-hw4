# Design (Problem 10) — "Varsity Stockroom"

The idea: the site should feel like a student-run campus shop. That means a varsity jacket patch, hang tags on a clothing rack and Polaroids pinned on a dorm wall, not a generic e-commerce template.

## What changed and why

**Color palette**
- **Change:** Yale blue `#00356B` with warm cream paper `#FBF8F1`, a bright blue accent `#286DC0`, and a "game-day gold" `#F2B33D` used sparingly for highlights (price on the detail page, the hero underline, the sticker, Dan's avatar). Sold out is a red rubber stamp.
- **Why it helps buyers:** instantly reads as Yale without copying an official site. Gold draws the eye to exactly two things: prices and Dan. Cream is easier on the eyes than stark white, so shoppers browse longer.

**Type**
- **Change:** *Graduate* (varsity block letters) for the logo, eyebrows, prices and labels; *Fraunces* (an editorial serif with a great italic) for headlines; *DM Sans* for body text.
- **Why it helps buyers:** the varsity lettering is the "merch" signal. The serif headline makes it feel like a curated shop, not a warehouse. The sans body stays readable at small sizes.

**Hierarchy**
- **Change:**
  - The hero has one big promise ("Wear the *blue.* Own the day.") with one primary CTA and one chat CTA.
  - Then "Shop by category" photo tiles, then "Fan favorites", then a navy "Meet Dan" strip.
  - The detail page puts name → price → description → sizes → "Ask Dan" in reading order.
- **Why it helps buyers:** every screen has one obvious next step, so fewer people get lost before reaching a product page.

**Product presentation**
- **Change:**
  - Cards are hang tags: a dashed "stitch" line separates photo and text, and the price sits in a navy tag with a punched hole that tilts on hover.
  - The hero is a fanned stack of Polaroids with a wobbling "Boola Boola!" sticker.
  - The detail page frames the photo inside a stitched patch.
  - Size buttons show live stock: "Only 2 left", or striped and struck-through when sold out.
- **Why it helps buyers:** prices are always visible (no hunting), and stock is honest up front. "Only 2 left" adds gentle urgency where it's true.

**Motion**
- **Change:**
  - Cards rise in with a staggered delay and lift/tilt on hover.
  - A ticker runs along the top ("Free campus pickup…").
  - The gold underline draws itself under "blue".
  - The chat button pops in; the panel springs open from the corner; typing dots bounce.
  - All motion is turned off for users with *prefers-reduced-motion*.
- **Why it helps buyers:** small motion makes the site feel alive and rewards exploring without slowing anyone down. Respecting reduced motion keeps it accessible.

**Chat feel**
- **Change:**
  - The assistant has a name and face: **Dan's Desk**, with a gold paw avatar and a green "Real-time stock & prices" status dot.
  - A note says whether the chat is saved or a guest chat.
  - Navy user bubbles, white assistant bubbles, and a dotted-grid background.
  - Mini product cards inside the chat, and context-aware suggestion chips.
  - Search results also land in a navy **"Dan's picks"** shelf on the page itself, with the shopper's question as the title.
- **Why it helps buyers:** a friendly mascot lowers the barrier to asking. The status line builds trust that answers are real. Putting results *on the page* turns a chat answer into a browsable mini-collection, which is where buying happens.

**Brand marks**
- **Change:** an inline-SVG "CC" monogram drawn as a stitched varsity patch (also the favicon), plus a bulldog paw for Dan. There are no copied logos or images.
- **Why it helps buyers:** a recognizable identity, and it loads instantly.
