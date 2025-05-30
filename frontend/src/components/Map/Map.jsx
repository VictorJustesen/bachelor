import { useRef, useEffect, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import useSpin from './spin'

function Map({ params, markers = [], onMapLoad }) {
  const mapRef = useRef()
  const mapContainerRef = useRef()
  const markersRef = useRef([])
  const hoverRef = useRef({ hoveredId: null })
  
  // Use React state for values we want to trigger re-renders
  const [spinSpeed, setSpinSpeed] = useState(8) // Default spin speed in degrees per second

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
    }
  }, [])

  // NEW: wire up spin hook
  useSpin(mapRef, params, spinSpeed, setSpinSpeed)

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

  // bind/unbind hover on free mode only
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return

    function onMouseMove(e) {
      if (!params.interactive || !e.features.length) return
      // clear old
      if (hoverRef.current.hoveredId !== null) {
        map.setFeatureState(
          { source: 'composite', sourceLayer: 'building', id: hoverRef.current.hoveredId },
          { hover: false }
        )
      }
      // set new
      hoverRef.current.hoveredId = e.features[0].id
      map.setFeatureState(
        { source: 'composite', sourceLayer: 'building', id: hoverRef.current.hoveredId },
        { hover: true }
      )
      map.getCanvas().style.cursor = 'pointer'
    }

    function onMouseLeave() {
      if (!params.interactive) return
      if (hoverRef.current.hoveredId !== null) {
        map.setFeatureState(
          { source: 'composite', sourceLayer: 'building', id: hoverRef.current.hoveredId },
          { hover: false }
        )
        hoverRef.current.hoveredId = null
      }
      map.getCanvas().style.cursor = ''
    }

    map.on('mousemove', '3d-buildings', onMouseMove)
    map.on('mouseleave','3d-buildings', onMouseLeave)

    return () => {
      map.off('mousemove','3d-buildings', onMouseMove)
      map.off('mouseleave','3d-buildings', onMouseLeave)
      // ensure cursor reset if switching out of interactive
      map.getCanvas().style.cursor = ''
    }
  }, [params.interactive])

  return <div id="map-container" ref={mapContainerRef} />
}

export default Map