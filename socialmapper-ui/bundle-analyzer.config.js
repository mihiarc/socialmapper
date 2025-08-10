/**
 * Bundle Analyzer Configuration
 * Used for analyzing bundle size and optimizing performance
 */

module.exports = {
  // Performance budgets
  budgets: {
    bundles: [
      {
        name: 'vendor',
        maxSize: '200 KB',
        compression: 'gzip',
      },
      {
        name: 'main',
        maxSize: '150 KB',
        compression: 'gzip',
      },
      {
        name: 'maps',
        maxSize: '250 KB',
        compression: 'gzip',
      },
      {
        name: 'redux',
        maxSize: '50 KB',
        compression: 'gzip',
      },
    ],
    assets: [
      {
        path: 'dist/assets/*.js',
        maxSize: '500 KB',
        compression: 'none',
      },
      {
        path: 'dist/assets/*.css',
        maxSize: '100 KB',
        compression: 'none',
      },
    ],
  },

  // Analyzer options
  analyzerOptions: {
    analyzerMode: process.env.CI ? 'static' : 'server',
    analyzerHost: '127.0.0.1',
    analyzerPort: 8888,
    reportFilename: 'bundle-report.html',
    defaultSizes: 'gzip',
    openAnalyzer: !process.env.CI,
    generateStatsFile: true,
    statsFilename: 'bundle-stats.json',
    statsOptions: {
      source: false,
      reasons: false,
      chunks: true,
      chunkModules: true,
      chunkOrigins: false,
      modules: true,
      cached: false,
      cachedAssets: false,
    },
    excludeAssets: /\.map$/,
    logLevel: 'info',
  },

  // Optimization hints
  optimizationHints: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendor',
          priority: 10,
          reuseExistingChunk: true,
        },
        maps: {
          test: /[\\/]node_modules[\\/](mapbox-gl|react-map-gl|@turf)[\\/]/,
          name: 'maps',
          priority: 20,
        },
        antd: {
          test: /[\\/]node_modules[\\/](antd|@ant-design)[\\/]/,
          name: 'antd',
          priority: 20,
        },
        redux: {
          test: /[\\/]node_modules[\\/](@reduxjs|react-redux|redux)[\\/]/,
          name: 'redux',
          priority: 15,
        },
        common: {
          minChunks: 2,
          priority: 5,
          reuseExistingChunk: true,
        },
      },
    },
  },

  // CI-specific settings
  ci: {
    failOnWarning: false,
    failOnError: true,
    budgetErrorThreshold: 1.2, // 20% over budget fails the build
    generateReport: true,
    uploadArtifacts: true,
    compareWithBaseline: true,
  },
};