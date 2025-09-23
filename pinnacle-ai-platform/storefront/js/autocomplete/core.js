/**
 * Pinnacle AI Boutique Storefront - Auto-Completion Core Library
 *
 * This library provides the core functionality for auto-completion across the storefront,
 * including API communication, caching, context management, and real-time WebSocket integration.
 */

class StorefrontAutoCompletionCore {
    constructor(options = {}) {
        this.options = {
            baseUrl: options.baseUrl || '/api/v1/autocomplete',
            wsUrl: options.wsUrl || this.getWebSocketUrl(),
            cacheEnabled: options.cacheEnabled !== false,
            cacheSize: options.cacheSize || 50, // Smaller cache for storefront
            debounceDelay: options.debounceDelay || 200, // Faster response for storefront
            maxRetries: options.maxRetries || 2,
            retryDelay: options.retryDelay || 800,
            requestTimeout: options.requestTimeout || 3000, // Faster timeout for storefront
            ...options
        };

        this.cache = new Map();
        this.pendingRequests = new Map();
        this.context = {
            user_id: null,
            session_id: this.generateSessionId(),
            app_context: 'storefront',
            current_page: null,
            user_preferences: {},
            recent_queries: [],
            provider_usage: {},
            cart_context: {},
            search_history: [],
            product_views: []
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
        console.log('🛍️ Storefront auto-completion core initialized');
    }

    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws/autocomplete`;
    }

    generateSessionId() {
        return 'sf_ac_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    initializeWebSocket() {
        try {
            this.websocket = new WebSocket(this.options.wsUrl);

            this.websocket.onopen = () => {
                console.log('🔗 Storefront auto-completion WebSocket connected');
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
                console.log('🔌 Storefront auto-completion WebSocket disconnected');
                this.isConnected = false;
                this.emit('websocket:disconnected');

                // Attempt to reconnect after delay
                setTimeout(() => {
                    this.initializeWebSocket();
                }, 3000); // Faster reconnect for storefront
            };

            this.websocket.onerror = (error) => {
                console.error('Storefront auto-completion WebSocket error:', error);
                this.emit('websocket:error', error);
            };

        } catch (error) {
            console.error('Failed to initialize storefront auto-completion WebSocket:', error);
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
            case 'product_recommendation':
                this.handleProductRecommendation(data);
                break;
            case 'search_suggestion':
                this.handleSearchSuggestion(data);
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

    handleProductRecommendation(data) {
        this.emit('product:recommendation', data);
    }

    handleSearchSuggestion(data) {
        this.emit('search:suggestion', data);
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

        // Listen for cart changes to update context
        window.addEventListener('cart:updated', (e) => {
            this.updateCartContext(e.detail);
        });

        // Listen for product views to update context
        window.addEventListener('product:viewed', (e) => {
            this.updateProductViewContext(e.detail);
        });
    }

    handlePageHidden() {
        // Pause WebSocket connection when page is hidden
        if (this.websocket && this.isConnected) {
            this.websocket.send(JSON.stringify({
                type: 'pause',
                session_id: this.context.session_id,
                app_context: 'storefront'
            }));
        }
    }

    handlePageVisible() {
        // Resume WebSocket connection when page becomes visible
        if (this.websocket && this.isConnected) {
            this.websocket.send(JSON.stringify({
                type: 'resume',
                session_id: this.context.session_id,
                app_context: 'storefront'
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
            const saved = localStorage.getItem('pinnacle_storefront_autocomplete_context');
            if (saved) {
                const parsed = JSON.parse(saved);
                this.context = { ...this.context, ...parsed };
            }
        } catch (error) {
            console.error('Error loading persisted storefront context:', error);
        }
    }

    savePersistedContext() {
        try {
            localStorage.setItem('pinnacle_storefront_autocomplete_context', JSON.stringify(this.context));
        } catch (error) {
            console.error('Error saving persisted storefront context:', error);
        }
    }

    updateContext(updates) {
        this.context = { ...this.context, ...updates };
        this.savePersistedContext();
        this.emit('context:changed', this.context);
    }

    updateCartContext(cartData) {
        this.updateContext({
            cart_context: {
                item_count: cartData.itemCount || 0,
                total_value: cartData.total || 0,
                last_updated: Date.now()
            }
        });
    }

    updateProductViewContext(productData) {
        this.updateContext({
            product_views: [
                {
                    id: productData.id,
                    name: productData.name,
                    category: productData.category,
                    timestamp: Date.now()
                },
                ...this.context.product_views.slice(0, 9)
            ]
        });
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
            // Check if cache entry is still valid (3 minutes TTL for storefront)
            if (Date.now() - cached.timestamp < 3 * 60 * 1000) {
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
            provider_types: options.providerTypes || ['search', 'database'], // Focus on search and product providers
            max_results: options.maxResults || 8, // Fewer results for storefront
            timeout: options.timeout || this.options.requestTimeout,
            user_id: options.userId || this.context.user_id,
            session_id: options.sessionId || this.context.session_id,
            metadata: {
                ...options.metadata,
                cart_context: this.context.cart_context,
                search_history: this.context.search_history.slice(0, 5)
            },
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
            max_results: options.max_results,
            cart_context: options.metadata?.cart_context
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
                search_history: [
                    {
                        query: options.query,
                        timestamp: Date.now(),
                        provider_used: result.provider_used
                    },
                    ...this.context.search_history.slice(0, 19)
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
            if (retryCount < this.options.maxRetries && error.name !== 'AbortError') {
                console.warn(`Storefront request failed, retrying (${retryCount + 1}/${this.options.maxRetries}):`, error.message);

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
            console.error('Failed to update storefront context on server:', error);
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
            console.error('Failed to get storefront context from server:', error);
            return null;
        }
    }

    // Product-specific methods
    async requestProductCompletions(query, options = {}) {
        return this.requestCompletions(query, {
            providerTypes: ['search', 'database'],
            maxResults: 6,
            metadata: {
                ...options.metadata,
                product_search: true,
                cart_context: this.context.cart_context
            },
            ...options
        });
    }

    async requestCategoryCompletions(query, options = {}) {
        return this.requestCompletions(query, {
            providerTypes: ['search'],
            maxResults: 5,
            metadata: {
                ...options.metadata,
                category_search: true
            },
            ...options
        });
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
                    console.error('Error in storefront event listener:', error);
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
            console.error('Storefront health check failed:', error);
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
window.StorefrontAutoCompletionCore = StorefrontAutoCompletionCore;</code>
</edit_file>