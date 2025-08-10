/**
 * Demo Scenarios page - Project 1.1 requirement
 * Pre-built scenarios for instant demonstration
 */
import React, { useState } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Button, 
  Typography, 
  Space, 
  Tag, 
  Slider, 
  Select, 
  Switch,
  Divider,
  Alert,
  Modal
} from 'antd';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import {
  PlayCircleOutlined,
  SettingOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

import { useSubmitLocationAnalysisMutation } from '@store/api/analysisApi';
import { addActiveJob } from '@store/slices/analysisSlice';
import { showSuccessNotification, showErrorNotification } from '@store/slices/uiSlice';
import { TravelMode, GeographicLevel, type LocationAnalysisRequest } from '@types/api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface DemoScenario {
  id: string;
  title: string;
  description: string;
  category: string;
  location: string;
  poi_type: string;
  poi_name: string;
  defaultTravelTime: number;
  defaultTravelMode: TravelMode;
  tags: string[];
  insights: string[];
  estimatedDuration: string;
}

const demoScenarios: DemoScenario[] = [
  {
    id: 'library_access_denver',
    title: 'Public Library Access in Denver',
    description: 'Analyze accessibility to public libraries in Denver, Colorado with demographic overlays',
    category: 'Education & Culture',
    location: 'Denver, Colorado',
    poi_type: 'amenity',
    poi_name: 'library',
    defaultTravelTime: 15,
    defaultTravelMode: TravelMode.WALK,
    tags: ['Education', 'Public Services', 'Walking Access'],
    insights: [
      'Identify underserved neighborhoods',
      'Compare access by income levels',
      'Evaluate public transit connectivity'
    ],
    estimatedDuration: '2-3 minutes',
  },
  {
    id: 'grocery_access_rural',
    title: 'Grocery Store Access in Rural Areas',
    description: 'Study food accessibility in rural communities with driving analysis',
    category: 'Food Security',
    location: 'Fresno, California',
    poi_type: 'shop',
    poi_name: 'supermarket',
    defaultTravelTime: 30,
    defaultTravelMode: TravelMode.DRIVE,
    tags: ['Food Security', 'Rural Planning', 'Driving Access'],
    insights: [
      'Identify food deserts',
      'Analyze population coverage',
      'Study demographic disparities'
    ],
    estimatedDuration: '3-4 minutes',
  },
  {
    id: 'hospital_access_urban',
    title: 'Hospital Emergency Access',
    description: 'Critical healthcare accessibility analysis in urban areas',
    category: 'Healthcare',
    location: 'Atlanta, Georgia',
    poi_type: 'amenity',
    poi_name: 'hospital',
    defaultTravelTime: 20,
    defaultTravelMode: TravelMode.DRIVE,
    tags: ['Healthcare', 'Emergency Access', 'Urban Planning'],
    insights: [
      'Evaluate emergency response coverage',
      'Identify high-risk areas',
      'Analyze demographic health equity'
    ],
    estimatedDuration: '3-4 minutes',
  },
  {
    id: 'park_access_family',
    title: 'Family Park and Recreation Access',
    description: 'Recreation accessibility for families with children',
    category: 'Recreation',
    location: 'Portland, Oregon',
    poi_type: 'leisure',
    poi_name: 'park',
    defaultTravelTime: 10,
    defaultTravelMode: TravelMode.WALK,
    tags: ['Recreation', 'Family Planning', 'Green Spaces'],
    insights: [
      'Assess family recreation opportunities',
      'Study walkability for children',
      'Evaluate green space equity'
    ],
    estimatedDuration: '2-3 minutes',
  },
  {
    id: 'transit_access_comprehensive',
    title: 'Public Transit Accessibility Study',
    description: 'Comprehensive public transportation access analysis',
    category: 'Transportation',
    location: 'Seattle, Washington',
    poi_type: 'public_transport',
    poi_name: 'bus_stop',
    defaultTravelTime: 5,
    defaultTravelMode: TravelMode.WALK,
    tags: ['Public Transit', 'Transportation Equity', 'Urban Mobility'],
    insights: [
      'Evaluate transit coverage',
      'Identify transit deserts',
      'Study mobility equity'
    ],
    estimatedDuration: '2-3 minutes',
  },
];

/**
 * Demo Scenarios page with parameter adjustment and instant execution
 */
