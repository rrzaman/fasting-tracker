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

    // MOUSE TRACKING
    const mouse = { x: -1000, y: -1000 }
    let mouseSparkles =[]

    const handleMouseMove = (e) => {
      // Support for both mouse AND mobile touch screens
      mouse.x = e.clientX || (e.touches && e.touches[0].clientX) || -1000
      mouse.y = e.clientY || (e.touches && e.touches[0].clientY) || -1000

      // Spawn only 1 particle per movement (down from 4), with an 80% chance
      if (Math.random() < 0.8) {
        mouseSparkles.push({
          x: mouse.x + (Math.random() - 0.5) * 10, // Tighter spread
          y: mouse.y + (Math.random() - 0.5) * 10,
          vx: (Math.random() - 0.5) * 1, 
          vy: Math.random() * 1 + 0.5,   
          r: Math.random() * 1.5 + 0.5, // Much smaller radius
          life: 1,
          decay: Math.random() * 0.03 + 0.015 // Fades away faster
        })
      }
    }

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('touchmove', handleMouseMove) // Added touch support

    const drawCrossStar = (x, y, r, opacity) => {
      ctx.save()
      ctx.beginPath()
      ctx.translate(x, y)
      
      // Increased from 0.35 to 0.45 to make the "arms" of the star much thicker
      ctx.moveTo(0, -r)
      ctx.quadraticCurveTo(0, 0, r*0.45, 0)
      ctx.quadraticCurveTo(0, 0, 0, r)
      ctx.quadraticCurveTo(0, 0, -r*0.45, 0)
      ctx.quadraticCurveTo(0, 0, 0, -r)
      
      const grad = ctx.createRadialGradient(0, 0, 0, 0, 0, r)
      grad.addColorStop(0, `rgba(255, 255, 255, ${opacity})`)
      grad.addColorStop(0.4, `rgba(255, 255, 255, ${opacity * 0.6})`)
      grad.addColorStop(1, 'transparent')
      
      ctx.fillStyle = grad
      ctx.fill()

      // ADDED: A solid inner core so the star is always distinctly visible
      ctx.beginPath()
      ctx.arc(0, 0, r * 0.25, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`
      ctx.fill()

      ctx.restore()
    }

    const bgStars = Array.from({ length: 150 }, () => {
      const startX = Math.random() * window.innerWidth
      const startY = Math.random() * window.innerHeight
      return {
        x: startX,  y: startY,
        ox: startX, oy: startY, 
        vx: 0,      vy: 0,      
        r: Math.random() * 3 + 3, // UPGRADED: Now between 3px and 6px wide
        baseOpacity: Math.random() * 0.4 + 0.4, // UPGRADED: Minimum brightness raised so they don't fade to black
        twinkleSpeed: Math.random() * 0.015 + 0.005,
        twinkleOffset: Math.random() * Math.PI * 2,
      }
    })

    class ShootingStar {
      constructor() { this.reset() }

      reset() {
        this.x = Math.random() * window.innerWidth * 0.7
        this.y = Math.random() * window.innerHeight * 0.4
        this.size = Math.random() * 0.8 + 0.4 
        this.maxOpacity = Math.random() * 0.6 + 0.4 
        this.speed = (Math.random() * 4 + 3) * (this.size * 0.8) 
        this.angle = (Math.PI / 5) + (Math.random() - 0.5) * 0.2
        this.opacity = 0
        this.fadeIn = true
        this.trail =[]
        this.active = false
        this.sparkles =[] 
        this.delay = Math.random() * 20000 + 8000
        setTimeout(() => { this.active = true }, this.delay) 
      }

      update() {
        if (!this.active) return
        if (this.fadeIn && this.opacity < this.maxOpacity) {
          this.opacity += 0.05
        } else {
          this.fadeIn = false
        }

        this.trail.push({ x: this.x, y: this.y, opacity: this.opacity })
        if (this.trail.length > 25 * this.size) this.trail.shift() 

        this.x += Math.cos(this.angle) * this.speed
        this.y += Math.sin(this.angle) * this.speed

        if (Math.random() < 0.4 * this.size) {
          this.sparkles.push({
            x: this.x + (Math.random() - 0.5) * 10 * this.size,
            y: this.y + (Math.random() - 0.5) * 10 * this.size,
            r: (Math.random() * 1.5 + 0.5) * this.size,
            life: 1,
            decay: Math.random() * 0.04 + 0.02,
          })
        }

        this.sparkles = this.sparkles
          .map(s => ({ ...s, life: s.life - s.decay }))
          .filter(s => s.life > 0)

        if (this.x > window.innerWidth + 100 || this.y > window.innerHeight + 100) {
          this.reset()
        }
      }

      draw(ctx) {
        if (!this.active || this.trail.length < 2) return

        ctx.beginPath()
        ctx.moveTo(this.trail[0].x, this.trail[0].y)
        for (let i = 1; i < this.trail.length; i++) {
          ctx.lineTo(this.trail[i].x, this.trail[i].y)
        }
        
        const grad = ctx.createLinearGradient(this.trail[0].x, this.trail[0].y, this.x, this.y)
        grad.addColorStop(0, 'transparent')
        grad.addColorStop(1, `rgba(255, 255, 220, ${this.opacity * 0.8})`)
        ctx.strokeStyle = grad
        ctx.lineWidth = 2 * this.size
        ctx.stroke()

        const headRadius = 8 * this.size
        const headGrad = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, headRadius)
        headGrad.addColorStop(0, `rgba(255, 255, 255, ${this.opacity})`)
        headGrad.addColorStop(0.3, `rgba(240, 192, 64, ${this.opacity * 0.5})`)
        headGrad.addColorStop(1, 'transparent')
        
        ctx.beginPath()
        ctx.arc(this.x, this.y, headRadius, 0, Math.PI * 2)
        ctx.fillStyle = headGrad
        ctx.fill()

        this.sparkles.forEach(s => {
          ctx.beginPath()
          ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(240, 192, 64, ${s.life * this.opacity})`
          ctx.fill()
        })
      }
    }

    const shootingStars = Array.from({ length: 2 }, (_, i) => {
      const star = new ShootingStar()
      star.delay = i * 8000 + Math.random() * 10000
      setTimeout(() => { star.active = true }, star.delay)
      return star
    })

    const CONSTELLATION_DIST = 130
    const CONSTELLATION_SQ   = CONSTELLATION_DIST * CONSTELLATION_DIST

    let t = 0

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      t += 1

      // PHASE 1: physics — update positions and cache opacity
      bgStars.forEach(s => {
        const dx = mouse.x - s.x
        const dy = mouse.y - s.y
        const dist = Math.sqrt(dx * dx + dy * dy)

        if (dist < 120) {
          const force = (120 - dist) / 120
          s.vx -= (dx / dist) * force * 0.6
          s.vy -= (dy / dist) * force * 0.6
        }

        s.vx += (s.ox - s.x) * 0.02
        s.vy += (s.oy - s.y) * 0.02
        s.vx *= 0.9
        s.vy *= 0.9
        s.x += s.vx
        s.y += s.vy

        const twinkle = Math.cos(t * s.twinkleSpeed + s.twinkleOffset) * Math.sin(t * s.twinkleSpeed * 0.5)
        s._opacity = Math.max(0, s.baseOpacity + twinkle * 0.4)
      })

      // PHASE 2: constellation lines (drawn under stars)
      ctx.save()
      ctx.lineWidth = 0.4
      for (let i = 0; i < bgStars.length; i++) {
        const a = bgStars[i]
        for (let j = i + 1; j < bgStars.length; j++) {
          const b = bgStars[j]
          const dx = b.x - a.x
          const dy = b.y - a.y
          const dSq = dx * dx + dy * dy
          if (dSq < CONSTELLATION_SQ) {
            const alpha = (1 - Math.sqrt(dSq) / CONSTELLATION_DIST) * 0.07
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.strokeStyle = `rgba(82,212,148,${alpha.toFixed(3)})`
            ctx.stroke()
          }
        }
      }
      ctx.restore()

      // PHASE 3: draw stars on top of lines
      bgStars.forEach(s => {
        drawCrossStar(s.x, s.y, s.r, s._opacity)
      })

      // MOUSE STARDUST
      mouseSparkles.forEach(s => {
        s.x += s.vx
        s.y += s.vy
        s.life -= s.decay

        if (s.life > 0) {
          // Inner core - slightly transparent now
          ctx.beginPath()
          ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(255, 220, 100, ${s.life * 0.7})`
          ctx.fill()
          
          // Outer magical glow ring - smaller and much softer
          ctx.beginPath()
          ctx.arc(s.x, s.y, s.r * 1.8, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(240, 192, 64, ${s.life * 0.15})`
          ctx.fill()
        }
      })
      mouseSparkles = mouseSparkles.filter(s => s.life > 0)

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
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('touchmove', handleMouseMove)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: -1,
      }}
    />
  )
}