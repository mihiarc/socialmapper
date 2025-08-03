import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useAPI } from '@/contexts'
import { useMapData } from '@/hooks'
import { Button, Input, Card, CardHeader, CardTitle, CardContent, Spinner } from '@/components'
import { TravelMode, AnalysisRequest, ExportFormat } from '@/types'

interface TravelModeResult {
  mode: TravelMode;
  result: any;
  color: string;
}

export function TravelModesPage() {
  const api = useAPI()
  const { setIsochrones, clearMap, loadAnalysisResult } = useMapData()
  const [location, setLocation] = useState('Portland, OR')
  const [travelTime, setTravelTime] = useState(15)
  const [selectedModes, setSelectedModes] = useState<TravelMode[]>([
    TravelMode.Walk,
    TravelMode.Bike
  ])
  const [results, setResults] = useState<TravelModeResult[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const travelModeConfig = [
    { mode: TravelMode.Walk, label: 'Walking', color: '#10b981', icon: '🚶' },
    { mode: TravelMode.Bike, label: 'Biking', color: '#3b82f6', icon: '🚴' },
    { mode: TravelMode.Drive, label: 'Driving', color: '#f59e0b', icon: '🚗' },
    { mode: TravelMode.Transit, label: 'Transit', color: '#8b5cf6', icon: '🚌' }
  ]

  const handleAnalysis = async () => {
    if (selectedModes.length === 0) {
      alert('Please select at least one travel mode')
      return
    }

    setIsAnalyzing(true)
    setResults([])
    clearMap()

    try {
      const analysisPromises = selectedModes.map(async (mode) => {
        const response = await api.createLocationAnalysis({
          location,
          travel_mode: mode,
          travel_time_minutes: travelTime,
          census_variables: ['B01003_001E'], // Total population
          poi_types: ['amenity:library', 'amenity:school', 'amenity:hospital']
        })

        const result = await api.pollJobStatus(response.job_id, (status) => {
          console.log(`${mode} analysis progress:`, status.progress)
        })

        return {
          mode,
          result,
          color: travelModeConfig.find(c => c.mode === mode)?.color || '#6b7280'
        }
      })

      const allResults = await Promise.all(analysisPromises)
      setResults(allResults)

      // Load all isochrones on the map
      const isochrones = allResults.map((r, index) => ({
        id: `${r.mode}-${index}`,
        geojson: r.result.isochrones,
        travelTime,
        travelMode: r.mode,
        color: r.color,
        opacity: 0.4
      }))
      setIsochrones(isochrones)

    } catch (error) {
      console.error('Analysis failed:', error)
      alert(`Analysis failed: ${error.message}`)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const toggleMode = (mode: TravelMode) => {
    setSelectedModes(prev => {
      if (prev.includes(mode)) {
        return prev.filter(m => m !== mode)
      }
      return [...prev, mode]
    })
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-3xl font-bold text-gray-900">Travel Modes Comparison</h1>
      <p className="mt-2 text-lg text-gray-600">
        Compare accessibility across different modes of transportation
      </p>

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Configuration */}
        <Card variant="bordered">
          <CardHeader>
            <CardTitle>Analysis Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Input
                label="Location"
                placeholder="e.g., Portland, OR"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                required
              />

              <Input
                type="number"
                label="Travel Time (minutes)"
                value={travelTime}
                onChange={(e) => setTravelTime(parseInt(e.target.value))}
                min={5}
                max={60}
                required
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Travel Modes to Compare
                </label>
                <div className="space-y-2">
                  {travelModeConfig.map(({ mode, label, icon, color }) => (
                    <label
                      key={mode}
                      className="flex items-center p-3 border rounded-md cursor-pointer hover:bg-gray-50"
                      style={{
                        borderColor: selectedModes.includes(mode) ? color : '#e5e7eb',
                        backgroundColor: selectedModes.includes(mode) ? `${color}10` : 'transparent'
                      }}
                    >
                      <input
                        type="checkbox"
                        className="mr-3"
                        checked={selectedModes.includes(mode)}
                        onChange={() => toggleMode(mode)}
                      />
                      <span className="text-2xl mr-2">{icon}</span>
                      <span className="font-medium">{label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <Button
                onClick={handleAnalysis}
                disabled={isAnalyzing || !location || selectedModes.length === 0}
                className="w-full"
              >
                {isAnalyzing ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Analyzing {selectedModes.length} modes...
                  </>
                ) : (
                  'Compare Travel Modes'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results Comparison */}
        <Card variant="bordered" className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Comparison Results</CardTitle>
          </CardHeader>
          <CardContent>
            {results.length === 0 && !isAnalyzing && (
              <p className="text-gray-500">
                Select travel modes and run analysis to see comparison
              </p>
            )}

            {isAnalyzing && (
              <div className="flex items-center justify-center py-8">
                <Spinner size="lg" />
              </div>
            )}

            {results.length > 0 && (
              <div className="space-y-6">
                {/* Summary Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {results.map(({ mode, result, color }) => {
                    const config = travelModeConfig.find(c => c.mode === mode)
                    return (
                      <div
                        key={mode}
                        className="border rounded-lg p-4"
                        style={{ borderColor: color }}
                      >
                        <div className="flex items-center mb-2">
                          <span className="text-2xl mr-2">{config?.icon}</span>
                          <h4 className="font-semibold text-lg">{config?.label}</h4>
                        </div>
                        
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">POIs Accessible:</span>
                            <span className="font-bold" style={{ color }}>
                              {result.poi_count || 0}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Area Coverage:</span>
                            <span className="font-medium">
                              {result.analysis_area_km2?.toFixed(1) || 0} km²
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Population:</span>
                            <span className="font-medium">
                              {result.population_covered?.toLocaleString() || 0}
                            </span>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Comparison Chart */}
                <div className="border rounded-lg p-4">
                  <h5 className="font-semibold mb-3">Accessibility Comparison</h5>
                  <div className="space-y-3">
                    {results.map(({ mode, result, color }) => {
                      const config = travelModeConfig.find(c => c.mode === mode)
                      const maxPOIs = Math.max(...results.map(r => r.result.poi_count || 0))
                      const percentage = maxPOIs > 0 
                        ? ((result.poi_count || 0) / maxPOIs) * 100 
                        : 0

                      return (
                        <div key={mode}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium">
                              {config?.icon} {config?.label}
                            </span>
                            <span className="text-sm text-gray-600">
                              {result.poi_count || 0} POIs
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-4">
                            <div
                              className="h-4 rounded-full transition-all duration-500"
                              style={{
                                width: `${percentage}%`,
                                backgroundColor: color
                              }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Export Options */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      // Export combined results
                      const combinedData = {
                        location,
                        travel_time: travelTime,
                        results: results.map(r => ({
                          mode: r.mode,
                          poi_count: r.result.poi_count,
                          area_km2: r.result.analysis_area_km2,
                          population: r.result.population_covered
                        }))
                      }
                      const blob = new Blob([JSON.stringify(combinedData, null, 2)], 
                        { type: 'application/json' })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url
                      a.download = `travel_modes_comparison_${Date.now()}.json`
                      a.click()
                      URL.revokeObjectURL(url)
                    }}
                  >
                    Export Comparison (JSON)
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}