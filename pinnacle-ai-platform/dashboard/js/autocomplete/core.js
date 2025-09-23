/**
 * Pinnacle AI Platform Dashboard - Auto-Completion Core Library
 *
 * This library provides the core functionality for auto-completion across the dashboard,
 * including API communication, caching, context management, and real-time WebSocket integration.
 */

class AutoCompletionCore {
    constructor(options = {}) {
        this.options = {
            baseUrl: options.baseUrl || '/api/v1/autocomplete',
            wsUrl: options.wsUrl || this.getWebSocketUrl(),
            cacheEnabled: options.cacheEnabled !== false,
            cacheSize: options.cacheSize || 100,
            debounceDelay: options.debounceDelay || 300,
            maxRetries: options.maxRetries || 3,
            retryDelay: options.retryDelay || 1000,
            requestTimeout: options.requestTimeout || 5000,
            ...options
        };

        this.cache = new Map();
        this.pendingRequests = new Map();
        this.context = {
            user_id: null,
            session_id: this.generateSessionId(),
            app_context: 'dashboard',
            current_page: null,
            user_preferences: {},
            recent_queries: [],
            provider_usage: {}
        };

        this.websocket = null;
        this.isConnected = false;
        this.eventListeners = new Map();

        this.init();
    }

    init() {
        this.initializeWebSocket();
        this.initializeEventListeners();
        this.loadPersistedContext();
        console.log('🔧 Auto-completion core initialized');
    }

    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws/autocomplete`;
    }

    generateSessionId() {
        return 'ac_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    initializeWebSocket() {
        try {
            this.websocket = new WebSocket(this.options.wsUrl);

            this.websocket.onopen = () => {
                console.log('🔗 Auto-completion WebSocket connected');
                this.isConnected = true;
                this.emit('websocket:connected');
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.websocket.onclose = () => {
                console.log('🔌 Auto-completion WebSocket disconnected');
                this.isConnected = false;
                this.emit('websocket:disconnected');

                // Attempt to reconnect after delay
                setTimeout(() => {
                    this.initializeWebSocket();
                }, 5000);
            };

            this.websocket.onerror = (error) => {
                console.error('Auto-completion WebSocket error:', error);
                this.emit('websocket:error', error);
            };

        } catch (error) {
            console.error('Failed to initialize auto-completion WebSocket:', error);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'completion_suggestion':
                this.handleRealTimeSuggestion(data);
                break;
            case 'context_update':
                this.handleContextUpdate(data);
                break;
            case 'cache_update':
                this.handleCacheUpdate(data);
                break;
            case 'provider_status':
                this.handleProviderStatus(data);
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    handleRealTimeSuggestion(data) {
        this.emit('realtime:suggestion', data);
    }

    handleContextUpdate(data) {
        this.updateContext(data.updates);
        this.emit('context:updated', data);
    }

    handleCacheUpdate(data) {
        if (this.options.cacheEnabled) {
            this.updateCache(data.key, data.value);
        }
        this.emit('cache:updated', data);
    }

    handleProviderStatus(data) {
        this.emit('provider:status', data);
    }

    initializeEventListeners() {
        // Listen for page visibility changes to manage WebSocket connection
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handlePageHidden();
            } else {
                this.handlePageVisible();
            }
        });

        // Listen for beforeunload to clean up
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }

    handlePageHidden() {
        // Pause WebSocket connection when page is hidden
        if (this.websocket && this.isConnected) {
            this.websocket.send(JSON.stringify({
                type: 'pause',
                session_id: this.context.session_id
            }));
        }
    }

    handlePageVisible() {
        // Resume WebSocket connection when page becomes visible
        if (this.websocket && this.isConnected) {
            this.websocket.send(JSON.stringify({
                type: 'resume',
                session_id: this.context.session_id
            }));
        }
    }

    cleanup() {
        if (this.websocket) {
            this.websocket.close();
        }
        this.savePersistedContext();
    }

    loadPersistedContext() {
        try {
            const saved = localStorage.getItem('pinnacle_autocomplete_context');
            if (saved) {
                const parsed = JSON.parse(saved);
                this.context = { ...this.context, ...parsed };
            }
        } catch (error) {
            console.error('Error loading persisted context:', error);
        }
    }

    savePersistedContext() {
        try {
            localStorage.setItem('pinnacle_autocomplete_context', JSON.stringify(this.context));
        } catch (error) {
            console.error('Error saving persisted context:', error);
        }
    }

    updateContext(updates) {
        this.context = { ...this.context, ...updates };
        this.savePersistedContext();
        this.emit('context:changed', this.context);
    }

    updateCache(key, value) {
        if (!this.options.cacheEnabled) return;

        // Implement LRU-like cache eviction
        if (this.cache.size >= this.options.cacheSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }

        this.cache.set(key, {
            value,
            timestamp: Date.now()
        });
    }

    getCached(key) {
        if (!this.options.cacheEnabled) return null;

        const cached = this.cache.get(key);
        if (cached) {
            // Check if cache entry is still valid (5 minutes TTL)
            if (Date.now() - cached.timestamp < 5 * 60 * 1000) {
                return cached.value;
            } else {
                this.cache.delete(key);
            }
        }
        return null;
    }

    async requestCompletions(query, options = {}) {
        const requestOptions = {
            query,
            context: options.context || this.context.app_context,
            provider_types: options.providerTypes || ['all'],
            max_results: options.maxResults || 10,
            timeout: options.timeout || this.options.requestTimeout,
            user_id: options.userId || this.context.user_id,
            session_id: options.sessionId || this.context.session_id,
            metadata: options.metadata || {},
            ...options
        };

        const cacheKey = this.generateCacheKey(requestOptions);

        // Check cache first
        const cachedResult = this.getCached(cacheKey);
        if (cachedResult) {
            this.emit('cache:hit', { query, cachedResult });
            return cachedResult;
        }

        // Check for pending request
        if (this.pendingRequests.has(cacheKey)) {
            return this.pendingRequests.get(cacheKey);
        }

        // Create new request
        const requestPromise = this.makeRequest(requestOptions, cacheKey);
        this.pendingRequests.set(cacheKey, requestPromise);

        try {
            const result = await requestPromise;
            this.pendingRequests.delete(cacheKey);
            return result;
        } catch (error) {
            this.pendingRequests.delete(cacheKey);
            throw error;
        }
    }

    generateCacheKey(options) {
        return btoa(JSON.stringify({
            query: options.query,
            context: options.context,
            provider_types: options.provider_types,
            max_results: options.max_results
        })).replace(/[^a-zA-Z0-9]/g, '').substr(0, 32);
    }

    async makeRequest(options, cacheKey) {
        const startTime = Date.now();

        try {
            const response = await this.fetchWithRetry('/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                },
                body: JSON.stringify(options)
            });

            const result = await response.json();

            // Cache the result
            if (this.options.cacheEnabled) {
                this.updateCache(cacheKey, result);
            }

            // Update context with request info
            this.updateContext({
                recent_queries: [
                    options.query,
                    ...this.context.recent_queries.slice(0, 9)
                ],
                provider_usage: {
                    ...this.context.provider_usage,
                    [result.provider_used]: (this.context.provider_usage[result.provider_used] || 0) + 1
                }
            });

            this.emit('request:completed', {
                query: options.query,
                result,
                responseTime: Date.now() - startTime
            });

            return result;

        } catch (error) {
            this.emit('request:error', {
                query: options.query,
                error,
                responseTime: Date.now() - startTime
            });
            throw error;
        }
    }

    async fetchWithRetry(endpoint, options, retryCount = 0) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.options.requestTimeout);

            const response = await fetch(`${this.options.baseUrl}${endpoint}`, {
                ...options,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return response;

        } catch (error) {
            if (retryCount < this.options.maxRetries && !error.name === 'AbortError') {
                console.warn(`Request failed, retrying (${retryCount + 1}/${this.options.maxRetries}):`, error.message);

                await new Promise(resolve => setTimeout(resolve, this.options.retryDelay * Math.pow(2, retryCount)));
                return this.fetchWithRetry(endpoint, options, retryCount + 1);
            }
            throw error;
        }
    }

    async updateContextOnServer(updates) {
        try {
            await this.fetchWithRetry('/context', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                },
                body: JSON.stringify({
                    user_id: this.context.user_id,
                    session_id: this.context.session_id,
                    app_context: this.context.app_context,
                    updates
                })
            });

            this.updateContext(updates);
        } catch (error) {
            console.error('Failed to update context on server:', error);
        }
    }

    async getContextFromServer() {
        try {
            const response = await this.fetchWithRetry(`/context/${this.context.user_id}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                }
            });

            const serverContext = await response.json();
            this.updateContext(serverContext);
            return serverContext;
        } catch (error) {
            console.error('Failed to get context from server:', error);
            return null;
        }
    }

    // Event system
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in event listener:', error);
                }
            });
        }
    }

    // Utility methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Health check
    async healthCheck() {
        try {
            const response = await this.fetchWithRetry('/health', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('pinnacle_auth_token')}`
                }
            });

            const health = await response.json();
            return health;
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'unhealthy', error: error.message };
        }
    }

    // Statistics
    getStats() {
        return {
            cacheSize: this.cache.size,
            pendingRequests: this.pendingRequests.size,
            isConnected: this.isConnected,
            sessionId: this.context.session_id,
            context: this.context
        };
    }
}

// Export for global use
window.AutoCompletionCore = AutoCompletionCore;</code>
</edit_file>