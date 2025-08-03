import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useAPI } from '@/contexts'
import { Button, Input, Select, Card, CardHeader, CardTitle, CardContent, Spinner } from '@/components'
import { TravelMode, AnalysisRequest, ExportFormat } from '@/types'

export function GettingStartedPage() {
  const api = useAPI()
  const [location, setLocation] = useState('')
  const [travelMode, setTravelMode] = useState<TravelMode>(TravelMode.Walk)
  const [travelTime, setTravelTime] = useState(15)
  const [selectedPOITypes, setSelectedPOITypes] = useState<string[]>(['amenity:library'])
  const [selectedCensusVars, setSelectedCensusVars] = useState<string[]>(['B01003_001E'])

  // Fetch available POI types
  const { data: poiTypesData } = useQuery({
    queryKey: ['poiTypes'],
    queryFn: () => api.getPOITypes({ limit: 50 })
  })

  // Fetch available census variables
  const { data: censusVarsData } = useQuery({
    queryKey: ['censusVariables'],
    queryFn: () => api.getCensusVariables({ limit: 20 })
  })

  // Create analysis mutation
  const analysisMutation = useMutation({
    mutationFn: async (request: AnalysisRequest) => {
      const response = await api.createLocationAnalysis(request)
      return api.pollJobStatus(response.job_id, (status) => {
        console.log('Analysis progress:', status.progress)
      })
    }
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    analysisMutation.mutate({
      location,
      travel_mode: travelMode,
      travel_time_minutes: travelTime,
      poi_types: selectedPOITypes,
      census_variables: selectedCensusVars
    })
  }

  const travelModeOptions = [
    { value: TravelMode.Walk, label: 'Walking' },
    { value: TravelMode.Bike, label: 'Biking' },
    { value: TravelMode.Drive, label: 'Driving' },
    { value: TravelMode.Transit, label: 'Transit' }
  ]

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="text-center">
        <h1 className="text-4xl font-display font-bold gradient-text mb-4">Getting Started</h1>
        <p className="text-xl text-gray-600 dark:text-gray-400">
          Analyze community accessibility by entering a location and selecting your parameters
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Analysis Form */}
        <Card variant="gradient" className="animate-scale-in">
          <CardHeader>
            <CardTitle size="xl" className="gradient-text">Location Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Location"
                placeholder="e.g., Portland, OR"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                required
              />

              <Select
                label="Travel Mode"
                value={travelMode}
                onChange={(e) => setTravelMode(e.target.value as TravelMode)}
                options={travelModeOptions}
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
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Points of Interest
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto glass rounded-xl p-4">
                  {poiTypesData?.poi_types.map((poi) => (
                    <label key={`${poi.type}:${poi.name}`} className="flex items-center">
                      <input
                        type="checkbox"
                        className="mr-2"
                        value={`${poi.type}:${poi.name}`}
                        checked={selectedPOITypes.includes(`${poi.type}:${poi.name}`)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedPOITypes([...selectedPOITypes, e.target.value])
                          } else {
                            setSelectedPOITypes(selectedPOITypes.filter(t => t !== e.target.value))
                          }
                        }}
                      />
                      <span className="text-sm">{poi.name} ({poi.category})</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Census Variables
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto glass rounded-xl p-4">
                  {censusVarsData?.variables.map((variable) => (
                    <label key={variable.code} className="flex items-center">
                      <input
                        type="checkbox"
                        className="mr-2"
                        value={variable.code}
                        checked={selectedCensusVars.includes(variable.code)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedCensusVars([...selectedCensusVars, e.target.value])
                          } else {
                            setSelectedCensusVars(selectedCensusVars.filter(v => v !== e.target.value))
                          }
                        }}
                      />
                      <span className="text-sm">{variable.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                disabled={analysisMutation.isPending || !location}
                fullWidth
              >
                {analysisMutation.isPending ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Analyzing...
                  </>
                ) : (
                  'Run Analysis'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Results Display */}
        <Card variant="gradient" className="animate-scale-in" style={{ animationDelay: '100ms' }}>
          <CardHeader>
            <CardTitle size="xl" className="gradient-text">Analysis Results</CardTitle>
          </CardHeader>
          <CardContent>
            {analysisMutation.isIdle && (
              <div className="text-center py-12">
                <p className="text-gray-500 dark:text-gray-400">
                  Submit an analysis to see results here
                </p>
              </div>
            )}
            
            {analysisMutation.isPending && (
              <div className="flex flex-col items-center justify-center py-12 space-y-4">
                <Spinner size="lg" />
                <p className="text-gray-600 dark:text-gray-400 animate-pulse">Analyzing location data...</p>
              </div>
            )}

            {analysisMutation.isError && (
              <div className="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800">
                <p className="text-red-600 dark:text-red-400 font-medium">
                  Error: {analysisMutation.error?.message}
                </p>
              </div>
            )}

            {analysisMutation.isSuccess && analysisMutation.data && (
              <div className="space-y-6">
                <div className="glass rounded-xl p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">POIs Found</h4>
                  <p className="text-3xl font-bold gradient-text">
                    {analysisMutation.data.poi_count || 0}
                  </p>
                </div>

                <div className="glass rounded-xl p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Analysis Area</h4>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {analysisMutation.data.analysis_area_km2?.toFixed(2) || 0} km²
                  </p>
                </div>

                <div className="glass rounded-xl p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Population Covered</h4>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {analysisMutation.data.population_covered?.toLocaleString() || 0}
                  </p>
                </div>

                {analysisMutation.data.demographics && (
                  <div className="glass rounded-xl p-4">
                    <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">Demographics</h4>
                    <div className="space-y-2">
                      {Object.entries(analysisMutation.data.demographics).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center py-1">
                          <span className="text-sm text-gray-600 dark:text-gray-400">{key}:</span>
                          <span className="font-semibold text-gray-900 dark:text-gray-100">{value.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="pt-4 space-y-3">
                  <Button
                    variant="outline"
                    size="md"
                    fullWidth
                    leftIcon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
                    onClick={() => api.downloadExport(analysisMutation.data!.job_id, ExportFormat.CSV)}
                  >
                    Download CSV
                  </Button>
                  <Button
                    variant="outline"
                    size="md"
                    fullWidth
                    leftIcon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" /></svg>}
                    onClick={() => api.downloadExport(analysisMutation.data!.job_id, ExportFormat.GeoJSON)}
                  >
                    Download GeoJSON
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