import { useEffect, useRef } from 'react'
import { useChat } from '../chat'
import { Paw } from './Brand'
import ProductCard from './ProductCard'

/** "Dan's picks" shelf: when the agent returns structured product matches, they are rendered here,
 *  on whatever page the shopper is on. Each card opens the normal single-item page. */
export default function ChatPicks() {
  const { picks, dismissPicks, page } = useChat()
  const ref = useRef<HTMLElement>(null)
  // A shelf holding only the product already on screen adds nothing; the chat bubble still shows it.
  const onlyCurrent = picks?.products.length === 1 && picks.products[0].product_id === page.product_id

  useEffect(() => {
    if (picks && !onlyCurrent) ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [picks, onlyCurrent])

  if (!picks || onlyCurrent) return null
  return (
    <section className="picks" ref={ref} aria-live="polite">
      <div className="picks-head">
        <div>
          <span className="eyebrow">
            <Paw size={14} /> Dan's picks from the chat
          </span>
          <h2>“{picks.prompt}”</h2>
        </div>
        <button className="btn btn-ghost" onClick={dismissPicks}>
          Hide picks
        </button>
      </div>
      <div className="grid grid-picks">
        {picks.products.map((p, i) => (
          <ProductCard key={`${picks.prompt}-${p.product_id}`} product={p} index={i} />
        ))}
      </div>
    </section>
  )
}
