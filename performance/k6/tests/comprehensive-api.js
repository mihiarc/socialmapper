/**
 * k6 Comprehensive API Load Test
 * 
 * This test simulates realistic user workflows across all API endpoints
 * with mixed load patterns and user behaviors.
 */

import { check, sleep, group } from 'k6';
import { makeRequest, validateHealthResponse, validateMetadataResponse, randomSleep, generateTestData, logError } from '../utils/helpers.js';
import { baseThresholds, loadProfiles, environments } from '../config/thresholds.js';

// Test configuration
const TEST_ENV = __ENV.TEST_ENV || 'staging';
const LOAD_PROFILE = __ENV.LOAD_PROFILE || 'load';
const BASE_URL = environments[TEST_ENV]?.baseUrl || environments.staging.baseUrl;

export let options = {
  ...loadProfiles[LOAD_PROFILE],
  thresholds: {
    ...baseThresholds,
    // Add workflow-specific thresholds
    'group_duration{group:::01_health_check}': ['avg<100'],
    'group_duration{group:::02_metadata_discovery}': ['avg<1000'],
    'group_duration{group:::03_analysis_workflow}': ['avg<5000'],
    'group_duration{group:::04_results_retrieval}': ['avg<2000'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  tags: {
    test_type: 'comprehensive_api',
    environment: TEST_ENV,
    load_profile: LOAD_PROFILE
  }
};

export default function() {
  const testData = generateTestData();
  const sessionId = `session_${__VU}_${__ITER}_${Date.now()}`;
  
  // Simulate realistic user workflow
  group('01_health_check', function() {
    healthCheckWorkflow();
  });
  
  randomSleep(1, 2);
  
  group('02_metadata_discovery', function() {
    metadataDiscoveryWorkflow(testData);
  });
  
  randomSleep(2, 4);
  
  group('03_analysis_workflow', function() {
    analysisWorkflow(testData, sessionId);
  });
  
  randomSleep(1, 3);
  
  group('04_results_retrieval', function() {
    resultsRetrievalWorkflow(sessionId);
  });
  
  randomSleep(3, 6);
}

function healthCheckWorkflow() {
  // Quick health validation before starting workflow
  const healthResponse = makeRequest('GET', `${BASE_URL}/api/v1/health`);
  
  const healthValid = check(healthResponse, {
    'workflow starts with healthy system': (r) => r.status === 200,
    'health check is fast': (r) => r.timings.duration < 200
  });
  
  if (!healthValid) {
    logError(healthResponse, 'Health Check Workflow');
    return false;
  }
  
  return true;
}

function metadataDiscoveryWorkflow(testData) {
  // Simulate user browsing available data
  
  // 1. Get census variables (common starting point)
  const censusResponse = makeRequest('GET', `${BASE_URL}/api/v1/metadata/census-variables`);
  
  check(censusResponse, {
    'census variables loaded': (r) => r.status === 200,
    'census data structure valid': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.variables && body.categories;
      } catch {
        return false;
      }
    }
  });
  
  randomSleep(2, 4); // User reading/selecting variables
  
  // 2. Filter by specific group (user interaction)
  const filteredCensusResponse = makeRequest('GET', 
    `${BASE_URL}/api/v1/metadata/census-variables?group=${testData.randomGroup}&limit=10`);
  
  check(filteredCensusResponse, {
    'filtered census variables loaded': (r) => r.status === 200,
    'filtered results reasonable size': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.variables && body.variables.length <= 10;
      } catch {
        return false;
      }
    }
  });
  
  randomSleep(1, 2);
  
  // 3. Get POI types for analysis
  const poiResponse = makeRequest('GET', `${BASE_URL}/api/v1/metadata/poi-types?category=Healthcare`);
  
  check(poiResponse, {
    'poi types loaded': (r) => r.status === 200,
    'poi types have healthcare category': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.poi_types && body.poi_types.length > 0;
      } catch {
        return false;
      }
    }
  });
  
  randomSleep(1, 3);
  
  // 4. Search for location
  const locationResponse = makeRequest('GET', 
    `${BASE_URL}/api/v1/metadata/geography-search?q=${testData.randomCity}&limit=5`);
  
  check(locationResponse, {
    'location search successful': (r) => r.status === 200,
    'location results found': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.results && body.results.length > 0;
      } catch {
        return false;
      }
    }
  });
}