const DemoScenarios: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [submitAnalysis] = useSubmitLocationAnalysisMutation();
  
  const [selectedScenario, setSelectedScenario] = useState<DemoScenario | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isRunning, setIsRunning] = useState<string | null>(null);
  
  // Parameter state for customization
  const [travelTime, setTravelTime] = useState(15);
  const [travelMode, setTravelMode] = useState<TravelMode>(TravelMode.WALK);
  const [includeIsochrones, setIncludeIsochrones] = useState(true);
  const [includeDemographics, setIncludeDemographics] = useState(true);

  const handleScenarioClick = (scenario: DemoScenario) => {
    setSelectedScenario(scenario);
    setTravelTime(scenario.defaultTravelTime);
    setTravelMode(scenario.defaultTravelMode);
    setIsModalVisible(true);
  };

  const handleRunScenario = async () => {
    if (!selectedScenario) return;

    setIsRunning(selectedScenario.id);

    const analysisRequest: LocationAnalysisRequest = {
      location: selectedScenario.location,
      poi_type: selectedScenario.poi_type,
      poi_name: selectedScenario.poi_name,
      travel_time: travelTime,
      travel_mode: travelMode,
      geographic_level: GeographicLevel.BLOCK_GROUP,
      census_variables: ['B01003_001E', 'B19013_001E', 'B25003_001E'], // Population, Income, Housing
      include_isochrones: includeIsochrones,
      include_demographics: includeDemographics,
    };

    try {
      const result = await submitAnalysis(analysisRequest).unwrap();
      
      // Add to active jobs
      dispatch(addActiveJob({
        id: result.job_id,
        status: result.status,
        progress: 0,
        message: 'Analysis started',
        created_at: result.created_at,
        started_at: undefined,
        updated_at: result.created_at,
      }));

      dispatch(showSuccessNotification({
        title: 'Demo Analysis Started',
        message: `${selectedScenario.title} analysis is running. You'll be redirected to view results.`,
      }));

      setIsModalVisible(false);
      navigate(`/results/${result.job_id}`);
    } catch (error) {
      console.error('Failed to submit analysis:', error);
      dispatch(showErrorNotification({
        title: 'Analysis Failed',
        message: 'Failed to start the demo analysis. Please try again.',
      }));
    } finally {
      setIsRunning(null);
    }
  };

  const CategoryColors = {
    'Education & Culture': '#722ed1',
    'Food Security': '#fa8c16',
    'Healthcare': '#f5222d',
    'Recreation': '#52c41a',
    'Transportation': '#1890ff',
  };

  return (
    <div style={{ padding: '24px', minHeight: '100vh', background: '#f5f5f5' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <Title level={2}>Demo Scenarios</Title>
        <Paragraph>
          Explore pre-built analysis scenarios with instant results. 
          Each scenario demonstrates real-world accessibility analysis use cases.
        </Paragraph>
        
        <Alert
          type="info"
          icon={<InfoCircleOutlined />}
          message="Quick Demo Mode"
          description="These scenarios are designed to complete in under 5 minutes with customizable parameters for immediate insights."
          style={{ marginBottom: '24px' }}
        />
      </div>

      {/* Scenarios Grid */}
      <Row gutter={[24, 24]}>
        {demoScenarios.map((scenario) => (
          <Col xs={24} md={12} lg={8} key={scenario.id}>
            <Card
              hoverable
              style={{ height: '100%' }}
              actions={[
                <Button
                  key="run"
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  loading={isRunning === scenario.id}
                  onClick={() => handleScenarioClick(scenario)}
                >
                  Run Scenario
                </Button>,
                <Button
                  key="customize"
                  icon={<SettingOutlined />}
                  onClick={() => handleScenarioClick(scenario)}
                >
                  Customize
                </Button>,
              ]}
            >
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Tag color={CategoryColors[scenario.category as keyof typeof CategoryColors]}>
                    {scenario.category}
                  </Tag>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {scenario.estimatedDuration}
                  </Text>
                </div>
                
                <Title level={4} style={{ margin: '8px 0' }}>
                  {scenario.title}
                </Title>
                
                <Text type="secondary" style={{ fontSize: '13px' }}>
                  {scenario.description}
                </Text>
                
                <div style={{ margin: '12px 0' }}>
                  <Space size={[0, 8]} wrap>
                    {scenario.tags.map((tag) => (
                      <Tag key={tag} size="small">
                        {tag}
                      </Tag>
                    ))}
                  </Space>
                </div>
                
                <div>
                  <Text strong style={{ fontSize: '12px' }}>
                    Location: 
                  </Text>
                  <Text style={{ fontSize: '12px', marginLeft: '4px' }}>
                    {scenario.location}
                  </Text>
                </div>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Parameter Customization Modal */}
      <Modal
        title={selectedScenario?.title}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setIsModalVisible(false)}>
            Cancel
          </Button>,
          <Button
            key="run"
            type="primary"
            icon={<PlayCircleOutlined />}
            loading={isRunning === selectedScenario?.id}
            onClick={handleRunScenario}
          >
            Run Analysis
          </Button>,
        ]}
        width={600}
      >
        {selectedScenario && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div>
              <Text type="secondary">
                {selectedScenario.description}
              </Text>
            </div>

            <Divider />

            {/* Parameter Controls */}
            <div>
              <Title level={5}>Analysis Parameters</Title>
              
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Text strong>Travel Time: {travelTime} minutes</Text>
                  <Slider
                    min={5}
                    max={60}
                    value={travelTime}
                    onChange={setTravelTime}
                    marks={{
                      5: '5m',
                      15: '15m',
                      30: '30m',
                      60: '60m',
                    }}
                  />
                </Col>
                
                <Col span={12}>
                  <Text strong>Travel Mode</Text>
                  <Select
                    value={travelMode}
                    onChange={setTravelMode}
                    style={{ width: '100%', marginTop: '8px' }}
                  >
                    <Option value="walk">Walking</Option>
                    <Option value="bike">Cycling</Option>
                    <Option value="drive">Driving</Option>
                    <Option value="transit">Public Transit</Option>
                  </Select>
                </Col>
              </Row>
              
              <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
                <Col span={12}>
                  <Space>
                    <Text strong>Include Isochrones</Text>
                    <Switch
                      checked={includeIsochrones}
                      onChange={setIncludeIsochrones}
                    />
                  </Space>
                </Col>
                
                <Col span={12}>
                  <Space>
                    <Text strong>Include Demographics</Text>
                    <Switch
                      checked={includeDemographics}
                      onChange={setIncludeDemographics}
                    />
                  </Space>
                </Col>
              </Row>
            </div>

            <Divider />

            {/* Expected Insights */}
            <div>
              <Title level={5}>Expected Insights</Title>
              <ul style={{ margin: 0, paddingLeft: '20px' }}>
                {selectedScenario.insights.map((insight, index) => (
                  <li key={index} style={{ marginBottom: '4px' }}>
                    <Text>{insight}</Text>
                  </li>
                ))}
              </ul>
            </div>
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default DemoScenarios;