import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { money } from '../api'
import type { ProductCard as Product } from '../types'

/** One product "hang tag". Used on the Products page, the home page and for chat results:
 *  every card links to the same single-item page, /products/:id. */
export default function ProductCard({ product, index = 0, compact = false }: { product: Product; index?: number; compact?: boolean }) {
  const soldOut = product.total_stock === 0
  return (
    <Link
      to={`/products/${encodeURIComponent(product.product_id)}`}
      className={`card${compact ? ' card-compact' : ''}`}
      style={{ '--i': index } as CSSProperties}
    >
      <div className="card-img">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {soldOut && <span className="stamp">Sold out</span>}
      </div>
      <div className="card-body">
        <span className="card-type">{product.garment_type}</span>
        <h3 className="card-name">{product.name}</h3>
        {!compact && <p className="card-desc">{product.short_description}</p>}
      </div>
      <span className="price-tag">{money(product.price)}</span>
    </Link>
  )
}