function analysisWorkflow(testData, sessionId) {
  // Simulate submitting an analysis request
  
  const analysisPayload = {
    session_id: sessionId,
    location: {
      type: 'point',
      coordinates: [testData.randomCoordinate.lng, testData.randomCoordinate.lat],
      name: testData.randomCity
    },
    poi_types: ['library', 'school', 'hospital'],
    census_variables: ['B01003_001E', 'B19013_001E'],
    travel_mode: 'walk',
    travel_time_minutes: 15,
    analysis_type: 'accessibility'
  };
  
  // Submit analysis (this might be async)
  const analysisResponse = makeRequest('POST', `${BASE_URL}/api/v1/analysis/submit`, analysisPayload);
  
  const analysisSubmitted = check(analysisResponse, {
    'analysis submitted successfully': (r) => r.status === 200 || r.status === 202,
    'analysis response has job id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.job_id !== undefined || body.analysis_id !== undefined;
      } catch {
        return false;
      }
    },
    'analysis submission time reasonable': (r) => r.timings.duration < 3000
  });
  
  if (!analysisSubmitted) {
    logError(analysisResponse, 'Analysis Submission');
    return null;
  }
  
  let jobId;
  try {
    const body = JSON.parse(analysisResponse.body);
    jobId = body.job_id || body.analysis_id;
  } catch {
    console.error('Could not parse analysis response');
    return null;
  }
  
  return jobId;
}

function resultsRetrievalWorkflow(sessionId) {
  // Simulate checking for results
  
  // 1. List available results for session
  const resultsListResponse = makeRequest('GET', `${BASE_URL}/api/v1/results?session_id=${sessionId}`);
  
  check(resultsListResponse, {
    'results list retrieved': (r) => r.status === 200,
    'results list has expected format': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body) || body.results !== undefined;
      } catch {
        return false;
      }
    }
  });
  
  randomSleep(1, 2);
  
  // 2. Get specific result (if available)
  // This might return empty results for new submissions
  const specificResultResponse = makeRequest('GET', `${BASE_URL}/api/v1/results/latest`);
  
  check(specificResultResponse, {
    'specific result request handled': (r) => r.status === 200 || r.status === 404,
    'result response time acceptable': (r) => r.timings.duration < 2000
  });
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString();
  
  // Calculate workflow-specific metrics
  const workflowMetrics = {};
  if (data.metrics['group_duration{group:::01_health_check}']) {
    workflowMetrics.health_check_avg = data.metrics['group_duration{group:::01_health_check}'].values.avg;
  }
  if (data.metrics['group_duration{group:::02_metadata_discovery}']) {
    workflowMetrics.metadata_discovery_avg = data.metrics['group_duration{group:::02_metadata_discovery}'].values.avg;
  }
  if (data.metrics['group_duration{group:::03_analysis_workflow}']) {
    workflowMetrics.analysis_workflow_avg = data.metrics['group_duration{group:::03_analysis_workflow}'].values.avg;
  }
  if (data.metrics['group_duration{group:::04_results_retrieval}']) {
    workflowMetrics.results_retrieval_avg = data.metrics['group_duration{group:::04_results_retrieval}'].values.avg;
  }
  
  const summary = {
    test_type: 'comprehensive_api',
    environment: TEST_ENV,
    load_profile: LOAD_PROFILE,
    timestamp: timestamp,
    workflow_performance: workflowMetrics,
    overall_metrics: {
      total_requests: data.metrics.http_reqs.values.count,
      avg_response_time: data.metrics.http_req_duration.values.avg,
      p95_response_time: data.metrics.http_req_duration.values['p(95)'],
      p99_response_time: data.metrics.http_req_duration.values['p(99)'],
      error_rate: data.metrics.http_req_failed.values.rate,
      throughput_rps: data.metrics.http_reqs.values.rate,
      max_concurrent_users: data.metrics.vus_max.values.max
    },
    quality_metrics: {
      checks_passed: data.root_group.checks.passes,
      checks_failed: data.root_group.checks.fails,
      success_rate: (data.root_group.checks.passes / (data.root_group.checks.passes + data.root_group.checks.fails)) * 100
    }
  };
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    [`/tmp/k6-comprehensive-${TEST_ENV}-${timestamp.replace(/:/g, '-')}.json`]: JSON.stringify(data, null, 2)
  };
}