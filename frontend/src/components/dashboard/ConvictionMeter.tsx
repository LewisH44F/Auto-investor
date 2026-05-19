import { useEffect, useRef } from 'react'
import { clsx } from 'clsx'
import { getConfidenceBgColor } from '@/utils/colors'

interface ConvictionMeterProps {
  score: number // 0-100
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
  animated?: boolean
}

export default function ConvictionMeter({
  score,
  size = 'md',
  showLabel = true,
  className,
  animated = true,
}: ConvictionMeterProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animRef = useRef<number>(0)
  const currentScoreRef = useRef(0)

  const dimensions = { sm: 80, md: 140, lg: 200 }
  const dim = dimensions[size]

  const color = getConfidenceBgColor(score)

  const getLabel = (s: number) => {
    if (s >= 80) return 'HIGH CONVICTION'
    if (s >= 65) return 'MODERATE'
    if (s >= 40) return 'LOW'
    return 'MINIMAL'
  }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const cx = dim / 2
    const cy = dim / 2
    const radius = (dim / 2) * 0.78
    const lineWidth = size === 'sm' ? 8 : size === 'md' ? 14 : 18
    const startAngle = Math.PI * 0.75
    const endAngle = Math.PI * 2.25
    const totalAngle = endAngle - startAngle

    const draw = (currentScore: number) => {
      ctx.clearRect(0, 0, dim, dim)

      // Background arc
      ctx.beginPath()
      ctx.arc(cx, cy, radius, startAngle, endAngle)
      ctx.strokeStyle = 'rgba(255,255,255,0.06)'
      ctx.lineWidth = lineWidth
      ctx.lineCap = 'round'
      ctx.stroke()

      // Tick marks
      for (let i = 0; i <= 10; i++) {
        const angle = startAngle + (totalAngle * i) / 10
        const innerR = radius - lineWidth / 2 - 3
        const outerR = radius - lineWidth / 2 - 8
        ctx.beginPath()
        ctx.moveTo(cx + Math.cos(angle) * innerR, cy + Math.sin(angle) * innerR)
        ctx.lineTo(cx + Math.cos(angle) * outerR, cy + Math.sin(angle) * outerR)
        ctx.strokeStyle = 'rgba(255,255,255,0.1)'
        ctx.lineWidth = 1
        ctx.stroke()
      }

      if (currentScore > 0) {
        // Glow effect
        ctx.beginPath()
        ctx.arc(cx, cy, radius, startAngle, startAngle + (totalAngle * currentScore) / 100)
        ctx.strokeStyle = color + '40'
        ctx.lineWidth = lineWidth + 6
        ctx.lineCap = 'round'
        ctx.stroke()

        // Main arc
        ctx.beginPath()
        ctx.arc(cx, cy, radius, startAngle, startAngle + (totalAngle * currentScore) / 100)
        ctx.strokeStyle = color
        ctx.lineWidth = lineWidth
        ctx.lineCap = 'round'
        ctx.stroke()
      }

      // Score text
      ctx.fillStyle = '#ffffff'
      ctx.font = `bold ${size === 'sm' ? 16 : size === 'md' ? 28 : 40}px JetBrains Mono, monospace`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(Math.round(currentScore).toString(), cx, cy - (size === 'sm' ? 4 : 6))

      // Percent label
      ctx.fillStyle = 'rgba(255,255,255,0.4)'
      ctx.font = `${size === 'sm' ? 9 : 11}px JetBrains Mono, monospace`
      ctx.fillText('CONFIDENCE', cx, cy + (size === 'sm' ? 10 : 18))
    }

    if (animated) {
      const targetScore = score
      const duration = 800
      const startTime = performance.now()
      const startScore = currentScoreRef.current

      const animate = (now: number) => {
        const elapsed = now - startTime
        const progress = Math.min(elapsed / duration, 1)
        const eased = 1 - Math.pow(1 - progress, 3)
        const current = startScore + (targetScore - startScore) * eased
        currentScoreRef.current = current
        draw(current)
        if (progress < 1) {
          animRef.current = requestAnimationFrame(animate)
        }
      }

      animRef.current = requestAnimationFrame(animate)
    } else {
      currentScoreRef.current = score
      draw(score)
    }

    return () => cancelAnimationFrame(animRef.current)
  }, [score, dim, size, color, animated])

  return (
    <div className={clsx('flex flex-col items-center gap-2', className)}>
      <canvas
        ref={canvasRef}
        width={dim}
        height={dim}
        className="block"
        style={{ width: dim, height: dim }}
      />
      {showLabel && (
        <div
          className={clsx(
            'text-[10px] font-bold tracking-widest px-3 py-1 rounded-full border',
            score >= 80
              ? 'text-gain border-gain/30 bg-gain/10'
              : score >= 65
              ? 'text-brand border-brand/30 bg-brand/10'
              : score >= 40
              ? 'text-warning border-warning/30 bg-warning/10'
              : 'text-loss border-loss/30 bg-loss/10'
          )}
        >
          {getLabel(score)}
        </div>
      )}
    </div>
  )
}
