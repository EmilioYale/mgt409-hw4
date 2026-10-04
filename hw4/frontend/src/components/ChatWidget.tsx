import { useEffect, useRef } from 'react'
import { useChat } from '../chat'
import { Paw } from './Brand'
import Markdown from './Markdown'
import ProductCard from './ProductCard'

const CHAT_CARD_LIMIT = 3 // the full set is shown in the on-page picks shelf

/** Quick-reply chips change with the page: product pages get product questions. */
function suggestionsFor(onProductPage: boolean): string[] {
  return onProductPage
    ? ['Is this in stock in M?', 'What colors does this come in?', 'Show me something similar']
    : ['What hoodies do you have?', 'Navy crewnecks under $60', 'Any Harvard–Yale gear?']
}

export default function ChatWidget() {
  const chat = useChat()
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const onProductPage = Boolean(chat.page.product_id)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [chat.messages, chat.sending, chat.open])

  useEffect(() => {
    if (chat.open) inputRef.current?.focus()
  }, [chat.open, chat.draft])

  return (
    <div className={`chat ${chat.open ? 'is-open' : ''}`}>
      {chat.open && (
        <section className="chat-panel" aria-label="Chat with Dan's Desk">
          <header className="chat-head">
            <div className="chat-avatar">
              <Paw size={22} />
            </div>
            <div>
              <h2>Dan's Desk</h2>
              <p>
                <span className="dot" /> Real-time stock &amp; prices
                {chat.saved ? ' · history saved' : ' · guest chat'}
              </p>
            </div>
            <div className="chat-head-actions">
              {chat.messages.length > 0 && (
                <button className="icon-btn" title="Clear chat" onClick={() => void chat.clear()}>
                  ↺
                </button>
              )}
              <button className="icon-btn" title="Close chat" aria-label="Close chat" onClick={() => chat.setOpen(false)}>
                ✕
              </button>
            </div>
          </header>

          <div className="chat-log" ref={listRef}>
            {chat.messages.length === 0 && (
              <div className="chat-empty">
                <p className="chat-hello">Hey! I'm Dan 🐾</p>
                <p>Ask me what's in stock, what fits your budget, or about the item you're looking at.</p>
              </div>
            )}
            {chat.messages.map((m, i) => (
              <div key={i} className={`bubble-row ${m.role}`}>
                <div className={`bubble ${m.role}`}>
                  {m.role === 'assistant' ? <Markdown text={m.content} /> : m.content}
                </div>
                {m.products.length > 0 && (
                  <div className="chat-cards">
                    {m.products.slice(0, CHAT_CARD_LIMIT).map((p, j) => (
                      <ProductCard key={p.product_id} product={p} index={j} compact />
                    ))}
                    {m.products.length > CHAT_CARD_LIMIT && (
                      <p className="chat-more">+{m.products.length - CHAT_CARD_LIMIT} more in Dan's picks on the page</p>
                    )}
                  </div>
                )}
              </div>
            ))}
            {chat.sending && (
              <div className="bubble-row assistant">
                <div className="bubble assistant typing" aria-label="Dan is typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            {chat.error && <div className="chat-error">{chat.error}</div>}
          </div>

          <div className="chips">
            {suggestionsFor(onProductPage).map((s) => (
              <button key={s} className="chip" disabled={chat.sending} onClick={() => void chat.send(s)}>
                {s}
              </button>
            ))}
          </div>

          <form
            className="chat-input"
            onSubmit={(e) => {
              e.preventDefault()
              void chat.send(chat.draft)
            }}
          >
            <textarea
              ref={inputRef}
              rows={1}
              maxLength={1000}
              placeholder={onProductPage ? 'Ask about this item…' : 'Ask about hoodies, sizes, prices…'}
              value={chat.draft}
              onChange={(e) => chat.setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  void chat.send(chat.draft)
                }
              }}
            />
            <button className="send" type="submit" disabled={chat.sending || !chat.draft.trim()} aria-label="Send">
              ➤
            </button>
          </form>
        </section>
      )}

      <button
        className="chat-fab"
        onClick={() => chat.setOpen(!chat.open)}
        aria-label={chat.open ? 'Close chat' : 'Open chat'}
      >
        {chat.open ? '✕' : <Paw size={28} />}
        {!chat.open && <span className="fab-label">Ask Dan</span>}
      </button>
    </div>
  )
}
