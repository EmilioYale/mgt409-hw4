import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { api } from './api'
import { useAuth } from './auth'
import type { ChatTurn, PageContext, ProductCard } from './types'

const GUEST_KEY = 'cc_guest_chat'
const GUEST_HISTORY_SENT = 12 // guests: recent turns sent back so follow-ups work (nothing stored server-side)

export interface ChatPicks {
  prompt: string
  products: ProductCard[]
}

interface ChatState {
  open: boolean
  setOpen: (open: boolean) => void
  messages: ChatTurn[]
  sending: boolean
  error: string | null
  draft: string
  setDraft: (text: string) => void
  send: (text: string) => Promise<void>
  ask: (text: string, sendNow?: boolean) => void
  clear: () => Promise<void>
  picks: ChatPicks | null
  dismissPicks: () => void
  page: PageContext
  saved: boolean
}

const ChatContext = createContext<ChatState | null>(null)

/** Which page is the shopper on? Sent with every message so "this" can be resolved. */
function pageContextFor(pathname: string): PageContext {
  const m = pathname.match(/^\/products\/([^/]+)$/)
  return { path: pathname, product_id: m ? decodeURIComponent(m[1]) : null }
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth()
  const location = useLocation()
  const page = useMemo(() => pageContextFor(location.pathname), [location.pathname])

  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatTurn[]>([])
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [picks, setPicks] = useState<ChatPicks | null>(null)
  const messagesRef = useRef(messages)
  messagesRef.current = messages

  // Load history whenever the signed-in user changes: DB history for members, sessionStorage for guests.
  useEffect(() => {
    if (!ready) return
    setError(null)
    if (user) {
      api
        .chatHistory()
        .then(setMessages)
        .catch(() => setMessages([]))
    } else {
      try {
        setMessages(JSON.parse(sessionStorage.getItem(GUEST_KEY) || '[]'))
      } catch {
        setMessages([])
      }
    }
  }, [user, ready])

  useEffect(() => {
    if (!user) sessionStorage.setItem(GUEST_KEY, JSON.stringify(messages.slice(-40)))
  }, [messages, user])

  const send = useCallback(
    async (text: string) => {
      const message = text.trim()
      if (!message || sending) return
      setError(null)
      setDraft('')
      const history = user ? [] : messagesRef.current.slice(-GUEST_HISTORY_SENT)
      setMessages((m) => [...m, { role: 'user', content: message, products: [] }])
      setSending(true)
      try {
        const res = await api.chat(message, page, history)
        setMessages((m) => [...m, { role: 'assistant', content: res.reply, products: res.products }])
        if (res.products.length) setPicks({ prompt: message, products: res.products })
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Something went wrong')
      } finally {
        setSending(false)
      }
    },
    [page, sending, user],
  )

  const ask = useCallback(
    (text: string, sendNow = false) => {
      setOpen(true)
      if (sendNow) void send(text)
      else setDraft(text)
    },
    [send],
  )

  const clear = useCallback(async () => {
    if (user) await api.clearChatHistory()
    sessionStorage.removeItem(GUEST_KEY)
    setMessages([])
    setPicks(null)
    setError(null)
  }, [user])

  const value: ChatState = {
    open,
    setOpen,
    messages,
    sending,
    error,
    draft,
    setDraft,
    send,
    ask,
    clear,
    picks,
    dismissPicks: () => setPicks(null),
    page,
    saved: Boolean(user),
  }
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used inside <ChatProvider>')
  return ctx
}
