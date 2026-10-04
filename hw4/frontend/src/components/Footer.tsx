import { Link } from 'react-router-dom'
import { Monogram } from './Brand'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <Monogram size={52} />
          <p>
            Campus Customs is a student-run merch shop in New Haven. Every order helps fund student jobs and campus
            events.
          </p>
        </div>
        <div className="footer-cols">
          <div>
            <h4>Shop</h4>
            <Link to="/products">All products</Link>
            <Link to="/products?category=Hoodies">Hoodies</Link>
            <Link to="/products?category=Crewnecks">Crewnecks</Link>
            <Link to="/products?category=Tees">Tees</Link>
          </div>
          <div>
            <h4>Us</h4>
            <Link to="/about">Our story</Link>
            <Link to="/login">Log in</Link>
            <Link to="/signup">Create account</Link>
          </div>
        </div>
      </div>
      <p className="footer-fine">MGT 409 class project · Not an official Yale University store</p>
    </footer>
  )
}
