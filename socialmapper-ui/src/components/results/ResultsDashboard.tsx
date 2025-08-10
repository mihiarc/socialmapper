/**
 * ResultsDashboard Component - Interactive results visualization and export
 * Displays analysis results with maps, charts, and export functionality
 */
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Typography, 
  Space, 
  Button, 
  Statistic, 
  Tabs, 
  Table, 
  Tag, 
  Divider,
  Alert,
  Modal,
  Select,
  message,
  Tooltip
} from 'antd';
import {
  DownloadOutlined,
  MapOutlined,
  BarChartOutlined,
  TableOutlined,
  ShareAltOutlined,
  InfoCircleOutlined,
  FileTextOutlined,
  FileImageOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import mapboxgl from 'mapbox-gl';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { useGetAnalysisResultQuery, useExportResultsMutation } from '@/store/api/analysisApi';
import { ExportFormat, type AnalysisResult } from '@/types/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface ResultsDashboardProps {
  jobId: string;
  onShare?: (shareUrl: string) => void;
}

// Mapbox access token
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

// Export format configurations
const EXPORT_FORMATS = [
  {
    format: ExportFormat.CSV,
    label: 'CSV (Spreadsheet)',
    icon: <TableOutlined />,
    description: 'Compatible with Excel, Google Sheets',
    size: 'Small'
  },
  {
    format: ExportFormat.GEOJSON,
    label: 'GeoJSON (Maps)',
    icon: <MapOutlined />,
    description: 'Geographic data for mapping applications',
    size: 'Medium'
  },
  {
    format: ExportFormat.PARQUET,
    label: 'Parquet (Analytics)',
    icon: <DatabaseOutlined />,
    description: 'Optimized for data analysis tools',
    size: 'Small'
  },
  {
    format: ExportFormat.GEOPARQUET,
    label: 'GeoParquet (Advanced)',
    icon: <BarChartOutlined />,
    description: 'Geographic data with analytics optimization',
    size: 'Medium'
  }
];

/**
 * Comprehensive results dashboard with interactive visualization
 */
