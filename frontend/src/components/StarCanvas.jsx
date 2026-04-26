import { useEffect, useRef } from 'react'

export default function StarCanvas() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let animationId

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    // Static background stars
    const bgStars = Array.from({ length: 120 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() < 0.1 ? Math.random() * 2 + 1.5 : Math.random() * 1.2,  // 10% bigger stars
      opacity: Math.random() * 0.7 + 0.15,
      twinkleSpeed: Math.random() * 0.03 + 0.005,
      twinkleOffset: Math.random() * Math.PI * 2,
    }))

    // Shooting star class
    class ShootingStar {
      constructor() { this.reset() }

      reset() {
        this.x = Math.random() * window.innerWidth * 0.7
        this.y = Math.random() * window.innerHeight * 0.4
        this.len = Math.random() * 120 + 60
        this.speed = Math.random() * 4 + 2
        this.angle = (Math.PI / 5) + (Math.random() - 0.5) * 0.3
        this.opacity = 0
        this.fadeIn = true
        this.trail = []
        this.active = false
        this.delay = Math.random() * 20000 + 12000
        this.active = false
        this.sparkles = false
        setTimeout(() => { this.active = true }, this.delay) 
      }

      update() {
        if (!this.active) return

        if (this.fadeIn && this.opacity < 1) {
          this.opacity += 0.05
        } else {
          this.fadeIn = false
        }

        this.trail.push({ x: this.x, y: this.y, opacity: this.opacity })
        if (this.trail.length > 20) this.trail.shift()

        this.x += Math.cos(this.angle) * this.speed
        this.y += Math.sin(this.angle) * this.speed

        // Random sparkles along the trail
        if (Math.random() < 0.3) {
          this.sparkles.push({
            x: this.x + (Math.random() - 0.5) * 10,
            y: this.y + (Math.random() - 0.5) * 10,
            r: Math.random() * 2 + 0.5,
            life: 1,
            decay: Math.random() * 0.05 + 0.03,
          })
        }

        this.sparkles = this.sparkles
          .map(s => ({ ...s, life: s.life - s.decay }))
          .filter(s => s.life > 0)

        if (
          this.x > window.innerWidth + 100 ||
          this.y > window.innerHeight + 100
        ) {
          this.reset()
        }
      }

      draw(ctx) {
        if (!this.active || this.trail.length < 2) return

        // Draw trail
        for (let i = 1; i < this.trail.length; i++) {
          const t = i / this.trail.length
          const prev = this.trail[i - 1]
          const curr = this.trail[i]

          ctx.beginPath()
          ctx.moveTo(prev.x, prev.y)
          ctx.lineTo(curr.x, curr.y)
          ctx.strokeStyle = `rgba(255, 255, 220, ${t * this.opacity * 0.8})`
          ctx.lineWidth = t * 2
          ctx.stroke()
        }

        // Draw head glow
        const grad = ctx.createRadialGradient(
          this.x, this.y, 0,
          this.x, this.y, 6
        )
        grad.addColorStop(0, `rgba(255, 255, 200, ${this.opacity})`)
        grad.addColorStop(1, 'transparent')
        ctx.beginPath()
        ctx.arc(this.x, this.y, 6, 0, Math.PI * 2)
        ctx.fillStyle = grad
        ctx.fill()

        // Draw sparkles
        this.sparkles.forEach(s => {
          ctx.beginPath()
          ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(232, 184, 75, ${s.life})`
          ctx.fill()
        })
      }
    }

    const shootingStars = Array.from({ length: 3 }, (_, i) => {
      const star = new ShootingStar()
      // Force stagger — each star starts at a different point in time
      star.delay = i * 8000 + Math.random() * 5000
      setTimeout(() => { star.active = true }, star.delay)
      return star
    })

    let t = 0

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      t += 0.01

      // Draw twinkling background stars
      bgStars.forEach(s => {
        const opacity = s.opacity * (0.3 + 0.7 * Math.abs(Math.sin(t * s.twinkleSpeed * 60 + s.twinkleOffset)))

        ctx.beginPath()
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`
        ctx.fill()
      })

      // Draw shooting stars
      shootingStars.forEach(s => {
        s.update()
        s.draw(ctx)
      })

      animationId = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  )
}