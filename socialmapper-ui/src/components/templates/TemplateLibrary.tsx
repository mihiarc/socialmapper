/**
 * TemplateLibrary Component - Pre-configured analysis templates
 * Provides ready-to-use configurations for common analysis scenarios
 */
import React, { useState, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Button,
  Space,
  Tag,
  Modal,
  List,
  Badge,
  Input,
  Tooltip,
  message,
  Tabs,
  Avatar
} from 'antd';
import {
  MedicineBoxOutlined,
  ShoppingCartOutlined,
  BookOutlined,
  CarOutlined,
  HomeOutlined,
  TeamOutlined,
  EnvironmentOutlined,
  ClockCircleOutlined,
  RocketOutlined,
  SaveOutlined,
  StarOutlined,
  StarFilled,
  SearchOutlined,
  FilterOutlined,
  ThunderboltOutlined,
  AppstoreOutlined
} from '@ant-design/icons';
import { useAppDispatch } from '@/store/hooks';
import { updateConfiguration, setCurrentStep } from '@/store/slices/analysisSlice';
import { TravelMode, GeographicLevel } from '@/types/api';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;

interface AnalysisTemplate {
  id: string;
  name: string;
  description: string;
  category: 'healthcare' | 'education' | 'retail' | 'equity' | 'transportation' | 'custom';
  icon: React.ReactNode;
  color: string;
  featured: boolean;
  popularity: number;
  estimatedTime: string;
  configuration: {
    poi_type: string;
    poi_name: string;
    travel_mode: TravelMode;
    travel_time: number;
    geographic_level: GeographicLevel;
    census_variables: string[];
    include_isochrones: boolean;
    include_demographics: boolean;
  };
  useCases: string[];
  requiredData?: string[];
}

interface TemplateLibraryProps {
  onTemplateSelect?: (template: AnalysisTemplate) => void;
  onClose?: () => void;
  embedded?: boolean;
}

