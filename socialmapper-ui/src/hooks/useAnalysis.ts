/**
 * React hook for managing SocialMapper analysis state and operations
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { 
  apiClient,
  LocationAnalysisRequest,
  CustomPOIAnalysisRequest,
  AnalysisResponse,
  AnalysisResult,
  JobStatus,
  JobStatusEnum,
  APIClientError
} from '../services/apiClient';
import { config } from '../config/settings';

export interface AnalysisState {
  status: 'idle' | 'submitting' | 'running' | 'completed' | 'failed' | 'cancelled';
  jobId: string | null;
  result: AnalysisResult | null;
  error: Error | null;
  progress: number;
  message: string | null;
}

export interface UseAnalysisOptions {
  onProgress?: (status: JobStatus) => void;
  onComplete?: (result: AnalysisResult) => void;
  onError?: (error: Error) => void;
  pollInterval?: number;
}

/**
 * Hook for managing analysis lifecycle
 */
export function useAnalysis(options: UseAnalysisOptions = {}) {
  const queryClient = useQueryClient();
  const [state, setState] = useState<AnalysisState>({
    status: 'idle',
    jobId: null,
    result: null,
    error: null,
    progress: 0,
    message: null,
  });
  
  const currentJobIdRef = useRef<string | null>(null);
  
  // Mutation for submitting location analysis
  const submitLocationAnalysis = useMutation({
    mutationFn: (request: LocationAnalysisRequest) => apiClient.analyzeLocation(request),
    onSuccess: (response: AnalysisResponse) => {
      currentJobIdRef.current = response.job_id;
      setState(prev => ({
        ...prev,
        status: 'running',
        jobId: response.job_id,
        error: null,
        progress: 0,
        message: response.message || 'Analysis started',
      }));
    },
    onError: (error: Error) => {
      setState(prev => ({
        ...prev,
        status: 'failed',
        error,
        progress: 0,
        message: error.message,
      }));
      options.onError?.(error);
    },
  });
  
  // Mutation for submitting custom POI analysis
  const submitCustomPOIAnalysis = useMutation({
    mutationFn: (request: CustomPOIAnalysisRequest) => apiClient.analyzeCustomPOIs(request),
    onSuccess: (response: AnalysisResponse) => {
      currentJobIdRef.current = response.job_id;
      setState(prev => ({
        ...prev,
        status: 'running',
        jobId: response.job_id,
        error: null,
        progress: 0,
        message: response.message || 'Analysis started',
      }));
    },
    onError: (error: Error) => {
      setState(prev => ({
        ...prev,
        status: 'failed',
        error,
        progress: 0,
        message: error.message,
      }));
      options.onError?.(error);
    },
  });
  
  // Query for polling job status
  const { data: jobStatus } = useQuery({
    queryKey: ['job-status', state.jobId],
    queryFn: () => state.jobId ? apiClient.getJobStatus(state.jobId) : null,
    enabled: state.status === 'running' && !!state.jobId,
    refetchInterval: options.pollInterval || config.pollInterval,
    refetchIntervalInBackground: true,
  });
  
  // Handle job status updates
  useEffect(() => {
    if (!jobStatus) return;
    
    // Update progress
    setState(prev => ({
      ...prev,
      progress: jobStatus.progress,
      message: jobStatus.message || null,
    }));
    
    // Call progress callback
    options.onProgress?.(jobStatus);
    
    // Handle completion
    if (jobStatus.status === JobStatusEnum.COMPLETED) {
      // Fetch full results
      apiClient.getAnalysisResult(jobStatus.job_id)
        .then(result => {
          setState(prev => ({
            ...prev,
            status: 'completed',
            result,
            progress: 1,
            message: 'Analysis completed',
          }));
          
          // Cache the result
          queryClient.setQueryData(['analysis-result', jobStatus.job_id], result);
          
          // Call completion callback
          options.onComplete?.(result);
        })
        .catch(error => {
          setState(prev => ({
            ...prev,
            status: 'failed',
            error,
            message: error.message,
          }));
          options.onError?.(error);
        });
    }
    
    // Handle failure
    if (jobStatus.status === JobStatusEnum.FAILED) {
      const error = new Error(jobStatus.error || 'Analysis failed');
      setState(prev => ({
        ...prev,
        status: 'failed',
        error,
        message: jobStatus.error || 'Analysis failed',
      }));
      options.onError?.(error);
    }
    
    // Handle cancellation
    if (jobStatus.status === JobStatusEnum.CANCELLED) {
      setState(prev => ({
        ...prev,
        status: 'cancelled',
        message: 'Analysis cancelled',
      }));
    }
  }, [jobStatus, queryClient, options]);
  
  // Cancel analysis
  const cancel = useCallback(() => {
    if (state.jobId && state.status === 'running') {
      apiClient.cancelRequest(state.jobId);
      setState(prev => ({
        ...prev,
        status: 'cancelled',
        progress: 0,
        message: 'Analysis cancelled',
      }));
    }
  }, [state.jobId, state.status]);
  
  // Reset state
  const reset = useCallback(() => {
    if (currentJobIdRef.current) {
      apiClient.cancelRequest(currentJobIdRef.current);
    }
    setState({
      status: 'idle',
      jobId: null,
      result: null,
      error: null,
      progress: 0,
      message: null,
    });
    currentJobIdRef.current = null;
  }, []);
  
  // Export results
  const exportResults = useCallback(async (
    format: 'csv' | 'geojson' | 'parquet' | 'geoparquet',
    includeIsochrones = true,
    includeDemographics = true
  ): Promise<Blob | null> => {
    if (!state.result?.job_id) return null;
    
    try {
      return await apiClient.exportResults(
        state.result.job_id,
        format as any,
        includeIsochrones,
        includeDemographics
      );
    } catch (error) {
      console.error('Export failed:', error);
      throw error;
    }
  }, [state.result]);
  
  // Delete results
  const deleteResults = useCallback(async () => {
    if (!state.result?.job_id) return;
    
    try {
      await apiClient.deleteResults(state.result.job_id);
      queryClient.removeQueries(['analysis-result', state.result.job_id]);
      reset();
    } catch (error) {
      console.error('Delete failed:', error);
      throw error;
    }
  }, [state.result, queryClient, reset]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (currentJobIdRef.current) {
        apiClient.cancelRequest(currentJobIdRef.current);
      }
    };
  }, []);
  
  return {
    // State
    state,
    isIdle: state.status === 'idle',
    isSubmitting: submitLocationAnalysis.isLoading || submitCustomPOIAnalysis.isLoading,
    isRunning: state.status === 'running',
    isCompleted: state.status === 'completed',
    isFailed: state.status === 'failed',
    isCancelled: state.status === 'cancelled',
    
    // Actions
    analyzeLocation: submitLocationAnalysis.mutate,
    analyzeCustomPOIs: submitCustomPOIAnalysis.mutate,
    cancel,
    reset,
    exportResults,
    deleteResults,
    
    // Data
    result: state.result,
    error: state.error,
    progress: state.progress,
    message: state.message,
  };
}

/**
 * Hook for managing cached analysis results
 */
export function useCachedAnalysisResult(jobId: string | null) {
  const queryClient = useQueryClient();
  
  const { data: result, isLoading, error } = useQuery({
    queryKey: ['analysis-result', jobId],
    queryFn: () => jobId ? apiClient.getAnalysisResult(jobId) : null,
    enabled: !!jobId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
  });
  
  const invalidate = useCallback(() => {
    if (jobId) {
      queryClient.invalidateQueries(['analysis-result', jobId]);
    }
  }, [jobId, queryClient]);
  
  return {
    result,
    isLoading,
    error,
    invalidate,
  };
}