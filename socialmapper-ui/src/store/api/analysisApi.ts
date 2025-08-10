/**
 * RTK Query API for analysis operations
 * Provides caching, background updates, and optimistic updates
 */
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type {
  AnalysisResponse,
  AnalysisResult,
  CustomPOIAnalysisRequest,
  ExportFormat,
  JobStatus,
  LocationAnalysisRequest,
} from "@/types/api";

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const analysisApi = createApi({
  reducerPath: 'analysisApi',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
  }),
  tagTypes: ['Analysis', 'Job'],
  endpoints: (builder) => ({
    // Submit location-based analysis
    submitLocationAnalysis: builder.mutation<AnalysisResponse, LocationAnalysisRequest>({
      query: (analysisRequest) => ({
        url: '/analysis/location',
        method: 'POST',
        body: analysisRequest,
      }),
      invalidatesTags: ['Analysis'],
    }),

    // Submit custom POI analysis
    submitCustomPOIAnalysis: builder.mutation<AnalysisResponse, CustomPOIAnalysisRequest>({
      query: (analysisRequest) => ({
        url: '/analysis/custom-poi',
        method: 'POST',
        body: analysisRequest,
      }),
      invalidatesTags: ['Analysis'],
    }),

    // Get job status with polling support
    getJobStatus: builder.query<JobStatus, string>({
      query: (jobId) => `/analysis/${jobId}/status`,
      providesTags: (result, error, jobId) => [{ type: 'Job', id: jobId }],
      // Poll every 2 seconds for pending/running jobs
      async onCacheEntryAdded(jobId, { updateCachedData, cacheDataLoaded, cacheEntryRemoved }) {
        const pollInterval = setInterval(async () => {
          try {
            const { data } = await cacheDataLoaded;
            if (data.status === 'pending' || data.status === 'running') {
              // Continue polling
            } else {
              // Stop polling for completed/failed jobs
              clearInterval(pollInterval);
            }
          } catch {
            clearInterval(pollInterval);
          }
        }, 2000);

        await cacheEntryRemoved;
        clearInterval(pollInterval);
      },
    }),

    // Get analysis results
    getAnalysisResult: builder.query<AnalysisResult, string>({
      query: (jobId) => `/analysis/${jobId}/result`,
      providesTags: (result, error, jobId) => [{ type: 'Analysis', id: jobId }],
    }),

    // Get results (alternative endpoint)
    getResults: builder.query<AnalysisResult, string>({
      query: (jobId) => `/results/${jobId}`,
      providesTags: (result, error, jobId) => [{ type: 'Analysis', id: jobId }],
    }),

    // Delete analysis job
    deleteAnalysisJob: builder.mutation<{ message: string; job_id: string }, string>({
      query: (jobId) => ({
        url: `/analysis/${jobId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, jobId) => [
        { type: 'Job', id: jobId },
        { type: 'Analysis', id: jobId },
      ],
    }),

    // Export results
    exportResults: builder.mutation<
      Blob,
      {
        jobId: string;
        format: ExportFormat;
        includeIsochrones?: boolean;
        includeDemographics?: boolean;
      }
    >({
      query: ({ jobId, format, includeIsochrones = true, includeDemographics = true }) => ({
        url: `/results/${jobId}/export`,
        method: 'GET',
        params: {
          format,
          include_isochrones: includeIsochrones,
          include_demographics: includeDemographics,
        },
        responseHandler: (response) => response.blob(),
      }),
    }),

    // Get all jobs (admin/debug)
    getAllJobs: builder.query<any, void>({
      query: () => '/analysis/jobs',
      providesTags: ['Analysis'],
    }),
  }),
});

export const {
  useSubmitLocationAnalysisMutation,
  useSubmitCustomPOIAnalysisMutation,
  useGetJobStatusQuery,
  useGetAnalysisResultQuery,
  useGetResultsQuery,
  useDeleteAnalysisJobMutation,
  useExportResultsMutation,
  useGetAllJobsQuery,
  useLazyGetJobStatusQuery,
  useLazyGetAnalysisResultQuery,
} = analysisApi;