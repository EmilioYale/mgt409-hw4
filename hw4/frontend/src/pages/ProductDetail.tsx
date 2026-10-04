import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, money } from '../api'
import { Paw } from '../components/Brand'
import ProductCard from '../components/ProductCard'
import { useChat } from '../chat'
import type { ProductDetail as Detail } from '../types'
import { useCatalogue } from '../useCatalogue'

/** Single-item page: big image on one side, full info + live per-size stock on the other. */
export default function ProductDetail() {
  const { id = '' } = useParams()
  const [product, setProduct] = useState<Detail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [size, setSize] = useState<string | null>(null)
  const { data } = useCatalogue()
  const { ask } = useChat()
  const low = data?.low_stock_threshold ?? 3

  useEffect(() => {
    setProduct(null)
    setError(null)
    setSize(null)
    api
      .product(id)
      .then(setProduct)
      .catch((e) => setError(e.status === 404 ? 'We couldn’t find that product.' : e.message))
    window.scrollTo({ top: 0 })
  }, [id])

  if (error)
    return (
      <div className="page">
        <p className="form-error">{error}</p>
        <Link to="/products" className="link-arrow">
          ← Back to all products
        </Link>
      </div>
    )
  if (!product) return <div className="page muted">Loading…</div>

  const selected = product.sizes.find((s) => s.size === size)
  const category = data?.products.find((p) => p.product_id === product.product_id)?.category
  const related = (data?.products ?? [])
    .filter((p) => p.category === category && p.product_id !== product.product_id && p.total_stock > 0)
    .slice(0, 4)

  return (
    <div className="page detail-page">
      <nav className="crumbs">
        <Link to="/products">Products</Link>
        {category && (
          <>
            {' / '}
            <Link to={`/products?category=${encodeURIComponent(category)}`}>{category}</Link>
          </>
        )}
        {' / '}
        <span>{product.name}</span>
      </nav>

      <div className="detail">
        <div className="detail-img">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="detail-info">
          <span className="eyebrow">{product.garment_type}</span>
          <h1>{product.name}</h1>
          <p className="detail-price">{money(product.price)}</p>
          <p className="detail-desc">{product.description}</p>

          {product.colors.length > 0 && (
            <div className="detail-block">
              <h4>Colors</h4>
              <div className="color-list">
                {product.colors.map((c) => (
                  <span key={c} className="color-pill">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="detail-block">
            <h4>Sizes &amp; stock</h4>
            <div className="sizes">
              {product.sizes.map((s) => (
                <button
                  key={s.size}
                  className={`size ${s.in_stock ? '' : 'is-out'} ${size === s.size ? 'is-selected' : ''}`}
                  disabled={!s.in_stock}
                  onClick={() => setSize(s.size)}
                  title={s.in_stock ? `${s.quantity} in stock` : 'Sold out'}
                >
                  <b>{s.size}</b>
                  <small>{s.in_stock ? (s.quantity <= low ? `Only ${s.quantity} left` : `${s.quantity} left`) : 'Sold out'}</small>
                </button>
              ))}
            </div>
            <p className="stock-note">
              {product.total_stock === 0
                ? 'Sold out in every size right now.'
                : selected
                  ? `Size ${selected.size}: ${selected.quantity} in stock.`
                  : `${product.total_stock} in stock across all sizes. Tap a size to check it.`}
            </p>
          </div>

          <div className="detail-actions">
            <button
              className="btn btn-primary btn-lg"
              onClick={() =>
                ask(selected ? `Is the ${product.name} in stock in size ${selected.size}?` : `Tell me about the ${product.name}`)
              }
            >
              <Paw size={18} /> Ask Dan about this
            </button>
            <span className="muted small">Dan sees which product you’re on, so “this one” works.</span>
          </div>
        </div>
      </div>

      {related.length > 0 && (
        <section className="section">
          <div className="section-head">
            <h2>More {category?.toLowerCase()}</h2>
          </div>
          <div className="grid">
            {related.map((p, i) => (
              <ProductCard key={p.product_id} product={p} index={i} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
