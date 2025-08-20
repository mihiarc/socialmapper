/**
 * Comprehensive performance monitoring utilities for SocialMapper React app
 * Includes Web Vitals, custom metrics, and performance tracking
 */

import { getCLS, getFID, getFCP, getLCP, getTTFB, Metric } from 'web-vitals';

// Performance metrics interface
export interface PerformanceMetrics {
  // Core Web Vitals
  cls?: number;  // Cumulative Layout Shift
  fid?: number;  // First Input Delay
  fcp?: number;  // First Contentful Paint
  lcp?: number;  // Largest Contentful Paint
  ttfb?: number; // Time to First Byte
  
  // Custom application metrics
  appLoadTime?: number;
  routeChangeTime?: number;
  apiResponseTime?: number;
  errorCount?: number;
  memoryUsage?: number;
  
  // Business metrics
  analysisStartTime?: number;
  analysisCompleteTime?: number;
  userEngagementTime?: number;
  featureUsage?: Record<string, number>;
  
  // User info
  userAgent?: string;
  viewport?: string;
  connection?: string;
  timestamp?: number;
  sessionId?: string;
  userId?: string;
}

// Performance thresholds
export const PERFORMANCE_THRESHOLDS = {
  // Core Web Vitals thresholds (Google recommendations)
  CLS: { good: 0.1, needsImprovement: 0.25 },
  FID: { good: 100, needsImprovement: 300 },
  LCP: { good: 2500, needsImprovement: 4000 },
  FCP: { good: 1800, needsImprovement: 3000 },
  TTFB: { good: 800, needsImprovement: 1800 },
  
  // Custom thresholds
  APP_LOAD: { good: 3000, needsImprovement: 5000 },
  ROUTE_CHANGE: { good: 500, needsImprovement: 1000 },
  API_RESPONSE: { good: 1000, needsImprovement: 3000 },
} as const;

class PerformanceMonitor {
  private metrics: PerformanceMetrics = {};
  private observers: PerformanceObserver[] = [];
  private sessionId: string;
  private analyticsEndpoint: string;
  private isEnabled: boolean;

  constructor(config: {
    analyticsEndpoint?: string;
    enabled?: boolean;
    sessionId?: string;
  } = {}) {
    this.analyticsEndpoint = config.analyticsEndpoint || '/api/v1/analytics/performance';
    this.isEnabled = config.enabled ?? true;
    this.sessionId = config.sessionId || this.generateSessionId();
    
    if (this.isEnabled && typeof window !== 'undefined') {
      this.initializeMonitoring();
    }
  }

  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private initializeMonitoring(): void {
    // Initialize Web Vitals
    this.initializeWebVitals();
    
    // Initialize custom performance observers
    this.initializeCustomObservers();
    
    // Initialize user info collection
    this.collectUserInfo();
    
    // Initialize memory monitoring
    this.initializeMemoryMonitoring();
    
    // Initialize navigation monitoring
    this.initializeNavigationMonitoring();
    
    // Initialize error monitoring
    this.initializeErrorMonitoring();
    
    // Initialize resource monitoring
    this.initializeResourceMonitoring();
    
    // Send initial metrics
    this.scheduleMetricsSending();
  }

  private initializeWebVitals(): void {
    const handleMetric = (metric: Metric) => {
      const metricName = metric.name.toLowerCase() as keyof PerformanceMetrics;
      (this.metrics as any)[metricName] = metric.value;
      
      // Log performance issues
      this.logPerformanceIssue(metric);
      
      // Send real-time critical metrics
      if (this.isCriticalMetric(metric)) {
        this.sendMetricsImmediate();
      }
    };

    getCLS(handleMetric);
    getFID(handleMetric);
    getFCP(handleMetric);
    getLCP(handleMetric);
    getTTFB(handleMetric);
  }

