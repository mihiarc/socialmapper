/**
 * POICategoryPicker Component - Visual POI category selection
 * Displays POI categories with icons, descriptions, and examples
 */
import React, { useEffect, useState, useCallback } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Typography, 
  Tag, 
  Input, 
  Space, 
  Badge,
  Tooltip,
  Spin,
  Alert,
  Button
} from 'antd';
import { 
  ShopOutlined,
  MedicineBoxOutlined,
  BookOutlined,
  CarOutlined,
  CoffeeOutlined,
  BankOutlined,
  HomeOutlined,
  EnvironmentOutlined,
  SearchOutlined,
  HeartOutlined,
  ShoppingOutlined,
  RestOutlined
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { updateConfiguration } from '@/store/slices/analysisSlice';
import { useGetPOITypesQuery } from '@/store/api/metadataApi';
import type { POIType } from '@/types/api';

const { Title, Text } = Typography;
const { Search } = Input;

interface POICategoryPickerProps {
  onSelectionChange?: (selectedTypes: string[], selectedNames: string[]) => void;
  maxSelections?: number;
}

// Icon mapping for POI categories
const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  'healthcare': <MedicineBoxOutlined />,
  'education': <BookOutlined />,
  'retail': <ShopOutlined />,
  'food': <CoffeeOutlined />,
  'finance': <BankOutlined />,
  'transportation': <CarOutlined />,
  'government': <BankOutlined />,
  'recreation': <HeartOutlined />,
  'shopping': <ShoppingOutlined />,
  'accommodation': <RestOutlined />,
  'services': <HomeOutlined />,
  'default': <EnvironmentOutlined />
};

// Color mapping for categories
const CATEGORY_COLORS: Record<string, string> = {
  'healthcare': '#52c41a',
  'education': '#1890ff',
  'retail': '#722ed1',
  'food': '#fa8c16',
  'finance': '#13c2c2',
  'transportation': '#eb2f96',
  'government': '#2f54eb',
  'recreation': '#f5222d',
  'shopping': '#a0d911',
  'accommodation': '#faad14',
  'services': '#595959',
  'default': '#d9d9d9'
};

// Popular POI combinations for quick selection
const POPULAR_COMBINATIONS = [
  {
    name: 'Essential Services',
    description: 'Healthcare, grocery stores, pharmacies',
    types: ['hospital', 'pharmacy', 'supermarket'],
    color: '#52c41a'
  },
  {
    name: 'Daily Needs',
    description: 'Banks, post offices, government services',
    types: ['bank', 'post_office', 'government'],
    color: '#1890ff'
  },
  {
    name: 'Education & Learning',
    description: 'Schools, libraries, universities',
    types: ['school', 'library', 'university'],
    color: '#722ed1'
  },
  {
    name: 'Recreation & Leisure',
    description: 'Parks, gyms, entertainment venues',
    types: ['park', 'gym', 'movie_theater'],
    color: '#fa8c16'
  }
];

/**
 * Visual POI category picker with search, filtering, and popular combinations
 */
