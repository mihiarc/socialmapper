import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useAPI } from '@/contexts'
import { Button, Input, Select, Card, CardHeader, CardTitle, CardContent, Spinner } from '@/components'
import { TravelMode, AnalysisRequest, ExportFormat } from '@/types'

export function ZCTAAnalysisPage() {
  const api = useAPI()
  const [location, setLocation] = useState('')
  const [zipCode, setZipCode] = useState('')
  const [travelMode, setTravelMode] = useState<TravelMode>(TravelMode.Drive)
  const [travelTime, setTravelTime] = useState(20)
  const [selectedPOITypes, setSelectedPOITypes] = useState<string[]>(['shop:supermarket'])
  const [selectedCensusVars, setSelectedCensusVars] = useState<string[]>([
    'B01003_001E', // Total population
    'B19013_001E', // Median household income
    'B25001_001E'  // Total housing units
  ])

  // Fetch available POI types
  const { data: poiTypesData } = useQuery({
    queryKey: ['poiTypes', 'food'],
    queryFn: () => api.getPOITypes({ category: 'Food & Shopping', limit: 20 })
  })

  // Fetch income-related census variables
  const { data: censusVarsData } = useQuery({
    queryKey: ['censusVariables', 'income'],
    queryFn: () => api.getCensusVariables({ group: 'Income', limit: 10 })
  })

  // Create analysis mutation
  const analysisMutation = useMutation({
    mutationFn: async (request: AnalysisRequest) => {
      const response = await api.createLocationAnalysis(request)
      return api.pollJobStatus(response.job_id, (status) => {
        console.log('ZIP Code analysis progress:', status.progress)
      })
    }
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Use either location or ZIP code
    const analysisLocation = zipCode ? `ZIP ${zipCode}` : location
    
    analysisMutation.mutate({
      location: analysisLocation,
      travel_mode: travelMode,
      travel_time_minutes: travelTime,
      poi_types: selectedPOITypes,
      census_variables: selectedCensusVars,
      use_zcta: true // Key parameter for ZIP Code analysis
    })
  }

  const travelModeOptions = [
    { value: TravelMode.Walk, label: 'Walking' },
    { value: TravelMode.Bike, label: 'Biking' },
    { value: TravelMode.Drive, label: 'Driving' },
    { value: TravelMode.Transit, label: 'Transit' }
  ]

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-3xl font-bold text-gray-900">ZIP Code Analysis</h1>
      <p className="mt-2 text-lg text-gray-600">
        Analyze accessibility at the ZIP Code level for broader demographic insights
      </p>

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Analysis Form */}
        <Card variant="bordered">
          <CardHeader>
            <CardTitle>ZIP Code Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="bg-blue-50 p-4 rounded-md mb-4">
                <p className="text-sm text-blue-800">
                  <strong>ZIP Code Analysis:</strong> This analysis aggregates data at the ZIP Code 
                  level, providing broader geographic coverage but less granular 
                  detail than block group analysis.
                </p>
              </div>

              <div className="space-y-4">
                <Input
                  label="ZIP Code"
                  placeholder="e.g., 97209"
                  value={zipCode}
                  onChange={(e) => setZipCode(e.target.value)}
                  pattern="[0-9]{5}"
                  maxLength={5}
                />
                
                <div className="text-center text-sm text-gray-500">OR</div>
                
                <Input
                  label="City/Location"
                  placeholder="e.g., Portland, OR"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  disabled={!!zipCode}
                />
              </div>

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
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Points of Interest (Food Access)
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto border rounded-md p-2">
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
                      <span className="text-sm">{poi.name} - {poi.description}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Census Variables (Income & Demographics)
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto border rounded-md p-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="mr-2"
                      value="B01003_001E"
                      checked={selectedCensusVars.includes('B01003_001E')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedCensusVars([...selectedCensusVars, 'B01003_001E'])
                        } else {
                          setSelectedCensusVars(selectedCensusVars.filter(v => v !== 'B01003_001E'))
                        }
                      }}
                    />
                    <span className="text-sm">Total Population</span>
                  </label>
                  
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
                disabled={analysisMutation.isPending || (!location && !zipCode)}
                className="w-full"
              >
                {analysisMutation.isPending ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Analyzing ZIP Code...
                  </>
                ) : (
                  'Run ZIP Code Analysis'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Results Display */}
        <Card variant="bordered">
          <CardHeader>
            <CardTitle>ZIP Code Analysis Results</CardTitle>
          </CardHeader>
          <CardContent>
            {analysisMutation.isIdle && (
              <div>
                <p className="text-gray-500 mb-4">
                  Submit a ZIP Code analysis to see results
                </p>
                <div className="bg-gray-50 p-4 rounded-md">
                  <h4 className="font-semibold text-sm mb-2">About ZIP Code Analysis</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Analyzes entire ZIP Code areas instead of smaller block groups</li>
                    <li>• Useful for food desert analysis and broader demographic patterns</li>
                    <li>• Provides aggregated census data at the ZIP code level</li>
                    <li>• Better for regional planning and policy analysis</li>
                  </ul>
                </div>
              </div>
            )}
            
            {analysisMutation.isPending && (
              <div className="flex items-center justify-center py-8">
                <Spinner size="lg" />
              </div>
            )}

            {analysisMutation.isError && (
              <div className="text-red-600">
                Error: {analysisMutation.error?.message}
              </div>
            )}

            {analysisMutation.isSuccess && analysisMutation.data && (
              <div className="space-y-4">
                <div className="bg-green-50 p-3 rounded-md">
                  <p className="text-sm text-green-800">
                    Analysis completed at ZIP Code level for broader geographic coverage
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="border rounded-lg p-3">
                    <h4 className="text-xs text-gray-500 uppercase">Food Outlets</h4>
                    <p className="text-2xl font-bold text-primary-600">
                      {analysisMutation.data.poi_count || 0}
                    </p>
                  </div>
                  
                  <div className="border rounded-lg p-3">
                    <h4 className="text-xs text-gray-500 uppercase">Coverage Area</h4>
                    <p className="text-2xl font-bold">
                      {analysisMutation.data.analysis_area_km2?.toFixed(1) || 0} km²
                    </p>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">ZIP Code Demographics</h4>
                  <p className="text-sm text-gray-600 mb-2">
                    Aggregated at ZIP Code level:
                  </p>
                  
                  {analysisMutation.data.demographics && (
                    <div className="space-y-2 bg-gray-50 p-3 rounded-md">
                      {Object.entries(analysisMutation.data.demographics).map(([key, value]) => {
                        // Map census codes to friendly names
                        const friendlyNames: Record<string, string> = {
                          'B01003_001E': 'Total Population',
                          'B19013_001E': 'Median Household Income',
                          'B25001_001E': 'Total Housing Units'
                        }
                        
                        return (
                          <div key={key} className="flex justify-between text-sm">
                            <span className="text-gray-600">
                              {friendlyNames[key] || key}:
                            </span>
                            <span className="font-medium">
                              {key.includes('income') ? `$${value.toLocaleString()}` : value.toLocaleString()}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {/* Food Desert Indicator */}
                  {analysisMutation.data.demographics?.['B19013_001E'] && (
                    <div className="mt-4 p-3 rounded-md border-2"
                      style={{
                        borderColor: analysisMutation.data.poi_count < 3 ? '#ef4444' : '#10b981',
                        backgroundColor: analysisMutation.data.poi_count < 3 ? '#fef2f2' : '#f0fdf4'
                      }}
                    >
                      <h5 className="font-semibold text-sm mb-1">
                        Food Access Assessment
                      </h5>
                      <p className="text-sm">
                        {analysisMutation.data.poi_count < 3 ? (
                          <span className="text-red-700">
                            ⚠️ Limited food access detected. This area may be a food desert.
                          </span>
                        ) : (
                          <span className="text-green-700">
                            ✓ Adequate food access with {analysisMutation.data.poi_count} outlets nearby.
                          </span>
                        )}
                      </p>
                    </div>
                  )}
                </div>

                <div className="pt-4 space-y-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => api.downloadExport(analysisMutation.data!.job_id, ExportFormat.CSV)}
                  >
                    Download ZIP Code Data (CSV)
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => api.downloadExport(analysisMutation.data!.job_id, ExportFormat.GeoJSON)}
                  >
                    Download ZIP Code Boundaries (GeoJSON)
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