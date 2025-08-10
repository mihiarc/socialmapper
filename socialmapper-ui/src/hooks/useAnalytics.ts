/**
 * Analytics Hook - Privacy-compliant user behavior tracking
 * Tracks user journeys, interactions, and conversion events
 */
import { useCallback, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import type { 
  UserAnalyticsEvent, 
  UserJourneyStep,
  UserSession 
} from '@types/api';

interface AnalyticsConfig {
  enableTracking?: boolean;
  sessionTimeout?: number; // minutes
  batchEvents?: boolean;
  batchSize?: number;
  flushInterval?: number; // milliseconds
}

interface UseAnalyticsReturn {
  trackEvent: (event: Omit<UserAnalyticsEvent, 'timestamp' | 'session_id'>) => void;
  trackPageView: (pageName?: string) => void;
  trackJourneyStep: (stepName: string, completed?: boolean, error?: string) => void;
  trackConversion: (conversionType: string, value?: number) => void;
  trackError: (error: string, context?: Record<string, any>) => void;
  startSession: () => void;
  endSession: () => void;
  getSessionId: () => string;
}

// Generate anonymous session ID
const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Generate anonymous user ID (persisted in localStorage)
const getUserId = (): string => {
  const existingId = localStorage.getItem('socialmapper_user_id');
  if (existingId) {
    return existingId;
  }
  
  const newId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  localStorage.setItem('socialmapper_user_id', newId);
  return newId;
};

const DEFAULT_CONFIG: Required<AnalyticsConfig> = {
  enableTracking: true,
  sessionTimeout: 30, // 30 minutes
  batchEvents: true,
  batchSize: 10,
  flushInterval: 30000, // 30 seconds
};

export const useAnalytics = (config: AnalyticsConfig = {}): UseAnalyticsReturn => {
  const fullConfig = { ...DEFAULT_CONFIG, ...config };
  const location = useLocation();
  
  const sessionIdRef = useRef<string>(generateSessionId());
  const userIdRef = useRef<string>(getUserId());
  const eventBatchRef = useRef<UserAnalyticsEvent[]>([]);
  const sessionStartRef = useRef<number>(Date.now());
  const lastActivityRef = useRef<number>(Date.now());
  const flushTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Check if user has consented to analytics
  const hasConsent = (): boolean => {
    const consent = localStorage.getItem('socialmapper_analytics_consent');
    return consent === 'granted';
  };

  // Flush events to server
  const flushEvents = useCallback(async () => {
    if (!fullConfig.enableTracking || !hasConsent() || eventBatchRef.current.length === 0) {
      return;
    }

    const eventsToFlush = [...eventBatchRef.current];
    eventBatchRef.current = [];

    try {
      // TODO: Send to analytics API endpoint
      console.log('Flushing analytics events:', eventsToFlush);
      
      // In production, this would send to your analytics API
      // await fetch('/api/v1/analytics/events', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ events: eventsToFlush })
      // });
      
    } catch (error) {
      console.error('Failed to send analytics events:', error);
      // Add events back to batch for retry
      eventBatchRef.current.unshift(...eventsToFlush);
    }
  }, [fullConfig.enableTracking]);

  // Add event to batch
  const addEvent = useCallback((event: UserAnalyticsEvent) => {
    if (!fullConfig.enableTracking || !hasConsent()) {
      return;
    }

    lastActivityRef.current = Date.now();
    
    const fullEvent: UserAnalyticsEvent = {
      ...event,
      timestamp: new Date().toISOString(),
      session_id: sessionIdRef.current,
      user_id: userIdRef.current,
    };

    eventBatchRef.current.push(fullEvent);

    // Flush if batch is full or not batching
    if (!fullConfig.batchEvents || eventBatchRef.current.length >= fullConfig.batchSize) {
      flushEvents();
    }
  }, [fullConfig.enableTracking, fullConfig.batchEvents, fullConfig.batchSize, flushEvents]);

  // Track generic event
  const trackEvent = useCallback((event: Omit<UserAnalyticsEvent, 'timestamp' | 'session_id'>) => {
    addEvent(event as UserAnalyticsEvent);
  }, [addEvent]);

  // Track page view
  const trackPageView = useCallback((pageName?: string) => {
    const page = pageName || location.pathname;
    addEvent({
      event_name: 'page_view',
      event_category: 'navigation',
      properties: {
        page,
        referrer: document.referrer,
        url: window.location.href,
      },
    });
  }, [location.pathname, addEvent]);

  // Track journey step
  const trackJourneyStep = useCallback((stepName: string, completed: boolean = true, error?: string) => {
    addEvent({
      event_name: 'journey_step',
      event_category: completed ? 'conversion' : 'interaction',
      properties: {
        step_name: stepName,
        completed,
        error,
        duration_ms: Date.now() - lastActivityRef.current,
      },
    });
  }, [addEvent]);

  // Track conversion event
  const trackConversion = useCallback((conversionType: string, value?: number) => {
    addEvent({
      event_name: 'conversion',
      event_category: 'conversion',
      properties: {
        conversion_type: conversionType,
        value,
      },
    });
  }, [addEvent]);

  // Track error
  const trackError = useCallback((error: string, context?: Record<string, any>) => {
    addEvent({
      event_name: 'error',
      event_category: 'error',
      properties: {
        error,
        context,
        url: window.location.href,
      },
    });
  }, [addEvent]);

  // Start new session
  const startSession = useCallback(() => {
    sessionIdRef.current = generateSessionId();
    sessionStartRef.current = Date.now();
    lastActivityRef.current = Date.now();
    
    addEvent({
      event_name: 'session_start',
      event_category: 'navigation',
      properties: {
        user_agent: navigator.userAgent,
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
    });
  }, [addEvent]);

  // End session
  const endSession = useCallback(() => {
    const sessionDuration = Date.now() - sessionStartRef.current;
    
    addEvent({
      event_name: 'session_end',
      event_category: 'navigation',
      properties: {
        duration_ms: sessionDuration,
      },
    });

    // Flush any remaining events
    flushEvents();
  }, [addEvent, flushEvents]);

  // Get current session ID
  const getSessionId = useCallback(() => sessionIdRef.current, []);

  // Set up automatic page view tracking
  useEffect(() => {
    trackPageView();
  }, [location.pathname, trackPageView]);

  // Set up periodic flush timer
  useEffect(() => {
    if (fullConfig.batchEvents) {
      flushTimerRef.current = setInterval(() => {
        flushEvents();
      }, fullConfig.flushInterval);

      return () => {
        if (flushTimerRef.current) {
          clearInterval(flushTimerRef.current);
        }
      };
    }
  }, [fullConfig.batchEvents, fullConfig.flushInterval, flushEvents]);

  // Check for session timeout
  useEffect(() => {
    const checkSessionTimeout = () => {
      const timeSinceLastActivity = Date.now() - lastActivityRef.current;
      const timeoutMs = fullConfig.sessionTimeout * 60 * 1000;
      
      if (timeSinceLastActivity > timeoutMs) {
        endSession();
        startSession();
      }
    };

    const timeoutChecker = setInterval(checkSessionTimeout, 60000); // Check every minute
    return () => clearInterval(timeoutChecker);
  }, [fullConfig.sessionTimeout, endSession, startSession]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      flushEvents(); // Flush remaining events
    };
  }, [flushEvents]);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        flushEvents(); // Flush events when page becomes hidden
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [flushEvents]);

  return {
    trackEvent,
    trackPageView,
    trackJourneyStep,
    trackConversion,
    trackError,
    startSession,
    endSession,
    getSessionId,
  };
};