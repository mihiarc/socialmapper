/**
 * React component for performance monitoring and Web Vitals tracking
 */

import React, { useEffect, useState } from 'react';
import { Alert, Badge, Collapse, Progress, Typography } from 'antd';
import { 
  DashboardOutlined, 
  ThunderboltOutlined, 
  ClockCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { usePerformanceMonitoring, PerformanceMetrics, PERFORMANCE_THRESHOLDS } from '../../utils/performance';

const { Panel } = Collapse;
const { Text, Title } = Typography;

interface PerformanceMonitorProps {
  showDetails?: boolean;
  compact?: boolean;
  onPerformanceIssue?: (issue: { metric: string; value: number; threshold: number }) => void;
}

const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({
  showDetails = false,
  compact = false,
  onPerformanceIssue
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({});
  const [performanceScore, setPerformanceScore] = useState({ score: 0, details: {} });
  const [visible, setVisible] = useState(false);
  const performanceMonitoring = usePerformanceMonitoring();

  useEffect(() => {
    // Only show in development or when explicitly enabled
    const shouldShow = import.meta.env.MODE === 'development' || 
                      localStorage.getItem('show-performance-monitor') === 'true' ||
                      showDetails;
    
    setVisible(shouldShow);

    if (shouldShow) {
      const updateMetrics = () => {
        const currentMetrics = performanceMonitoring.getMetrics();
        const score = performanceMonitoring.getPerformanceScore();
        
        setMetrics(currentMetrics);
        setPerformanceScore(score);

        // Check for performance issues
        checkPerformanceIssues(currentMetrics);
      };

      // Update metrics immediately and then every 5 seconds
      updateMetrics();
      const interval = setInterval(updateMetrics, 5000);

      return () => clearInterval(interval);
    }
    return undefined;
  }, [showDetails, performanceMonitoring, onPerformanceIssue]);

  const checkPerformanceIssues = (currentMetrics: PerformanceMetrics) => {
    if (!onPerformanceIssue) return;

    const issues: Array<{ metric: string; value: number; threshold: number }> = [];

    // Check Web Vitals
    if (currentMetrics.cls && currentMetrics.cls > PERFORMANCE_THRESHOLDS.CLS.needsImprovement) {
      issues.push({ metric: 'CLS', value: currentMetrics.cls, threshold: PERFORMANCE_THRESHOLDS.CLS.needsImprovement });
    }
    if (currentMetrics.fid && currentMetrics.fid > PERFORMANCE_THRESHOLDS.FID.needsImprovement) {
      issues.push({ metric: 'FID', value: currentMetrics.fid, threshold: PERFORMANCE_THRESHOLDS.FID.needsImprovement });
    }
    if (currentMetrics.lcp && currentMetrics.lcp > PERFORMANCE_THRESHOLDS.LCP.needsImprovement) {
      issues.push({ metric: 'LCP', value: currentMetrics.lcp, threshold: PERFORMANCE_THRESHOLDS.LCP.needsImprovement });
    }

    issues.forEach(issue => onPerformanceIssue(issue));
  };

  const getMetricStatus = (value: number | undefined, thresholds: { good: number; needsImprovement: number }) => {
    if (value === undefined) return { status: 'default', color: '#d9d9d9' };
    
    if (value <= thresholds.good) return { status: 'success', color: '#52c41a' };
    if (value <= thresholds.needsImprovement) return { status: 'warning', color: '#faad14' };
    return { status: 'error', color: '#ff4d4f' };
  };

  const formatDuration = (ms: number | undefined) => {
    if (ms === undefined) return 'N/A';
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatBytes = (bytes: number | undefined) => {
    if (bytes === undefined) return 'N/A';
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!visible && !showDetails) {
    return null;
  }

  const WebVitalsPanel = () => (
    <div style={{ marginBottom: 16 }}>
      <Title level={5}>
        <ThunderboltOutlined /> Core Web Vitals
      </Title>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
        {[
          { key: 'lcp', label: 'Largest Contentful Paint', value: metrics.lcp, thresholds: PERFORMANCE_THRESHOLDS.LCP },
          { key: 'fid', label: 'First Input Delay', value: metrics.fid, thresholds: PERFORMANCE_THRESHOLDS.FID },
          { key: 'cls', label: 'Cumulative Layout Shift', value: metrics.cls, thresholds: PERFORMANCE_THRESHOLDS.CLS },
          { key: 'fcp', label: 'First Contentful Paint', value: metrics.fcp, thresholds: PERFORMANCE_THRESHOLDS.FCP },
          { key: 'ttfb', label: 'Time to First Byte', value: metrics.ttfb, thresholds: PERFORMANCE_THRESHOLDS.TTFB }
        ].map(({ key, label, value, thresholds }) => {
          const status = getMetricStatus(value, thresholds);
          return (
            <div key={key} style={{ padding: 8, border: '1px solid #f0f0f0', borderRadius: 4 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text strong style={{ fontSize: 12 }}>{label}</Text>
                <Badge status={status.status as any} />
              </div>
              <div style={{ fontSize: 18, fontWeight: 'bold', color: status.color }}>
                {key === 'cls' ? (value?.toFixed(3) || 'N/A') : formatDuration(value)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const ApplicationMetricsPanel = () => (
    <div style={{ marginBottom: 16 }}>
      <Title level={5}>
        <DashboardOutlined /> Application Metrics
      </Title>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
        <div style={{ padding: 8, border: '1px solid #f0f0f0', borderRadius: 4 }}>
          <Text strong style={{ fontSize: 12 }}>App Load Time</Text>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>
            {formatDuration(metrics.appLoadTime)}
          </div>
        </div>
        <div style={{ padding: 8, border: '1px solid #f0f0f0', borderRadius: 4 }}>
          <Text strong style={{ fontSize: 12 }}>Route Change Time</Text>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>
            {formatDuration(metrics.routeChangeTime)}
          </div>
        </div>
        <div style={{ padding: 8, border: '1px solid #f0f0f0', borderRadius: 4 }}>
          <Text strong style={{ fontSize: 12 }}>API Response Time</Text>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>
            {formatDuration(metrics.apiResponseTime)}
          </div>
        </div>
        <div style={{ padding: 8, border: '1px solid #f0f0f0', borderRadius: 4 }}>
          <Text strong style={{ fontSize: 12 }}>Memory Usage</Text>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>
            {formatBytes(metrics.memoryUsage)}
          </div>
        </div>
      </div>
    </div>
  );

  const BusinessMetricsPanel = () => (
    <div style={{ marginBottom: 16 }}>
      <Title level={5}>
        <ClockCircleOutlined /> Business Metrics
      </Title>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
        <div style={{ padding: 8, border: '1px solid #f0f0f0', borderRadius: 4 }}>
          <Text strong style={{ fontSize: 12 }}>Analysis Time</Text>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>
            {formatDuration(metrics.analysisCompleteTime)}
          </div>
        </div>
        <div style={{ padding: 8, border: '1px solid #f0f0f0', borderRadius: 4 }}>
          <Text strong style={{ fontSize: 12 }}>User Engagement</Text>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>
            {formatDuration(metrics.userEngagementTime)}
          </div>
        </div>
        <div style={{ padding: 8, border: '1px solid #f0f0f0', borderRadius: 4 }}>
          <Text strong style={{ fontSize: 12 }}>Error Count</Text>
          <div style={{ fontSize: 18, fontWeight: 'bold', color: metrics.errorCount && metrics.errorCount > 0 ? '#ff4d4f' : '#52c41a' }}>
            {metrics.errorCount || 0}
          </div>
        </div>
        <div style={{ padding: 8, border: '1px solid #f0f0f0', borderRadius: 4 }}>
          <Text strong style={{ fontSize: 12 }}>Feature Usage</Text>
          <div style={{ fontSize: 14 }}>
            {metrics.featureUsage ? Object.keys(metrics.featureUsage).length : 0} features used
          </div>
        </div>
      </div>
    </div>
  );

  if (compact) {
    return (
      <div style={{ position: 'fixed', top: 10, right: 10, zIndex: 1000 }}>
        <Badge count={performanceScore.score} showZero>
          <div 
            style={{ 
              padding: '4px 8px', 
              background: performanceScore.score >= 80 ? '#f6ffed' : performanceScore.score >= 60 ? '#fff7e6' : '#fff2f0',
              border: `1px solid ${performanceScore.score >= 80 ? '#b7eb8f' : performanceScore.score >= 60 ? '#ffd591' : '#ffccc7'}`,
              borderRadius: 4,
              fontSize: 12,
              cursor: 'pointer'
            }}
            onClick={() => setVisible(!visible)}
          >
            Performance: {performanceScore.score}
          </div>
        </Badge>
      </div>
    );
  }

  return (
    <div style={{ margin: '16px 0' }}>
      {performanceScore.score < 60 && (
        <Alert
          message="Performance Issue Detected"
          description="Some performance metrics are below recommended thresholds. Check the details below."
          type="warning"
          icon={<ExclamationCircleOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}

      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 8 }}>
          <Title level={4} style={{ margin: 0 }}>Performance Score</Title>
          <Badge 
            count={performanceScore.score} 
            showZero 
            style={{ 
              backgroundColor: performanceScore.score >= 80 ? '#52c41a' : 
                             performanceScore.score >= 60 ? '#faad14' : '#ff4d4f' 
            }} 
          />
        </div>
        <Progress 
          percent={performanceScore.score} 
          strokeColor={
            performanceScore.score >= 80 ? '#52c41a' : 
            performanceScore.score >= 60 ? '#faad14' : '#ff4d4f'
          }
        />
      </div>

      <Collapse defaultActiveKey={showDetails ? ['1', '2', '3'] : []}>
        <Panel header="Core Web Vitals" key="1">
          <WebVitalsPanel />
        </Panel>
        <Panel header="Application Metrics" key="2">
          <ApplicationMetricsPanel />
        </Panel>
        <Panel header="Business Metrics" key="3">
          <BusinessMetricsPanel />
        </Panel>
      </Collapse>

      {import.meta.env.MODE === 'development' && (
        <div style={{ marginTop: 16, fontSize: 12, color: '#666' }}>
          Session: {metrics.sessionId} | Viewport: {metrics.viewport} | Connection: {metrics.connection}
        </div>
      )}
    </div>
  );
};

export default PerformanceMonitor;