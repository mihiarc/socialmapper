/**
 * ParameterSliders Component - Travel and demographic parameter controls
 * Handles travel time, travel mode, and census variable selection
 */
import React, { useCallback, useEffect, useState } from 'react';
import { 
  Card, 
  Slider, 
  Select, 
  Switch, 
  Typography, 
  Row, 
  Col, 
  Space,
  Tag,
  Tooltip,
  Alert,
  Divider,
  Button
} from 'antd';
import {
  UserOutlined as WalkIcon,
  CarOutlined as BikeIcon,
  CarOutlined,
  CarOutlined as TransitIcon,
  ClockCircleOutlined,
  UserOutlined,
  BarChartOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { updateConfiguration } from '@/store/slices/analysisSlice';
import { useGetCensusVariablesQuery } from '@/store/api/metadataApi';
import { TravelMode, GeographicLevel, type CensusVariable } from '@/types/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface ParameterSlidersProps {
  onParameterChange?: (config: any) => void;
}

// Travel mode configurations with icons and descriptions
const TRAVEL_MODES = [
  {
    value: TravelMode.WALK,
    label: 'Walking',
    icon: <WalkIcon />,
    description: 'Pedestrian access via sidewalks and walking paths',
    color: '#52c41a',
    defaultTime: 15,
    speedRange: '3-5 km/h'
  },
  {
    value: TravelMode.BIKE,
    label: 'Biking', 
    icon: <BikeIcon />,
    description: 'Bicycle access via bike lanes and roads',
    color: '#1890ff',
    defaultTime: 10,
    speedRange: '12-20 km/h'
  },
  {
    value: TravelMode.DRIVE,
    label: 'Driving',
    icon: <CarOutlined />,
    description: 'Car access via roads and highways',
    color: '#fa8c16',
    defaultTime: 10,
    speedRange: '30-80 km/h'
  },
  {
    value: TravelMode.TRANSIT,
    label: 'Public Transit',
    icon: <TransitIcon />,
    description: 'Public transportation including bus, train, and subway',
    color: '#722ed1',
    defaultTime: 20,
    speedRange: '15-50 km/h'
  }
];

// Geographic level options
const GEOGRAPHIC_LEVELS = [
  {
    value: GeographicLevel.BLOCK_GROUP,
    label: 'Block Group',
    description: 'Smallest census unit (600-3,000 people)',
    precision: 'High precision, neighborhood level'
  },
  {
    value: GeographicLevel.TRACT,
    label: 'Census Tract', 
    description: 'Mid-level census unit (1,200-8,000 people)',
    precision: 'Medium precision, community level'
  },
  {
    value: GeographicLevel.COUNTY,
    label: 'County',
    description: 'Largest census unit (entire county)',
    precision: 'Low precision, regional level'
  }
];

// Popular census variable combinations
const VARIABLE_PRESETS = [
  {
    name: 'Basic Demographics',
    description: 'Population, age, and household data',
    variables: ['B01003_001E', 'B25001_001E', 'B19013_001E'],
    color: '#1890ff'
  },
  {
    name: 'Economic Indicators',
    description: 'Income, employment, and poverty data', 
    variables: ['B19013_001E', 'B08303_001E', 'B17001_002E'],
    color: '#52c41a'
  },
  {
    name: 'Housing Characteristics',
    description: 'Housing units, ownership, and values',
    variables: ['B25001_001E', 'B25003_001E', 'B25077_001E'],
    color: '#fa8c16'
  },
  {
    name: 'Transportation',
    description: 'Commute patterns and vehicle access',
    variables: ['B08303_001E', 'B08141_001E', 'B25044_001E'],
    color: '#722ed1'
  }
];

/**
 * Parameter configuration component with sliders, selectors, and presets
 */