// Pre-configured analysis templates
const ANALYSIS_TEMPLATES: AnalysisTemplate[] = [
  {
    id: 'food-desert',
    name: 'Food Desert Analysis',
    description: 'Identify areas with limited access to grocery stores and fresh food',
    category: 'equity',
    icon: <ShoppingCartOutlined />,
    color: '#52c41a',
    featured: true,
    popularity: 95,
    estimatedTime: '2-3 minutes',
    configuration: {
      poi_type: 'supermarket,grocery_store,farmers_market',
      poi_name: 'Supermarkets,Grocery Stores,Farmers Markets',
      travel_mode: TravelMode.DRIVE,
      travel_time: 10,
      geographic_level: GeographicLevel.BLOCK_GROUP,
      census_variables: [
        'B01003_001E', // Total population
        'B19013_001E', // Median household income
        'B17001_002E', // Population below poverty level
        'B25044_003E', // No vehicle available
      ],
      include_isochrones: true,
      include_demographics: true
    },
    useCases: [
      'Urban planning and zoning decisions',
      'Public health interventions',
      'Transportation planning',
      'Social equity assessments'
    ],
    requiredData: ['Census data', 'POI database']
  },
  {
    id: 'healthcare-access',
    name: 'Healthcare Accessibility',
    description: 'Analyze access to hospitals, clinics, and medical facilities',
    category: 'healthcare',
    icon: <MedicineBoxOutlined />,
    color: '#ff4d4f',
    featured: true,
    popularity: 90,
    estimatedTime: '3-4 minutes',
    configuration: {
      poi_type: 'hospital,clinic,pharmacy,urgent_care',
      poi_name: 'Hospitals,Clinics,Pharmacies,Urgent Care',
      travel_mode: TravelMode.DRIVE,
      travel_time: 15,
      geographic_level: GeographicLevel.TRACT,
      census_variables: [
        'B01003_001E', // Total population
        'B01001_020E', // Male 65-66 years
        'B01001_021E', // Male 67-69 years
        'B01001_044E', // Female 65-66 years
        'B01001_045E', // Female 67-69 years
        'B27001_001E', // Health insurance coverage
      ],
      include_isochrones: true,
      include_demographics: true
    },
    useCases: [
      'Healthcare facility planning',
      'Emergency response planning',
      'Public health policy',
      'Insurance coverage analysis'
    ]
  },
  {
    id: 'school-walkability',
    name: 'School Walkability Study',
    description: 'Assess walkable access to schools for families with children',
    category: 'education',
    icon: <BookOutlined />,
    color: '#1890ff',
    featured: true,
    popularity: 85,
    estimatedTime: '2-3 minutes',
    configuration: {
      poi_type: 'school,kindergarten,elementary_school,high_school',
      poi_name: 'Schools,Kindergartens,Elementary Schools,High Schools',
      travel_mode: TravelMode.WALK,
      travel_time: 15,
      geographic_level: GeographicLevel.BLOCK_GROUP,
      census_variables: [
        'B01001_003E', // Male under 5 years
        'B01001_004E', // Male 5-9 years
        'B01001_005E', // Male 10-14 years
        'B01001_027E', // Female under 5 years
        'B01001_028E', // Female 5-9 years
        'B01001_029E', // Female 10-14 years
      ],
      include_isochrones: true,
      include_demographics: true
    },
    useCases: [
      'School district planning',
      'Safe routes to school programs',
      'Real estate development',
      'Community walkability assessments'
    ]
  },
  {
    id: 'transit-equity',
    name: 'Transit Equity Analysis',
    description: 'Evaluate public transit accessibility for underserved communities',
    category: 'transportation',
    icon: <CarOutlined />,
    color: '#722ed1',
    featured: false,
    popularity: 75,
    estimatedTime: '3-4 minutes',
    configuration: {
      poi_type: 'bus_station,subway_station,train_station,transit_stop',
      poi_name: 'Bus Stations,Subway Stations,Train Stations,Transit Stops',
      travel_mode: TravelMode.WALK,
      travel_time: 10,
      geographic_level: GeographicLevel.BLOCK_GROUP,
      census_variables: [
        'B01003_001E', // Total population
        'B19013_001E', // Median household income
        'B25044_003E', // No vehicle available
        'B08301_010E', // Public transportation to work
        'B17001_002E', // Below poverty level
      ],
      include_isochrones: true,
      include_demographics: true
    },
    useCases: [
      'Transit planning and optimization',
      'Environmental justice assessments',
      'Accessibility compliance',
      'Community development'
    ]
  },
  {
    id: 'senior-services',
    name: 'Senior Services Access',
    description: 'Analyze accessibility to services for elderly populations',
    category: 'healthcare',
    icon: <TeamOutlined />,
    color: '#13c2c2',
    featured: false,
    popularity: 70,
    estimatedTime: '2-3 minutes',
    configuration: {
      poi_type: 'pharmacy,hospital,community_center,park',
      poi_name: 'Pharmacies,Hospitals,Community Centers,Parks',
      travel_mode: TravelMode.DRIVE,
      travel_time: 10,
      geographic_level: GeographicLevel.TRACT,
      census_variables: [
        'B01001_020E', // Male 65+ years
        'B01001_044E', // Female 65+ years
        'B25072_001E', // Household income
        'B18101_001E', // Disability status
      ],
      include_isochrones: true,
      include_demographics: true
    },
    useCases: [
      'Age-friendly community planning',
      'Senior center placement',
      'Healthcare service planning',
      'Social services allocation'
    ]
  },
  {
    id: 'retail-analysis',
    name: 'Retail Market Analysis',
    description: 'Assess retail accessibility and market potential',
    category: 'retail',
    icon: <ShoppingCartOutlined />,
    color: '#fa8c16',
    featured: false,
    popularity: 65,
    estimatedTime: '2-3 minutes',
    configuration: {
      poi_type: 'mall,shopping_center,department_store,retail',
      poi_name: 'Malls,Shopping Centers,Department Stores,Retail',
      travel_mode: TravelMode.DRIVE,
      travel_time: 15,
      geographic_level: GeographicLevel.TRACT,
      census_variables: [
        'B01003_001E', // Total population
        'B19013_001E', // Median household income
        'B25001_001E', // Total housing units
        'B08303_001E', // Commute time
      ],
      include_isochrones: true,
      include_demographics: true
    },
    useCases: [
      'Site selection for new stores',
      'Market penetration analysis',
      'Competition assessment',
      'Customer demographic profiling'
    ]
  }
];

// Template categories with metadata
const TEMPLATE_CATEGORIES = [
  { key: 'all', label: 'All Templates', icon: <AppstoreOutlined /> },
  { key: 'healthcare', label: 'Healthcare', icon: <MedicineBoxOutlined />, color: '#ff4d4f' },
  { key: 'education', label: 'Education', icon: <BookOutlined />, color: '#1890ff' },
  { key: 'retail', label: 'Retail', icon: <ShoppingCartOutlined />, color: '#fa8c16' },
  { key: 'equity', label: 'Equity', icon: <TeamOutlined />, color: '#52c41a' },
  { key: 'transportation', label: 'Transportation', icon: <CarOutlined />, color: '#722ed1' },
  { key: 'custom', label: 'Custom', icon: <RocketOutlined />, color: '#595959' }
];

