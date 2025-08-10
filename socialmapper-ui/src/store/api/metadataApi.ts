/**
 * RTK Query API for metadata operations
 * Provides cached access to census variables, POI types, and location search
 */
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type {
  CensusVariablesResponse,
  LocationSearchResponse,
  POITypesResponse,
} from '@types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const metadataApi = createApi({
  reducerPath: 'metadataApi',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
  }),
  tagTypes: ['Metadata'],
  endpoints: (builder) => ({
    // Get census variables with caching
    getCensusVariables: builder.query<CensusVariablesResponse, void>({
      query: () => '/metadata/census-variables',
      providesTags: ['Metadata'],
      // Cache for 1 hour
      keepUnusedDataFor: 3600,
    }),

    // Get POI types with caching
    getPOITypes: builder.query<POITypesResponse, void>({
      query: () => '/metadata/poi-types',
      providesTags: ['Metadata'],
      // Cache for 1 hour
      keepUnusedDataFor: 3600,
    }),

    // Get travel modes
    getTravelModes: builder.query<{ travel_modes: string[] }, void>({
      query: () => '/metadata/travel-modes',
      providesTags: ['Metadata'],
      // Cache for 1 hour
      keepUnusedDataFor: 3600,
    }),

    // Search locations with debouncing
    searchLocations: builder.query<LocationSearchResponse, string>({
      query: (query) => ({
        url: '/metadata/locations/search',
        params: { query },
      }),
      // Only cache for 5 minutes for location searches
      keepUnusedDataFor: 300,
    }),
  }),
});

export const {
  useGetCensusVariablesQuery,
  useGetPOITypesQuery,
  useGetTravelModesQuery,
  useSearchLocationsQuery,
  useLazySearchLocationsQuery,
} = metadataApi;