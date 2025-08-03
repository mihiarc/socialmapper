import { renderHook, act } from '@testing-library/react';
import { useMapData, useMapInteraction } from './useMapData';
import type { LatLngExpression } from 'leaflet';

describe('useMapData', () => {
  describe('initial state', () => {
    it('should have default initial values', () => {
      const { result } = renderHook(() => useMapData());

      expect(result.current.mapData).toEqual({
        center: [40.7128, -74.0060], // NYC
        zoom: 12,
        pois: [],
        isochrones: [],
        showIsochrones: true,
        showPOIs: true,
        baseLayer: 'streets',
      });

      expect(result.current.hasData).toBe(false);
      expect(result.current.visiblePOIs).toEqual([]);
      expect(result.current.visibleIsochrones).toEqual([]);
    });

    it('should accept custom default values', () => {
      const defaultCenter: LatLngExpression = [45.5152, -122.6784]; // Portland
      const defaultZoom = 14;

      const { result } = renderHook(() =>
        useMapData({ defaultCenter, defaultZoom })
      );

      expect(result.current.mapData.center).toEqual(defaultCenter);
      expect(result.current.mapData.zoom).toBe(defaultZoom);
    });
  });

  describe('setView', () => {
    it('should update center and zoom', () => {
      const { result } = renderHook(() => useMapData());
      const newCenter: LatLngExpression = [47.6062, -122.3321]; // Seattle
      const newZoom = 15;

      act(() => {
        result.current.setView(newCenter, newZoom);
      });

      expect(result.current.mapData.center).toEqual(newCenter);
      expect(result.current.mapData.zoom).toBe(newZoom);
    });

    it('should update only center when zoom not provided', () => {
      const { result } = renderHook(() => useMapData());
      const originalZoom = result.current.mapData.zoom;
      const newCenter: LatLngExpression = [37.7749, -122.4194]; // San Francisco

      act(() => {
        result.current.setView(newCenter);
      });

      expect(result.current.mapData.center).toEqual(newCenter);
      expect(result.current.mapData.zoom).toBe(originalZoom);
    });
  });

  describe('POI management', () => {
    it('should add POIs', () => {
      const { result } = renderHook(() => useMapData());
      const newPOIs = [
        {
          id: 'poi-1',
          name: 'Library 1',
          position: [45.5152, -122.6784] as LatLngExpression,
          type: 'library',
        },
        {
          id: 'poi-2',
          name: 'Library 2',
          position: [45.5162, -122.6794] as LatLngExpression,
          type: 'library',
        },
      ];

      act(() => {
        result.current.addPOIs(newPOIs);
      });

      expect(result.current.mapData.pois).toEqual(newPOIs);
      expect(result.current.hasData).toBe(true);
    });

    it('should replace all POIs', () => {
      const { result } = renderHook(() => useMapData());
      const initialPOIs = [
        {
          id: 'poi-1',
          name: 'Old POI',
          position: [45.5152, -122.6784] as LatLngExpression,
          type: 'library',
        },
      ];
      const newPOIs = [
        {
          id: 'poi-2',
          name: 'New POI',
          position: [45.5162, -122.6794] as LatLngExpression,
          type: 'school',
        },
      ];

      act(() => {
        result.current.setPOIs(initialPOIs);
      });

      expect(result.current.mapData.pois).toEqual(initialPOIs);

      act(() => {
        result.current.setPOIs(newPOIs);
      });

      expect(result.current.mapData.pois).toEqual(newPOIs);
    });

    it('should remove POI by ID', () => {
      const { result } = renderHook(() => useMapData());
      const pois = [
        {
          id: 'poi-1',
          name: 'POI 1',
          position: [45.5152, -122.6784] as LatLngExpression,
          type: 'library',
        },
        {
          id: 'poi-2',
          name: 'POI 2',
          position: [45.5162, -122.6794] as LatLngExpression,
          type: 'library',
        },
      ];

      act(() => {
        result.current.setPOIs(pois);
      });

      act(() => {
        result.current.removePOI('poi-1');
      });

      expect(result.current.mapData.pois).toHaveLength(1);
      expect(result.current.mapData.pois[0].id).toBe('poi-2');
    });

    it('should select and deselect POI', () => {
      const onPOISelect = jest.fn();
      const { result } = renderHook(() => useMapData({ onPOISelect }));

      act(() => {
        result.current.selectPOI('poi-1');
      });

      expect(result.current.mapData.selectedPOI).toBe('poi-1');
      expect(onPOISelect).toHaveBeenCalledWith('poi-1');

      act(() => {
        result.current.selectPOI(undefined);
      });

      expect(result.current.mapData.selectedPOI).toBeUndefined();
    });
  });

  describe('isochrone management', () => {
    it('should add isochrone', () => {
      const { result } = renderHook(() => useMapData());
      const isochrone = {
        id: 'iso-1',
        geojson: {
          type: 'FeatureCollection' as const,
          features: [],
        },
        travelTime: 15,
        travelMode: 'walk',
        color: '#10b981',
        opacity: 0.6,
      };

      act(() => {
        result.current.addIsochrone(isochrone);
      });

      expect(result.current.mapData.isochrones).toEqual([isochrone]);
      expect(result.current.hasData).toBe(true);
    });

    it('should replace all isochrones', () => {
      const { result } = renderHook(() => useMapData());
      const isochrones = [
        {
          id: 'iso-1',
          geojson: { type: 'FeatureCollection' as const, features: [] },
          travelTime: 15,
          travelMode: 'walk',
        },
        {
          id: 'iso-2',
          geojson: { type: 'FeatureCollection' as const, features: [] },
          travelTime: 30,
          travelMode: 'bike',
        },
      ];

      act(() => {
        result.current.setIsochrones(isochrones);
      });

      expect(result.current.mapData.isochrones).toEqual(isochrones);
    });

    it('should remove isochrone by ID', () => {
      const { result } = renderHook(() => useMapData());
      const isochrones = [
        {
          id: 'iso-1',
          geojson: { type: 'FeatureCollection' as const, features: [] },
          travelTime: 15,
          travelMode: 'walk',
        },
        {
          id: 'iso-2',
          geojson: { type: 'FeatureCollection' as const, features: [] },
          travelTime: 30,
          travelMode: 'bike',
        },
      ];

      act(() => {
        result.current.setIsochrones(isochrones);
      });

      act(() => {
        result.current.removeIsochrone('iso-1');
      });

      expect(result.current.mapData.isochrones).toHaveLength(1);
      expect(result.current.mapData.isochrones[0].id).toBe('iso-2');
    });
  });

  describe('visibility toggles', () => {
    it('should toggle isochrone visibility', () => {
      const { result } = renderHook(() => useMapData());
      const isochrone = {
        id: 'iso-1',
        geojson: { type: 'FeatureCollection' as const, features: [] },
        travelTime: 15,
        travelMode: 'walk',
      };

      act(() => {
        result.current.setIsochrones([isochrone]);
      });

      expect(result.current.visibleIsochrones).toHaveLength(1);

      act(() => {
        result.current.toggleIsochrones();
      });

      expect(result.current.mapData.showIsochrones).toBe(false);
      expect(result.current.visibleIsochrones).toHaveLength(0);

      act(() => {
        result.current.toggleIsochrones();
      });

      expect(result.current.mapData.showIsochrones).toBe(true);
      expect(result.current.visibleIsochrones).toHaveLength(1);
    });

    it('should toggle POI visibility', () => {
      const { result } = renderHook(() => useMapData());
      const poi = {
        id: 'poi-1',
        name: 'Test POI',
        position: [45.5152, -122.6784] as LatLngExpression,
        type: 'library',
      };

      act(() => {
        result.current.setPOIs([poi]);
      });

      expect(result.current.visiblePOIs).toHaveLength(1);

      act(() => {
        result.current.togglePOIs();
      });

      expect(result.current.mapData.showPOIs).toBe(false);
      expect(result.current.visiblePOIs).toHaveLength(0);
    });
  });

  describe('base layer', () => {
    it('should change base layer', () => {
      const { result } = renderHook(() => useMapData());

      act(() => {
        result.current.setBaseLayer('satellite');
      });

      expect(result.current.mapData.baseLayer).toBe('satellite');

      act(() => {
        result.current.setBaseLayer('terrain');
      });

      expect(result.current.mapData.baseLayer).toBe('terrain');
    });
  });

  describe('clearMap', () => {
    it('should clear all map data', () => {
      const { result } = renderHook(() => useMapData());

      // Add some data
      act(() => {
        result.current.setPOIs([
          {
            id: 'poi-1',
            name: 'Test POI',
            position: [45.5152, -122.6784] as LatLngExpression,
            type: 'library',
          },
        ]);
        result.current.setIsochrones([
          {
            id: 'iso-1',
            geojson: { type: 'FeatureCollection' as const, features: [] },
            travelTime: 15,
            travelMode: 'walk',
          },
        ]);
        result.current.selectPOI('poi-1');
      });

      expect(result.current.hasData).toBe(true);

      act(() => {
        result.current.clearMap();
      });

      expect(result.current.mapData.pois).toEqual([]);
      expect(result.current.mapData.isochrones).toEqual([]);
      expect(result.current.mapData.selectedPOI).toBeUndefined();
      expect(result.current.hasData).toBe(false);
    });
  });

  describe('loadAnalysisResult', () => {
    it('should load analysis result with POIs and isochrones', () => {
      const { result } = renderHook(() => useMapData());
      const analysisResult = {
        pois: [
          { id: 'poi-1', name: 'Library 1', lat: 45.5152, lon: -122.6784, type: 'library' },
          { id: 'poi-2', name: 'Library 2', latitude: 45.5162, longitude: -122.6794, type: 'library' },
        ],
        isochrones: {
          type: 'FeatureCollection',
          features: [{ type: 'Feature', geometry: null, properties: {} }],
        },
        request: {
          travel_mode: 'walk',
          travel_time_minutes: 15,
        },
      };

      act(() => {
        result.current.loadAnalysisResult(analysisResult);
      });

      expect(result.current.mapData.pois).toHaveLength(2);
      expect(result.current.mapData.isochrones).toHaveLength(1);
      expect(result.current.mapData.isochrones[0].travelMode).toBe('walk');
      expect(result.current.mapData.isochrones[0].color).toBe('#10b981');
    });

    it('should handle multiple isochrones by travel mode', () => {
      const { result } = renderHook(() => useMapData());
      const analysisResult = {
        isochrones: {
          walk: {
            type: 'FeatureCollection',
            features: [],
          },
          bike: {
            type: 'FeatureCollection',
            features: [],
          },
        },
        request: {
          travel_time_minutes: 20,
        },
      };

      act(() => {
        result.current.loadAnalysisResult(analysisResult);
      });

      expect(result.current.mapData.isochrones).toHaveLength(2);
      expect(result.current.mapData.isochrones[0].travelMode).toBe('walk');
      expect(result.current.mapData.isochrones[1].travelMode).toBe('bike');
    });
  });
});

