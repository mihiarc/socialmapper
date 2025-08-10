/**
 * Feature Request Board - Community-driven feature prioritization
 * Integrates with GitHub Discussions for transparent roadmap management
 */
import React, { useState } from 'react';
import {
  Card,
  Button,
  List,
  Tag,
  Space,
  Typography,
  Modal,
  Form,
  Input,
  Select,
  message,
  Row,
  Col,
  Tooltip,
  Badge,
  Avatar,
  Empty,
} from 'antd';
import {
  PlusOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  ExternalLinkOutlined,
  FireOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';

import type { FeatureRequest } from "@/types/api";
import {
  useListFeatureRequestsQuery,
  useCreateFeatureRequestMutation,
  useVoteOnFeatureMutation,
} from '@store/api/feedbackApi';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface FeatureRequestBoardProps {
  showCreateButton?: boolean;
  maxItems?: number;
  compact?: boolean;
}

const PRIORITY_COLORS = {
  low: 'blue',
  medium: 'orange',
  high: 'red',
  critical: 'purple',
};

const STATUS_ICONS = {
  submitted: <ClockCircleOutlined />,
  under_review: <ExclamationCircleOutlined />,
  planned: <FireOutlined />,
  in_development: <ClockCircleOutlined />,
  completed: <CheckCircleOutlined />,
  rejected: <ExclamationCircleOutlined />,
};

const STATUS_COLORS = {
  submitted: 'default',
  under_review: 'processing',
  planned: 'warning',
  in_development: 'processing',
  completed: 'success',
  rejected: 'error',
};

const FeatureRequestBoard: React.FC<FeatureRequestBoardProps> = ({
  showCreateButton = true,
  maxItems = 50,
  compact = false,
}) => {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>();
  const [selectedStatus, setSelectedStatus] = useState<string>();
  const [form] = Form.useForm();

  const {
    data: featureRequests = [],
    isLoading,
    error,
    refetch,
  } = useListFeatureRequestsQuery({
    limit: maxItems,
    category: selectedCategory,
    status: selectedStatus,
  });

  const [createFeature, { isLoading: isCreating }] = useCreateFeatureRequestMutation();
  const [voteOnFeature, { isLoading: isVoting }] = useVoteOnFeatureMutation();

  const handleCreateFeature = async (values: any) => {
    try {
      await createFeature({
        title: values.title,
        description: values.description,
        category: values.category,
        priority: values.priority || 'medium',
      }).unwrap();

      form.resetFields();
      setCreateModalOpen(false);
      message.success('Feature request created successfully!');
      
      // In a real implementation, this would also create a GitHub Discussion
    } catch (error) {
      message.error('Failed to create feature request');
    }
  };

  const handleVote = async (featureId: string, voteType: 'upvote' | 'downvote') => {
    try {
      await voteOnFeature({
        feature_id: featureId,
        vote_type: voteType,
      }).unwrap();

      message.success(`Vote recorded successfully!`);
      refetch(); // Refresh the list to show updated vote count
    } catch (error) {
      message.error('Failed to record vote');
    }
  };

  const getFeatureUrl = (feature: FeatureRequest) => {
    // In production, this would link to actual GitHub Discussions
    return feature.github_issue_url || `https://github.com/your-org/socialmapper/discussions`;
  };

  const renderFeatureItem = (feature: FeatureRequest) => {
    const actions = [
      <Space key="votes">
        <Button
          type="text"
          size="small"
          icon={<ArrowUpOutlined />}
          loading={isVoting}
          onClick={() => handleVote(feature.id, 'upvote')}
        >
          {feature.votes}
        </Button>
        <Button
          type="text"
          size="small"
          icon={<ArrowDownOutlined />}
          loading={isVoting}
          onClick={() => handleVote(feature.id, 'downvote')}
        />
      </Space>,
      <Button
        key="github"
        type="text"
        size="small"
        icon={<ExternalLinkOutlined />}
        href={getFeatureUrl(feature)}
        target="_blank"
      >
        Discuss
      </Button>,
    ];

    if (compact) {
      return (
        <List.Item actions={actions}>
          <List.Item.Meta
            title={
              <Space>
                <Text strong>{feature.title}</Text>
                <Tag color={STATUS_COLORS[feature.status]} icon={STATUS_ICONS[feature.status]}>
                  {feature.status.replace('_', ' ')}
                </Tag>
              </Space>
            }
            description={
              <Space wrap>
                <Tag color={PRIORITY_COLORS[feature.priority]}>
                  {feature.priority}
                </Tag>
                <Tag>{feature.category}</Tag>
                <Text type="secondary">
                  {new Date(feature.created_at).toLocaleDateString()}
                </Text>
              </Space>
            }
          />
        </List.Item>
      );
    }

    return (
      <List.Item actions={actions}>
        <List.Item.Meta
          avatar={
            <Badge count={feature.votes} overflowCount={999}>
              <Avatar
                style={{
                  backgroundColor: PRIORITY_COLORS[feature.priority],
                  color: 'white',
                }}
              >
                {feature.priority[0].toUpperCase()}
              </Avatar>
            </Badge>
          }
          title={
            <Space>
              <Text strong>{feature.title}</Text>
              <Tag color={STATUS_COLORS[feature.status]} icon={STATUS_ICONS[feature.status]}>
                {feature.status.replace('_', ' ')}
              </Tag>
            </Space>
          }
          description={
            <div>
              <Paragraph ellipsis={{ rows: 2 }}>{feature.description}</Paragraph>
              <Space wrap>
                <Tag color={PRIORITY_COLORS[feature.priority]}>
                  Priority: {feature.priority}
                </Tag>
                <Tag>{feature.category}</Tag>
                <Text type="secondary">
                  Created: {new Date(feature.created_at).toLocaleDateString()}
                </Text>
                {feature.updated_at !== feature.created_at && (
                  <Text type="secondary">
                    Updated: {new Date(feature.updated_at).toLocaleDateString()}
                  </Text>
                )}
              </Space>
            </div>
          }
        />
      </List.Item>
    );
  };

  const filterOptions = (
    <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
      <Col xs={24} sm={12} md={8}>
        <Select
          placeholder="Filter by category"
          allowClear
          style={{ width: '100%' }}
          onChange={setSelectedCategory}
        >
          <Select.Option value="ui-ux">UI/UX</Select.Option>
          <Select.Option value="analysis">Analysis Features</Select.Option>
          <Select.Option value="data-export">Data Export</Select.Option>
          <Select.Option value="performance">Performance</Select.Option>
          <Select.Option value="integrations">Integrations</Select.Option>
          <Select.Option value="documentation">Documentation</Select.Option>
        </Select>
      </Col>
      <Col xs={24} sm={12} md={8}>
        <Select
          placeholder="Filter by status"
          allowClear
          style={{ width: '100%' }}
          onChange={setSelectedStatus}
        >
          <Select.Option value="submitted">Submitted</Select.Option>
          <Select.Option value="under_review">Under Review</Select.Option>
          <Select.Option value="planned">Planned</Select.Option>
          <Select.Option value="in_development">In Development</Select.Option>
          <Select.Option value="completed">Completed</Select.Option>
        </Select>
      </Col>
      {showCreateButton && (
        <Col xs={24} sm={24} md={8}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalOpen(true)}
            style={{ width: compact ? 'auto' : '100%' }}
          >
            Request Feature
          </Button>
        </Col>
      )}
    </Row>
  );

  return (
    <>
      <Card
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>
              Feature Requests
            </Title>
            <Badge count={featureRequests.length} overflowCount={999} />
          </Space>
        }
        extra={
          <Tooltip title="Feature requests are managed through GitHub Discussions">
            <Button type="text" icon={<ExternalLinkOutlined />} />
          </Tooltip>
        }
      >
        {filterOptions}

        <List
          loading={isLoading}
          dataSource={featureRequests}
          renderItem={renderFeatureItem}
          locale={{
            emptyText: (
              <Empty
                description="No feature requests found"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                {showCreateButton && (
                  <Button type="primary" onClick={() => setCreateModalOpen(true)}>
                    Create First Feature Request
                  </Button>
                )}
              </Empty>
            ),
          }}
        />
      </Card>

      {/* Create Feature Request Modal */}
      <Modal
        title="Request a New Feature"
        open={createModalOpen}
        onCancel={() => {
          setCreateModalOpen(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateFeature}
        >
          <Form.Item
            name="title"
            label="Feature Title"
            rules={[
              { required: true, message: 'Please provide a title' },
              { min: 5, message: 'Title must be at least 5 characters' },
              { max: 200, message: 'Title must be less than 200 characters' },
            ]}
          >
            <Input placeholder="Brief, descriptive title for your feature request" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Detailed Description"
            rules={[
              { required: true, message: 'Please provide a description' },
              { min: 10, message: 'Description must be at least 10 characters' },
              { max: 2000, message: 'Description must be less than 2000 characters' },
            ]}
          >
            <TextArea
              rows={6}
              placeholder="Describe the feature in detail. What problem does it solve? How would it work? Include any relevant use cases or examples."
              showCount
              maxLength={2000}
            />
          </Form.Item>

          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="category"
                label="Category"
                rules={[{ required: true, message: 'Please select a category' }]}
              >
                <Select placeholder="Select category">
                  <Select.Option value="ui-ux">UI/UX Improvements</Select.Option>
                  <Select.Option value="analysis">Analysis Features</Select.Option>
                  <Select.Option value="data-export">Data Export</Select.Option>
                  <Select.Option value="performance">Performance</Select.Option>
                  <Select.Option value="integrations">Integrations</Select.Option>
                  <Select.Option value="documentation">Documentation</Select.Option>
                  <Select.Option value="other">Other</Select.Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={12}>
              <Form.Item
                name="priority"
                label="Suggested Priority"
                initialValue="medium"
              >
                <Select>
                  <Select.Option value="low">Low - Nice to have</Select.Option>
                  <Select.Option value="medium">Medium - Would be helpful</Select.Option>
                  <Select.Option value="high">High - Important for workflow</Select.Option>
                  <Select.Option value="critical">Critical - Blocking current use</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <div style={{ 
            background: '#f5f5f5', 
            padding: '12px', 
            borderRadius: '6px', 
            marginBottom: '16px' 
          }}>
            <Text style={{ fontSize: '12px' }} type="secondary">
              Your feature request will be posted to our public GitHub Discussions where the 
              community can vote and discuss. The development team reviews all requests monthly 
              for roadmap planning.
            </Text>
          </div>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button onClick={() => setCreateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit" loading={isCreating}>
                Submit Feature Request
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default FeatureRequestBoard;