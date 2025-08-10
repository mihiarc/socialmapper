/**
 * k6 Load Test for Metadata Endpoints
 * 
 * Tests the performance of metadata endpoints including census variables,
 * POI types, and location search functionality.
 */

import { check, sleep } from 'k6';
import { makeRequest, validateMetadataResponse, randomSleep, generateTestData, logError } from '../utils/helpers.js';
import { baseThresholds, endpointSpecificThresholds, loadProfiles, environments } from '../config/thresholds.js';

// Test configuration
const TEST_ENV = __ENV.TEST_ENV || 'staging';
const LOAD_PROFILE = __ENV.LOAD_PROFILE || 'load';
const BASE_URL = environments[TEST_ENV]?.baseUrl || environments.staging.baseUrl;

export let options = {
  ...loadProfiles[LOAD_PROFILE],
  thresholds: {
    ...baseThresholds,
    ...endpointSpecificThresholds.metadata
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  tags: {
    test_type: 'metadata_endpoints',
    environment: TEST_ENV,
    load_profile: LOAD_PROFILE
  }
};

export default function() {
  const testData = generateTestData();
  
  // Test 1: Census Variables Endpoint
  testCensusVariables(testData);
  
  randomSleep(1, 2);
  
  // Test 2: POI Types Endpoint  
  testPOITypes(testData);
  
  randomSleep(1, 2);
  
  // Test 3: Location Search Endpoint
  testLocationSearch(testData);
  
  randomSleep(2, 4);
}

function testCensusVariables(testData) {
  // Test basic census variables endpoint
  const censusResponse = makeRequest('GET', `${BASE_URL}/api/v1/metadata/census-variables`);
  
  const censusValid = check(censusResponse, {
    'census variables endpoint responds': (r) => r.status === 200,
    'census variables response is JSON': (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch {
        return false;
      }
    },
    'census variables has expected structure': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.variables !== undefined && body.total_count !== undefined;
      } catch {
        return false;
      }
    },
    'census variables response time acceptable': (r) => r.timings.duration < 500
  });

  if (!censusValid) {
    logError(censusResponse, 'Census Variables Basic');
  }

  // Test with group filter
  const groupFilterResponse = makeRequest('GET', 
    `${BASE_URL}/api/v1/metadata/census-variables?group=${testData.randomGroup}`);
  
  check(groupFilterResponse, {
    'census variables group filter works': (r) => r.status === 200,
    'group filtered response has data': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.variables && Array.isArray(body.variables);
      } catch {
        return false;
      }
    }
  });

  // Test with search parameter
  const searchResponse = makeRequest('GET', 
    `${BASE_URL}/api/v1/metadata/census-variables?search=population`);
  
  check(searchResponse, {
    'census variables search works': (r) => r.status === 200,
    'search response structure valid': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.variables !== undefined && body.total_count !== undefined;
      } catch {
        return false;
      }
    }
  });

  // Test pagination
  const paginationResponse = makeRequest('GET', 
    `${BASE_URL}/api/v1/metadata/census-variables?limit=5&offset=0`);
  
  check(paginationResponse, {
    'census variables pagination works': (r) => r.status === 200,
    'pagination limits results': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.variables && body.variables.length <= 5;
      } catch {
        return false;
      }
    }
  });
}

function testPOITypes(testData) {
  // Test basic POI types endpoint
  const poiResponse = makeRequest('GET', `${BASE_URL}/api/v1/metadata/poi-types`);
  
  const poiValid = check(poiResponse, {
    'poi types endpoint responds': (r) => r.status === 200,
    'poi types response is JSON': (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch {
        return false;
      }
    },
    'poi types has expected structure': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.poi_types !== undefined && body.total_count !== undefined;
      } catch {
        return false;
      }
    },
    'poi types response time acceptable': (r) => r.timings.duration < 500
  });

  if (!poiValid) {
    logError(poiResponse, 'POI Types Basic');
  }

  // Test with category filter
  const categoryResponse = makeRequest('GET', 
    `${BASE_URL}/api/v1/metadata/poi-types?category=Healthcare`);
  
  check(categoryResponse, {
    'poi types category filter works': (r) => r.status === 200,
    'category filtered response has data': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.poi_types && Array.isArray(body.poi_types);
      } catch {
        return false;
      }
    }
  });

  // Test with search parameter
  const poiSearchResponse = makeRequest('GET', 
    `${BASE_URL}/api/v1/metadata/poi-types?search=library`);
  
  check(poiSearchResponse, {
    'poi types search works': (r) => r.status === 200,
    'poi search response structure valid': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.poi_types !== undefined && body.total_count !== undefined;
      } catch {
        return false;
      }
    }
  });
}

function testLocationSearch(testData) {
  // Test location search with city name
  const locationResponse = makeRequest('GET', 
    `${BASE_URL}/api/v1/metadata/geography-search?q=${testData.randomCity}`);
  
  const locationValid = check(locationResponse, {
    'location search endpoint responds': (r) => r.status === 200,
    'location search response is JSON': (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch {
        return false;
      }
    },
    'location search has expected structure': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.results !== undefined && body.query !== undefined;
      } catch {
        return false;
      }
    },
    'location search response time acceptable': (r) => r.timings.duration < 1000
  });

  if (!locationValid) {
    logError(locationResponse, 'Location Search');
  }

  // Test location search with city and state
  const detailedLocationResponse = makeRequest('GET', 
    `${BASE_URL}/api/v1/metadata/geography-search?q=${testData.randomCity}, ${testData.randomState}`);
  
  check(detailedLocationResponse, {
    'detailed location search works': (r) => r.status === 200,
    'detailed search has results': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.results && Array.isArray(body.results);
      } catch {
        return false;
      }
    }
  });

  // Test location search with limit
  const limitedLocationResponse = makeRequest('GET', 
    `${BASE_URL}/api/v1/metadata/geography-search?q=Portland&limit=3`);
  
  check(limitedLocationResponse, {
    'limited location search works': (r) => r.status === 200,
    'limited search respects limit': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.results && body.results.length <= 3;
      } catch {
        return false;
      }
    }
  });
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString();
  
  const summary = {
    test_type: 'metadata_endpoints',
    environment: TEST_ENV,
    load_profile: LOAD_PROFILE,
    timestamp: timestamp,
    endpoints_tested: [
      'census-variables',
      'poi-types', 
      'geography-search'
    ],
    summary: {
      total_requests: data.metrics.http_reqs.values.count,
      avg_response_time: data.metrics.http_req_duration.values.avg,
      p95_response_time: data.metrics.http_req_duration.values['p(95)'],
      error_rate: data.metrics.http_req_failed.values.rate,
      throughput: data.metrics.http_reqs.values.rate,
      data_transferred: {
        received: data.metrics.data_received.values.count,
        sent: data.metrics.data_sent.values.count
      }
    },
    performance_assertions: {
      passed: data.root_group.checks.passes,
      failed: data.root_group.checks.fails,
      success_rate: (data.root_group.checks.passes / (data.root_group.checks.passes + data.root_group.checks.fails)) * 100
    }
  };
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    [`/tmp/k6-metadata-${TEST_ENV}-${timestamp.replace(/:/g, '-')}.json`]: JSON.stringify(data, null, 2)
  };
}