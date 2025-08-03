import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useAPI } from '@/contexts'
import { useMapData } from '@/hooks'
import { Button, Input, Select, Card, CardHeader, CardTitle, CardContent, Spinner } from '@/components'
import { TravelMode, AnalysisRequest, ExportFormat, LocationSearchResult } from '@/types'

export function AddressGeocodingPage() {
  const api = useAPI()
  const { setView, setPOIs, setIsochrones, clearMap } = useMapData()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLocation, setSelectedLocation] = useState<LocationSearchResult | null>(null)
  const [travelMode, setTravelMode] = useState<TravelMode>(TravelMode.Walk)
  const [travelTime, setTravelTime] = useState(15)
  const [selectedPOITypes, setSelectedPOITypes] = useState<string[]>(['amenity:pharmacy', 'amenity:clinic'])
  
  // Search for locations
  const searchMutation = useMutation({
    mutationFn: async (query: string) => {
      return api.searchLocations({ q: query, limit: 5 })
    }
  })

  // Fetch healthcare POI types
  const { data: poiTypesData } = useQuery({
    queryKey: ['poiTypes', 'healthcare'],
    queryFn: () => api.getPOITypes({ category: 'Healthcare', limit: 10 })
  })

  // Create analysis mutation
  const analysisMutation = useMutation({
    mutationFn: async (request: AnalysisRequest) => {
      const response = await api.createLocationAnalysis(request)
      return api.pollJobStatus(response.job_id, (status) => {
        console.log('Address analysis progress:', status.progress)
      })
    }
  })

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    
    searchMutation.mutate(searchQuery)
  }

  const handleLocationSelect = (location: LocationSearchResult) => {
    setSelectedLocation(location)
    // Center map on selected location
    setView([location.latitude, location.longitude], 14)
    // Add a marker for the selected address
    setPOIs([{
      id: 'selected-address',
      name: location.display_name,
      position: [location.latitude, location.longitude],
      type: 'address',
      category: 'Selected Location'
    }])
  }

  const handleAnalysis = async () => {
    if (!selectedLocation) {
      alert('Please select a location first')
      return
    }

    clearMap()
    
    analysisMutation.mutate({
      location: selectedLocation.display_name,
      travel_mode: travelMode,
      travel_time_minutes: travelTime,
      poi_types: selectedPOITypes,
      census_variables: ['B01003_001E', 'B15003_022E'] // Population and education
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
      <h1 className="text-3xl font-bold text-gray-900">Address Geocoding</h1>
      <p className="mt-2 text-lg text-gray-600">
        Search for specific addresses and analyze accessibility from that exact location
      </p>

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Address Search and Configuration */}
        <div className="space-y-6">
          <Card variant="bordered">
            <CardHeader>
              <CardTitle>Search Address</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSearch} className="space-y-4">
                <Input
                  label="Enter Address"
                  placeholder="e.g., 123 Main St, Portland, OR"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  required
                />
                
                <Button
                  type="submit"
                  disabled={searchMutation.isPending || !searchQuery.trim()}
                  className="w-full"
                >
                  {searchMutation.isPending ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      Searching...
                    </>
                  ) : (
                    'Search Address'
                  )}
                </Button>
              </form>

              {/* Search Results */}
              {searchMutation.isSuccess && searchMutation.data && (
                <div className="mt-4">
                  <h4 className="font-medium text-sm text-gray-700 mb-2">
                    Search Results ({searchMutation.data.total_count})
                  </h4>
                  <div className="space-y-2">
                    {searchMutation.data.results.map((result, index) => (
                      <div
                        key={index}
                        className={`p-3 border rounded-md cursor-pointer transition-colors ${
                          selectedLocation?.display_name === result.display_name
                            ? 'bg-primary-50 border-primary-500'
                            : 'hover:bg-gray-50'
                        }`}
                        onClick={() => handleLocationSelect(result)}
                      >
                        <p className="text-sm font-medium">{result.display_name}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {result.city && `${result.city}, `}
                          {result.state && `${result.state}, `}
                          {result.country}
                        </p>
                        <p className="text-xs text-gray-400">
                          Coordinates: {result.latitude.toFixed(4)}, {result.longitude.toFixed(4)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {searchMutation.isError && (
                <div className="mt-4 text-red-600 text-sm">
                  Error searching for address. Please try again.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Analysis Configuration */}
          {selectedLocation && (
            <Card variant="bordered">
              <CardHeader>
                <CardTitle>Analysis Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-3 bg-green-50 rounded-md">
                    <p className="text-sm text-green-800">
                      <strong>Selected:</strong> {selectedLocation.display_name}
                    </p>
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
                      Healthcare Facilities to Find
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

                  <Button
                    onClick={handleAnalysis}
                    disabled={analysisMutation.isPending}
                    className="w-full"
                  >
                    {analysisMutation.isPending ? (
                      <>
                        <Spinner size="sm" className="mr-2" />
                        Analyzing...
                      </>
                    ) : (
                      'Analyze From This Address'
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Results Display */}
        <Card variant="bordered">
          <CardHeader>
            <CardTitle>Analysis Results</CardTitle>
          </CardHeader>
          <CardContent>
            {!selectedLocation && !analysisMutation.data && (
              <div>
                <p className="text-gray-500 mb-4">
                  Search for an address to begin analysis
                </p>
                <div className="bg-gray-50 p-4 rounded-md">
                  <h4 className="font-semibold text-sm mb-2">How Address Geocoding Works</h4>
                  <ol className="text-sm text-gray-600 space-y-2">
                    <li>1. Enter a specific street address</li>
                    <li>2. Select from the search results</li>
                    <li>3. Configure travel time and mode</li>
                    <li>4. Choose which facilities to search for</li>
                    <li>5. Run analysis from that exact location</li>
                  </ol>
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
                <div className="bg-blue-50 p-3 rounded-md">
                  <p className="text-sm text-blue-800">
                    <strong>Analysis from:</strong><br />
                    {selectedLocation?.display_name}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="border rounded-lg p-3">
                    <h4 className="text-xs text-gray-500 uppercase">Healthcare Facilities</h4>
                    <p className="text-2xl font-bold text-primary-600">
                      {analysisMutation.data.poi_count || 0}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      within {travelTime} min {travelMode}
                    </p>
                  </div>
                  
                  <div className="border rounded-lg p-3">
                    <h4 className="text-xs text-gray-500 uppercase">Service Area</h4>
                    <p className="text-2xl font-bold">
                      {analysisMutation.data.analysis_area_km2?.toFixed(1) || 0} km²
                    </p>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Area Demographics</h4>
                  {analysisMutation.data.demographics && (
                    <div className="space-y-2 bg-gray-50 p-3 rounded-md">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Total Population:</span>
                        <span className="font-medium">
                          {analysisMutation.data.demographics['B01003_001E']?.toLocaleString() || 0}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Bachelor's Degree or Higher:</span>
                        <span className="font-medium">
                          {analysisMutation.data.demographics['B15003_022E']?.toLocaleString() || 0}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Facility List */}
                <div>
                  <h4 className="font-semibold mb-2">Nearest Facilities</h4>
                  <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                    <p>Found {analysisMutation.data.poi_count || 0} healthcare facilities 
                    within a {travelTime}-minute {travelMode} from this address.</p>
                    
                    {analysisMutation.data.poi_count === 0 && (
                      <p className="mt-2 text-amber-600">
                        ⚠️ No facilities found within the specified travel time. 
                        Try increasing the travel time or changing the mode of transport.
                      </p>
                    )}
                  </div>
                </div>

                <div className="pt-4 space-y-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => api.downloadExport(analysisMutation.data!.job_id, ExportFormat.CSV)}
                  >
                    Download Results (CSV)
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => api.downloadExport(analysisMutation.data!.job_id, ExportFormat.GeoJSON)}
                  >
                    Download Service Area (GeoJSON)
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