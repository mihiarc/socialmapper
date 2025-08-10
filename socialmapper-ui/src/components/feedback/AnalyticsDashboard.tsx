/**
 * Analytics Dashboard - Comprehensive feedback and usage analytics
 * Provides insights for continuous product improvement and decision making
 */
import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Select,
  Typography,
  Space,
  Progress,
  List,
  Tag,
  Alert,
  Tabs,
  Empty,
  Button,
  DatePicker,
  Table,
} from 'antd';
import {
  RiseOutlined,
  UserOutlined,
  StarOutlined,
  BugOutlined,
  BulbOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

import {
  useGetFeedbackSummaryQuery,
  useGetAnalyticsSummaryQuery,
  useGetFeedbackInsightsQuery,
  useListFeatureRequestsQuery,
} from '@store/api/feedbackApi';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

interface AnalyticsDashboardProps {
  showExportControls?: boolean;
  compact?: boolean;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  showExportControls = true,
  compact = false,
}) => {
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'days'),
    dayjs(),
  ]);
  
  const days = Math.abs(dateRange[0].diff(dateRange[1], 'days'));

  // Fetch analytics data
  const {
    data: feedbackSummary,
    isLoading: feedbackLoading,
    refetch: refetchFeedback,
  } = useGetFeedbackSummaryQuery({ days });

  const {
    data: analyticsSummary,
    isLoading: analyticsLoading,
    refetch: refetchAnalytics,
  } = useGetAnalyticsSummaryQuery({ days });

  const {
    data: insights,
    isLoading: insightsLoading,
    refetch: refetchInsights,
  } = useGetFeedbackInsightsQuery({ days });

  const {
    data: featureRequests = [],
    isLoading: featuresLoading,
  } = useListFeatureRequestsQuery({ limit: 10 });

  const handleDateRangeChange = (dates: any) => {
    if (dates) {
      setDateRange([dates[0], dates[1]]);
    }
  };

  const handleExportData = () => {
    const data = {
      feedbackSummary,
      analyticsSummary,
      insights,
      featureRequests,
      dateRange: dateRange.map(d => d.format('YYYY-MM-DD')),
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `socialmapper-analytics-${dayjs().format('YYYY-MM-DD')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const refreshAll = () => {
    refetchFeedback();
    refetchAnalytics();
    refetchInsights();
  };

  const renderFeedbackOverview = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Total Feedback"
            value={feedbackSummary?.total_feedback || 0}
            prefix={<StarOutlined />}
            loading={feedbackLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Average Rating"
            value={feedbackSummary?.average_rating || 0}
            precision={1}
            suffix="/ 5"
            prefix={<StarOutlined />}
            loading={feedbackLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Response Rate"
            value={feedbackSummary?.response_rate || 0}
            precision={1}
            suffix="%"
            prefix={<RiseOutlined />}
            loading={feedbackLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Recent Feedback"
            value={feedbackSummary?.recent_feedback_count || 0}
            prefix={<ClockCircleOutlined />}
            loading={feedbackLoading}
          />
        </Card>
      </Col>
    </Row>
  );

  const renderUserAnalytics = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Total Sessions"
            value={analyticsSummary?.total_sessions || 0}
            prefix={<UserOutlined />}
            loading={analyticsLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Page Views"
            value={analyticsSummary?.total_page_views || 0}
            prefix={<RiseOutlined />}
            loading={analyticsLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Conversions"
            value={analyticsSummary?.total_conversions || 0}
            prefix={<StarOutlined />}
            loading={analyticsLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Avg Session"
            value={analyticsSummary?.average_session_duration_ms ? 
              Math.round(analyticsSummary.average_session_duration_ms / 1000 / 60) : 0}
            suffix="min"
            prefix={<ClockCircleOutlined />}
            loading={analyticsLoading}
          />
        </Card>
      </Col>
    </Row>
  );

  const renderFeedbackBreakdown = () => {
    if (!feedbackSummary) return <Empty description="No feedback data" />;

    const typeData = Object.entries(feedbackSummary.feedback_by_type).map(([type, count]) => ({
      type,
      count,
      percentage: Math.round(((count as number) / feedbackSummary.total_feedback) * 100),
    }));

    const touchpointData = Object.entries(feedbackSummary.feedback_by_touchpoint).map(([touchpoint, count]) => ({
      touchpoint,
      count,
      percentage: Math.round(((count as number) / feedbackSummary.total_feedback) * 100),
    }));

    return (
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Feedback by Type" loading={feedbackLoading}>
            <List
              size="small"
              dataSource={typeData}
              renderItem={item => (
                <List.Item>
                  <Row style={{ width: '100%' }} align="middle">
                    <Col flex="auto">
                      <Space>
                        {item.type === 'bug_report' && <BugOutlined />}
                        {item.type === 'feature_request' && <BulbOutlined />}
                        {item.type === 'rating' && <StarOutlined />}
                        <Text>{item.type.replace('_', ' ')}</Text>
                      </Space>
                    </Col>
                    <Col>
                      <Space>
                        <Text strong>{String(item.count)}</Text>
                        <Progress 
                          percent={item.percentage} 
                          size="small" 
                          style={{ width: '60px' }}
                        />
                      </Space>
                    </Col>
                  </Row>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="Feedback by Touchpoint" loading={feedbackLoading}>
            <List
              size="small"
              dataSource={touchpointData}
              renderItem={item => (
                <List.Item>
                  <Row style={{ width: '100%' }} align="middle">
                    <Col flex="auto">
                      <Text>{item.touchpoint.replace('_', ' ')}</Text>
                    </Col>
                    <Col>
                      <Space>
                        <Text strong>{String(item.count)}</Text>
                        <Progress 
                          percent={item.percentage} 
                          size="small" 
                          style={{ width: '60px' }}
                        />
                      </Space>
                    </Col>
                  </Row>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  const renderInsights = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title="AI-Generated Insights" loading={insightsLoading}>
          {insights ? (
            <Space direction="vertical" style={{ width: '100%' }}>
              {insights.sentiment_score !== undefined && insights.sentiment_score !== null && (
                <div>
                  <Text strong>Overall Sentiment: </Text>
                  <Tag color={insights.sentiment_score > 0.2 ? 'green' : 
                               insights.sentiment_score < -0.2 ? 'red' : 'orange'}>
                    {insights.sentiment_score > 0.2 ? 'Positive' : 
                     insights.sentiment_score < -0.2 ? 'Negative' : 'Neutral'}
                  </Tag>
                </div>
              )}
              
              {insights.common_themes && insights.common_themes.length > 0 && (
                <div>
                  <Text strong>Common Themes:</Text>
                  <div style={{ marginTop: '8px' }}>
                    {insights.common_themes.map((theme: string) => (
                      <Tag key={theme}>{theme}</Tag>
                    ))}
                  </div>
                </div>
              )}
              
              {insights.improvement_suggestions.length > 0 && (
                <div>
                  <Text strong>Improvement Suggestions:</Text>
                  <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                    {insights.improvement_suggestions.map((suggestion: any, index: number) => (
                      <li key={index}>{suggestion.suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Space>
          ) : (
            <Empty description="No insights available" />
          )}
        </Card>
      </Col>
      
      <Col xs={24} lg={12}>
        <Card title="User Journey Funnel" loading={analyticsLoading}>
          {analyticsSummary?.user_journey_funnel ? (
            <List
              size="small"
              dataSource={analyticsSummary.user_journey_funnel}
              renderItem={(item: any) => (
                <List.Item>
                  <Row style={{ width: '100%' }} align="middle">
                    <Col flex="auto">
                      <Text>{item.step}</Text>
                    </Col>
                    <Col>
                      <Space>
                        <Text strong>{item.users}</Text>
                        <Progress 
                          percent={Math.round((item.users / (analyticsSummary.user_journey_funnel?.[0]?.users || 1)) * 100)}
                          size="small" 
                          style={{ width: '60px' }}
                        />
                      </Space>
                    </Col>
                  </Row>
                </List.Item>
              )}
            />
          ) : (
            <Empty description="No funnel data available" />
          )}
        </Card>
      </Col>
    </Row>
  );

  const renderTopFeatureRequests = () => (
    <Card 
      title="Top Feature Requests" 
      loading={featuresLoading}
      extra={
        <Button type="link" size="small">
          View All
        </Button>
      }
    >
      <List
        size="small"
        dataSource={featureRequests.slice(0, 5)}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Space key="votes">
                <Text strong>{item.votes}</Text>
                <Text type="secondary">votes</Text>
              </Space>
            ]}
          >
            <List.Item.Meta
              title={item.title}
              description={
                <Space>
                  <Tag color="blue">{item.category}</Tag>
                  <Tag color="orange">{item.priority}</Tag>
                  <Tag color="green">{item.status}</Tag>
                </Space>
              }
            />
          </List.Item>
        )}
        locale={{
          emptyText: <Empty description="No feature requests" />
        }}
      />
    </Card>
  );

  return (
    <div>
      {/* Header Controls */}
      <Card style={{ marginBottom: '16px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              Analytics Dashboard
            </Title>
          </Col>
          <Col>
            <Space>
              <RangePicker
                value={dateRange}
                onChange={handleDateRangeChange}
                presets={[
                  { label: 'Last 7 Days', value: [dayjs().subtract(7, 'days'), dayjs()] },
                  { label: 'Last 30 Days', value: [dayjs().subtract(30, 'days'), dayjs()] },
                  { label: 'Last 3 Months', value: [dayjs().subtract(3, 'months'), dayjs()] },
                ]}
              />
              <Button icon={<ReloadOutlined />} onClick={refreshAll}>
                Refresh
              </Button>
              {showExportControls && (
                <Button icon={<DownloadOutlined />} onClick={handleExportData}>
                  Export
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Main Content */}
      <Tabs defaultActiveKey="overview">
        <TabPane tab="Overview" key="overview">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Card title="Feedback Metrics">
              {renderFeedbackOverview()}
            </Card>
            <Card title="User Analytics">
              {renderUserAnalytics()}
            </Card>
            {renderTopFeatureRequests()}
          </Space>
        </TabPane>

        <TabPane tab="Feedback Analysis" key="feedback">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {renderFeedbackBreakdown()}
          </Space>
        </TabPane>

        <TabPane tab="User Behavior" key="behavior">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {renderInsights()}
          </Space>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default AnalyticsDashboard;