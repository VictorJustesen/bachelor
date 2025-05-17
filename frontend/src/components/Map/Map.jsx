import { useRef, useEffect, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

function Map({ params, markers = [], onMapLoad }) {
  const mapRef = useRef()
  const mapContainerRef = useRef()
  const spinRef = useRef()
  const decayTimerRef = useRef(null)
  const markersRef = useRef([])
  
  // Use React state for values we want to trigger re-renders
  const [spinSpeed, setSpinSpeed] = useState(8) // Default spin speed in degrees per second
  
  // Use refs for values that don't need to trigger re-renders
  const spinStateRef = useRef({
    isSpinning: false,
    direction: 1, // 1 for clockwise, -1 for counter-clockwise
    lastDragPosition: null,
    dragStarted: false,
    lastDragTime: null,
    decayRate: 0.95 // Speed will decrease by 5% every decay interval
  })

  useEffect(() => {
    mapboxgl.accessToken = 'pk.eyJ1IjoiZ2luZ2VybG9yZCIsImEiOiJjbWFzMTRremowYjNpMmxzaG05bG1pajA1In0.stYxpVfJdphbhzGq1c0Xlw'
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/streets-v12',    // ← ensure composite source is present
      center: params.center,
      zoom: params.zoom,
      pitch: params.pitch,
      bearing: params.bearing,
      interactive: params.interactive !== false,
      attributionControl: false,
      maxPitch: 85,
      maxZoom: 20,
    })

    // once style is ready, add 3d‐buildings and events
    mapRef.current.on('style.load', () => {
      const map = mapRef.current

      // add the 3d build-extrusion layer
      if (!map.getLayer('3d-buildings')) {
        map.addLayer({
          id: '3d-buildings',
          source: 'composite',
          'source-layer': 'building',
          type: 'fill-extrusion',
          minzoom: 14,
          paint: {
            'fill-extrusion-color': [
              'case',
              ['boolean', ['feature-state', 'select'], false], '#00ff00',   // selected = green
              ['boolean', ['feature-state', 'hover'], false], '#ff0000',  // hover = red
              '#aaa'                                                      // default
            ],
            'fill-extrusion-height': ['get', 'height'],
            'fill-extrusion-base': ['get', 'min_height'],
            'fill-extrusion-opacity': 1
          }
        }, 'road-label')
      }

      // add house‐number labels
      if (!map.getLayer('house-numbers')) {
        map.addLayer({
          id: 'house-numbers',
          type: 'symbol',
          source: 'composite',
          'source-layer': 'housenum_label',
          minzoom: 16,
          layout: {
            'text-field': ['get', 'house_num'],      // the feature property
            'text-font': ['DIN Offc Pro Medium','Arial Unicode MS Regular'],
            'text-size': 12,
            'text-offset': [0, 0.5],
          },
          paint: {
            'text-color': '#222',
            'text-halo-color': '#fff',
            'text-halo-width': 1,
          }
        })
      }

      // only wire up hover/click when interactive
      if (params.interactive) {
        let hoveredId = null

        // hover
        map.on('mousemove', '3d-buildings', e => {
          if (!e.features.length) return
          // clear old hover
          if (hoveredId !== null) {
            map.setFeatureState(
              { source: 'composite', sourceLayer: 'building', id: hoveredId },
              { hover: false }
            )
          }
          hoveredId = e.features[0].id
          map.setFeatureState(
            { source: 'composite', sourceLayer: 'building', id: hoveredId },
            { hover: true }
          )
          map.getCanvas().style.cursor = 'pointer'
        })

        // leave
        map.on('mouseleave', '3d-buildings', () => {
          if (hoveredId !== null) {
            map.setFeatureState(
              { source: 'composite', sourceLayer: 'building', id: hoveredId },
              { hover: false }
            )
            hoveredId = null
          }
          map.getCanvas().style.cursor = ''
        })

        // click
        map.on('click', '3d-buildings', async e => {
          if (!e.features.length) return
          const { lng, lat } = e.lngLat
          // reverse-geocode via Mapbox
          const resp = await fetch(
            `https://api.mapbox.com/geocoding/v5/mapbox.places/` +
            `${lng},${lat}.json?access_token=${mapboxgl.accessToken}`
          )
          const json = await resp.json()
          const address = json.features[0]?.place_name || 'Address not found'
          // show popup
          console.log('address', address)
        })
      }
    })

    if (onMapLoad) onMapLoad(mapRef.current)
    return () => {
      mapRef.current.remove()
      if (spinRef.current) cancelAnimationFrame(spinRef.current)
    }
  }, [])

  // Smooth spinning using Mapbox's rotateTo with drag direction control
  useEffect(() => {
    if (!mapRef.current) return
    const map = mapRef.current
    
    // Function to handle speed decay
    function startSpeedDecay() {
      // Clear any existing decay timer
      if (decayTimerRef.current) {
        clearInterval(decayTimerRef.current);
      }
      
      // Set up decay timer - runs every 100ms
      decayTimerRef.current = setInterval(() => {
        // Only decay if we're above minimum speed
        if (Math.abs(spinSpeed) > 8) {
          // Apply decay to current speed
          setSpinSpeed(prevSpeed => {
            const decayedSpeed = prevSpeed * spinStateRef.current.decayRate;
            
            // If speed is very low, reset to minimum in the current direction
            if (Math.abs(decayedSpeed) < 0.5) {
              return spinStateRef.current.direction * 0.5;
            }
            
            return decayedSpeed;
          });
        }
      }, 100);
    }
    
    if (params.spin) {
      // Set up spin animation
      let lastTime = performance.now()
      
      function animate(now) {
        const bearing = map.getBearing()
        const delta = ((now - lastTime) / 1000) * Math.abs(spinSpeed)
        // Get direction from the sign of spinSpeed
        const direction = Math.sign(spinSpeed) || 1;
        
        // Apply the direction to the rotation
        map.rotateTo(
          (bearing + delta * direction) % 360, 
          { duration: 0 }
        )
        lastTime = now
        spinRef.current = requestAnimationFrame(animate)
      }
      
      spinStateRef.current.isSpinning = true
      spinRef.current = requestAnimationFrame(animate)
      startSpeedDecay()
      
      // Set up drag handlers for direction control
      function handleDragStart(e) {
        // Prevent default behavior to avoid confusion with map panning
        if (e.originalEvent.preventDefault) {
          e.originalEvent.preventDefault()
        }
        
        spinStateRef.current.dragStarted = true
        spinStateRef.current.lastDragPosition = [
          e.originalEvent.clientX || (e.originalEvent.touches && e.originalEvent.touches[0].clientX),
          e.originalEvent.clientY || (e.originalEvent.touches && e.originalEvent.touches[0].clientY)
        ]
        spinStateRef.current.lastDragTime = performance.now()
      }

      function handleDrag(e) {
        if (!spinStateRef.current.dragStarted || !spinStateRef.current.lastDragPosition) return
        
        // Get current position
        const clientX = e.originalEvent.clientX || (e.originalEvent.touches && e.originalEvent.touches[0].clientX)
        const clientY = e.originalEvent.clientY || (e.originalEvent.touches && e.originalEvent.touches[0].clientY)
        if (!clientX || !clientY) return
        
        const currentPos = [clientX, clientY]
        const lastPos = spinStateRef.current.lastDragPosition
        const currentTime = performance.now()
        const timeDelta = currentTime - spinStateRef.current.lastDragTime
        
        // Skip if the time delta is too small (prevents jitter)
        if (timeDelta < 30) return
        
        // Center of the map container for reference
        const mapContainer = map.getContainer()
        const centerX = mapContainer.offsetWidth / 2
        const centerY = mapContainer.offsetHeight / 2
        
        // Calculate vectors from center to last and current positions
        const lastVector = [lastPos[0] - centerX, lastPos[1] - centerY]
        const currentVector = [currentPos[0] - centerX, currentPos[1] - centerY]
        
        // Calculate angle between these vectors to determine direction
        const angleBetween = Math.atan2(
          lastVector[0] * currentVector[1] - lastVector[1] * currentVector[0],
          lastVector[0] * currentVector[0] + lastVector[1] * currentVector[1]
        )
        
        // Determine direction based on the angle
        const dragDirection = angleBetween > 0 ? 1 : -1
        spinStateRef.current.direction = dragDirection
        
        // Calculate drag distance and velocity
        const distance = Math.sqrt(
          Math.pow(currentPos[0] - lastPos[0], 2) + 
          Math.pow(currentPos[1] - lastPos[1], 2)
        )
        
        // Calculate velocity (distance / time)
        const velocity = distance / (timeDelta / 1000)
        console.log(velocity)
        // Calculate new speed increment based on velocity
        const speedIncrement = Math.min(velocity * 0.01, 5) * -dragDirection
        
        // Update speed (additive)
        setSpinSpeed(prevSpeed => {
          // Limit maximum speed
          const newSpeed = prevSpeed + speedIncrement
          return Math.max(Math.min(newSpeed, 100), -100)
        })
        
        // Update position and time for next calculation
        spinStateRef.current.lastDragPosition = currentPos
        spinStateRef.current.lastDragTime = currentTime
        
        // Reset the decay timer
        startSpeedDecay()
      }

      function handleDragEnd() {
        spinStateRef.current.dragStarted = false
        spinStateRef.current.lastDragPosition = null
        spinStateRef.current.lastDragTime = null
      }

      // Attach the event listeners for drag control
      map.on('mousedown', handleDragStart)
      map.on('touchstart', handleDragStart)
      map.on('mousemove', handleDrag)
      map.on('touchmove', handleDrag)
      map.on('mouseup', handleDragEnd)
      map.on('touchend', handleDragEnd)
      map.on('mouseleave', handleDragEnd)
      
      return () => {
        // Clean up animation
        if (spinRef.current) {
          cancelAnimationFrame(spinRef.current)
        }
        
        // Clean up decay timer
        if (decayTimerRef.current) {
          clearInterval(decayTimerRef.current)
        }
        
        spinStateRef.current.isSpinning = false
        
        // Remove all event listeners
        map.off('mousedown', handleDragStart)
        map.off('touchstart', handleDragStart)
        map.off('mousemove', handleDrag)
        map.off('touchmove', handleDrag)
        map.off('mouseup', handleDragEnd)
        map.off('touchend', handleDragEnd)
        map.off('mouseleave', handleDragEnd)
      }
    } else {
      // If spinning is turned off, make sure we cancel any existing animation
      if (spinRef.current) {
        cancelAnimationFrame(spinRef.current)
        spinStateRef.current.isSpinning = false
      }
      
      // Clear decay timer
      if (decayTimerRef.current) {
        clearInterval(decayTimerRef.current)
      }
    }
  }, [params.spin, spinSpeed])

  // Animate to new params with flyTo if requested
  useEffect(() => {
    if (!mapRef.current) return
    if (params.flyToOnMount) {
      mapRef.current.flyTo({
        center: params.center,
        zoom: params.zoom,
        bearing: params.bearing,
        pitch: params.pitch,
        speed: 1.2, // adjust for slower/faster animation
        curve: 1.8,
        essential: true,
      })
    } else {
      mapRef.current.setCenter(params.center)
      mapRef.current.setZoom(params.zoom)
      mapRef.current.setPitch(params.pitch)
      if (!params.spin) {
        mapRef.current.setBearing(params.bearing)
      }
    }
  }, [params.center, params.zoom, params.pitch, params.bearing, params.spin, params.flyToOnMount])

  // toggle map interactivity on the fly
  useEffect(() => {
    if (!mapRef.current) return
    const map = mapRef.current
    if (params.interactive) {
      map.scrollZoom.enable()
      map.boxZoom.enable()
      map.dragRotate.enable()
      map.dragPan.enable()
      map.keyboard.enable()
      map.doubleClickZoom.enable()
      map.touchZoomRotate.enable()
    } else {
      map.scrollZoom.disable()
      map.boxZoom.disable()
      map.dragRotate.disable()
      map.dragPan.disable()
      map.keyboard.disable()
      map.doubleClickZoom.disable()
      map.touchZoomRotate.disable()
    }
  }, [params.interactive])

  // render house markers
  useEffect(() => {
    if (!mapRef.current) return
    // clear old markers
    markersRef.current.forEach(m => m.remove())
    // add new ones
    markersRef.current = markers.map(({ lngLat, number, highlight }) => {
      const el = document.createElement('div')
      el.className = 'house-marker'
      if (highlight) el.classList.add('highlight')
      el.innerText = number
      return new mapboxgl.Marker({ element: el })
        .setLngLat(lngLat)
        .addTo(mapRef.current)
    })
  }, [markers])

  return <div id="map-container" ref={mapContainerRef} />
}

export default Map