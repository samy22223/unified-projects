const os = require('os');
const logger = require('../logger');

class MonitoringService {
  constructor() {
    this.startTime = Date.now();
    this.requestCount = 0;
    this.errorCount = 0;
    this.metrics = {
      uptime: 0,
      memoryUsage: {},
      cpuUsage: 0,
      requestRate: 0,
      errorRate: 0
    };
  }

  // Middleware to track requests
  requestTracker(req, res, next) {
    this.requestCount++;
    const start = Date.now();

    res.on('finish', () => {
      const duration = Date.now() - start;
      logger.http(`${req.method} ${req.url} ${res.statusCode} - ${duration}ms`);

      if (res.statusCode >= 400) {
        this.errorCount++;
      }
    });

    next();
  }

  // Get system health metrics
  getHealthMetrics() {
    const memUsage = process.memoryUsage();
    const totalMemory = os.totalmem();
    const freeMemory = os.freemem();

    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: {
        used: Math.round(memUsage.heapUsed / 1024 / 1024),
        total: Math.round(memUsage.heapTotal / 1024 / 1024),
        external: Math.round(memUsage.external / 1024 / 1024),
        system: {
          total: Math.round(totalMemory / 1024 / 1024),
          free: Math.round(freeMemory / 1024 / 1024),
          used: Math.round((totalMemory - freeMemory) / 1024 / 1024)
        }
      },
      cpu: {
        usage: os.loadavg()[0], // 1 minute load average
        cores: os.cpus().length
      },
      requests: {
        total: this.requestCount,
        errors: this.errorCount,
        successRate: this.requestCount > 0 ? ((this.requestCount - this.errorCount) / this.requestCount * 100).toFixed(2) : 100
      },
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development'
    };
  }

  // Get detailed metrics for monitoring dashboards
  getDetailedMetrics() {
    const healthMetrics = this.getHealthMetrics();

    return {
      ...healthMetrics,
      process: {
        pid: process.pid,
        nodeVersion: process.version,
        platform: process.platform,
        architecture: process.arch
      },
      system: {
        hostname: os.hostname(),
        type: os.type(),
        release: os.release(),
        uptime: os.uptime()
      },
      performance: {
        eventLoopLag: this.measureEventLoopLag(),
        gcStats: this.getGCStats()
      }
    };
  }

  // Measure event loop lag
  measureEventLoopLag() {
    const start = process.hrtime.bigint();
    return new Promise(resolve => {
      setImmediate(() => {
        const end = process.hrtime.bigint();
        const lag = Number(end - start) / 1000000; // Convert to milliseconds
        resolve(Math.round(lag * 100) / 100);
      });
    });
  }

  // Get garbage collection statistics if available
  getGCStats() {
    if (typeof gc !== 'function') {
      return null;
    }

    // This would require additional setup for production monitoring
    return {
      available: true,
      note: 'GC stats require additional monitoring setup'
    };
  }

  // Log performance metrics periodically
  startPeriodicLogging(intervalMinutes = 5) {
    setInterval(() => {
      const metrics = this.getHealthMetrics();
      logger.info('Performance metrics:', {
        uptime: metrics.uptime,
        memoryUsed: metrics.memory.used,
        requestCount: metrics.requests.total,
        errorRate: metrics.requests.successRate
      });
    }, intervalMinutes * 60 * 1000);
  }

  // Alert on high error rates
  checkErrorThreshold(threshold = 0.1) { // 10% error rate
    const metrics = this.getHealthMetrics();
    const errorRate = 1 - (parseFloat(metrics.requests.successRate) / 100);

    if (errorRate > threshold) {
      logger.warn('High error rate detected:', {
        errorRate: (errorRate * 100).toFixed(2) + '%',
        totalRequests: metrics.requests.total,
        totalErrors: metrics.requests.errors
      });
    }
  }

  // Reset counters (useful for testing or periodic resets)
  resetCounters() {
    this.requestCount = 0;
    this.errorCount = 0;
    logger.info('Monitoring counters reset');
  }
}

module.exports = new MonitoringService();