  private initializeCustomObservers(): void {
    // Navigation timing
    if ('PerformanceObserver' in window) {
      const navObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.entryType === 'navigation') {
            const navEntry = entry as PerformanceNavigationTiming;
            this.metrics.appLoadTime = navEntry.loadEventEnd - navEntry.fetchStart;
          }
        });
      });
      
      navObserver.observe({ entryTypes: ['navigation'] });
      this.observers.push(navObserver);
    }

    // Paint timing
    if ('PerformanceObserver' in window) {
      const paintObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.name === 'first-contentful-paint') {
            this.metrics.fcp = entry.startTime;
          }
        });
      });
      
      try {
        paintObserver.observe({ entryTypes: ['paint'] });
        this.observers.push(paintObserver);
      } catch (e) {
        console.warn('Paint timing not supported');
      }
    }
  }

  private collectUserInfo(): void {
    this.metrics.userAgent = navigator.userAgent;
    this.metrics.viewport = `${window.innerWidth}x${window.innerHeight}`;
    this.metrics.timestamp = Date.now();
    this.metrics.sessionId = this.sessionId;
    
    // Connection information
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      if (connection) {
        this.metrics.connection = `${connection.effectiveType}-${connection.downlink}mbps`;
      }
    }
  }

  private initializeMemoryMonitoring(): void {
    if ('memory' in performance) {
      const updateMemoryUsage = () => {
        const memory = (performance as any).memory;
        this.metrics.memoryUsage = memory.usedJSHeapSize;
      };
      
      updateMemoryUsage();
      setInterval(updateMemoryUsage, 30000); // Update every 30 seconds
    }
  }

  private initializeNavigationMonitoring(): void {
    // Monitor route changes (assuming React Router)
    let routeChangeStart: number;
    
    const originalPushState = history.pushState;
    history.pushState = function(...args) {
      routeChangeStart = performance.now();
      originalPushState.apply(this, args);
    };

    const originalReplaceState = history.replaceState;
    history.replaceState = function(...args) {
      routeChangeStart = performance.now();
      originalReplaceState.apply(this, args);
    };

    // Listen for route changes completion
    window.addEventListener('popstate', () => {
      if (routeChangeStart) {
        this.metrics.routeChangeTime = performance.now() - routeChangeStart;
      }
    });
  }

  private initializeErrorMonitoring(): void {
    this.metrics.errorCount = 0;
    
    window.addEventListener('error', (event) => {
      this.metrics.errorCount = (this.metrics.errorCount || 0) + 1;
      this.logError('javascript', event.error);
    });

    window.addEventListener('unhandledrejection', (event) => {
      this.metrics.errorCount = (this.metrics.errorCount || 0) + 1;
      this.logError('promise', event.reason);
    });
  }

  private initializeResourceMonitoring(): void {
    if ('PerformanceObserver' in window) {
      const resourceObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          // Monitor API calls specifically
          if (entry.name.includes('/api/')) {
            const resourceEntry = entry as PerformanceResourceTiming;
            const duration = resourceEntry.responseEnd - resourceEntry.requestStart;
            this.recordApiResponse(entry.name, duration);
          }
        });
      });
      
      try {
        resourceObserver.observe({ entryTypes: ['resource'] });
        this.observers.push(resourceObserver);
      } catch (e) {
        console.warn('Resource timing not supported');
      }
    }
  }

  private isCriticalMetric(metric: Metric): boolean {
    const thresholds = PERFORMANCE_THRESHOLDS;
    
    switch (metric.name) {
      case 'CLS':
        return metric.value > thresholds.CLS.needsImprovement;
      case 'FID':
        return metric.value > thresholds.FID.needsImprovement;
      case 'LCP':
        return metric.value > thresholds.LCP.needsImprovement;
      case 'FCP':
        return metric.value > thresholds.FCP.needsImprovement;
      case 'TTFB':
        return metric.value > thresholds.TTFB.needsImprovement;
      default:
        return false;
    }
  }

  private logPerformanceIssue(metric: Metric): void {
    if (this.isCriticalMetric(metric)) {
      console.warn(`Performance issue detected: ${metric.name} = ${metric.value}`);
      
      // Could send to error tracking service
      this.sendErrorToTracking({
        type: 'performance',
        metric: metric.name,
        value: metric.value,
        timestamp: Date.now(),
        url: window.location.href,
        userAgent: navigator.userAgent
      });
    }
  }

  private logError(type: string, error: any): void {
    console.error(`${type} error:`, error);
    
    this.sendErrorToTracking({
      type,
      error: error?.message || String(error),
      stack: error?.stack,
      timestamp: Date.now(),
      url: window.location.href
    });
  }

  private sendErrorToTracking(errorData: any): void {
    // Send to your error tracking service
    if (this.analyticsEndpoint) {
      fetch(`${this.analyticsEndpoint}/errors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorData),
        keepalive: true
      }).catch(() => {
        // Silently fail to avoid infinite error loops
      });
    }
  }

  // Public methods for application to use
  public recordApiResponse(url: string, duration: number): void {
    this.metrics.apiResponseTime = duration;
    
    if (duration > PERFORMANCE_THRESHOLDS.API_RESPONSE.needsImprovement) {
      console.warn(`Slow API response: ${url} took ${duration}ms`);
    }
  }

  public recordAnalysisStart(): void {
    this.metrics.analysisStartTime = performance.now();
  }

  public recordAnalysisComplete(): void {
    if (this.metrics.analysisStartTime) {
      const duration = performance.now() - this.metrics.analysisStartTime;
      this.metrics.analysisCompleteTime = duration;
    }
  }

  public recordFeatureUsage(feature: string, metadata?: Record<string, any>): void {
    if (!this.metrics.featureUsage) {
      this.metrics.featureUsage = {};
    }
    // Track usage count
    this.metrics.featureUsage[feature] = (this.metrics.featureUsage[feature] || 0) + 1;
    
    // Optionally log metadata for debugging/analytics
    if (metadata && this.isEnabled) {
      console.debug(`Feature usage: ${feature}`, metadata);
    }
  }

  public recordUserEngagement(startTime: number): void {
    this.metrics.userEngagementTime = performance.now() - startTime;
  }

  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  public getPerformanceScore(): { score: number; details: Record<string, string> } {
    const details: Record<string, string> = {};
    let totalScore = 0;
    let metricCount = 0;

    // Score Web Vitals
    const webVitals = [
      { name: 'CLS', value: this.metrics.cls, thresholds: PERFORMANCE_THRESHOLDS.CLS },
      { name: 'FID', value: this.metrics.fid, thresholds: PERFORMANCE_THRESHOLDS.FID },
      { name: 'LCP', value: this.metrics.lcp, thresholds: PERFORMANCE_THRESHOLDS.LCP },
      { name: 'FCP', value: this.metrics.fcp, thresholds: PERFORMANCE_THRESHOLDS.FCP },
      { name: 'TTFB', value: this.metrics.ttfb, thresholds: PERFORMANCE_THRESHOLDS.TTFB }
    ];

    webVitals.forEach(({ name, value, thresholds }) => {
      if (value !== undefined) {
        metricCount++;
        if (value <= thresholds.good) {
          totalScore += 90;
          details[name] = 'Good';
        } else if (value <= thresholds.needsImprovement) {
          totalScore += 50;
          details[name] = 'Needs Improvement';
        } else {
          totalScore += 10;
          details[name] = 'Poor';
        }
      }
    });

    const averageScore = metricCount > 0 ? Math.round(totalScore / metricCount) : 0;
    return { score: averageScore, details };
  }

  private scheduleMetricsSending(): void {
    // Send metrics periodically
    setInterval(() => {
      this.sendMetrics();
    }, 30000); // Every 30 seconds

    // Send metrics on page unload
    window.addEventListener('beforeunload', () => {
      this.sendMetricsImmediate();
    });

    // Send metrics on visibility change (when user switches tabs)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.sendMetricsImmediate();
      }
    });
  }

  private async sendMetrics(): Promise<void> {
    if (!this.analyticsEndpoint) return;

    try {
      await fetch(this.analyticsEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...this.metrics,
          timestamp: Date.now()
        })
      });
    } catch (error) {
      console.warn('Failed to send performance metrics:', error);
    }
  }

  private sendMetricsImmediate(): void {
    if (!this.analyticsEndpoint) return;

    // Use sendBeacon for reliability on page unload
    const data = JSON.stringify({
      ...this.metrics,
      timestamp: Date.now()
    });

    if (navigator.sendBeacon) {
      navigator.sendBeacon(this.analyticsEndpoint, data);
    } else {
      // Fallback for older browsers
      this.sendMetrics().catch(() => {});
    }
  }

  public cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor({
  enabled: import.meta.env.MODE === 'production',
  analyticsEndpoint: import.meta.env.VITE_ANALYTICS_ENDPOINT
});

// React hook for performance monitoring
export function usePerformanceMonitoring() {
  return {
    recordApiResponse: performanceMonitor.recordApiResponse.bind(performanceMonitor),
    recordAnalysisStart: performanceMonitor.recordAnalysisStart.bind(performanceMonitor),
    recordAnalysisComplete: performanceMonitor.recordAnalysisComplete.bind(performanceMonitor),
    recordFeatureUsage: performanceMonitor.recordFeatureUsage.bind(performanceMonitor),
    recordUserEngagement: performanceMonitor.recordUserEngagement.bind(performanceMonitor),
    getMetrics: performanceMonitor.getMetrics.bind(performanceMonitor),
    getPerformanceScore: performanceMonitor.getPerformanceScore.bind(performanceMonitor)
  };
}