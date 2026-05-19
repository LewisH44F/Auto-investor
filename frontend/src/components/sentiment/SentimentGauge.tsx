import { useEffect, useRef } from 'react'
import { clsx } from 'clsx'
import { formatSentimentScore } from '@/utils/formatters'

interface SentimentGaugeProps {
  score: number // -1 to 1
  size?: number
  label?: string
  className?: string
}

export default function SentimentGauge({
  score,
  size = 120,
  label,
  className,
}: SentimentGaugeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Normalize -1..1 to 0..1
  const normalized = (score + 1) / 2

  const getColor = (s: number) => {
    if (s > 0.6) return '#10b981'
    if (s > 0.4) return '#34d399'
    if (s > 0.35) return '#f59e0b'
    if (s > 0.2) return '#f87171'
    return '#ef4444'
  }

  const color = getColor(normalized)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const cx = size / 2
    const cy = size / 2
    const radius = (size / 2) * 0.75
    const startAngle = Math.PI
    const endAngle = Math.PI * 2

    ctx.clearRect(0, 0, size, size)

    // Background arc
    ctx.beginPath()
    ctx.arc(cx, cy, radius, startAngle, endAngle)
    ctx.strokeStyle = 'rgba(255,255,255,0.06)'
    ctx.lineWidth = 10
    ctx.lineCap = 'round'
    ctx.stroke()

    // Color arc
    if (normalized > 0.01) {
      ctx.beginPath()
      ctx.arc(cx, cy, radius, startAngle, startAngle + (endAngle - startAngle) * normalized)
      ctx.strokeStyle = color
      ctx.lineWidth = 10
      ctx.lineCap = 'round'
      ctx.stroke()
    }

    // Center score
    ctx.fillStyle = '#ffffff'
    ctx.font = `bold ${size * 0.16}px JetBrains Mono, monospace`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(
      `${score > 0 ? '+' : ''}${score.toFixed(2)}`,
      cx,
      cy - size * 0.05
    )

    ctx.fillStyle = 'rgba(255,255,255,0.3)'
    ctx.font = `${size * 0.09}px Inter, sans-serif`
    ctx.fillText('SENTIMENT', cx, cy + size * 0.12)
  }, [score, normalized, size, color])

  return (
    <div className={clsx('flex flex-col items-center gap-2', className)}>
      <canvas ref={canvasRef} width={size} height={size / 1.6} />
      <div className={clsx('text-xs font-medium px-2 py-0.5 rounded-full border',
        score > 0.3 ? 'text-gain border-gain/30 bg-gain/10' :
        score > -0.3 ? 'text-warning border-warning/30 bg-warning/10' :
        'text-loss border-loss/30 bg-loss/10'
      )}>
        {label || formatSentimentScore(score)}
      </div>
    </div>
  )
}
