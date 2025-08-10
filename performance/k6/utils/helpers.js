/**
 * Common utilities and helpers for k6 tests
 */

import { check, sleep } from 'k6';
import http from 'k6/http';

/**
 * Makes an HTTP request with common error handling and validation
 */
export function makeRequest(method, url, payload = null, params = {}) {
  const defaultParams = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-load-test/1.0'
    },
    timeout: '30s',
    ...params
  };

  let response;
  
  switch (method.toUpperCase()) {
    case 'GET':
      response = http.get(url, defaultParams);
      break;
    case 'POST':
      response = http.post(url, payload ? JSON.stringify(payload) : null, defaultParams);
      break;
    case 'PUT':
      response = http.put(url, payload ? JSON.stringify(payload) : null, defaultParams);
      break;
    case 'DELETE':
      response = http.del(url, null, defaultParams);
      break;
    default:
      throw new Error(`Unsupported HTTP method: ${method}`);
  }

  return response;
}

/**
 * Validates a standard API response structure
 */
export function validateApiResponse(response, expectedStatus = 200) {
  const checks = {
    [`status is ${expectedStatus}`]: (r) => r.status === expectedStatus,
    'response time is acceptable': (r) => r.timings.duration < 2000,
    'response has body': (r) => r.body.length > 0,
  };

  // Additional checks for JSON responses
  if (response.headers['Content-Type'] && response.headers['Content-Type'].includes('application/json')) {
    checks['response is valid JSON'] = (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch {
        return false;
      }
    };
  }

  return check(response, checks);
}

/**
 * Validates health check response structure
 */
export function validateHealthResponse(response) {
  const baseCheck = validateApiResponse(response, 200);
  
  const healthChecks = check(response, {
    'health response has status': (r) => {
      const body = JSON.parse(r.body);
      return body.status !== undefined;
    },
    'health status is healthy': (r) => {
      const body = JSON.parse(r.body);
      return body.status === 'healthy';
    },
    'health response has timestamp': (r) => {
      const body = JSON.parse(r.body);
      return body.timestamp !== undefined;
    },
    'health response has version': (r) => {
      const body = JSON.parse(r.body);
      return body.version !== undefined;
    }
  });

  return baseCheck && healthChecks;
}

/**
 * Validates metadata response structure
 */
export function validateMetadataResponse(response, expectedFields = []) {
  const baseCheck = validateApiResponse(response, 200);
  
  const metadataChecks = check(response, {
    'metadata response has data': (r) => {
      const body = JSON.parse(r.body);
      return Array.isArray(body) || (typeof body === 'object' && body !== null);
    },
    'metadata response has required fields': (r) => {
      if (expectedFields.length === 0) return true;
      
      const body = JSON.parse(r.body);
      if (Array.isArray(body) && body.length > 0) {
        return expectedFields.every(field => body[0].hasOwnProperty(field));
      }
      return expectedFields.every(field => body.hasOwnProperty(field));
    }
  });

  return baseCheck && metadataChecks;
}

/**
 * Simulates realistic user think time
 */
export function randomSleep(min = 1, max = 3) {
  const sleepTime = Math.random() * (max - min) + min;
  sleep(sleepTime);
}

/**
 * Generates random test data
 */
export function generateTestData() {
  const cities = ['Portland', 'Chicago', 'Durham', 'Seattle', 'Austin', 'Denver'];
  const states = ['OR', 'IL', 'NC', 'WA', 'TX', 'CO'];
  const groups = ['Demographics', 'Income', 'Education', 'Transportation', 'Housing'];
  
  return {
    randomCity: cities[Math.floor(Math.random() * cities.length)],
    randomState: states[Math.floor(Math.random() * states.length)],
    randomGroup: groups[Math.floor(Math.random() * groups.length)],
    randomCoordinate: {
      lat: 40.7128 + (Math.random() - 0.5) * 10, // Around NYC with variation
      lng: -74.0060 + (Math.random() - 0.5) * 10
    }
  };
}

/**
 * Creates a custom metrics summary
 */
export function createCustomMetrics() {
  return {
    api_response_time: Trend('api_response_time'),
    api_success_rate: Rate('api_success_rate'),
    endpoint_errors: Counter('endpoint_errors'),
    concurrent_users: Gauge('concurrent_users')
  };
}

/**
 * Logs detailed error information
 */
export function logError(response, context = '') {
  console.error(`ERROR ${context}: Status ${response.status}, Body: ${response.body.substring(0, 200)}`);
  
  if (response.error) {
    console.error(`Error details: ${response.error}`);
  }
}