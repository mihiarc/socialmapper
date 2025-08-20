/**
 * ProgressTracker Component - Real-time analysis progress tracking
 * Uses WebSocket for live bidirectional progress updates during analysis
 */
import React, { useEffect, useCallback, useState } from 'react';
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
import { removeActiveJob } from '@/store/slices/analysisSlice';
import { useDeleteAnalysisJobMutation } from '@/store/api/analysisApi';
import { JobStatusEnum } from '@/types/api';
import { websocketService, type WebSocketMessage } from '@/services/websocket';

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
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error' | 'disconnected'>('connecting');
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [estimatedCompletion, setEstimatedCompletion] = useState<string>('');
  const [currentStage, setCurrentStage] = useState<string>('initializing');
  const [errorDetails, setErrorDetails] = useState<string>('');
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  const { activeJobs } = useAppSelector(state => state.analysis);
  const currentJob = activeJobs.find(job => job.id === jobId);

  const [deleteJob] = useDeleteAnalysisJobMutation();

  // Initialize WebSocket connection
  useEffect(() => {
    if (!jobId) return;

    let unsubscribe: (() => void) | undefined;
    let mounted = true;

    const connectWebSocket = async () => {
      try {
        setConnectionStatus('connecting');
        await websocketService.connect(jobId);
        
        if (!mounted) return;
        
        setConnectionStatus('connected');
        setReconnectAttempt(0);
        console.log('WebSocket connected for job:', jobId);

        // Subscribe to messages
        unsubscribe = websocketService.subscribe(jobId, (message: WebSocketMessage) => {
          if (!mounted) return;
          
          handleWebSocketMessage(message);
        });
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        if (mounted) {
          setConnectionStatus('error');
          // Retry with exponential backoff
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 30000);
          setTimeout(() => {
            if (mounted) {
              setReconnectAttempt(prev => prev + 1);
              connectWebSocket();
            }
          }, delay);
        }
      }
    };

    connectWebSocket();

    // Monitor connection status
    const statusInterval = setInterval(() => {
      if (mounted) {
        const state = websocketService.getConnectionState(jobId);
        setConnectionStatus(state);
      }
    }, 1000);

    return () => {
      mounted = false;
      if (unsubscribe) {
        unsubscribe();
      }
      websocketService.disconnect(jobId);
      clearInterval(statusInterval);
    };
  }, [jobId]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    setLastUpdate(new Date().toLocaleTimeString());
    
    switch (message.type) {
      case 'progress':
      case 'stage_change':
        if (message.data.stage) {
          setCurrentStage(message.data.stage);
        }
        if (message.data.estimated_completion) {
          setEstimatedCompletion(message.data.estimated_completion);
        }
        break;
        
      case 'completed':
        setConnectionStatus('disconnected');
        onComplete?.(message.job_id);
        break;
        
      case 'failed':
        setErrorDetails(message.data.error_details || message.data.error || 'Unknown error occurred');
        setConnectionStatus('disconnected');
        break;
    }
  }, [onComplete]);

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
          websocketService.disconnect(jobId);
          onCancel?.(jobId);
        } catch (error) {
          console.error('Failed to cancel job:', error);
        }
      }
    });
  }, [jobId, deleteJob, dispatch, onCancel]);

  // Retry connection
  const handleRetryConnection = useCallback(async () => {
    try {
      setConnectionStatus('connecting');
      setReconnectAttempt(0);
      await websocketService.connect(jobId);
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Failed to reconnect:', error);
      setConnectionStatus('error');
    }
  }, [jobId]);

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
              <Tag color="green">Live Updates (WebSocket)</Tag>
            )}
            {connectionStatus === 'connecting' && (
              <Tag color="blue">Connecting...</Tag>
            )}
            {reconnectAttempt > 0 && connectionStatus === 'connecting' && (
              <Tag color="orange">Reconnecting (Attempt {reconnectAttempt})</Tag>
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
        {(connectionStatus === 'error' || connectionStatus === 'disconnected') && (
          <Alert
            message="Connection Lost"
            description={`WebSocket connection to progress updates was lost. ${reconnectAttempt > 0 ? `Reconnection attempt ${reconnectAttempt}...` : 'Click Retry to reconnect.'}`}
            type="warning"
            showIcon
            action={
              <Button size="small" onClick={handleRetryConnection}>
                Retry Connection
              </Button>
            }
          />
        )}

        {/* Last Update Time and Connection Info */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
          {lastUpdate && connectionStatus === 'connected' && (
            <Text type="secondary" style={{ fontSize: '11px' }}>
              Last update: {lastUpdate}
            </Text>
          )}
          <Text type="secondary" style={{ fontSize: '10px' }}>
            Connection: {connectionStatus}
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default ProgressTracker;