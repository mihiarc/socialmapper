/**
 * Dashboard page - Enhanced demo platform landing page with instant access
 * No-registration required, <5 minute time to first analysis
 */
import React, { useState } from 'react';
import { Row, Col, Card, Button, Typography, Space, Statistic, List, Badge, Carousel, Tag, Progress, Tooltip } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  PlusOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  PlayCircleOutlined,
  RocketOutlined,
  ThunderboltOutlined,
  GlobalOutlined,
  TeamOutlined,
  SafetyOutlined,
  DashboardOutlined,
  FileSearchOutlined,
  EnvironmentOutlined,
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
  const [hoveredDemo, setHoveredDemo] = useState<number | null>(null);

  // Demo scenarios for instant access
  const demoScenarios = [
    {
      id: 1,
      title: 'Healthcare Access Analysis',
      description: 'Analyze hospital and clinic accessibility in urban areas',
      icon: <SafetyOutlined style={{ fontSize: 32, color: '#52c41a' }} />,
      duration: '2-3 min',
      difficulty: 'Easy',
      tags: ['Healthcare', 'Urban Planning'],
      color: '#52c41a',
      action: () => navigate('/demo?scenario=healthcare')
    },
    {
      id: 2,
      title: 'Food Desert Detection',
      description: 'Identify areas with limited grocery store access',
      icon: <FileSearchOutlined style={{ fontSize: 32, color: '#fa8c16' }} />,
      duration: '3-4 min',
      difficulty: 'Medium',
      tags: ['Food Security', 'Demographics'],
      color: '#fa8c16',
      action: () => navigate('/demo?scenario=food')
    },
    {
      id: 3,
      title: 'Public Transit Coverage',
      description: 'Evaluate public transportation accessibility',
      icon: <GlobalOutlined style={{ fontSize: 32, color: '#1890ff' }} />,
      duration: '2-3 min',
      difficulty: 'Easy',
      tags: ['Transportation', 'Equity'],
      color: '#1890ff',
      action: () => navigate('/demo?scenario=transit')
    },
    {
      id: 4,
      title: 'Education Access Study',
      description: 'Map school and library accessibility for families',
      icon: <TeamOutlined style={{ fontSize: 32, color: '#722ed1' }} />,
      duration: '3-4 min',
      difficulty: 'Medium',
      tags: ['Education', 'Family Services'],
      color: '#722ed1',
      action: () => navigate('/demo?scenario=education')
    },
    {
      id: 5,
      title: 'Park & Recreation Access',
      description: 'Analyze green space accessibility for communities',
      icon: <EnvironmentOutlined style={{ fontSize: 32, color: '#52c41a' }} />,
      duration: '2-3 min',
      difficulty: 'Easy',
      tags: ['Recreation', 'Health'],
      color: '#52c41a',
      action: () => navigate('/demo?scenario=parks')
    }
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
    <div style={{ padding: '24px', minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      {/* Hero Section with Enhanced Visual Appeal */}
      <div style={{ 
        marginBottom: '48px', 
        textAlign: 'center',
        padding: '48px 24px',
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '16px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.1)'
      }}>
        <Space direction="vertical" size="large">
          <div>
            <Badge.Ribbon text="No Registration Required" color="green">
              <Title level={1} style={{ 
                marginBottom: '8px',
                fontSize: window.innerWidth <= 768 ? '32px' : '48px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>
                SocialMapper Platform
              </Title>
            </Badge.Ribbon>
          </div>
          
          <Paragraph style={{ 
            fontSize: window.innerWidth <= 768 ? '16px' : '20px', 
            color: '#444', 
            maxWidth: '800px', 
            margin: '0 auto',
            lineHeight: 1.6
          }}>
            Transform complex geospatial data into actionable insights.
            <br />
            <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
              Start your first analysis in under 5 minutes - no technical expertise required.
            </Text>
          </Paragraph>

          <Space size="large" wrap>
            <Button 
              type="primary" 
              size="large"
              icon={<RocketOutlined />}
              onClick={() => navigate('/demo')}
              style={{ 
                minWidth: '200px',
                height: '50px',
                fontSize: '16px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none'
              }}
            >
              Try Demo Now
            </Button>
            <Button 
              size="large"
              icon={<PlusOutlined />}
              onClick={() => navigate('/analysis')}
              style={{ 
                minWidth: '200px',
                height: '50px',
                fontSize: '16px'
              }}
            >
              Custom Analysis
            </Button>
          </Space>

          <div style={{ marginTop: '24px' }}>
            <Space split="|" size="large">
              <Statistic 
                value="< 5 min" 
                valueStyle={{ color: '#52c41a', fontSize: '20px' }}
                prefix={<ClockCircleOutlined />}
                title="Time to Insights"
              />
              <Statistic 
                value="0" 
                valueStyle={{ color: '#1890ff', fontSize: '20px' }}
                prefix="$"
                title="Cost to Start"
              />
              <Statistic 
                value="100%" 
                valueStyle={{ color: '#722ed1', fontSize: '20px' }}
                prefix={<CheckCircleOutlined />}
                title="No Code"
              />
            </Space>
          </div>
        </Space>
      </div>

      {/* Quick Access Demo Scenarios */}
      <div style={{ marginBottom: '48px' }}>
        <Card 
          title={
            <Space>
              <ThunderboltOutlined style={{ color: '#fa8c16' }} />
              <span>Quick Start: Pre-Built Demo Scenarios</span>
            </Space>
          }
          extra={
            <Button type="link" onClick={() => navigate('/demo')}>
              View All Demos →
            </Button>
          }
          style={{ borderRadius: '12px' }}
        >
          <Row gutter={[16, 16]}>
            {demoScenarios.map((demo) => (
              <Col xs={24} sm={12} lg={8} xl={6} key={demo.id}>
                <Card
                  hoverable
                  style={{ 
                    height: '280px',
                    borderRadius: '8px',
                    transform: hoveredDemo === demo.id ? 'translateY(-4px)' : 'none',
                    transition: 'all 0.3s',
                    borderTop: `3px solid ${demo.color}`
                  }}
                  onMouseEnter={() => setHoveredDemo(demo.id)}
                  onMouseLeave={() => setHoveredDemo(null)}
                  onClick={demo.action}
                  bodyStyle={{ 
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%'
                  }}
                >
                  <Space direction="vertical" style={{ flex: 1, width: '100%' }}>
                    <div style={{ textAlign: 'center', marginBottom: '12px' }}>
                      {demo.icon}
                    </div>
                    
                    <Title level={5} style={{ 
                      margin: '0 0 8px 0',
                      textAlign: 'center',
                      minHeight: '48px'
                    }}>
                      {demo.title}
                    </Title>
                    
                    <Text type="secondary" style={{ 
                      fontSize: '12px',
                      textAlign: 'center',
                      flex: 1
                    }}>
                      {demo.description}
                    </Text>
                    
                    <div style={{ marginTop: 'auto' }}>
                      <Space wrap size={4}>
                        {demo.tags.map(tag => (
                          <Tag key={tag} style={{ fontSize: '10px' }}>
                            {tag}
                          </Tag>
                        ))}
                      </Space>
                    </div>
                    
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginTop: '12px',
                      paddingTop: '12px',
                      borderTop: '1px solid #f0f0f0'
                    }}>
                      <Space size={4}>
                        <ClockCircleOutlined style={{ fontSize: '12px' }} />
                        <Text style={{ fontSize: '12px' }}>{demo.duration}</Text>
                      </Space>
                      <Tag color={demo.difficulty === 'Easy' ? 'green' : 'orange'}>
                        {demo.difficulty}
                      </Tag>
                    </div>
                  </Space>
                  
                  {hoveredDemo === demo.id && (
                    <Button 
                      type="primary" 
                      block 
                      style={{ marginTop: '12px' }}
                      icon={<PlayCircleOutlined />}
                    >
                      Start Demo
                    </Button>
                  )}
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      </div>

      {/* How It Works - Visual Steps */}
      <Card 
        title="How It Works" 
        style={{ marginBottom: '32px', borderRadius: '12px' }}
        extra={
          <Tag color="green">No Registration Required</Tag>
        }
      >
        <Row gutter={[24, 24]}>
          {[
            {
              step: 1,
              title: 'Select Location',
              description: 'Click on a map or search for any US address',
              icon: <EnvironmentOutlined style={{ fontSize: '32px', color: '#1890ff' }} />,
              duration: '30 seconds'
            },
            {
              step: 2,
              title: 'Choose POIs',
              description: 'Select places of interest (hospitals, schools, parks)',
              icon: <DashboardOutlined style={{ fontSize: '32px', color: '#52c41a' }} />,
              duration: '1 minute'
            },
            {
              step: 3,
              title: 'Set Parameters',
              description: 'Configure travel time, mode, and demographics',
              icon: <BarChartOutlined style={{ fontSize: '32px', color: '#fa8c16' }} />,
              duration: '1 minute'
            },
            {
              step: 4,
              title: 'Get Results',
              description: 'View interactive maps and download data',
              icon: <CheckCircleOutlined style={{ fontSize: '32px', color: '#722ed1' }} />,
              duration: '2-3 minutes'
            }
          ].map((item) => (
            <Col xs={24} sm={12} lg={6} key={item.step}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ 
                  width: '80px', 
                  height: '80px', 
                  margin: '0 auto 16px',
                  borderRadius: '50%',
                  background: '#f0f0f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {item.icon}
                </div>
                <Tag color="blue" style={{ marginBottom: '8px' }}>
                  Step {item.step}
                </Tag>
                <Title level={5}>{item.title}</Title>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {item.description}
                </Text>
                <div style={{ marginTop: '8px' }}>
                  <Text style={{ fontSize: '11px', color: '#52c41a' }}>
                    <ClockCircleOutlined /> {item.duration}
                  </Text>
                </div>
              </div>
            </Col>
          ))}
        </Row>
        
        <div style={{ marginTop: '32px', textAlign: 'center' }}>
          <Progress 
            percent={100} 
            steps={4}
            strokeColor="#52c41a"
            format={() => 'Total: < 5 minutes'}
          />
        </div>
      </Card>

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

      {/* Call to Action */}
      <Card 
        style={{ 
          marginTop: '32px',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '12px',
          border: 'none'
        }}
        bodyStyle={{ padding: '48px 24px', textAlign: 'center' }}
      >
        <Space direction="vertical" size="large">
          <Title level={2} style={{ color: 'white', margin: 0 }}>
            Ready to Transform Your Spatial Analysis?
          </Title>
          <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '18px' }}>
            Join thousands of researchers, planners, and analysts using SocialMapper
          </Text>
          <Space size="large" wrap>
            <Button 
              type="primary"
              size="large"
              icon={<RocketOutlined />}
              onClick={() => navigate('/demo')}
              style={{ 
                minWidth: '180px',
                height: '48px',
                fontSize: '16px',
                background: 'white',
                color: '#764ba2',
                border: 'none'
              }}
            >
              Try Demo Instantly
            </Button>
            <Button 
              size="large"
              ghost
              onClick={() => navigate('/analysis')}
              style={{ 
                minWidth: '180px',
                height: '48px',
                fontSize: '16px',
                borderColor: 'white',
                color: 'white'
              }}
            >
              Start Custom Analysis
            </Button>
          </Space>
          <div style={{ marginTop: '24px' }}>
            <Space split={<span style={{ color: 'rgba(255,255,255,0.5)' }}>|</span>} size="large">
              <Text style={{ color: 'white' }}>
                <CheckCircleOutlined /> No Sign-up Required
              </Text>
              <Text style={{ color: 'white' }}>
                <ThunderboltOutlined /> Results in Minutes
              </Text>
              <Text style={{ color: 'white' }}>
                <SafetyOutlined /> Secure & Private
              </Text>
            </Space>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default Dashboard;