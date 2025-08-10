/**
 * Dashboard page - landing page with overview and quick actions
 */
import React from 'react';
import { Row, Col, Card, Button, Typography, Space, Statistic, List, Badge } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  PlusOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';

import type { RootState } from '@store/index';
import { useGetAllJobsQuery } from '@store/api/analysisApi';

const { Title, Text, Paragraph } = Typography;

/**
 * Dashboard with overview, quick actions, and recent activity
 */
const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { activeJobs, recentAnalyses } = useSelector((state: RootState) => state.analysis);
  const { data: allJobsData } = useGetAllJobsQuery();

  const quickActions = [
    {
      title: 'Start New Analysis',
      description: 'Configure and run a custom accessibility analysis',
      icon: <PlusOutlined />,
      action: () => navigate('/analysis'),
      type: 'primary',
    },
    {
      title: 'Try Demo Scenarios',
      description: 'Explore pre-built scenarios with instant results',
      icon: <ExperimentOutlined />,
      action: () => navigate('/demo'),
      type: 'default',
    },
  ];

  const features = [
    'Census demographic data integration',
    'Point of Interest (POI) discovery and analysis', 
    'Travel time and accessibility calculations',
    'Geospatial analysis and mapping',
    'Multiple export formats (CSV, GeoJSON, Parquet)',
    'Real-time progress tracking',
  ];

  return (
    <div style={{ padding: '24px', minHeight: '100vh', background: '#f5f5f5' }}>
      {/* Header Section */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <Title level={1} style={{ marginBottom: '8px' }}>
          Welcome to SocialMapper
        </Title>
        <Paragraph style={{ fontSize: '16px', color: '#666', maxWidth: '600px', margin: '0 auto' }}>
          Analyze point of interest accessibility and demographics with powerful geospatial tools.
          Create meaningful insights in under 5 minutes.
        </Paragraph>
      </div>

      {/* Quick Actions */}
      <Row gutter={[24, 24]} style={{ marginBottom: '32px' }}>
        {quickActions.map((action, index) => (
          <Col xs={24} md={12} key={index}>
            <Card
              hoverable
              style={{ height: '150px', cursor: 'pointer' }}
              onClick={action.action}
            >
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div style={{ fontSize: '32px', color: '#1890ff' }}>
                  {action.icon}
                </div>
                <Title level={4} style={{ margin: 0 }}>
                  {action.title}
                </Title>
                <Text type="secondary">
                  {action.description}
                </Text>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Statistics Row */}
      <Row gutter={[24, 24]} style={{ marginBottom: '32px' }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Active Jobs"
              value={activeJobs.length}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Completed Analyses"
              value={recentAnalyses.length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Success Rate"
              value={95}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Content Row */}
      <Row gutter={[24, 24]}>
        {/* Active Jobs Panel */}
        <Col xs={24} lg={12}>
          <Card
            title="Active Jobs"
            extra={
              activeJobs.length > 0 && (
                <Badge count={activeJobs.length} />
              )
            }
          >
            {activeJobs.length === 0 ? (
              <Text type="secondary">No active jobs running</Text>
            ) : (
              <List
                dataSource={activeJobs.slice(0, 5)}
                renderItem={(job) => (
                  <List.Item
                    key={job.id}
                    actions={[
                      <Button
                        key="view"
                        type="link"
                        size="small"
                        onClick={() => navigate(`/results/${job.id}`)}
                      >
                        View
                      </Button>
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <Text code>{job.id.slice(0, 8)}...</Text>
                          <Badge status={job.status === 'running' ? 'processing' : 'default'} text={job.status} />
                        </Space>
                      }
                      description={`Progress: ${Math.round(job.progress * 100)}%`}
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>

        {/* Platform Features */}
        <Col xs={24} lg={12}>
          <Card title="Platform Features">
            <List
              dataSource={features}
              renderItem={(feature) => (
                <List.Item style={{ padding: '8px 0' }}>
                  <Space>
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                    <Text>{feature}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* Getting Started Section */}
      <Card
        style={{ marginTop: '32px' }}
        title="Getting Started"
      >
        <Row gutter={[24, 24]}>
          <Col xs={24} md={8}>
            <Space direction="vertical" size="small">
              <Title level={5}>1. Choose Your Analysis Type</Title>
              <Text type="secondary">
                Select from POI analysis, custom locations, or demographic studies
              </Text>
            </Space>
          </Col>
          <Col xs={24} md={8}>
            <Space direction="vertical" size="small">
              <Title level={5}>2. Configure Parameters</Title>
              <Text type="secondary">
                Set travel time, mode, census variables, and analysis area
              </Text>
            </Space>
          </Col>
          <Col xs={24} md={8}>
            <Space direction="vertical" size="small">
              <Title level={5}>3. View Results</Title>
              <Text type="secondary">
                Explore interactive maps, export data, and share findings
              </Text>
            </Space>
          </Col>
        </Row>
        
        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <Button
            type="primary"
            size="large"
            icon={<BarChartOutlined />}
            onClick={() => navigate('/analysis')}
          >
            Start Your First Analysis
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;