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
  Tag
} from 'antd';
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';

import FeedbackTrigger from '@components/feedback/FeedbackTrigger';
import { useAnalytics } from '@hooks/useAnalytics';
import ResultsDashboard from '@components/results/ResultsDashboard';

import { 
  useGetJobStatusQuery, 
  useGetResultsQuery
} from '@store/api/analysisApi';

const { Title, Text, Paragraph } = Typography;

/**
 * Results page showing analysis progress and completed results
 */
const Results: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
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
        <>
          {/* Integrated Results Dashboard */}
          {isResultsLoading ? (
            <Card>
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin size="large" />
                <Title level={4} style={{ marginTop: '16px' }}>
                  Loading Results
                </Title>
                <Paragraph type="secondary">
                  Fetching your analysis results...
                </Paragraph>
              </div>
            </Card>
          ) : resultsError ? (
            <Card>
              <Alert
                type="error"
                message="Failed to load results"
                description="There was an error loading your analysis results. Please try again."
                action={
                  <Button size="small" onClick={() => refetchResults()}>
                    Retry
                  </Button>
                }
              />
            </Card>
          ) : (
            <ResultsDashboard 
              jobId={jobId!} 
              onShare={(shareUrl) => {
                trackEvent({
                  event_name: 'results_shared',
                  event_category: 'interaction',
                  properties: {
                    jobId,
                    shareUrl,
                  },
                });
                trackJourneyStep('results_shared');
              }}
            />
          )}

          {/* Additional Feedback Section */}
          <Row gutter={[24, 24]} style={{ marginTop: '24px' }}>
            <Col xs={24}>
              <Card>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Title level={4}>How was your experience?</Title>
                  <Paragraph type="secondary">
                    Your feedback helps us improve SocialMapper for all users.
                  </Paragraph>
                  <Space wrap>
                    <FeedbackTrigger
                      touchpoint="results_dashboard"
                      context={{
                        jobId: jobId!,
                        featureUsed: 'results_view',
                      }}
                      trigger="button"
                      type="primary"
                      text="Rate Results Quality"
                      tooltip="How helpful are these results?"
                    />
                    <FeedbackTrigger
                      touchpoint="export_download"
                      context={{
                        jobId: jobId!,
                        featureUsed: 'export',
                      }}
                      trigger="button"
                      type="default"
                      text="Rate Export Options"
                      tooltip="How was the export process?"
                    />
                    <Button 
                      onClick={() => navigate('/query')}
                    >
                      Run Another Analysis
                    </Button>
                  </Space>
                </Space>
              </Card>
            </Col>
          </Row>
        </>
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