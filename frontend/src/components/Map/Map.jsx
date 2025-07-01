import { useRef, useEffect, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import useSpin from './spin'
import { reverseGeocode } from '../../api/mapbox.js'
import { useTheme } from '../../contexts/ThemeContext.jsx' // Make sure this path is correct

function Map({ params, markers = [], onMapLoad }) {
  const mapRef = useRef()
  const mapContainerRef = useRef()
  const markersRef = useRef([])
  const hoverRef = useRef({ hoveredId: null })
  const transitionTimerRef = useRef(null)

  
  const [spinSpeed, setSpinSpeed] = useState(8)
  const { isDark, setIsTransitioning } = useTheme()

  useEffect(() => {
    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/standard',
      center: params.center,
      zoom: params.zoom,
      pitch: params.pitch,
      bearing: params.bearing,
      interactive: params.interactive !== false,
      attributionControl: false,
      maxPitch: 85,
      maxZoom: 20,
    })

    mapRef.current.on('style.load', () => {
      const map = mapRef.current

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
              ['boolean', ['feature-state', 'select'], false], '#00ff00',
              ['boolean', ['feature-state', 'hover'], false], '#ff0000',
              '#aaa'
            ],
            'fill-extrusion-height': ['get', 'height'],
            'fill-extrusion-base': ['get', 'min_height'],
            'fill-extrusion-opacity': 1
          }
        }, 'road-label')
      }

      if (!map.getLayer('house-numbers')) {
        map.addLayer({
          id: 'house-numbers',
          type: 'symbol',
          source: 'composite',
          'source-layer': 'housenum_label',
          minzoom: 16,
          layout: {
            'text-field': ['get', 'house_num'],
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

      if (params.interactive) {
        map.on('click', '3d-buildings', async e => {
          if (!e.features.length) return
          const { lng, lat } = e.lngLat
          
          const features = await reverseGeocode(lng, lat)
          const address = features[0]?.place_name || 'Address not found'
          
          console.log('address', address)
        })
      }
    })

    if (onMapLoad) onMapLoad(mapRef.current)
    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
      }
    }
  }, [])
    useEffect(() => {
    const map = mapRef.current
    if (!map) return

    const updateLightPreset = () => {
      setIsTransitioning(true)
      const lightPreset = isDark ? 'dusk' : 'light'
      map.setConfigProperty('basemap', 'lightPreset', lightPreset)
      
      map.once('styledata', () => {
        if (transitionTimerRef.current) {
          clearTimeout(transitionTimerRef.current)
        }
        transitionTimerRef.current = setTimeout(() => {
          setIsTransitioning(false)
        }, 500)
      })
    }

    if (map.isStyleLoaded()) {
      updateLightPreset()
    } else {
      map.once('style.load', updateLightPreset)
    }

    return () => {
      if (transitionTimerRef.current) {
        clearTimeout(transitionTimerRef.current)
      }
    }
  }, [isDark, setIsTransitioning])

  useSpin(mapRef, params, spinSpeed, setSpinSpeed)

  useEffect(() => {
    if (!mapRef.current) return
    if (params.flyToOnMount) {
      mapRef.current.flyTo({
        center: params.center,
        zoom: params.zoom,
        bearing: params.bearing,
        pitch: params.pitch,
        speed: 1.2,
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

  useEffect(() => {
    if (!mapRef.current) return
    markersRef.current.forEach(m => m.remove())
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

  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return

    const onMouseMove = e => {
      if (!params.interactive || !e.features.length) return
      if (hoverRef.current.hoveredId !== null) {
        map.setFeatureState(
          { source: 'composite', sourceLayer: 'building', id: hoverRef.current.hoveredId },
          { hover: false }
        )
      }
      hoverRef.current.hoveredId = e.features[0].id
      map.setFeatureState(
        { source: 'composite', sourceLayer: 'building', id: hoverRef.current.hoveredId },
        { hover: true }
      )
      map.getCanvas().style.cursor = 'pointer'
    }

    const onMouseLeave = () => {
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
      if (map.isStyleLoaded()) {
        map.off('mousemove','3d-buildings', onMouseMove)
        map.off('mouseleave','3d-buildings', onMouseLeave)
        if(map.getCanvas()) {
            map.getCanvas().style.cursor = ''
        }
      }
    }
  }, [params.interactive])

  return <div id="map-container" ref={mapContainerRef} />
}

export default Map