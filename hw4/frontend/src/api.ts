import type {
  AuthResponse,
  CatalogueResponse,
  ChatResponse,
  ChatTurn,
  PageContext,
  ProductDetail,
  User,
} from './types'

const TOKEN_KEY = 'cc_token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body) headers.set('Content-Type', 'application/json')
  const token = tokenStore.get()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(path, { ...init, headers })
  if (!res.ok) {
    let message = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') message = body.detail
      else if (Array.isArray(body.detail)) message = body.detail.map((d: { msg: string }) => d.msg).join('; ')
    } catch {
      /* not JSON */
    }
    throw new ApiError(res.status, message)
  }
  return res.json() as Promise<T>
}

export const api = {
  catalogue: () => request<CatalogueResponse>('/api/products'),
  product: (id: string) => request<ProductDetail>(`/api/products/${encodeURIComponent(id)}`),

  signup: (body: { first_name: string; last_name: string; email: string; password: string }) =>
    request<AuthResponse>('/api/auth/signup', { method: 'POST', body: JSON.stringify(body) }),
  login: (email: string, password: string) =>
    request<AuthResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request<User>('/api/auth/me'),
  logout: () => request<{ ok: boolean }>('/api/auth/logout', { method: 'POST' }),

  chat: (message: string, page: PageContext, history: ChatTurn[]) =>
    request<ChatResponse>('/api/chat', { method: 'POST', body: JSON.stringify({ message, page, history }) }),
  chatHistory: () => request<ChatTurn[]>('/api/chat/history'),
  clearChatHistory: () => request<{ ok: boolean }>('/api/chat/history', { method: 'DELETE' }),
}

export const money = (n: number) => `$${n.toFixed(n % 1 === 0 ? 0 : 2)}`
