/**
 * k6 Load Test for Health Check Endpoints
 * 
 * This test validates the performance and reliability of health check endpoints
 * under various load conditions.
 */

import { check, sleep } from 'k6';
import { makeRequest, validateHealthResponse, randomSleep } from '../utils/helpers.js';
import { baseThresholds, endpointSpecificThresholds, loadProfiles, environments } from '../config/thresholds.js';

// Test configuration
const TEST_ENV = __ENV.TEST_ENV || 'staging';
const LOAD_PROFILE = __ENV.LOAD_PROFILE || 'load';
const BASE_URL = environments[TEST_ENV]?.baseUrl || environments.staging.baseUrl;

// Apply load profile
export let options = {
  ...loadProfiles[LOAD_PROFILE],
  thresholds: {
    ...baseThresholds,
    ...endpointSpecificThresholds.health
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  tags: {
    test_type: 'health_endpoints',
    environment: TEST_ENV,
    load_profile: LOAD_PROFILE
  }
};

export default function() {
  const testData = {
    timestamp: Date.now(),
    user_id: __VU,
    iteration: __ITER
  };

  // Test 1: Basic health check endpoint
  const healthResponse = makeRequest('GET', `${BASE_URL}/api/v1/health`);
  const healthValid = validateHealthResponse(healthResponse);
  
  if (!healthValid) {
    console.error(`Health check failed for VU ${__VU} at iteration ${__ITER}`);
  }

  // Add custom metrics
  check(healthResponse, {
    'health endpoint response time < 100ms': (r) => r.timings.duration < 100,
    'health endpoint has correct content-type': (r) => 
      r.headers['Content-Type'] && r.headers['Content-Type'].includes('application/json')
  });

  randomSleep(0.5, 1.5);

  // Test 2: Detailed status endpoint (if available)
  const statusResponse = makeRequest('GET', `${BASE_URL}/api/v1/status`);
  
  const statusValid = check(statusResponse, {
    'status endpoint responds': (r) => r.status === 200,
    'status response has system info': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.system_info !== undefined;
      } catch {
        return false;
      }
    },
    'status response has configuration': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.configuration !== undefined;
      } catch {
        return false;
      }
    }
  });

  if (!statusValid) {
    console.error(`Status check failed for VU ${__VU} at iteration ${__ITER}`);
  }

  randomSleep(1, 2);

  // Test 3: Health check under rapid requests (burst test)
  for (let i = 0; i < 3; i++) {
    const burstResponse = makeRequest('GET', `${BASE_URL}/api/v1/health`);
    check(burstResponse, {
      [`burst request ${i + 1} successful`]: (r) => r.status === 200,
      [`burst request ${i + 1} fast`]: (r) => r.timings.duration < 200
    });
    
    sleep(0.1); // Very short sleep between burst requests
  }

  randomSleep(1, 3);
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString();
  
  return {
    'stdout': JSON.stringify({
      test_type: 'health_endpoints',
      environment: TEST_ENV,
      load_profile: LOAD_PROFILE,
      timestamp: timestamp,
      summary: {
        vus_max: data.metrics.vus_max.values.max,
        iterations: data.metrics.iterations.values.count,
        http_reqs: data.metrics.http_reqs.values.count,
        http_req_duration_avg: data.metrics.http_req_duration.values.avg,
        http_req_duration_p95: data.metrics.http_req_duration.values['p(95)'],
        http_req_failed_rate: data.metrics.http_req_failed.values.rate,
        data_received: data.metrics.data_received.values.count,
        data_sent: data.metrics.data_sent.values.count
      },
      thresholds_passed: data.root_group.checks.passes,
      thresholds_failed: data.root_group.checks.fails
    }, null, 2),
    
    [`/tmp/k6-health-${TEST_ENV}-${timestamp.replace(/:/g, '-')}.json`]: JSON.stringify(data, null, 2)
  };
}