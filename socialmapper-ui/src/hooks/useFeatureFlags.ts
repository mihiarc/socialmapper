/**
 * Feature Flags Hook - A/B testing and gradual feature rollout
 * Supports percentage-based rollouts, user segmentation, and experiment tracking
 */
import { useEffect, useState, useCallback, useMemo } from 'react';
import { useAnalytics } from './useAnalytics';

interface FeatureFlag {
  key: string;
  enabled: boolean;
  rolloutPercentage?: number; // 0-100
  userSegments?: string[]; // e.g., ['academic', 'government']
  experiment?: {
    name: string;
    variant: string; // 'control' | 'treatment' | custom variant
    description?: string;
  };
  metadata?: Record<string, any>;
}

interface FeatureFlagsConfig {
  [key: string]: FeatureFlag;
}

interface UseFeatureFlagsReturn {
  isEnabled: (flagKey: string) => boolean;
  getVariant: (flagKey: string) => string | null;
  trackExperiment: (flagKey: string, event: string, properties?: Record<string, any>) => void;
  getAllFlags: () => FeatureFlagsConfig;
  refreshFlags: () => void;
}

// Mock feature flags configuration (in production, this would come from a service)
const DEFAULT_FLAGS: FeatureFlagsConfig = {
  // UI/UX Experiments
  'new_results_layout': {
    key: 'new_results_layout',
    enabled: true,
    rolloutPercentage: 50, // 50% of users see new layout
    experiment: {
      name: 'Results Layout A/B Test',
      variant: 'control', // Will be set per user
      description: 'Testing new card-based results layout vs current table layout'
    }
  },
  
  'enhanced_feedback_modal': {
    key: 'enhanced_feedback_modal',
    enabled: true,
    rolloutPercentage: 25, // 25% rollout
    experiment: {
      name: 'Feedback Modal Enhancement',
      variant: 'control',
      description: 'Testing enhanced feedback modal with sentiment analysis'
    }
  },

  // Feature Rollouts
  'advanced_export_options': {
    key: 'advanced_export_options',
    enabled: true,
    rolloutPercentage: 75, // Gradual rollout
  },

  'real_time_collaboration': {
    key: 'real_time_collaboration',
    enabled: false, // Not ready yet
    rolloutPercentage: 0,
    userSegments: ['beta_testers'], // Only for beta testers when enabled
  },

  'ai_powered_insights': {
    key: 'ai_powered_insights',
    enabled: true,
    rolloutPercentage: 10, // Limited beta
    userSegments: ['academic', 'government'], // Only for specific user types
  },

  // Performance Experiments  
  'lazy_loading_maps': {
    key: 'lazy_loading_maps',
    enabled: true,
    rolloutPercentage: 50,
    experiment: {
      name: 'Map Loading Performance Test',
      variant: 'control',
      description: 'Testing lazy loading vs eager loading for map components'
    }
  },

  // Analytics Improvements
  'detailed_analytics': {
    key: 'detailed_analytics',
    enabled: true,
    rolloutPercentage: 80,
  },

  // Community Features
  'community_showcase': {
    key: 'community_showcase',
    enabled: true,
    rolloutPercentage: 100, // Fully rolled out
  },

  'user_profiles': {
    key: 'user_profiles',
    enabled: false, // In development
    rolloutPercentage: 0,
  }
};

// Generate consistent user hash for A/B testing
const getUserHash = (userId?: string): number => {
  const id = userId || localStorage.getItem('socialmapper_user_id') || 'anonymous';
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    const char = id.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
};

// Determine if user should be in rollout based on percentage
const shouldRolloutToUser = (percentage: number, userHash: number): boolean => {
  if (percentage >= 100) return true;
  if (percentage <= 0) return false;
  return (userHash % 100) < percentage;
};

// Get user segment (this would normally come from user profile)
const getUserSegment = (): string => {
  return localStorage.getItem('socialmapper_user_type') || 'individual';
};

export const useFeatureFlags = (): UseFeatureFlagsReturn => {
  const [flags, setFlags] = useState<FeatureFlagsConfig>(DEFAULT_FLAGS);
  const [userHash, setUserHash] = useState<number>(0);
  const { trackEvent } = useAnalytics();

  // Calculate user hash on mount
  useEffect(() => {
    const hash = getUserHash();
    setUserHash(hash);
  }, []);

  // Determine user's variant assignments
  const userVariants = useMemo(() => {
    const variants: Record<string, string> = {};
    const userSegment = getUserSegment();

    Object.values(flags).forEach(flag => {
      if (!flag.enabled) {
        variants[flag.key] = 'disabled';
        return;
      }

      // Check user segment restrictions
      if (flag.userSegments && !flag.userSegments.includes(userSegment)) {
        variants[flag.key] = 'not_eligible';
        return;
      }

      // Check rollout percentage
      if (flag.rolloutPercentage !== undefined) {
        const inRollout = shouldRolloutToUser(flag.rolloutPercentage, userHash);
        if (!inRollout) {
          variants[flag.key] = 'not_in_rollout';
          return;
        }
      }

      // Determine experiment variant
      if (flag.experiment) {
        const variantHash = (userHash + flag.key.length) % 100;
        variants[flag.key] = variantHash < 50 ? 'control' : 'treatment';
      } else {
        variants[flag.key] = 'enabled';
      }
    });

    return variants;
  }, [flags, userHash]);

  // Check if a feature flag is enabled for this user
  const isEnabled = useCallback((flagKey: string): boolean => {
    const variant = userVariants[flagKey];
    return variant && !['disabled', 'not_eligible', 'not_in_rollout'].includes(variant);
  }, [userVariants]);

  // Get the variant for a feature flag
  const getVariant = useCallback((flagKey: string): string | null => {
    return userVariants[flagKey] || null;
  }, [userVariants]);

  // Track experiment events
  const trackExperiment = useCallback((
    flagKey: string, 
    event: string, 
    properties?: Record<string, any>
  ) => {
    const flag = flags[flagKey];
    const variant = userVariants[flagKey];

    if (flag?.experiment && variant) {
      trackEvent({
        event_name: `experiment_${event}`,
        event_category: 'conversion',
        properties: {
          experiment_name: flag.experiment.name,
          experiment_key: flagKey,
          variant,
          ...properties,
        },
      });
    }
  }, [flags, userVariants, trackEvent]);

  // Get all flags (for debugging/admin)
  const getAllFlags = useCallback((): FeatureFlagsConfig => {
    return flags;
  }, [flags]);

  // Refresh flags from server (mock implementation)
  const refreshFlags = useCallback(() => {
    // In production, this would fetch from a feature flag service
    console.log('Refreshing feature flags...');
    
    // Mock server fetch
    setTimeout(() => {
      setFlags(prevFlags => ({
        ...prevFlags,
        // Could update flags based on server response
      }));
    }, 100);
  }, []);

  // Track flag assignments for analytics
  useEffect(() => {
    Object.entries(userVariants).forEach(([flagKey, variant]) => {
      const flag = flags[flagKey];
      if (flag?.experiment && variant && ['control', 'treatment'].includes(variant)) {
        trackEvent({
          event_name: 'experiment_assigned',
          event_category: 'interaction',
          properties: {
            experiment_name: flag.experiment.name,
            experiment_key: flagKey,
            variant,
          },
        });
      }
    });
  }, [userVariants, flags, trackEvent]);

  return {
    isEnabled,
    getVariant,
    trackExperiment,
    getAllFlags,
    refreshFlags,
  };
};