describe('useMapInteraction', () => {
  describe('drawing', () => {
    it('should manage drawing state', () => {
      const { result } = renderHook(() => useMapInteraction());

      expect(result.current.isDrawing).toBe(false);
      expect(result.current.drawnPoints).toEqual([]);

      act(() => {
        result.current.startDrawing();
      });

      expect(result.current.isDrawing).toBe(true);

      const point: LatLngExpression = [45.5152, -122.6784];
      act(() => {
        result.current.addPoint(point);
      });

      expect(result.current.drawnPoints).toEqual([point]);

      act(() => {
        result.current.stopDrawing();
      });

      expect(result.current.isDrawing).toBe(false);
    });

    it('should clear drawn points', () => {
      const { result } = renderHook(() => useMapInteraction());
      const points: LatLngExpression[] = [
        [45.5152, -122.6784],
        [45.5162, -122.6794],
      ];

      act(() => {
        result.current.startDrawing();
        points.forEach(point => result.current.addPoint(point));
      });

      expect(result.current.drawnPoints).toEqual(points);

      act(() => {
        result.current.clearDrawing();
      });

      expect(result.current.drawnPoints).toEqual([]);
    });
  });

  describe('measurement', () => {
    it('should manage measurement mode', () => {
      const { result } = renderHook(() => useMapInteraction());

      expect(result.current.measurementMode).toBeNull();

      act(() => {
        result.current.startMeasurement('distance');
      });

      expect(result.current.measurementMode).toBe('distance');
      expect(result.current.drawnPoints).toEqual([]);

      act(() => {
        result.current.startMeasurement('area');
      });

      expect(result.current.measurementMode).toBe('area');

      act(() => {
        result.current.stopMeasurement();
      });

      expect(result.current.measurementMode).toBeNull();
      expect(result.current.drawnPoints).toEqual([]);
    });
  });
});