/**
 * Template library component for quick-start analysis configurations
 */
const TemplateLibrary: React.FC<TemplateLibraryProps> = ({
  onTemplateSelect,
  onClose,
  embedded = false
}) => {
  const dispatch = useAppDispatch();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<AnalysisTemplate | null>(null);
  const [detailsModalVisible, setDetailsModalVisible] = useState(false);
  const [savedTemplates, setSavedTemplates] = useState<string[]>([]);

  // Filter templates based on category and search
  const filteredTemplates = ANALYSIS_TEMPLATES.filter(template => {
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    const matchesSearch = !searchQuery || 
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.useCases.some(useCase => 
        useCase.toLowerCase().includes(searchQuery.toLowerCase())
      );
    return matchesCategory && matchesSearch;
  });

  // Sort templates by popularity and featured status
  const sortedTemplates = [...filteredTemplates].sort((a, b) => {
    if (a.featured && !b.featured) return -1;
    if (!a.featured && b.featured) return 1;
    return b.popularity - a.popularity;
  });

  // Handle template selection
  const handleTemplateSelect = useCallback((template: AnalysisTemplate) => {
    // Update Redux store with template configuration
    dispatch(updateConfiguration(template.configuration));
    
    // Reset to first step to allow location selection
    dispatch(setCurrentStep(0));
    
    // Notify parent component
    onTemplateSelect?.(template);
    
    message.success(`Template "${template.name}" loaded successfully`);
    
    if (!embedded) {
      onClose?.();
    }
  }, [dispatch, onTemplateSelect, onClose, embedded]);

  // Show template details
  const showTemplateDetails = useCallback((template: AnalysisTemplate) => {
    setSelectedTemplate(template);
    setDetailsModalVisible(true);
  }, []);

  // Toggle saved templates
  const toggleSaveTemplate = useCallback((templateId: string) => {
    setSavedTemplates(prev => {
      if (prev.includes(templateId)) {
        message.info('Template removed from saved');
        return prev.filter(id => id !== templateId);
      } else {
        message.success('Template saved');
        return [...prev, templateId];
      }
    });
  }, []);

  // Render template card
  const renderTemplateCard = (template: AnalysisTemplate) => {
    const isSaved = savedTemplates.includes(template.id);
    const isMobile = window.innerWidth <= 768;
    
    return (
      <Card
        hoverable
        className="template-card"
        style={{
          height: '100%',
          borderTop: `3px solid ${template.color}`,
          position: 'relative'
        }}
        bodyStyle={{ 
          padding: isMobile ? '12px' : '16px',
          height: '100%',
          display: 'flex',
          flexDirection: 'column'
        }}
        actions={[
          <Button
            type="text"
            icon={isSaved ? <StarFilled /> : <StarOutlined />}
            onClick={(e) => {
              e.stopPropagation();
              toggleSaveTemplate(template.id);
            }}
            style={{ color: isSaved ? '#faad14' : undefined }}
          />,
          <Button
            type="text"
            onClick={(e) => {
              e.stopPropagation();
              showTemplateDetails(template);
            }}
          >
            Details
          </Button>,
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={(e) => {
              e.stopPropagation();
              handleTemplateSelect(template);
            }}
          >
            Use
          </Button>
        ]}
      >
        {template.featured && (
          <Badge.Ribbon text="Featured" color="red" />
        )}
        
        <Space direction="vertical" size={isMobile ? 4 : 8} style={{ width: '100%', flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Avatar
              size={isMobile ? 32 : 40}
              style={{ backgroundColor: template.color }}
              icon={template.icon}
            />
            <div style={{ flex: 1 }}>
              <Title level={5} style={{ 
                margin: 0, 
                fontSize: isMobile ? '14px' : '16px' 
              }}>
                {template.name}
              </Title>
              <Text type="secondary" style={{ fontSize: isMobile ? '11px' : '12px' }}>
                <ClockCircleOutlined /> {template.estimatedTime}
              </Text>
            </div>
          </div>
          
          <Paragraph 
            type="secondary" 
            ellipsis={{ rows: 2 }}
            style={{ 
              fontSize: isMobile ? '12px' : '13px',
              marginBottom: 8
            }}
          >
            {template.description}
          </Paragraph>
          
          <div style={{ marginTop: 'auto' }}>
            <Space wrap size={4}>
              <Tag color={template.color} style={{ fontSize: '11px' }}>
                {template.category}
              </Tag>
              <Tag style={{ fontSize: '11px' }}>
                {template.popularity}% match
              </Tag>
            </Space>
          </div>
        </Space>
      </Card>
    );
  };

  // Component render
  const content = (
    <div className="template-library">
      {/* Search and Filter Bar */}
      <Card style={{ marginBottom: 16 }} bodyStyle={{ padding: '12px' }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} md={12}>
            <Search
              placeholder="Search templates..."
              prefix={<SearchOutlined />}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              allowClear
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} md={12}>
            <Space wrap style={{ width: '100%', justifyContent: 'flex-end' }}>
              <FilterOutlined />
              {TEMPLATE_CATEGORIES.map(cat => (
                <Tag.CheckableTag
                  key={cat.key}
                  checked={selectedCategory === cat.key}
                  onChange={() => setSelectedCategory(cat.key)}
                  style={{
                    borderColor: cat.color,
                    color: selectedCategory === cat.key ? '#fff' : cat.color,
                    backgroundColor: selectedCategory === cat.key ? cat.color : undefined
                  }}
                >
                  {cat.label}
                </Tag.CheckableTag>
              ))}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Templates Grid */}
      <Row gutter={[16, 16]}>
        {sortedTemplates.map(template => (
          <Col xs={24} sm={12} lg={8} xl={6} key={template.id}>
            {renderTemplateCard(template)}
          </Col>
        ))}
      </Row>

      {sortedTemplates.length === 0 && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <EnvironmentOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
            <Title level={4} type="secondary" style={{ marginTop: 16 }}>
              No Templates Found
            </Title>
            <Text type="secondary">
              Try adjusting your search or filter criteria
            </Text>
          </div>
        </Card>
      )}

      {/* Template Details Modal */}
      <Modal
        title={selectedTemplate?.name}
        open={detailsModalVisible}
        onCancel={() => setDetailsModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setDetailsModalVisible(false)}>
            Close
          </Button>,
          <Button
            key="use"
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={() => {
              if (selectedTemplate) {
                handleTemplateSelect(selectedTemplate);
                setDetailsModalVisible(false);
              }
            }}
          >
            Use This Template
          </Button>
        ]}
        width={700}
      >
        {selectedTemplate && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div>
              <Text strong>Description:</Text>
              <Paragraph>{selectedTemplate.description}</Paragraph>
            </div>

            <div>
              <Text strong>Configuration:</Text>
              <List
                size="small"
                dataSource={[
                  { label: 'POI Types', value: selectedTemplate.configuration.poi_name },
                  { label: 'Travel Mode', value: selectedTemplate.configuration.travel_mode },
                  { label: 'Travel Time', value: `${selectedTemplate.configuration.travel_time} minutes` },
                  { label: 'Geographic Level', value: selectedTemplate.configuration.geographic_level },
                  { label: 'Census Variables', value: `${selectedTemplate.configuration.census_variables.length} variables` }
                ]}
                renderItem={item => (
                  <List.Item>
                    <Text type="secondary">{item.label}:</Text> {item.value}
                  </List.Item>
                )}
              />
            </div>

            <div>
              <Text strong>Use Cases:</Text>
              <ul>
                {selectedTemplate.useCases.map((useCase, idx) => (
                  <li key={idx}>{useCase}</li>
                ))}
              </ul>
            </div>

            {selectedTemplate.requiredData && (
              <div>
                <Text strong>Required Data:</Text>
                <Space wrap>
                  {selectedTemplate.requiredData.map((data, idx) => (
                    <Tag key={idx}>{data}</Tag>
                  ))}
                </Space>
              </div>
            )}
          </Space>
        )}
      </Modal>
    </div>
  );

  // Return wrapped or embedded content
  if (embedded) {
    return content;
  }

  return (
    <Modal
      title={
        <Space>
          <RocketOutlined />
          <span>Analysis Templates</span>
        </Space>
      }
      open={true}
      onCancel={onClose}
      footer={null}
      width={1200}
      bodyStyle={{ padding: '16px' }}
    >
      {content}
    </Modal>
  );
};

export default TemplateLibrary;