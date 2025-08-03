export const config = {
  apiBaseUrl: 'http://localhost:8000',
  apiTimeout: 300000,
  pollInterval: 2000,
  maxFileSizeMB: 10,
  allowedFileTypes: ['.csv', '.xlsx', '.xls', '.json', '.geojson'],
  defaultMapCenter: [45.5152, -122.6784] as [number, number],
  defaultMapZoom: 12,
  mapTileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  mapAttribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  enableBatchAnalysis: true,
  enableExperimentalFeatures: false,
  analyticsEnabled: false,
  analyticsId: undefined,
};

export function validateConfig(): void {
  // Mock validation - always passes in tests
}