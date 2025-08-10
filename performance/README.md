# Performance Testing Infrastructure

This directory contains comprehensive performance testing infrastructure for the SocialMapper project using k6 and Lighthouse CI.

## Structure

```
performance/
├── k6/                     # k6 load testing scripts
│   ├── tests/             # Individual test scripts
│   ├── config/            # Test configurations
│   └── utils/             # Shared utilities
├── lighthouse/            # Lighthouse CI configuration
├── results/               # Test results storage
├── dashboards/            # Performance monitoring dashboards
└── scripts/               # Automation scripts
```

## Tools Used

- **k6**: Load testing for API endpoints
- **Lighthouse CI**: Frontend performance auditing
- **Grafana**: Performance metrics visualization
- **GitHub Actions**: CI/CD integration

## Quick Start

See individual README files in each subdirectory for detailed instructions.