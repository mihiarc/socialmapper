/**
 * ProgressTracker Component - Real-time analysis progress tracking
 * Uses Server-Sent Events for live progress updates during analysis
 */
import React, { useEffect, useCallback, useRef, useState } from 'react';
import { 
  Progress, 
  Card, 
  Typography, 
  Steps, 
  Space,
  Button,
  Alert,
  Spin,
  Divider,
  Tag,
  Modal,
  Row,
  Col
} from 'antd';
import {
  LoadingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  StopOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { updateJobStatus, completeJob, removeActiveJob } from '@/store/slices/analysisSlice';
import { useDeleteAnalysisJobMutation } from '@/store/api/analysisApi';
import { JobStatusEnum } from '@/types/api';

const { Title, Text } = Typography;
const { Step } = Steps;

interface ProgressTrackerProps {
  jobId: string;
  onComplete?: (jobId: string) => void;
  onCancel?: (jobId: string) => void;
  showEstimatedTime?: boolean;
}

// Progress stages mapping
const PROGRESS_STAGES = [
  {
    key: 'initializing',
    title: 'Initializing',
    description: 'Setting up analysis parameters',
    minProgress: 0
  },
  {
    key: 'geocoding',
    title: 'Location Processing',
    description: 'Processing location and coordinates',
    minProgress: 10
  },
  {
    key: 'isochrone_generation',
    title: 'Travel Area Calculation',
    description: 'Calculating reachable areas by travel mode',
    minProgress: 25
  },
  {
    key: 'poi_discovery',
    title: 'Finding Points of Interest',
    description: 'Searching for places within travel range',
    minProgress: 50
  },
  {
    key: 'demographic_analysis',
    title: 'Demographic Analysis',
    description: 'Analyzing population and demographics',
    minProgress: 70
  },
  {
    key: 'finalizing',
    title: 'Finalizing Results',
    description: 'Preparing final analysis results',
    minProgress: 90
  }
];

/**
 * Real-time progress tracker with Server-Sent Events integration
 */
const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  jobId,
  onComplete,
  onCancel,
  showEstimatedTime = true
}) => {
  const dispatch = useAppDispatch();
  const eventSourceRef = useRef<EventSource | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error' | 'closed'>('connecting');
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [estimatedCompletion, setEstimatedCompletion] = useState<string>('');
  const [currentStage, setCurrentStage] = useState<string>('initializing');
  const [errorDetails, setErrorDetails] = useState<string>('');

  const { activeJobs } = useAppSelector(state => state.analysis);
  const currentJob = activeJobs.find(job => job.id === jobId);

  const [deleteJob] = useDeleteAnalysisJobMutation();

  // Initialize Server-Sent Events connection
  useEffect(() => {
    if (!jobId) return;

    const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
    const eventSource = new EventSource(`${API_BASE_URL}/analysis/${jobId}/progress`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setConnectionStatus('connected');
      console.log('SSE connection opened for job:', jobId);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleProgressUpdate(data);
      } catch (error) {
        console.error('Failed to parse progress update:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      setConnectionStatus('error');
      
      // Retry connection after 5 seconds
      setTimeout(() => {
        if (eventSourceRef.current?.readyState === EventSource.CLOSED) {
          setConnectionStatus('connecting');
          // Will be recreated by useEffect re-run
        }
      }, 5000);
    };

    // Custom event handlers for specific events
    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data);
      handleProgressUpdate(data);
    });

    eventSource.addEventListener('stage_change', (event) => {
      const data = JSON.parse(event.data);
      setCurrentStage(data.stage);
    });

    eventSource.addEventListener('completed', (event) => {
      const data = JSON.parse(event.data);
      handleJobCompletion(data);
    });

    eventSource.addEventListener('failed', (event) => {
      const data = JSON.parse(event.data);
      handleJobFailure(data);
    });

    return () => {
      eventSource.close();
      setConnectionStatus('closed');
    };
  }, [jobId]);

  // Handle progress updates from SSE
  const handleProgressUpdate = useCallback((data: any) => {
    const { job_id, status, progress, message, stage, estimated_completion } = data;
    
    setLastUpdate(new Date().toLocaleTimeString());
    
    if (stage) {
      setCurrentStage(stage);
    }
    
    if (estimated_completion) {
      setEstimatedCompletion(estimated_completion);
    }

    // Update Redux state
    dispatch(updateJobStatus({
      id: job_id,
      status: status || JobStatusEnum.RUNNING,
      progress: progress || 0,
      message: message || ''
    }));
  }, [dispatch]);

  // Handle job completion
  const handleJobCompletion = useCallback((data: any) => {
    dispatch(completeJob(data.job_id));
    setConnectionStatus('closed');
    onComplete?.(data.job_id);
  }, [dispatch, onComplete]);

  // Handle job failure
  const handleJobFailure = useCallback((data: any) => {
    const { job_id, error, error_details } = data;
    
    dispatch(updateJobStatus({
      id: job_id,
      status: JobStatusEnum.FAILED,
      progress: 0,
      message: error || 'Analysis failed'
    }));
    
    setErrorDetails(error_details || error || 'Unknown error occurred');
    setConnectionStatus('closed');
  }, [dispatch]);

  // Cancel job
  const handleCancelJob = useCallback(async () => {
    Modal.confirm({
      title: 'Cancel Analysis',
      content: 'Are you sure you want to cancel this analysis? This action cannot be undone.',
      okText: 'Yes, Cancel',
      cancelText: 'Keep Running',
      onOk: async () => {
        try {
          await deleteJob(jobId);
          dispatch(removeActiveJob(jobId));
          eventSourceRef.current?.close();
          onCancel?.(jobId);
        } catch (error) {
          console.error('Failed to cancel job:', error);
        }
      }
    });
  }, [jobId, deleteJob, dispatch, onCancel]);

  // Retry connection
  const handleRetryConnection = useCallback(() => {
    setConnectionStatus('connecting');
    // The useEffect will recreate the connection
  }, []);

  // Get current progress stage
  const getCurrentStageIndex = () => {
    return PROGRESS_STAGES.findIndex(stage => stage.key === currentStage);
  };

  // Get progress color based on status
  const getProgressColor = () => {
    if (currentJob?.status === JobStatusEnum.FAILED) return 'exception';
    if (currentJob?.status === JobStatusEnum.COMPLETED) return 'success';
    return 'active';
  };

  // Format estimated completion time
  const formatEstimatedTime = (timeString: string) => {
    if (!timeString) return '';
    try {
      const time = new Date(timeString);
      const now = new Date();
      const diffMs = time.getTime() - now.getTime();
      const diffMins = Math.ceil(diffMs / (1000 * 60));
      
      if (diffMins <= 0) return 'Completing soon...';
      if (diffMins < 60) return `~${diffMins} minutes remaining`;
      
      const hours = Math.ceil(diffMins / 60);
      return `~${hours} hour${hours > 1 ? 's' : ''} remaining`;
    } catch {
      return '';
    }
  };

  if (!currentJob) {
    return (
      <Alert
        message="Job Not Found"
        description="The requested analysis job could not be found."
        type="warning"
        showIcon
      />
    );
  }

  return (
    <div className="progress-tracker">
      <Card
        title={
          <Space>
            <LoadingOutlined spin={currentJob.status === JobStatusEnum.RUNNING} />
            <Text strong>Analysis Progress</Text>
            <Tag color={getProgressColor() === 'active' ? 'processing' : getProgressColor()}>
              {currentJob.status.toUpperCase()}
            </Tag>
          </Space>
        }
        extra={
          <Space>
            {connectionStatus === 'connected' && (
              <Tag color="green">Live Updates</Tag>
            )}
            {connectionStatus === 'error' && (
              <Button size="small" icon={<ReloadOutlined />} onClick={handleRetryConnection}>
                Retry
              </Button>
            )}
            {currentJob.status === JobStatusEnum.RUNNING && (
              <Button 
                size="small" 
                danger 
                icon={<StopOutlined />}
                onClick={handleCancelJob}
              >
                Cancel
              </Button>
            )}
          </Space>
        }
      >
        {/* Progress Bar */}
        <Progress
          percent={currentJob.progress || 0}
          status={getProgressColor()}
          strokeColor={{
            '0%': '#87ceeb',
            '100%': '#1890ff',
          }}
          format={(percent) => `${percent?.toFixed(1)}%`}
        />

        {/* Time Information */}
        {showEstimatedTime && (
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={12}>
              <Space>
                <ClockCircleOutlined />
                <Text type="secondary">Started:</Text>
                <Text>{currentJob.started_at ? new Date(currentJob.started_at).toLocaleTimeString() : 'N/A'}</Text>
              </Space>
            </Col>
            <Col span={12}>
              <Space>
                <ClockCircleOutlined />
                <Text type="secondary">Estimated completion:</Text>
                <Text>{formatEstimatedTime(estimatedCompletion) || 'Calculating...'}</Text>
              </Space>
            </Col>
          </Row>
        )}

        <Divider />

        {/* Progress Stages */}
        <div style={{ marginBottom: 16 }}>
          <Title level={5}>Processing Stages</Title>
          <Steps
            current={getCurrentStageIndex()}
            size="small"
            direction="vertical"
          >
            {PROGRESS_STAGES.map((stage, index) => {
              const isCompleted = (currentJob.progress || 0) > stage.minProgress;
              const isCurrent = getCurrentStageIndex() === index;
              
              return (
                <Step
                  key={stage.key}
                  title={stage.title}
                  description={stage.description}
                  status={
                    isCompleted ? 'finish' :
                    isCurrent ? 'process' :
                    'wait'
                  }
                  icon={
                    isCompleted ? <CheckCircleOutlined /> :
                    isCurrent ? <LoadingOutlined /> :
                    undefined
                  }
                />
              );
            })}
          </Steps>
        </div>

        {/* Current Status */}
        {currentJob.message && (
          <Alert
            message="Current Status"
            description={currentJob.message}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Error Details */}
        {currentJob.status === JobStatusEnum.FAILED && errorDetails && (
          <Alert
            message="Analysis Failed"
            description={errorDetails}
            type="error"
            showIcon
          />
        )}

        {/* Connection Status */}
        {connectionStatus === 'error' && (
          <Alert
            message="Connection Error"
            description="Lost connection to progress updates. Click Retry to reconnect."
            type="warning"
            showIcon
            action={
              <Button size="small" onClick={handleRetryConnection}>
                Retry Connection
              </Button>
            }
          />
        )}

        {/* Last Update Time */}
        {lastUpdate && connectionStatus === 'connected' && (
          <Text type="secondary" style={{ fontSize: '11px', float: 'right' }}>
            Last update: {lastUpdate}
          </Text>
        )}
      </Card>
    </div>
  );
};

export default ProgressTracker;