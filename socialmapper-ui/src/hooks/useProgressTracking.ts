/**
 * Custom hook for tracking analysis job progress with Server-Sent Events
 */
import { useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { updateJobStatus } from '@store/slices/analysisSlice';
import type { JobStatusEnum } from "@/types/api";

interface ProgressEvent {
  job_id: string;
  status: JobStatusEnum;
  progress: number;
  message?: string;
}

/**
 * Hook for real-time progress tracking using Server-Sent Events
 */
export const useProgressTracking = (jobId: string | null) => {
  const dispatch = useDispatch();
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) return;

    // Create Server-Sent Events connection
    const eventSource = new EventSource(`/api/v1/analysis/${jobId}/progress`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data: ProgressEvent = JSON.parse(event.data);
        
        // Update job status in Redux store
        dispatch(updateJobStatus({
          id: data.job_id,
          status: data.status,
          progress: data.progress,
          message: data.message,
        }));
        
        // Close connection if job is completed or failed
        if (data.status === 'completed' || data.status === 'failed') {
          eventSource.close();
        }
      } catch (error) {
        console.error('Failed to parse progress event:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('Progress tracking error:', error);
      eventSource.close();
    };

    // Cleanup on unmount
    return () => {
      eventSource.close();
    };
  }, [jobId, dispatch]);

  // Manual cleanup function
  const stopTracking = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  return { stopTracking };
};