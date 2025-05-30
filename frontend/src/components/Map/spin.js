import { useEffect, useRef } from 'react'

export default function useSpin(mapRef, params, spinSpeed, setSpinSpeed) {
  const spinRef = useRef(null)
  const decayTimerRef = useRef(null)
  const stateRef = useRef({
    direction: 1,
    lastDragPos: null,
    lastDragTime: null,
    decayRate: 0.95,
    dragStarted: false
  })

  useEffect(() => {
    const map = mapRef.current
    if (!map || !params.spin) return

    // start the RAF loop
    let lastTime = performance.now()
    function animate(now) {
      const delta = ((now - lastTime) / 1000) * Math.abs(spinSpeed)
      const dir = Math.sign(spinSpeed) || 1
      map.rotateTo((map.getBearing() + delta * dir) % 360, { duration: 0 })
      lastTime = now
      spinRef.current = requestAnimationFrame(animate)
    }
    spinRef.current = requestAnimationFrame(animate)

    // decay
    function startDecay() {
      clearInterval(decayTimerRef.current)
      decayTimerRef.current = setInterval(() => {
        setSpinSpeed(s => {
          const dec = s * stateRef.current.decayRate
          return Math.abs(dec) < 0.5
            ? Math.sign(s) * 0.5
            : dec
        })
      }, 100)
    }
    startDecay()

    // drag controls
    function onDragStart(e) {
      e.originalEvent.preventDefault?.()
      stateRef.current.dragStarted = true
      const ev = (e.originalEvent.touches?.[0] || e.originalEvent)
      stateRef.current.lastDragPos = [ev.clientX, ev.clientY]
      stateRef.current.lastDragTime = performance.now()
    }
    function onDrag(e) {
      if (!stateRef.current.dragStarted) return
      const ev = (e.originalEvent.touches?.[0] || e.originalEvent)
      const now = performance.now()
      const dt = now - stateRef.current.lastDragTime
      if (dt < 20) return

      const [lx, ly] = stateRef.current.lastDragPos
      const cx = ev.clientX, cy = ev.clientY
      // compute direction via cross product sign
      const rect = map.getContainer().getBoundingClientRect()
      const vx1 = lx - rect.width/2, vy1 = ly - rect.height/2
      const vx2 = cx - rect.width/2, vy2 = cy - rect.height/2
      const cross = vx1*vy2 - vy1*vx2
      stateRef.current.direction = cross > 0 ? 1 : -1

      const dist = Math.hypot(cx - lx, cy - ly)
      if (dist < 10) return
      const velocity = dist / (dt/1000)
      const incr = Math.min(velocity*0.01, 5) * -stateRef.current.direction
      setSpinSpeed(s => Math.max(-100, Math.min(100, s + incr)))

      stateRef.current.lastDragPos = [cx, cy]
      stateRef.current.lastDragTime = now
      startDecay()
    }
    function onDragEnd() {
      stateRef.current.dragStarted = false
    }

    map.on('mousedown', onDragStart)
    map.on('touchstart', onDragStart)
    map.on('mousemove', onDrag)
    map.on('touchmove', onDrag)
    map.on('mouseup', onDragEnd)
    map.on('touchend', onDragEnd)
    map.on('mouseleave', onDragEnd)

    return () => {
      if (spinRef.current) cancelAnimationFrame(spinRef.current)
      clearInterval(decayTimerRef.current)
      map.off('mousedown', onDragStart)
      map.off('touchstart', onDragStart)
      map.off('mousemove', onDrag)
      map.off('touchmove', onDrag)
      map.off('mouseup', onDragEnd)
      map.off('touchend', onDragEnd)
      map.off('mouseleave', onDragEnd)
    }
  }, [params.spin, spinSpeed])
}