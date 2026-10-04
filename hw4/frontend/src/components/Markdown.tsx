import { Fragment, type ReactNode } from 'react'

/** Tiny, safe markdown for chat replies: **bold**, *italic*, and "- " bullet lists. No HTML is ever injected. */
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g).map((chunk, i) => {
    if (chunk.startsWith('**') && chunk.endsWith('**')) return <strong key={i}>{chunk.slice(2, -2)}</strong>
    if (chunk.startsWith('*') && chunk.endsWith('*') && chunk.length > 2) return <em key={i}>{chunk.slice(1, -1)}</em>
    return <Fragment key={i}>{chunk}</Fragment>
  })
}

export default function Markdown({ text }: { text: string }) {
  const blocks: ReactNode[] = []
  let list: string[] = []
  const flush = () => {
    if (list.length) {
      blocks.push(
        <ul key={`ul${blocks.length}`}>
          {list.map((li, i) => (
            <li key={i}>{inline(li)}</li>
          ))}
        </ul>,
      )
      list = []
    }
  }
  for (const line of text.split('\n')) {
    const bullet = line.match(/^\s*(?:[-*•]|\d+\.)\s+(.*)$/)
    if (bullet) {
      list.push(bullet[1])
      continue
    }
    flush()
    if (line.trim()) blocks.push(<p key={`p${blocks.length}`}>{inline(line)}</p>)
  }
  flush()
  return <>{blocks}</>
}
