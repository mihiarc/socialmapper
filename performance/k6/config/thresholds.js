/**
 * Performance thresholds and configuration for k6 tests
 */

export const baseThresholds = {
  // Request duration thresholds
  http_req_duration: ['p(95)<500'], // 95% of requests must complete within 500ms
  http_req_duration_median: ['<200'], // Median response time under 200ms
  
  // Error rate thresholds
  http_req_failed: ['rate<0.01'], // Error rate must be less than 1%
  
  // Throughput thresholds
  http_reqs: ['rate>100'], // Minimum 100 requests per second
  
  // Connection thresholds
  http_req_connecting: ['p(95)<100'], // Connection time under 100ms for 95% of requests
  http_req_waiting: ['p(95)<400'], // Server processing time under 400ms
};

export const strictThresholds = {
  http_req_duration: ['p(95)<300', 'p(99)<800'],
  http_req_duration_median: ['<150'],
  http_req_failed: ['rate<0.005'], // Stricter error rate for production
  http_reqs: ['rate>200'],
  http_req_connecting: ['p(95)<50'],
  http_req_waiting: ['p(95)<250'],
};

export const endpointSpecificThresholds = {
  health: {
    http_req_duration: ['p(95)<100'], // Health check should be very fast
    http_req_duration_median: ['<50'],
    http_req_failed: ['rate<0.001'],
  },
  
  metadata: {
    http_req_duration: ['p(95)<300'], // Metadata endpoints are lightweight
    http_req_duration_median: ['<150'],
    http_req_failed: ['rate<0.005'],
  },
  
  analysis: {
    http_req_duration: ['p(95)<2000'], // Analysis endpoints can take longer
    http_req_duration_median: ['<1000'],
    http_req_failed: ['rate<0.02'],
  },
  
  results: {
    http_req_duration: ['p(95)<500'],
    http_req_duration_median: ['<250'],
    http_req_failed: ['rate<0.01'],
  }
};

export const loadProfiles = {
  smoke: {
    vus: 1,
    duration: '30s',
    description: 'Minimal load test to verify functionality'
  },
  
  load: {
    stages: [
      { duration: '2m', target: 10 }, // Ramp up
      { duration: '5m', target: 50 }, // Normal load
      { duration: '2m', target: 0 },  // Ramp down
    ],
    description: 'Normal expected load'
  },
  
  stress: {
    stages: [
      { duration: '2m', target: 50 },  // Ramp up to normal load
      { duration: '5m', target: 100 }, // Stress load
      { duration: '2m', target: 150 }, // Peak stress
      { duration: '5m', target: 100 }, // Scale down
      { duration: '2m', target: 0 },   // Ramp down
    ],
    description: 'High load stress test'
  },
  
  spike: {
    stages: [
      { duration: '1m', target: 10 },  // Normal load
      { duration: '30s', target: 200 }, // Sudden spike
      { duration: '1m', target: 10 },  // Back to normal
    ],
    description: 'Sudden traffic spike test'
  },
  
  soak: {
    stages: [
      { duration: '2m', target: 30 },  // Ramp up
      { duration: '30m', target: 30 }, // Sustained load
      { duration: '2m', target: 0 },   // Ramp down
    ],
    description: 'Extended duration test for memory leaks'
  }
};

export const environments = {
  staging: {
    baseUrl: 'https://staging-api.socialmapper.com',
    uiUrl: 'https://staging.socialmapper.com'
  },
  
  production: {
    baseUrl: 'https://api.socialmapper.com',
    uiUrl: 'https://demo.socialmapper.com'
  }
};