import { useRef, useEffect } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

function Map({ params, markers = [], onMapLoad }) {
  const mapRef = useRef()
  const mapContainerRef = useRef()
  const spinRef = useRef()
  const markersRef = useRef([])

  useEffect(() => {
    mapboxgl.accessToken = 'pk.eyJ1IjoiZ2luZ2VybG9yZCIsImEiOiJjbWFzMTRremowYjNpMmxzaG05bG1pajA1In0.stYxpVfJdphbhzGq1c0Xlw'
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: params.center,
      zoom: params.zoom,
      bearing: params.bearing,
      pitch: params.pitch,
      interactive: params.interactive !== false,
      attributionControl: false,
      maxPitch: 85,
      maxZoom: 20,
    })
    if (onMapLoad) onMapLoad(mapRef.current)
    return () => {
      mapRef.current.remove()
      if (spinRef.current) cancelAnimationFrame(spinRef.current)
    }
  }, [])

  // Smooth spinning using Mapbox's rotateTo
  useEffect(() => {
    if (!mapRef.current) return
    if (params.spin) {
      let lastTime = performance.now()
      function animate(now) {
        const map = mapRef.current
        const bearing = map.getBearing()
        const delta = ((now - lastTime) / 1000) * 4 // slower spin
        map.rotateTo((bearing + delta) % 360, { duration: 0 })
        lastTime = now
        spinRef.current = requestAnimationFrame(animate)
      }
      spinRef.current = requestAnimationFrame(animate)
      return () => cancelAnimationFrame(spinRef.current)
    }
  }, [params.spin])

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