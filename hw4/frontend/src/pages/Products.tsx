import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import { useCatalogue } from '../useCatalogue'

type Sort = 'featured' | 'price-asc' | 'price-desc' | 'name'

/** Products page with search, category chips, sort and an in-stock toggle (usability improvement #1).
 *  Filters live in the URL, so they survive refresh/back and can be shared. */
export default function Products() {
  const { data, error } = useCatalogue()
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const category = params.get('category') ?? 'All'
  const sort = (params.get('sort') as Sort) ?? 'featured'
  const inStockOnly = params.get('instock') === '1'

  const update = (key: string, value: string | null) => {
    const next = new URLSearchParams(params)
    if (value === null || value === '' || value === 'All' || value === 'featured') next.delete(key)
    else next.set(key, value)
    setParams(next, { replace: true })
  }

  const products = useMemo(() => {
    let list = data?.products ?? []
    if (category !== 'All') list = list.filter((p) => p.category === category)
    if (inStockOnly) list = list.filter((p) => p.total_stock > 0)
    const words = q.toLowerCase().split(/\s+/).filter(Boolean)
    if (words.length) {
      list = list.filter((p) => {
        const hay = `${p.name} ${p.garment_type} ${p.short_description} ${p.colors.join(' ')}`.toLowerCase()
        return words.every((w) => hay.includes(w))
      })
    }
    const sorted = [...list]
    if (sort === 'price-asc') sorted.sort((a, b) => a.price - b.price)
    if (sort === 'price-desc') sorted.sort((a, b) => b.price - a.price)
    if (sort === 'name') sorted.sort((a, b) => a.name.localeCompare(b.name))
    return sorted
  }, [data, category, inStockOnly, q, sort])

  const total = data?.products.length ?? 0

  return (
    <div className="page products-page">
      <div className="page-head">
        <span className="eyebrow">The full rack</span>
        <h1>Products</h1>
        <p className="muted">
          {total} styles of Yale gear. Every price and size comes straight from our stockroom database.
        </p>
      </div>

      <div className="toolbar">
        <label className="search">
          <span aria-hidden="true">⌕</span>
          <input
            type="search"
            placeholder="Search “navy hoodie”, “bulldog”, “quarter zip”…"
            value={q}
            onChange={(e) => update('q', e.target.value)}
          />
        </label>
        <div className="toolbar-right">
          <label className="toggle">
            <input type="checkbox" checked={inStockOnly} onChange={(e) => update('instock', e.target.checked ? '1' : null)} />
            In stock only
          </label>
          <select value={sort} onChange={(e) => update('sort', e.target.value)} aria-label="Sort products">
            <option value="featured">Sort: Featured</option>
            <option value="price-asc">Price: low → high</option>
            <option value="price-desc">Price: high → low</option>
            <option value="name">Name: A → Z</option>
          </select>
        </div>
      </div>

      <div className="filter-chips" role="tablist" aria-label="Categories">
        {['All', ...Object.keys(data?.categories ?? {})].map((c) => (
          <button
            key={c}
            role="tab"
            aria-selected={c === category}
            className={`chip chip-lg ${c === category ? 'is-active' : ''}`}
            onClick={() => update('category', c)}
          >
            {c}
            {c !== 'All' && <span className="chip-count">{data?.categories[c]}</span>}
          </button>
        ))}
      </div>

      {error && <p className="form-error">{error}</p>}
      {!data && !error && <p className="muted">Loading the rack…</p>}
      {data && (
        <p className="result-count">
          Showing <b>{products.length}</b> of {total}
        </p>
      )}
      {data && products.length === 0 && (
        <div className="empty">
          <p>Nothing matches that combo. Try fewer words or another category.</p>
          <button className="btn btn-ghost" onClick={() => setParams({}, { replace: true })}>
            Clear filters
          </button>
        </div>
      )}
      <div className="grid">
        {products.map((p, i) => (
          <ProductCard key={p.product_id} product={p} index={i % 12} />
        ))}
      </div>
    </div>
  )
}
