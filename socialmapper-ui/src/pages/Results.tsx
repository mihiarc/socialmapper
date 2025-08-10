/**
 * Results page - Display analysis results with interactive visualizations
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Row, 
  Col, 
  Card, 
  Button, 
  Typography, 
  Space, 
  Progress, 
  Alert, 
  Spin,
  Statistic,
  Tag,
  Descriptions
} from 'antd';
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';

import FeedbackTrigger from '@components/feedback/FeedbackTrigger';
import { useAnalytics } from '@hooks/useAnalytics';
import ResultsDashboard from '@components/results/ResultsDashboard';

import { 
  useGetJobStatusQuery, 
  useGetResultsQuery,
  useExportResultsMutation 
} from '@store/api/analysisApi';
import type { ExportFormat } from '@types/api';

const { Title, Text, Paragraph } = Typography;

/**
 * Results page showing analysis progress and completed results
 */
const Results: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [exportResults] = useExportResultsMutation();
  const { trackEvent, trackConversion, trackError, trackJourneyStep } = useAnalytics();

  // State to control polling
  const [shouldPoll, setShouldPoll] = useState(true);

  // Poll job status every 2 seconds for active jobs
  const {
    data: jobStatus,
    isLoading: isStatusLoading,
    error: statusError,
    refetch: refetchStatus
  } = useGetJobStatusQuery(jobId!, {
    pollingInterval: shouldPoll ? 2000 : 0,
    skip: !jobId,
  });

  // Stop polling when job is completed or failed
  useEffect(() => {
    if (jobStatus?.status && ['completed', 'failed', 'cancelled'].includes(jobStatus.status)) {
      setShouldPoll(false);
    }
  }, [jobStatus?.status]);

  // Only fetch results if job is completed
  const {
    data: results,
    isLoading: isResultsLoading,
    error: resultsError,
    refetch: refetchResults
  } = useGetResultsQuery(jobId!, {
    skip: !jobId || jobStatus?.status !== 'completed',
  });

  const handleExport = async (format: ExportFormat) => {
    if (!jobId) return;
    
    try {
      trackJourneyStep('export_started');
      
      const blob = await exportResults({
        jobId,
        format,
        includeIsochrones: true,
        includeDemographics: true,
      }).unwrap();
      
      // Download the file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `socialmapper_results_${jobId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      trackConversion('export_completed', 1);
      trackJourneyStep('export_completed');
    } catch (error) {
      console.error('Export failed:', error);
      trackError('export_failed', { format, jobId, error: error.toString() });
    }
  };

  if (!jobId) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert type="error" message="Invalid job ID" />
      </div>
    );
  }

  if (isStatusLoading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
        <Text style={{ display: 'block', marginTop: '16px' }}>
          Loading job status...
        </Text>
      </div>
    );
  }

  if (statusError) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          type="error"
          message="Failed to load job status"
          action={
            <Button size="small" onClick={() => refetchStatus()}>
              Retry
            </Button>
          }
        />
      </div>
    );
  }

  const isActive = jobStatus?.status === 'pending' || jobStatus?.status === 'running';
  const isCompleted = jobStatus?.status === 'completed';
  const isFailed = jobStatus?.status === 'failed';

  return (
    <div style={{ padding: '24px', minHeight: '100vh', background: '#f5f5f5' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Space>
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate('/')}
          >
            Back to Dashboard
          </Button>
          <Title level={3} style={{ margin: 0 }}>
            Analysis Results
          </Title>
          <Text code>{jobId}</Text>
        </Space>
      </div>

      {/* Job Status Card */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[24, 24]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Space direction="vertical" size="small">
              <Text strong>Status</Text>
              <Space>
                {isActive && <ReloadOutlined spin />}
                {isCompleted && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                {isFailed && <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
                <Tag color={
                  isCompleted ? 'success' : 
                  isFailed ? 'error' : 
                  isActive ? 'processing' : 'default'
                }>
                  {jobStatus?.status.toUpperCase()}
                </Tag>
              </Space>
            </Space>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text strong>Progress</Text>
              <Progress 
                percent={Math.round((jobStatus?.progress || 0) * 100)}
                status={isFailed ? 'exception' : isCompleted ? 'success' : 'active'}
                size="small"
              />
            </Space>
          </Col>
          
          <Col xs={24} md={8}>
            <Space direction="vertical" size="small">
              <Text strong>Created</Text>
              <Text type="secondary">
                {jobStatus?.created_at ? new Date(jobStatus.created_at).toLocaleString() : 'Unknown'}
              </Text>
            </Space>
          </Col>
        </Row>

        {jobStatus?.message && (
          <div style={{ marginTop: '16px' }}>
            <Text type="secondary">
              {jobStatus.message}
            </Text>
          </div>
        )}

        {isFailed && jobStatus?.error && (
          <Alert
            type="error"
            message="Analysis Failed"
            description={jobStatus.error}
            style={{ marginTop: '16px' }}
          />
        )}
      </Card>

      {/* Results Content */}
      {isActive && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <Title level={4} style={{ marginTop: '16px' }}>
              Analysis in Progress
            </Title>
            <Paragraph type="secondary">
              Your analysis is being processed. This page will automatically update when complete.
            </Paragraph>
            <Progress 
              percent={Math.round((jobStatus?.progress || 0) * 100)}
              style={{ maxWidth: '300px', margin: '0 auto' }}
            />
          </div>
        </Card>
      )}

      {isCompleted && (
        <Row gutter={[24, 24]}>
          {/* Results Summary */}
          <Col xs={24} lg={16}>
            <Card 
              title="Analysis Summary" 
              loading={isResultsLoading}
              extra={
                <Space>
                  <FeedbackTrigger
                    touchpoint="results_dashboard"
                    context={{
                      jobId: jobId!,
                      featureUsed: 'results_view',
                    }}
                    trigger="button"
                    type="text"
                    size="small"
                    text="Rate Results"
                    tooltip="How helpful are these results?"
                  />
                  <Button 
                    icon={<ReloadOutlined />}
                    onClick={() => refetchResults()}
                  >
                    Refresh
                  </Button>
                </Space>
              }
            >
              {results ? (
                <Row gutter={[16, 16]}>
                  <Col xs={24} sm={8}>
                    <Statistic
                      title="POIs Found"
                      value={results.poi_count || 0}
                      suffix="locations"
                    />
                  </Col>
                  <Col xs={24} sm={8}>
                    <Statistic
                      title="Analysis Area"
                      value={results.analysis_area_km2 || 0}
                      suffix="km²"
                      precision={2}
                    />
                  </Col>
                  <Col xs={24} sm={8}>
                    <Statistic
                      title="Population Covered"
                      value={results.population_covered || 0}
                      suffix="people"
                    />
                  </Col>
                </Row>
              ) : (
                <Text type="secondary">No summary data available</Text>
              )}
            </Card>

            {/* Map Visualization */}
            <Card title="Map Visualization" style={{ marginTop: '24px' }}>
              <div style={{ 
                height: '400px', 
                background: '#f5f5f5', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                border: '1px dashed #d9d9d9',
                borderRadius: '6px'
              }}>
                <Text type="secondary">Interactive map visualization coming soon</Text>
              </div>
            </Card>
          </Col>

          {/* Export and Actions */}
          <Col xs={24} lg={8}>
            <Card title="Export Results">
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Button 
                  type="primary" 
                  icon={<DownloadOutlined />}
                  block
                  onClick={() => handleExport('geojson' as ExportFormat)}
                >
                  Download GeoJSON
                </Button>
                <Button 
                  icon={<DownloadOutlined />}
                  block
                  onClick={() => handleExport('csv' as ExportFormat)}
                >
                  Download CSV
                </Button>
                <Button 
                  icon={<DownloadOutlined />}
                  block
                  onClick={() => handleExport('parquet' as ExportFormat)}
                >
                  Download Parquet
                </Button>
                <Button 
                  icon={<ShareAltOutlined />}
                  block
                >
                  Share Results
                </Button>
                
                {/* Export Feedback Trigger */}
                <FeedbackTrigger
                  touchpoint="export_download"
                  context={{
                    jobId: jobId!,
                    featureUsed: 'export',
                  }}
                  trigger="button"
                  type="dashed"
                  text="Rate Export Experience"
                  tooltip="How was the export process?"
                />
              </Space>
            </Card>

            {/* Job Details */}
            <Card title="Job Details" style={{ marginTop: '24px' }}>
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Job ID">
                  <Text code>{jobId}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Processing Time">
                  {results?.processing_time_seconds ? 
                    `${results.processing_time_seconds.toFixed(2)}s` : 
                    'N/A'
                  }
                </Descriptions.Item>
                <Descriptions.Item label="Started">
                  {jobStatus?.started_at ? 
                    new Date(jobStatus.started_at).toLocaleString() : 
                    'N/A'
                  }
                </Descriptions.Item>
                <Descriptions.Item label="Completed">
                  {results?.completed_at ? 
                    new Date(results.completed_at).toLocaleString() : 
                    'N/A'
                  }
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>
        </Row>
      )}

      {/* Auto-triggered Post-Analysis Feedback */}
      {isCompleted && (
        <FeedbackTrigger
          touchpoint="post_analysis"
          context={{
            jobId: jobId!,
            featureUsed: 'analysis_completion',
          }}
          trigger="auto"
          autoTrigger={true}
          autoTriggerDelay={3000} // 3 seconds after results are shown
          title="How was your analysis experience?"
          description="Your feedback helps us improve SocialMapper for researchers and planners like you."
          onFeedbackSubmit={(feedback) => {
            trackEvent({
              event_name: 'feedback_submitted',
              event_category: 'interaction',
              properties: {
                touchpoint: feedback.touchpoint,
                type: feedback.type,
                rating: feedback.rating,
              },
            });
          }}
        />
      )}
    </div>
  );
};

export default Results;