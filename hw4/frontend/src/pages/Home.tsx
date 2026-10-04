import { Link } from 'react-router-dom'
import { Paw } from '../components/Brand'
import ProductCard from '../components/ProductCard'
import { useChat } from '../chat'
import { useCatalogue } from '../useCatalogue'

const CATEGORY_BLURBS: Record<string, string> = {
  Hoodies: 'Library-to-tailgate layers',
  Crewnecks: 'The classic sweatshirt, done right',
  Tees: 'Everyday blue, every day',
  'Quarter-zips': 'Smart enough for section',
  'Jackets & fleece': 'For that New Haven wind',
}

const FEATURED = [
  '2025-yale-vs-harvard-t-shirt',
  'basic-hoodie-big-yale',
  'champion-reverse-weave-crewneck',
  'brooks-brothers-bomber-jacket-yale',
]

export default function Home() {
  const { data } = useCatalogue()
  const { ask } = useChat()
  const products = data?.products ?? []
  const featured = FEATURED.map((id) => products.find((p) => p.product_id === id)).filter((p) => p !== undefined)
  const hero = featured.slice(0, 3)
  const coverFor = (cat: string) => products.find((p) => p.category === cat && p.total_stock > 0)

  return (
    <div className="page home">
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Fall ’26 · Game Day collection</span>
          <h1>
            Wear the <em>blue.</em>
            <br />
            Own the day.
          </h1>
          <p className="lede">
            Hoodies, crewnecks and tees picked by students, for students. Whether it’s a 9 a.m. seminar or The Game,
            we’ve got the layer for it.
          </p>
          <div className="hero-cta">
            <Link to="/products" className="btn btn-primary btn-lg">
              Shop the collection
            </Link>
            <button className="btn btn-ghost btn-lg" onClick={() => ask('What hoodies do you have?', true)}>
              <Paw size={18} /> Ask Dan what’s in stock
            </button>
          </div>
          <ul className="hero-facts">
            <li>
              <b>{products.length || '100+'}</b> styles
            </li>
            <li>
              <b>XS–XXL</b> sizing
            </li>
            <li>
              <b>Live</b> stock in chat
            </li>
          </ul>
        </div>
        <div className="hero-collage" aria-hidden="true">
          {hero.map((p, i) => (
            <div key={p.product_id} className={`polaroid p${i}`}>
              <img src={p.image_url} alt="" />
              <span>{p.name}</span>
            </div>
          ))}
          <div className="sticker">
            Boola
            <br />
            Boola!
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Shop by category</h2>
          <Link to="/products" className="link-arrow">
            See everything →
          </Link>
        </div>
        <div className="categories">
          {Object.entries(data?.categories ?? {}).map(([cat, count]) => {
            const cover = coverFor(cat)
            return (
              <Link key={cat} to={`/products?category=${encodeURIComponent(cat)}`} className="category-tile">
                {cover && <img src={cover.image_url} alt="" loading="lazy" />}
                <div>
                  <h3>{cat}</h3>
                  <p>{CATEGORY_BLURBS[cat] ?? 'Campus favorites'}</p>
                  <span className="count">{count} styles</span>
                </div>
              </Link>
            )
          })}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Fan favorites</h2>
          <span className="muted">What the Old Campus crowd keeps buying</span>
        </div>
        <div className="grid">
          {featured.map((p, i) => (
            <ProductCard key={p.product_id} product={p} index={i} />
          ))}
        </div>
      </section>

      <section className="dan-strip">
        <div className="dan-badge">
          <Paw size={40} />
        </div>
        <div>
          <h2>Meet Dan, our shop assistant.</h2>
          <p>
            Dan checks the stockroom for you, live. Ask “do you have this in a medium?” on any product page, or
            “navy crewnecks under $60”, and the matches pop up right here on the site.
          </p>
        </div>
        <button className="btn btn-cream btn-lg" onClick={() => ask('Navy crewnecks under $60', true)}>
          Try it
        </button>
      </section>
    </div>
  )
}