const POICategoryPicker: React.FC<POICategoryPickerProps> = ({
  onSelectionChange,
  maxSelections = 10
}) => {
  const dispatch = useAppDispatch();
  const { currentConfig } = useAppSelector(state => state.analysis);
  
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedNames, setSelectedNames] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  
  // Fetch POI types from API
  const {
    data: poiTypesData,
    isLoading,
    error
  } = useGetPOITypesQuery();

  const poiTypes = poiTypesData?.poi_types || [];
  const categories = poiTypesData?.categories || [];

  // Filter POI types based on search and category
  const filteredPOITypes = poiTypes.filter((poi: POIType) => {
    const matchesSearch = !searchQuery || 
      poi.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      poi.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (poi.common_names || []).some(name => 
        name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    
    const matchesCategory = selectedCategory === 'all' || poi.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  // Handle POI type selection
  const handlePOISelect = useCallback((poiType: POIType) => {
    const isSelected = selectedTypes.includes(poiType.type);
    
    let newSelectedTypes: string[];
    let newSelectedNames: string[];
    
    if (isSelected) {
      // Remove from selection
      newSelectedTypes = selectedTypes.filter(type => type !== poiType.type);
      newSelectedNames = selectedNames.filter(name => name !== poiType.name);
    } else {
      // Add to selection (check max limit)
      if (selectedTypes.length >= maxSelections) {
        return; // Don't add if at max
      }
      newSelectedTypes = [...selectedTypes, poiType.type];
      newSelectedNames = [...selectedNames, poiType.name];
    }
    
    setSelectedTypes(newSelectedTypes);
    setSelectedNames(newSelectedNames);
    
    // Update Redux configuration
    dispatch(updateConfiguration({
      poi_type: newSelectedTypes.join(','),
      poi_name: newSelectedNames.join(',')
    }));
    
    // Callback to parent
    onSelectionChange?.(newSelectedTypes, newSelectedNames);
  }, [selectedTypes, selectedNames, maxSelections, dispatch, onSelectionChange]);

  // Handle popular combination selection
  const handleCombinationSelect = useCallback((combination: typeof POPULAR_COMBINATIONS[0]) => {
    const validTypes = combination.types.filter(type => 
      poiTypes.some((poi: POIType) => poi.type === type)
    );
    
    if (validTypes.length === 0) return;
    
    const validNames = validTypes.map(type => 
      poiTypes.find((poi: POIType) => poi.type === type)?.name || type
    );
    
    setSelectedTypes(validTypes);
    setSelectedNames(validNames);
    
    // Update Redux configuration
    dispatch(updateConfiguration({
      poi_type: validTypes.join(','),
      poi_name: validNames.join(',')
    }));
    
    // Callback to parent
    onSelectionChange?.(validTypes, validNames);
  }, [poiTypes, dispatch, onSelectionChange]);

  // Clear all selections
  const clearSelections = useCallback(() => {
    setSelectedTypes([]);
    setSelectedNames([]);
    dispatch(updateConfiguration({
      poi_type: '',
      poi_name: ''
    }));
    onSelectionChange?.([], []);
  }, [dispatch, onSelectionChange]);

  // Initialize from Redux state if present
  useEffect(() => {
    if (currentConfig.poi_type && currentConfig.poi_name) {
      const types = currentConfig.poi_type.split(',').filter(Boolean);
      const names = currentConfig.poi_name.split(',').filter(Boolean);
      setSelectedTypes(types);
      setSelectedNames(names);
    }
  }, [currentConfig.poi_type, currentConfig.poi_name]);

  if (error) {
    return (
      <Alert
        message="Failed to Load POI Types"
        description="Unable to load available POI categories. Please try refreshing the page."
        type="error"
        showIcon
      />
    );
  }

  return (
    <div className="poi-category-picker">
      <div style={{ marginBottom: 24 }}>
        <Title level={4}>Choose Points of Interest</Title>
        <Text type="secondary">
          Select the types of places you want to analyze. You can choose up to {maxSelections} types.
        </Text>
      </div>

      {/* Selection Summary */}
      {selectedTypes.length > 0 && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text strong>Selected POI Types ({selectedTypes.length}/{maxSelections})</Text>
              <Button size="small" type="link" onClick={clearSelections}>
                Clear All
              </Button>
            </div>
            <div>
              {selectedNames.map((name, index) => (
                <Tag
                  key={selectedTypes[index]}
                  closable
                  color={CATEGORY_COLORS[poiTypes.find((p: POIType) => p.type === selectedTypes[index])?.category || 'default']}
                  onClose={() => {
                    const poiType = poiTypes.find((p: POIType) => p.type === selectedTypes[index]);
                    if (poiType) handlePOISelect(poiType);
                  }}
                >
                  {name}
                </Tag>
              ))}
            </div>
          </Space>
        </Card>
      )}

      {/* Popular Combinations - Mobile Optimized */}
      <Card title="Quick Selection" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[8, 8]}>
          {POPULAR_COMBINATIONS.map((combo) => (
            <Col xs={12} sm={12} md={6} key={combo.name}>
              <Card
                hoverable
                size="small"
                onClick={() => handleCombinationSelect(combo)}
                style={{ 
                  borderColor: combo.color,
                  cursor: 'pointer',
                  padding: '8px'
                }}
                bodyStyle={{ padding: '8px' }}
              >
                <Space direction="vertical" size={4} style={{ width: '100%' }}>
                  <Text strong style={{ 
                    color: combo.color,
                    fontSize: window.innerWidth <= 400 ? '12px' : '14px'
                  }}>
                    {combo.name}
                  </Text>
                  <Text type="secondary" style={{ 
                    fontSize: window.innerWidth <= 400 ? '10px' : '12px',
                    lineHeight: 1.2
                  }}>
                    {combo.description}
                  </Text>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Search and Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Search
            placeholder="Search for POI types..."
            prefix={<SearchOutlined />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            allowClear
          />
          
          {/* Category Filter */}
          <div>
            <Text style={{ marginRight: 8 }}>Filter by category:</Text>
            <Tag.CheckableTag
              checked={selectedCategory === 'all'}
              onChange={() => setSelectedCategory('all')}
            >
              All Categories
            </Tag.CheckableTag>
            {categories.map((category: string) => (
              <Tag.CheckableTag
                key={category}
                checked={selectedCategory === category}
                onChange={() => setSelectedCategory(category)}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </Tag.CheckableTag>
            ))}
          </div>
        </Space>
      </Card>

      {/* POI Type Grid - Mobile Responsive */}
      <Spin spinning={isLoading}>
        <Row gutter={window.innerWidth <= 576 ? [8, 8] : [12, 12]}>
          {filteredPOITypes.map((poiType: POIType) => {
            const isSelected = selectedTypes.includes(poiType.type);
            const icon = CATEGORY_ICONS[poiType.category || 'default'];
            const color = CATEGORY_COLORS[poiType.category || 'default'];
            const isMobile = window.innerWidth <= 576;
            
            return (
              <Col xs={12} sm={12} md={8} lg={6} key={poiType.type}>
                <Badge
                  count={isSelected ? '✓' : 0}
                  style={{ backgroundColor: color }}
                >
                  <Card
                    hoverable
                    size="small"
                    className={`poi-type-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => handlePOISelect(poiType)}
                    style={{ 
                      borderColor: isSelected ? color : undefined,
                      backgroundColor: isSelected ? `${color}10` : undefined,
                      cursor: selectedTypes.length >= maxSelections && !isSelected ? 'not-allowed' : 'pointer',
                      opacity: selectedTypes.length >= maxSelections && !isSelected ? 0.5 : 1,
                      minHeight: isMobile ? '120px' : '150px'
                    }}
                    bodyStyle={{ 
                      padding: isMobile ? '8px' : '12px'
                    }}
                  >
                    <Space direction="vertical" align="center" style={{ width: '100%' }} size={isMobile ? 4 : 8}>
                      <div style={{ fontSize: isMobile ? '20px' : '24px', color: color }}>
                        {icon}
                      </div>
                      <Text strong style={{ 
                        textAlign: 'center', 
                        fontSize: isMobile ? '11px' : '12px',
                        lineHeight: 1.2
                      }}>
                        {poiType.name}
                      </Text>
                      {poiType.description && !isMobile && (
                        <Tooltip title={poiType.description}>
                          <Text type="secondary" style={{ 
                            fontSize: '10px',
                            textAlign: 'center',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden'
                          }}>
                            {poiType.description}
                          </Text>
                        </Tooltip>
                      )}
                      {poiType.common_names && poiType.common_names.length > 0 && !isMobile && (
                        <div style={{ textAlign: 'center' }}>
                          {poiType.common_names.slice(0, 2).map((name, idx) => (
                            <Tag key={idx} style={{ fontSize: '9px', margin: '1px', padding: '0 4px' }}>
                              {name}
                            </Tag>
                          ))}
                        </div>
                      )}
                    </Space>
                  </Card>
                </Badge>
              </Col>
            );
          })}
        </Row>
      </Spin>

      {filteredPOITypes.length === 0 && !isLoading && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <EnvironmentOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: 16 }} />
            <Title level={4} type="secondary">No POI Types Found</Title>
            <Text type="secondary">
              Try adjusting your search terms or category filter.
            </Text>
          </div>
        </Card>
      )}
    </div>
  );
};

export default React.memo(POICategoryPicker);