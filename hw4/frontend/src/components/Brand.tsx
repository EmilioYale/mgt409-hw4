/** Varsity-patch "CC" monogram and a bulldog paw: drawn inline so there are no image assets to ship. */

export function Monogram({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" className="monogram">
      <circle cx="32" cy="32" r="30" fill="var(--navy)" />
      <circle cx="32" cy="32" r="26" fill="none" stroke="var(--cream)" strokeWidth="1.5" strokeDasharray="3 3" />
      <text
        x="32"
        y="41"
        textAnchor="middle"
        fontFamily="Graduate, serif"
        fontSize="24"
        fill="var(--cream)"
        letterSpacing="-1"
      >
        CC
      </text>
    </svg>
  )
}

export function Paw({ size = 22, className = '' }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className={className}>
      <g fill="currentColor">
        <ellipse cx="16" cy="21.5" rx="7.5" ry="6.5" />
        <ellipse cx="6.5" cy="13" rx="3" ry="3.8" />
        <ellipse cx="12" cy="7.5" rx="3" ry="3.8" />
        <ellipse cx="20" cy="7.5" rx="3" ry="3.8" />
        <ellipse cx="25.5" cy="13" rx="3" ry="3.8" />
      </g>
    </svg>
  )
}