const ResultsDashboard: React.FC<ResultsDashboardProps> = ({ jobId, onShare }) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [selectedExportFormat, setSelectedExportFormat] = useState<ExportFormat>(ExportFormat.CSV);
  const [exportModalVisible, setExportModalVisible] = useState(false);
  const [shareModalVisible, setShareModalVisible] = useState(false);

  // API calls
  const { data: result, isLoading, error, refetch } = useGetAnalysisResultQuery(jobId);
  const [exportResults, { isLoading: isExporting }] = useExportResultsMutation();

  // Initialize map when results are loaded
  useEffect(() => {
    if (!result || !mapContainer.current || map.current) return;

    if (!MAPBOX_TOKEN) {
      message.error('Mapbox token not configured');
      return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [-98.5795, 39.8283], // Will be updated based on data
      zoom: 10
    });

    map.current.addControl(new mapboxgl.NavigationControl());

    // Add isochrones if available
    if (result.isochrones) {
      map.current.on('load', () => {
        // Add isochrone layer
        map.current!.addSource('isochrones', {
          type: 'geojson',
          data: result.isochrones!
        });

        map.current!.addLayer({
          id: 'isochrone-fill',
          type: 'fill',
          source: 'isochrones',
          paint: {
            'fill-color': '#1890ff',
            'fill-opacity': 0.3
          }
        });

        map.current!.addLayer({
          id: 'isochrone-outline',
          type: 'line',
          source: 'isochrones',
          paint: {
            'line-color': '#1890ff',
            'line-width': 2
          }
        });

        // Fit map to isochrone bounds
        const bounds = new mapboxgl.LngLatBounds();
        result.isochrones!.features.forEach((feature: any) => {
          if (feature.geometry.type === 'Polygon') {
            feature.geometry.coordinates[0].forEach((coord: [number, number]) => {
              bounds.extend(coord);
            });
          }
        });
        map.current!.fitBounds(bounds, { padding: 50 });
      });
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [result]);

  // Handle export
  const handleExport = useCallback(async () => {
    try {
      const blob = await exportResults({
        jobId,
        format: selectedExportFormat,
        includeIsochrones: true,
        includeDemographics: true
      }).unwrap();

      // Create download link
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `socialmapper-analysis-${jobId}.${selectedExportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      message.success('Results exported successfully');
      setExportModalVisible(false);
    } catch (error) {
      message.error('Export failed');
      console.error('Export error:', error);
    }
  }, [exportResults, jobId, selectedExportFormat]);

  // Handle share
  const handleShare = useCallback(() => {
    const shareUrl = `${window.location.origin}/results/${jobId}`;
    
    if (navigator.share) {
      navigator.share({
        title: 'SocialMapper Analysis Results',
        text: 'Check out these accessibility analysis results',
        url: shareUrl
      });
    } else {
      navigator.clipboard.writeText(shareUrl);
      message.success('Share link copied to clipboard');
    }
    
    setShareModalVisible(false);
    onShare?.(shareUrl);
  }, [jobId, onShare]);

  // Prepare demographic data for charts
  const getDemographicChartData = () => {
    if (!result?.demographics) return [];
    
    return Object.entries(result.demographics).map(([key, value]) => ({
      name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: typeof value === 'number' ? value : 0
    })).slice(0, 10); // Show top 10
  };

  // Table columns for detailed data
  const getTableColumns = () => [
    {
      title: 'Metric',
      dataIndex: 'metric',
      key: 'metric'
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      render: (value: any) => {
        if (typeof value === 'number') {
          return value.toLocaleString();
        }
        return String(value);
      }
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description'
    }
  ];

  // Prepare table data
  const getTableData = () => {
    if (!result) return [];
    
    const data = [];
    
    if (result.poi_count !== undefined) {
      data.push({
        key: 'poi_count',
        metric: 'Points of Interest Found',
        value: result.poi_count,
        description: 'Total number of POIs within travel range'
      });
    }
    
    if (result.population_covered !== undefined) {
      data.push({
        key: 'population_covered',
        metric: 'Population Covered',
        value: result.population_covered,
        description: 'Total population within travel areas'
      });
    }
    
    if (result.analysis_area_km2 !== undefined) {
      data.push({
        key: 'analysis_area',
        metric: 'Analysis Area',
        value: `${result.analysis_area_km2.toFixed(2)} km²`,
        description: 'Total area covered by analysis'
      });
    }
    
    if (result.processing_time_seconds !== undefined) {
      data.push({
        key: 'processing_time',
        metric: 'Processing Time',
        value: `${result.processing_time_seconds.toFixed(1)}s`,
        description: 'Time taken to complete analysis'
      });
    }

    return data;
  };

  if (isLoading) {
    return (
      <Card style={{ textAlign: 'center', padding: '60px 0' }}>
        <Space direction="vertical" size="large">
          <div style={{ fontSize: '48px' }}>📊</div>
          <Title level={3}>Loading Results...</Title>
          <Text type="secondary">Please wait while we prepare your analysis results</Text>
        </Space>
      </Card>
    );
  }

  if (error || !result) {
    return (
      <Card>
        <Alert
          message="Results Not Available"
          description="Unable to load analysis results. The analysis may still be running or may have failed."
          type="error"
          showIcon
          action={
            <Button onClick={() => refetch()}>
              Retry
            </Button>
          }
        />
      </Card>
    );
  }

  return (
    <div className="results-dashboard">
      {/* Header with Actions */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space direction="vertical" size="small">
              <Title level={3} style={{ margin: 0 }}>
                Analysis Results
              </Title>
              <Text type="secondary">
                Completed {result.completed_at ? new Date(result.completed_at).toLocaleString() : 'Recently'}
              </Text>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                icon={<ShareAltOutlined />}
                onClick={() => setShareModalVisible(true)}
              >
                Share
              </Button>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() => setExportModalVisible(true)}
              >
                Export Results
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Summary Statistics */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Points of Interest"
              value={result.poi_count || 0}
              prefix={<MapOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Population Covered"
              value={result.population_covered || 0}
              formatter={(value) => value?.toLocaleString()}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Analysis Area"
              value={result.analysis_area_km2 || 0}
              precision={2}
              suffix="km²"
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Processing Time"
              value={result.processing_time_seconds || 0}
              precision={1}
              suffix="seconds"
            />
          </Card>
        </Col>
      </Row>

      {/* Main Content Tabs */}
      <Tabs
        defaultActiveKey="map"
        items={[
          {
            key: 'map',
            label: (
              <Space>
                <MapOutlined />
                Interactive Map
              </Space>
            ),
            children: (
              <Card>
                <div style={{ marginBottom: 16 }}>
                  <Text strong>Geographic Visualization</Text>
                  <Divider type="vertical" />
                  <Text type="secondary">
                    Blue areas show locations reachable within your specified travel time
                  </Text>
                </div>
                <div
                  ref={mapContainer}
                  style={{
                    width: '100%',
                    height: '500px',
                    borderRadius: '8px'
                  }}
                />
              </Card>
            )
          },
          {
            key: 'demographics',
            label: (
              <Space>
                <BarChartOutlined />
                Demographics
              </Space>
            ),
            children: (
              <Card title="Demographic Analysis">
                {result.demographics ? (
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={getDemographicChartData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="name"
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis />
                      <RechartsTooltip />
                      <Bar dataKey="value" fill="#1890ff" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <Alert
                    message="No Demographic Data"
                    description="Demographic analysis was not included in this analysis."
                    type="info"
                  />
                )}
              </Card>
            )
          },
          {
            key: 'data',
            label: (
              <Space>
                <TableOutlined />
                Detailed Data
              </Space>
            ),
            children: (
              <Card title="Analysis Metrics">
                <Table
                  columns={getTableColumns()}
                  dataSource={getTableData()}
                  pagination={false}
                  size="small"
                />
              </Card>
            )
          }
        ]}
      />

      {/* Export Modal */}
      <Modal
        title="Export Analysis Results"
        open={exportModalVisible}
        onCancel={() => setExportModalVisible(false)}
        onOk={handleExport}
        confirmLoading={isExporting}
        okText="Export"
        cancelText="Cancel"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>Choose export format:</Text>
          <Select
            value={selectedExportFormat}
            onChange={setSelectedExportFormat}
            style={{ width: '100%' }}
            size="large"
          >
            {EXPORT_FORMATS.map(format => (
              <Option key={format.format} value={format.format}>
                <Space>
                  {format.icon}
                  <div>
                    <div>{format.label}</div>
                    <Text type="secondary" style={{ fontSize: '11px' }}>
                      {format.description} • {format.size} file size
                    </Text>
                  </div>
                </Space>
              </Option>
            ))}
          </Select>
          
          <Alert
            message="Export Options"
            description="Export will include all available data including geographic boundaries and demographic information."
            type="info"
            showIcon
          />
        </Space>
      </Modal>

      {/* Share Modal */}
      <Modal
        title="Share Analysis Results"
        open={shareModalVisible}
        onCancel={() => setShareModalVisible(false)}
        onOk={handleShare}
        okText="Share"
        cancelText="Cancel"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>Share this analysis with others:</Text>
          <Text code copyable style={{ wordBreak: 'break-all' }}>
            {`${window.location.origin}/results/${jobId}`}
          </Text>
          <Alert
            message="Public Link"
            description="Anyone with this link will be able to view the analysis results."
            type="warning"
            showIcon
          />
        </Space>
      </Modal>
    </div>
  );
};

export default React.memo(ResultsDashboard);