/**
 * Real-time progress tracking panel
 * Shows active analysis jobs with progress indicators
 */
import React from 'react';
import { Card, Progress, List, Badge, Button, Space, Typography, Divider } from 'antd';
import { useSelector, useDispatch } from 'react-redux';
import {
  CloseOutlined,
  ReloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';

import type { RootState } from '@store/index';
import { hideProgressPanel } from '@store/slices/uiSlice';
import { removeActiveJob } from '@store/slices/analysisSlice';
import { useDeleteAnalysisJobMutation } from '@store/api/analysisApi';

const { Text, Title } = Typography;

/**
 * Floating panel showing real-time progress for active analysis jobs
 */
const ProgressPanel: React.FC = () => {
  const dispatch = useDispatch();
  const { activeJobs } = useSelector((state: RootState) => state.analysis);
  const [deleteJob] = useDeleteAnalysisJobMutation();

  const handleClose = () => {
    dispatch(hideProgressPanel());
  };

  const handleDeleteJob = async (jobId: string) => {
    try {
      await deleteJob(jobId).unwrap();
      dispatch(removeActiveJob(jobId));
    } catch (error) {
      console.error('Failed to delete job:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'running':
        return <ReloadOutlined spin style={{ color: '#1890ff' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'processing';
      default:
        return 'default';
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: '80px',
        right: '24px',
        width: '400px',
        maxHeight: '60vh',
        zIndex: 1000,
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
      }}
    >
      <Card
        title={
          <Space>
            <Title level={5} style={{ margin: 0 }}>
              Active Analysis Jobs
            </Title>
            <Badge count={activeJobs.length} />
          </Space>
        }
        extra={
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={handleClose}
            size="small"
          />
        }
        size="small"
      >
        {activeJobs.length === 0 ? (
          <Text type="secondary">No active jobs</Text>
        ) : (
          <List
            size="small"
            dataSource={activeJobs}
            renderItem={(job) => (
              <List.Item
                key={job.id}
                style={{ padding: '8px 0' }}
                actions={[
                  <Button
                    key="view"
                    type="text"
                    icon={<EyeOutlined />}
                    size="small"
                    onClick={() => window.open(`/results/${job.id}`, '_blank')}
                  />,
                  <Button
                    key="delete"
                    type="text"
                    icon={<DeleteOutlined />}
                    size="small"
                    danger
                    onClick={() => handleDeleteJob(job.id)}
                  />,
                ]}
              >
                <List.Item.Meta
                  avatar={getStatusIcon(job.status)}
                  title={
                    <Space>
                      <Text strong style={{ fontSize: '12px' }}>
                        {job.id.slice(0, 8)}...
                      </Text>
                      <Badge status={getStatusColor(job.status) as any} text={job.status} />
                    </Space>
                  }
                  description={
                    <div>
                      <Progress
                        percent={Math.round(job.progress * 100)}
                        size="small"
                        status={job.status === 'failed' ? 'exception' : 'active'}
                        style={{ marginBottom: '4px' }}
                      />
                      <Text type="secondary" style={{ fontSize: '11px' }}>
                        {job.message || 'Processing...'}
                      </Text>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )}

        <Divider style={{ margin: '12px 0' }} />
        
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            Updates every 2 seconds
          </Text>
          <Button
            type="link"
            size="small"
            onClick={() => window.location.reload()}
            style={{ padding: 0, fontSize: '11px' }}
          >
            Refresh All
          </Button>
        </Space>
      </Card>
    </div>
  );
};

export default ProgressPanel;