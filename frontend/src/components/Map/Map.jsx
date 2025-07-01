import { useRef, useEffect, useState }from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import useSpin from './spin';
import { reverseGeocode } from '../../api/mapbox.js';
import { useTheme } from '../../contexts/ThemeContext.jsx';

function Map({ params, onMapLoad, onMapClick, pin }) {
  const mapRef = useRef();
  const mapContainerRef = useRef();
  const pinRef = useRef();
  const [spinSpeed, setSpinSpeed] = useState(8);
  const { isDark, setIsTransitioning } = useTheme();

  useEffect(() => {
    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
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
    });

    const map = mapRef.current;

    map.on('style.load', () => {
      if (params.interactive) {
        map.on('click', async e => {
          if (onMapClick) {
            onMapClick(e.lngLat);
          }
        });
      }
    });

    if (onMapLoad) onMapLoad(map);
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
      }
    };
  }, [onMapClick, onMapLoad, params.interactive]);

  useEffect(() => {
    if (pin && mapRef.current) {
      if (pinRef.current) {
        pinRef.current.remove();
      }
      pinRef.current = new mapboxgl.Marker()
        .setLngLat(pin)
        .addTo(mapRef.current);
    }
  }, [pin]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const updateLightPreset = () => {
      setIsTransitioning(true);
      const lightPreset = isDark ? 'dusk' : 'light';
      map.setConfigProperty('basemap', 'lightPreset', lightPreset);

      map.once('styledata', () => {
        setTimeout(() => {
          setIsTransitioning(false);
        }, 1000);
      });
    };

    if (map.isStyleLoaded()) {
      updateLightPreset();
    } else {
      map.once('style.load', updateLightPreset);
    }
  }, [isDark, setIsTransitioning]);

  useSpin(mapRef, params, spinSpeed, setSpinSpeed);

  useEffect(() => {
    if (!mapRef.current) return;
    if (params.flyToOnMount) {
      mapRef.current.flyTo({
        center: params.center,
        zoom: params.zoom,
        bearing: params.bearing,
        pitch: params.pitch,
        speed: 1.2,
        curve: 1.8,
        essential: true,
      });
    } else {
      mapRef.current.setCenter(params.center);
      mapRef.current.setZoom(params.zoom);
      mapRef.current.setPitch(params.pitch);
      if (!params.spin) {
        mapRef.current.setBearing(params.bearing);
      }
    }
  }, [params.center, params.zoom, params.pitch, params.bearing, params.spin, params.flyToOnMount]);

  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;
    if (params.interactive) {
      map.scrollZoom.enable();
      map.boxZoom.enable();
      map.dragRotate.enable();
      map.dragPan.enable();
      map.keyboard.enable();
      map.doubleClickZoom.enable();
      map.touchZoomRotate.enable();
    } else {
      map.scrollZoom.disable();
      map.boxZoom.disable();
      map.dragRotate.disable();
      map.dragPan.disable();
      map.keyboard.disable();
      map.doubleClickZoom.disable();
      map.touchZoomRotate.disable();
    }
  }, [params.interactive]);

  return <div id="map-container" ref={mapContainerRef} />;
}

export default Map;