import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Monogram } from './Brand'

const TICKER = [
  'Free campus pickup at the Old Campus tent',
  'Game Day ready: The Game gear is in',
  'Ask Dan in the chat — real stock, real prices',
  'Student-run since day one',
  'Boola boola!',
]

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="site-header">
      <div className="ticker" aria-hidden="true">
        <div className="ticker-track">
          {[...TICKER, ...TICKER].map((t, i) => (
            <span key={i}>
              {t} <b>✦</b>
            </span>
          ))}
        </div>
      </div>
      <nav className="nav">
        <Link to="/" className="brand" aria-label="Campus Customs home">
          <Monogram size={42} />
          <span className="brand-text">
            <span className="brand-name">Campus Customs</span>
            <span className="brand-sub">New Haven · Est. by students</span>
          </span>
        </Link>
        <div className="nav-links">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/products">Products</NavLink>
          <NavLink to="/about">About Us</NavLink>
        </div>
        <div className="nav-auth">
          {user ? (
            <>
              <span className="hello">
                Hi, <b>{user.first_name}</b>
              </span>
              <button
                className="btn btn-ghost"
                onClick={async () => {
                  await logout()
                  navigate('/')
                }}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="btn btn-ghost">
                Log in
              </NavLink>
              <NavLink to="/signup" className="btn btn-primary">
                Create account
              </NavLink>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
