import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Monogram } from '../components/Brand'

function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="page auth-page">
      <div className="auth-card">
        <Monogram size={56} />
        <h1>{title}</h1>
        <p className="muted">{subtitle}</p>
        {children}
      </div>
    </div>
  )
}

export function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(email, password)
      navigate('/products')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Log in to pick up your chat with Dan where you left off.">
      <form className="form" onSubmit={submit}>
        <label>
          Email
          <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button className="btn btn-primary btn-lg" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p className="muted small">
        New here? <Link to="/signup">Create an account</Link>
      </p>
    </AuthShell>
  )
}

export function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (form.password.length < 8) return setError('Password must be at least 8 characters.')
    if (form.password !== form.confirm) return setError('Passwords don’t match.')
    setBusy(true)
    setError(null)
    try {
      const { confirm: _confirm, ...body } = form
      await signup(body)
      navigate('/products')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-up failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell title="Join Campus Customs" subtitle="An account saves your chat history with Dan.">
      <form className="form" onSubmit={submit}>
        <div className="form-row">
          <label>
            First name
            <input autoComplete="given-name" required value={form.first_name} onChange={set('first_name')} />
          </label>
          <label>
            Last name
            <input autoComplete="family-name" required value={form.last_name} onChange={set('last_name')} />
          </label>
        </div>
        <label>
          Email
          <input type="email" autoComplete="email" required value={form.email} onChange={set('email')} />
        </label>
        <label>
          Password <small className="muted">(8+ characters)</small>
          <input type="password" autoComplete="new-password" required value={form.password} onChange={set('password')} />
        </label>
        <label>
          Confirm password
          <input type="password" autoComplete="new-password" required value={form.confirm} onChange={set('confirm')} />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button className="btn btn-primary btn-lg" disabled={busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="muted small">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </AuthShell>
  )
}
