/**
 * Custom hook for displaying notifications
 */
import { useDispatch } from 'react-redux';
import { 
  showSuccessNotification, 
  showErrorNotification, 
  showInfoNotification 
} from '@store/slices/uiSlice';

interface NotificationOptions {
  title: string;
  message: string;
}

/**
 * Hook for convenient notification management
 */
export const useNotification = () => {
  const dispatch = useDispatch();

  const showSuccess = ({ title, message }: NotificationOptions) => {
    dispatch(showSuccessNotification({ title, message }));
  };

  const showError = ({ title, message }: NotificationOptions) => {
    dispatch(showErrorNotification({ title, message }));
  };

  const showInfo = ({ title, message }: NotificationOptions) => {
    dispatch(showInfoNotification({ title, message }));
  };

  // Convenience methods for common scenarios
  const notifyAnalysisStarted = (jobId: string) => {
    showSuccess({
      title: 'Analysis Started',
      message: `Analysis job ${jobId.slice(0, 8)}... has been started successfully.`,
    });
  };

  const notifyAnalysisCompleted = (jobId: string) => {
    showSuccess({
      title: 'Analysis Completed',
      message: `Analysis job ${jobId.slice(0, 8)}... has completed successfully.`,
    });
  };

  const notifyAnalysisFailed = (jobId: string, error: string) => {
    showError({
      title: 'Analysis Failed',
      message: `Analysis job ${jobId.slice(0, 8)}... failed: ${error}`,
    });
  };

  const notifyExportReady = (format: string) => {
    showInfo({
      title: 'Export Ready',
      message: `Your ${format.toUpperCase()} export is ready for download.`,
    });
  };

  return {
    showSuccess,
    showError,
    showInfo,
    notifyAnalysisStarted,
    notifyAnalysisCompleted,
    notifyAnalysisFailed,
    notifyExportReady,
  };
};