const ParameterSliders: React.FC<ParameterSlidersProps> = ({ onParameterChange }) => {
  const dispatch = useAppDispatch();
  const { currentConfig } = useAppSelector(state => state.analysis);
  
  const [travelTime, setTravelTime] = useState(15);
  const [travelMode, setTravelMode] = useState<TravelMode>(TravelMode.WALK);
  const [geographicLevel, setGeographicLevel] = useState<GeographicLevel>(GeographicLevel.BLOCK_GROUP);
  const [selectedVariables, setSelectedVariables] = useState<string[]>(['B01003_001E']);
  const [includeIsochrones, setIncludeIsochrones] = useState(true);
  const [includeDemographics, setIncludeDemographics] = useState(true);

  // Fetch census variables
  const { 
    data: censusData, 
    isLoading: loadingCensus 
  } = useGetCensusVariablesQuery();

  const censusVariables = censusData?.variables || [];

  // Initialize from Redux state
  useEffect(() => {
    if (currentConfig) {
      setTravelTime(currentConfig.travel_time || 15);
      setTravelMode(currentConfig.travel_mode || TravelMode.WALK);
      setGeographicLevel(currentConfig.geographic_level || GeographicLevel.BLOCK_GROUP);
      setSelectedVariables(currentConfig.census_variables || ['B01003_001E']);
      setIncludeIsochrones(currentConfig.include_isochrones ?? true);
      setIncludeDemographics(currentConfig.include_demographics ?? true);
    }
  }, [currentConfig]);

  // Update configuration helper
  const updateConfig = useCallback((updates: any) => {
    dispatch(updateConfiguration(updates));
    onParameterChange?.(updates);
  }, [dispatch, onParameterChange]);

  // Handle travel time change
  const handleTravelTimeChange = useCallback((value: number) => {
    setTravelTime(value);
    updateConfig({ travel_time: value });
  }, [updateConfig]);

  // Handle travel mode change
  const handleTravelModeChange = useCallback((mode: TravelMode) => {
    setTravelMode(mode);
    const modeConfig = TRAVEL_MODES.find(m => m.value === mode);
    const suggestedTime = modeConfig?.defaultTime || 15;
    
    setTravelTime(suggestedTime);
    updateConfig({ 
      travel_mode: mode,
      travel_time: suggestedTime
    });
  }, [updateConfig]);

  // Handle geographic level change
  const handleGeographicLevelChange = useCallback((level: GeographicLevel) => {
    setGeographicLevel(level);
    updateConfig({ geographic_level: level });
  }, [updateConfig]);

  // Handle census variables change
  const handleVariablesChange = useCallback((variables: string[]) => {
    setSelectedVariables(variables);
    updateConfig({ census_variables: variables });
  }, [updateConfig]);

  // Apply variable preset
  const applyVariablePreset = useCallback((preset: typeof VARIABLE_PRESETS[0]) => {
    const availableVars = preset.variables.filter(code => 
      censusVariables.some((v: CensusVariable) => v.code === code)
    );
    if (availableVars.length > 0) {
      handleVariablesChange(availableVars);
    }
  }, [censusVariables, handleVariablesChange]);

  // Toggle switches
  const handleIncludeIsochronesChange = useCallback((checked: boolean) => {
    setIncludeIsochrones(checked);
    updateConfig({ include_isochrones: checked });
  }, [updateConfig]);

  const handleIncludeDemographicsChange = useCallback((checked: boolean) => {
    setIncludeDemographics(checked);
    updateConfig({ include_demographics: checked });
  }, [updateConfig]);

  // Get readable time display
  const getTimeDisplay = (minutes: number) => {
    if (minutes < 60) return `${minutes} minutes`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours} hour${hours > 1 ? 's' : ''}`;
  };

  const selectedModeConfig = TRAVEL_MODES.find(m => m.value === travelMode);

  return (
    <div className="parameter-sliders">
      <Title level={4}>Configure Analysis Parameters</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
        Set travel parameters and demographic variables for your analysis
      </Text>

      {/* Travel Mode Selection - Mobile Optimized */}
      <Card 
        title="Travel Mode" 
        style={{ marginBottom: 16 }}
        bodyStyle={{ padding: window.innerWidth <= 576 ? '12px' : '24px' }}
      >
        <Row gutter={window.innerWidth <= 576 ? [4, 4] : [12, 12]}>
          {TRAVEL_MODES.map((mode) => {
            const isSelected = travelMode === mode.value;
            const isMobile = window.innerWidth <= 576;
            return (
              <Col xs={12} sm={12} md={6} key={mode.value}>
                <Card
                  hoverable
                  size="small"
                  className={`travel-mode-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleTravelModeChange(mode.value)}
                  style={{
                    borderColor: isSelected ? mode.color : undefined,
                    backgroundColor: isSelected ? `${mode.color}10` : undefined,
                    cursor: 'pointer',
                    minHeight: isMobile ? '80px' : '100px'
                  }}
                  bodyStyle={{ padding: isMobile ? '8px' : '12px' }}
                >
                  <Space direction="vertical" align="center" style={{ width: '100%' }} size={isMobile ? 2 : 8}>
                    <div style={{ fontSize: isMobile ? '20px' : '24px', color: mode.color }}>
                      {mode.icon}
                    </div>
                    <Text strong style={{ fontSize: isMobile ? '12px' : '14px' }}>
                      {mode.label}
                    </Text>
                    {!isMobile && (
                      <Text type="secondary" style={{ 
                        fontSize: '11px', 
                        textAlign: 'center' 
                      }}>
                        {mode.speedRange}
                      </Text>
                    )}
                  </Space>
                </Card>
              </Col>
            );
          })}
        </Row>
        
        {selectedModeConfig && (
          <Alert
            message={selectedModeConfig.description}
            type="info"
            showIcon
            style={{ marginTop: 12 }}
          />
        )}
      </Card>

      {/* Travel Time Slider */}
      <Card 
        title={
          <Space>
            <ClockCircleOutlined />
            Travel Time: {getTimeDisplay(travelTime)}
          </Space>
        } 
        style={{ marginBottom: 16 }}
      >
        <Slider
          min={5}
          max={60}
          step={5}
          value={travelTime}
          onChange={handleTravelTimeChange}
          marks={{
            5: '5min',
            15: '15min',
            30: '30min',
            45: '45min',
            60: '1hr'
          }}
          tooltip={{
            formatter: (value) => getTimeDisplay(value || 0)
          }}
        />
        <Text type="secondary" style={{ fontSize: '12px' }}>
          Maximum travel time from selected location to points of interest
        </Text>
      </Card>

      {/* Geographic Level Selection */}
      <Card 
        title={
          <Space>
            <BarChartOutlined />
            Geographic Resolution
            <Tooltip title="The size of geographic areas used for demographic analysis">
              <QuestionCircleOutlined style={{ color: '#999' }} />
            </Tooltip>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Select
          value={geographicLevel}
          onChange={handleGeographicLevelChange}
          style={{ width: '100%' }}
          size="large"
        >
          {GEOGRAPHIC_LEVELS.map((level) => (
            <Option key={level.value} value={level.value}>
              <Space direction="vertical" size={2} style={{ width: '100%' }}>
                <Text strong>{level.label}</Text>
                <Text type="secondary" style={{ fontSize: '11px' }}>
                  {level.description} - {level.precision}
                </Text>
              </Space>
            </Option>
          ))}
        </Select>
      </Card>

      {/* Census Variables Selection */}
      <Card
        title={
          <Space>
            <UserOutlined />
            Demographic Variables
            <Text type="secondary">({selectedVariables.length} selected)</Text>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        {/* Variable Presets - Mobile Optimized */}
        <div style={{ marginBottom: 16 }}>
          <Text strong style={{ 
            display: 'block', 
            marginBottom: 8,
            fontSize: window.innerWidth <= 576 ? '12px' : '14px'
          }}>
            Quick Presets:
          </Text>
          <Row gutter={window.innerWidth <= 576 ? [4, 4] : [8, 8]}>
            {VARIABLE_PRESETS.map((preset) => (
              <Col xs={12} sm={12} md={6} key={preset.name}>
                <Button
                  size={window.innerWidth <= 576 ? 'small' : 'middle'}
                  style={{ 
                    borderColor: preset.color,
                    color: preset.color,
                    width: '100%',
                    fontSize: window.innerWidth <= 576 ? '11px' : '14px'
                  }}
                  onClick={() => applyVariablePreset(preset)}
                >
                  {preset.name}
                </Button>
              </Col>
            ))}
          </Row>
        </div>

        <Divider />

        {/* Variable Multi-Select */}
        <Select
          mode="multiple"
          value={selectedVariables}
          onChange={handleVariablesChange}
          placeholder="Search and select census variables..."
          style={{ width: '100%' }}
          loading={loadingCensus}
          maxTagCount="responsive"
          showSearch
          filterOption={(input, option) => {
            const variable = censusVariables.find((v: CensusVariable) => v.code === option?.value);
            if (!variable) return false;
            const searchText = input.toLowerCase();
            return (
              variable.code.toLowerCase().includes(searchText) ||
              variable.name.toLowerCase().includes(searchText) ||
              variable.concept.toLowerCase().includes(searchText)
            );
          }}
        >
          {censusVariables.map((variable: CensusVariable) => (
            <Option key={variable.code} value={variable.code}>
              <Space direction="vertical" size={2}>
                <Text strong>{variable.name}</Text>
                <Text type="secondary" style={{ fontSize: '11px' }}>
                  {variable.code} - {variable.concept}
                </Text>
              </Space>
            </Option>
          ))}
        </Select>

        {/* Selected Variables Display */}
        {selectedVariables.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
              Selected Variables:
            </Text>
            <Space wrap>
              {selectedVariables.map((code) => {
                const variable = censusVariables.find((v: CensusVariable) => v.code === code);
                return (
                  <Tooltip 
                    key={code} 
                    title={variable ? `${variable.concept} - ${variable.universe}` : code}
                  >
                    <Tag
                      closable
                      onClose={() => handleVariablesChange(selectedVariables.filter(v => v !== code))}
                    >
                      {variable?.name || code}
                    </Tag>
                  </Tooltip>
                );
              })}
            </Space>
          </div>
        )}
      </Card>

      {/* Output Options */}
      <Card title="Output Options" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>Include Isochrones</Text>
              <br />
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Geographic areas showing travel time boundaries
              </Text>
            </div>
            <Switch 
              checked={includeIsochrones}
              onChange={handleIncludeIsochronesChange}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>Include Demographics</Text>
              <br />
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Population and demographic analysis within travel areas
              </Text>
            </div>
            <Switch 
              checked={includeDemographics}
              onChange={handleIncludeDemographicsChange}
            />
          </div>
        </Space>
      </Card>

      {/* Configuration Summary */}
      <Card title="Configuration Summary" size="small">
        <Row gutter={[16, 8]}>
          <Col span={12}>
            <Text type="secondary">Travel Mode:</Text>
            <br />
            <Text strong>{selectedModeConfig?.label}</Text>
          </Col>
          <Col span={12}>
            <Text type="secondary">Travel Time:</Text>
            <br />
            <Text strong>{getTimeDisplay(travelTime)}</Text>
          </Col>
          <Col span={12}>
            <Text type="secondary">Geographic Level:</Text>
            <br />
            <Text strong>
              {GEOGRAPHIC_LEVELS.find(l => l.value === geographicLevel)?.label}
            </Text>
          </Col>
          <Col span={12}>
            <Text type="secondary">Variables:</Text>
            <br />
            <Text strong>{selectedVariables.length} selected</Text>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default React.memo(ParameterSliders);