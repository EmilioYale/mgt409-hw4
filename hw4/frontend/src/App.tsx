import { Link, Outlet, Route, Routes } from 'react-router-dom'
import ChatPicks from './components/ChatPicks'
import ChatWidget from './components/ChatWidget'
import Footer from './components/Footer'
import NavBar from './components/NavBar'
import About from './pages/About'
import { Login, Signup } from './pages/Auth'
import Home from './pages/Home'
import ProductDetail from './pages/ProductDetail'
import Products from './pages/Products'

function Layout() {
  return (
    <>
      <NavBar />
      <main>
        <ChatPicks />
        <Outlet />
      </main>
      <Footer />
      <ChatWidget />
    </>
  )
}

function NotFound() {
  return (
    <div className="page">
      <h1>Lost on Old Campus?</h1>
      <p className="muted">That page doesn’t exist.</p>
      <Link to="/" className="link-arrow">
        ← Back home
      </Link>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="products" element={<Products />} />
        <Route path="products/:id" element={<ProductDetail />} />
        <Route path="about" element={<About />} />
        <Route path="login" element={<Login />} />
        <Route path="signup" element={<Signup />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
