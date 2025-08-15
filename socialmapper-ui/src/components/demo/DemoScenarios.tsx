import React, { useState, useEffect } from 'react';
import { Card, Button, Row, Col, Spin, Alert, Badge, Statistic, Modal, Progress } from 'antd';
import {
  PlayCircleOutlined,
  ClockCircleOutlined,
  EnvironmentOutlined,
  TeamOutlined,
  InfoCircleOutlined,
  RocketOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@services/api';
import { performanceMonitor } from '@utils/performance';

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  city: string;
  estimated_runtime: number;
}

interface ScenarioInsights {
  key_metrics: {
    [key: string]: string | number;
  };
  key_findings: string[];
}

export const DemoScenarios: React.FC = () => {
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningScenario, setRunningScenario] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<DemoScenario | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadScenarios();
  }, []);

  const loadScenarios = async () => {
    try {
      const response = await apiClient.get('/api/v1/demo/scenarios');
      setScenarios(response.data);
    } catch (err) {
      setError('Failed to load demo scenarios');
      console.error('Error loading scenarios:', err);
    } finally {
      setLoading(false);
    }
  };

  const runScenario = async (scenario: DemoScenario) => {
    setRunningScenario(scenario.id);
    setSelectedScenario(scenario);
    setProgress(0);
    
    // Track demo usage
    performanceMonitor.recordFeatureUsage('demo-scenario', {
      scenario_id: scenario.id,
      scenario_name: scenario.name
    });

    try {
      // Start progress simulation
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + (90 / scenario.estimated_runtime) * 2;
        });
      }, 2000);

      // Run the scenario
      const response = await apiClient.post(`/api/v1/demo/scenarios/${scenario.id}/run`);
      
      clearInterval(progressInterval);
      setProgress(100);

      // Navigate to results with the data
      setTimeout(() => {
        navigate('/results', { 
          state: { 
            results: response.data,
            isDemo: true,
            scenarioName: scenario.name 
          }
        });
      }, 500);

    } catch (err) {
      setError(`Failed to run scenario: ${err.message}`);
      setRunningScenario(null);
      setProgress(0);
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'food-access': '#52c41a',
      'education': '#1890ff',
      'healthcare': '#ff4d4f',
      'recreation': '#52c41a',
      'transportation': '#722ed1'
    };
    return colors[category] || '#1890ff';
  };

  const getCategoryIcon = (category: string) => {
    const icons: { [key: string]: React.ReactNode } = {
      'food-access': '🍎',
      'education': '🏫',
      'healthcare': '🏥',
      'recreation': '🌳',
      'transportation': '🚌'
    };
    return icons[category] || '📍';
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="Loading demo scenarios..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error"
        description={error}
        type="error"
        showIcon
        closable
        onClose={() => setError(null)}
      />
    );
  }

  return (
    <>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ marginBottom: 8 }}>
          <RocketOutlined /> Demo Scenarios
        </h2>
        <p style={{ color: '#666', fontSize: 16 }}>
          Experience SocialMapper with real-world equity analyses. 
          Each demo takes less than a minute and requires no setup!
        </p>
      </div>

      <Row gutter={[16, 16]}>
        {scenarios.map(scenario => (
          <Col xs={24} sm={12} lg={8} key={scenario.id}>
            <Card
              hoverable
              style={{ height: '100%', position: 'relative' }}
              actions={[
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  loading={runningScenario === scenario.id}
                  onClick={() => runScenario(scenario)}
                  disabled={runningScenario !== null && runningScenario !== scenario.id}
                >
                  {runningScenario === scenario.id ? 'Running...' : 'Run Demo'}
                </Button>
              ]}
            >
              <Badge.Ribbon 
                text={scenario.category.replace('-', ' ').toUpperCase()} 
                color={getCategoryColor(scenario.category)}
              >
                <Card.Meta
                  avatar={
                    <div style={{ fontSize: 32 }}>
                      {scenario.icon}
                    </div>
                  }
                  title={
                    <div>
                      <h3 style={{ marginBottom: 4 }}>{scenario.name}</h3>
                      <div style={{ fontSize: 12, color: '#999' }}>
                        <EnvironmentOutlined /> {scenario.city}
                      </div>
                    </div>
                  }
                  description={
                    <div>
                      <p style={{ marginBottom: 12 }}>{scenario.description}</p>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: 12, color: '#666' }}>
                          <ClockCircleOutlined /> ~{scenario.estimated_runtime}s
                        </span>
                        <span style={{ fontSize: 12, color: '#666' }}>
                          <TeamOutlined /> High Impact
                        </span>
                      </div>
                    </div>
                  }
                />
              </Badge.Ribbon>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Quick Stats */}
      <Row gutter={16} style={{ marginTop: 32 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Total Demos"
              value={scenarios.length}
              prefix={<InfoCircleOutlined />}
              suffix="scenarios"
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Average Runtime"
              value={Math.round(scenarios.reduce((acc, s) => acc + s.estimated_runtime, 0) / scenarios.length)}
              prefix={<ClockCircleOutlined />}
              suffix="seconds"
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Cities Covered"
              value={new Set(scenarios.map(s => s.city)).size}
              prefix={<EnvironmentOutlined />}
              suffix="locations"
            />
          </Card>
        </Col>
      </Row>

      {/* Progress Modal */}
      <Modal
        visible={runningScenario !== null}
        footer={null}
        closable={false}
        centered
      >
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <h3>{selectedScenario?.name}</h3>
          <p style={{ color: '#666', marginBottom: 24 }}>
            Running analysis for {selectedScenario?.city}...
          </p>
          <Progress 
            percent={progress} 
            status="active"
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
          <p style={{ marginTop: 16, fontSize: 12, color: '#999' }}>
            This demo uses pre-computed data for instant results
          </p>
        </div>
      </Modal>
    </>
  );
};