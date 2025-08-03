/**
 * React hook for managing map data and visualization state
 */

import { useState, useCallback, useMemo } from 'react';
import type { LatLngExpression, LatLngBoundsExpression } from 'leaflet';

export interface POIMarker {
  id: string;
  name: string;
  position: LatLngExpression;
  type: string;
  category?: string;
}

export interface IsochroneLayer {
  id: string;
  geojson: GeoJSON.FeatureCollection;
  travelTime: number;
  travelMode: string;
  color?: string;
  opacity?: number;
}

export interface MapData {
  center: LatLngExpression;
  zoom: number;
  bounds?: LatLngBoundsExpression;
  pois: POIMarker[];
  isochrones: IsochroneLayer[];
  selectedPOI?: string;
  showIsochrones: boolean;
  showPOIs: boolean;
  baseLayer: 'streets' | 'satellite' | 'terrain';
}

export interface UseMapDataOptions {
  defaultCenter?: LatLngExpression;
  defaultZoom?: number;
  onPOISelect?: (poiId: string) => void;
}

/**
 * Hook for managing map visualization state
 */
export function useMapData(options: UseMapDataOptions = {}) {
  const [mapData, setMapData] = useState<MapData>({
    center: options.defaultCenter || [40.7128, -74.0060], // Default to NYC
    zoom: options.defaultZoom || 12,
    pois: [],
    isochrones: [],
    showIsochrones: true,
    showPOIs: true,
    baseLayer: 'streets',
  });

  // Update map center and zoom
  const setView = useCallback((center: LatLngExpression, zoom?: number) => {
    setMapData(prev => ({
      ...prev,
      center,
      zoom: zoom ?? prev.zoom,
    }));
  }, []);

  // Fit map to bounds
  const fitBounds = useCallback((bounds: LatLngBoundsExpression) => {
    setMapData(prev => ({
      ...prev,
      bounds,
    }));
  }, []);

  // Add POI markers
  const addPOIs = useCallback((pois: POIMarker[]) => {
    setMapData(prev => ({
      ...prev,
      pois: [...prev.pois, ...pois],
    }));
  }, []);

  // Replace all POIs
  const setPOIs = useCallback((pois: POIMarker[]) => {
    setMapData(prev => ({
      ...prev,
      pois,
    }));
  }, []);

  // Remove POI by ID
  const removePOI = useCallback((poiId: string) => {
    setMapData(prev => ({
      ...prev,
      pois: prev.pois.filter(poi => poi.id !== poiId),
      selectedPOI: prev.selectedPOI === poiId ? undefined : prev.selectedPOI,
    }));
  }, []);

  // Select POI
  const selectPOI = useCallback((poiId: string | undefined) => {
    setMapData(prev => ({
      ...prev,
      selectedPOI: poiId,
    }));
    if (poiId && options.onPOISelect) {
      options.onPOISelect(poiId);
    }
  }, [options]);

  // Add isochrone layer
  const addIsochrone = useCallback((isochrone: IsochroneLayer) => {
    setMapData(prev => ({
      ...prev,
      isochrones: [...prev.isochrones, isochrone],
    }));
  }, []);

  // Replace all isochrones
  const setIsochrones = useCallback((isochrones: IsochroneLayer[]) => {
    setMapData(prev => ({
      ...prev,
      isochrones,
    }));
  }, []);

  // Remove isochrone by ID
  const removeIsochrone = useCallback((isochroneId: string) => {
    setMapData(prev => ({
      ...prev,
      isochrones: prev.isochrones.filter(iso => iso.id !== isochroneId),
    }));
  }, []);

  // Clear all map data
  const clearMap = useCallback(() => {
    setMapData(prev => ({
      ...prev,
      pois: [],
      isochrones: [],
      selectedPOI: undefined,
    }));
  }, []);

  // Toggle layer visibility
  const toggleIsochrones = useCallback(() => {
    setMapData(prev => ({
      ...prev,
      showIsochrones: !prev.showIsochrones,
    }));
  }, []);

  const togglePOIs = useCallback(() => {
    setMapData(prev => ({
      ...prev,
      showPOIs: !prev.showPOIs,
    }));
  }, []);

  // Change base layer
  const setBaseLayer = useCallback((layer: 'streets' | 'satellite' | 'terrain') => {
    setMapData(prev => ({
      ...prev,
      baseLayer: layer,
    }));
  }, []);

  // Load data from analysis result
  const loadAnalysisResult = useCallback((result: any) => {
    if (!result) return;

    const newPOIs: POIMarker[] = [];
    const newIsochrones: IsochroneLayer[] = [];

    // Extract POIs from result (if available)
    if (result.pois && Array.isArray(result.pois)) {
      result.pois.forEach((poi: any, index: number) => {
        newPOIs.push({
          id: poi.id || `poi-${index}`,
          name: poi.name || `POI ${index + 1}`,
          position: [poi.lat || poi.latitude, poi.lon || poi.longitude] as LatLngExpression,
          type: poi.type || 'unknown',
          category: poi.category,
        });
      });
    }

    // Extract isochrones from result
    if (result.isochrones) {
      const travelModeColors = {
        walk: '#10b981',
        bike: '#3b82f6',
        drive: '#f59e0b',
        transit: '#8b5cf6',
      };

      if (result.isochrones.features) {
        // Single isochrone
        newIsochrones.push({
          id: 'isochrone-0',
          geojson: result.isochrones,
          travelTime: result.request?.travel_time_minutes || 15,
          travelMode: result.request?.travel_mode || 'walk',
          color: travelModeColors[result.request?.travel_mode as keyof typeof travelModeColors] || '#6b7280',
          opacity: 0.6,
        });
      } else if (typeof result.isochrones === 'object') {
        // Multiple isochrones by travel mode
        Object.entries(result.isochrones).forEach(([mode, geojson], index) => {
          if (geojson && typeof geojson === 'object' && 'features' in geojson) {
            newIsochrones.push({
              id: `isochrone-${mode}-${index}`,
              geojson: geojson as GeoJSON.FeatureCollection,
              travelTime: result.request?.travel_time_minutes || 15,
              travelMode: mode,
              color: travelModeColors[mode as keyof typeof travelModeColors] || '#6b7280',
              opacity: 0.6,
            });
          }
        });
      }
    }

    // Update map data
    setMapData(prev => ({
      ...prev,
      pois: newPOIs,
      isochrones: newIsochrones,
    }));

    // Fit map to show all data
    if (newPOIs.length > 0 || newIsochrones.length > 0) {
      // Calculate bounds from POIs and isochrones
      // This is a simplified version - in production you'd calculate proper bounds
      const firstPOI = newPOIs[0];
      if (firstPOI) {
        setView(firstPOI.position, 13);
      }
    }
  }, [setView]);

  // Computed values
  const hasData = useMemo(() => 
    mapData.pois.length > 0 || mapData.isochrones.length > 0,
    [mapData.pois.length, mapData.isochrones.length]
  );

  const visiblePOIs = useMemo(() => 
    mapData.showPOIs ? mapData.pois : [],
    [mapData.showPOIs, mapData.pois]
  );

  const visibleIsochrones = useMemo(() => 
    mapData.showIsochrones ? mapData.isochrones : [],
    [mapData.showIsochrones, mapData.isochrones]
  );

  return {
    // State
    mapData,
    hasData,
    visiblePOIs,
    visibleIsochrones,
    
    // Actions
    setView,
    fitBounds,
    addPOIs,
    setPOIs,
    removePOI,
    selectPOI,
    addIsochrone,
    setIsochrones,
    removeIsochrone,
    clearMap,
    toggleIsochrones,
    togglePOIs,
    setBaseLayer,
    loadAnalysisResult,
    
    // Direct state updates (for advanced use)
    setMapData,
  };
}

/**
 * Hook for managing map interactions
 */
export function useMapInteraction() {
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawnPoints, setDrawnPoints] = useState<LatLngExpression[]>([]);
  const [measurementMode, setMeasurementMode] = useState<'distance' | 'area' | null>(null);

  const startDrawing = useCallback(() => {
    setIsDrawing(true);
    setDrawnPoints([]);
  }, []);

  const stopDrawing = useCallback(() => {
    setIsDrawing(false);
  }, []);

  const addPoint = useCallback((point: LatLngExpression) => {
    if (isDrawing) {
      setDrawnPoints(prev => [...prev, point]);
    }
  }, [isDrawing]);

  const clearDrawing = useCallback(() => {
    setDrawnPoints([]);
  }, []);

  const startMeasurement = useCallback((mode: 'distance' | 'area') => {
    setMeasurementMode(mode);
    setDrawnPoints([]);
  }, []);

  const stopMeasurement = useCallback(() => {
    setMeasurementMode(null);
    setDrawnPoints([]);
  }, []);

  return {
    // State
    isDrawing,
    drawnPoints,
    measurementMode,
    
    // Actions
    startDrawing,
    stopDrawing,
    addPoint,
    clearDrawing,
    startMeasurement,
    stopMeasurement,
  };
}