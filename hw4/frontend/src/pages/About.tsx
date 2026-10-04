import { Link } from 'react-router-dom'
import { Monogram } from '../components/Brand'

export default function About() {
  return (
    <div className="page about">
      <div className="page-head">
        <span className="eyebrow">Our story</span>
        <h1>Made on campus, worn everywhere.</h1>
      </div>

      <div className="about-grid">
        <div className="about-copy">
          <p className="lede">
            Campus Customs started with a simple complaint: the merch we loved sold out right before every big game, and
            nobody could tell us when it’d be back. So a few of us decided to run the shop ourselves.
          </p>
          <p>
            Today we’re a small, student-run team that picks every hoodie, crewneck and tee on the rack. We look for
            heavyweight fabrics that survive a New Haven winter, prints that don’t crack after ten washes, and designs
            you’ll still want to wear after graduation.
          </p>
          <p>
            We also think shopping should be honest. That’s why our assistant, Dan, reads stock straight from the
            stockroom database. If your size is gone, he’ll tell you, and point you to something close that isn’t.
          </p>
        </div>

        <aside className="about-card">
          <Monogram size={72} />
          <ul>
            <li>
              <b>Student-run</b>
              <span>Staffed and curated by students</span>
            </li>
            <li>
              <b>Campus pickup</b>
              <span>Grab your order at the Old Campus tent</span>
            </li>
            <li>
              <b>Game Day ready</b>
              <span>Restocks timed for the big weekends</span>
            </li>
          </ul>
          <Link to="/products" className="btn btn-primary">
            Browse the rack
          </Link>
        </aside>
      </div>
    </div>
  )
}
