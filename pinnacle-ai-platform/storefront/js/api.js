/**
 * Pinnacle AI Boutique - API Client
 * 
 * This file contains the API client for communicating with the backend.
 * It includes all API endpoints and utility functions for data handling.
 */

// API Configuration
const API_CONFIG = {
    BASE_URL: 'http://localhost:8000/api/v1',
    TIMEOUT: 10000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000
};

// Custom API Error class
class APIError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

// Utility functions
const APIUtils = {
    // Generate session ID
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },
    
    // Format currency
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    // Format date
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        return new Date(date).toLocaleDateString('en-US', { ...defaultOptions, ...options });
    },
    
    // Debounce function
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
    },
    
    // Sleep function
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },
    
    // Validate email
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    // Sanitize string
    sanitizeString(str) {
        if (typeof str !== 'string') return str;
        return str.replace(/[<>]/g, '');
    }
};

// Base API Client class
class APIClient {
    constructor(baseURL = API_CONFIG.BASE_URL) {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }
    
    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            timeout: API_CONFIG.TIMEOUT,
            ...options
        };
        
        // Add session ID to headers if available
        const sessionId = localStorage.getItem('cart_session_id');
        if (sessionId) {
            config.headers['X-Session-ID'] = sessionId;
        }
        
        let lastError;
        
        for (let attempt = 1; attempt <= API_CONFIG.RETRY_ATTEMPTS; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), config.timeout);
                
                const response = await fetch(url, {
                    ...config,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new APIError(
                        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
                        response.status,
                        errorData
                    );
                }
                
                const data = await response.json();
                return data;
                
            } catch (error) {
                lastError = error;
                
                if (error.name === 'AbortError') {
                    throw new APIError('Request timeout', 408);
                }
                
                if (error instanceof APIError) {
                    throw error;
                }
                
                if (attempt === API_CONFIG.RETRY_ATTEMPTS) {
                    throw new APIError(
                        `Network error: ${error.message}`,
                        0,
                        { originalError: error.message }
                    );
                }
                
                // Wait before retry
                await APIUtils.sleep(API_CONFIG.RETRY_DELAY * attempt);
            }
        }
        
        throw lastError;
    }
    
    // GET request
    async get(endpoint, params = {}) {
        const url = new URL(`${this.baseURL}${endpoint}`);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        return this.request(url.pathname + url.search);
    }
    
    // POST request
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    // PUT request
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// Categories API
class CategoriesAPI {
    static async getAll() {
        const client = new APIClient();
        return client.get('/ecommerce/categories');
    }
    
    static async getById(id) {
        const client = new APIClient();
        return client.get(`/ecommerce/categories/${id}`);
    }
    
    static async create(data) {
        const client = new APIClient();
        return client.post('/ecommerce/categories', data);
    }
    
    static async update(id, data) {
        const client = new APIClient();
        return client.put(`/ecommerce/categories/${id}`, data);
    }
    
    static async delete(id) {
        const client = new APIClient();
        return client.delete(`/ecommerce/categories/${id}`);
    }
}

// Products API
class ProductsAPI {
    static async getAll(params = {}) {
        const client = new APIClient();
        return client.get('/ecommerce/products', params);
    }
    
    static async getById(id) {
        const client = new APIClient();
        return client.get(`/ecommerce/products/${id}`);
    }
    
    static async getFeatured(limit = 8) {
        const client = new APIClient();
        return client.get('/ecommerce/products/featured', { limit });
    }
    
    static async getOnSale(limit = 8) {
        const client = new APIClient();
        return client.get('/ecommerce/products/on-sale', { limit });
    }
    
    static async search(query, params = {}) {
        const client = new APIClient();
        return client.get('/ecommerce/products/search', { q: query, ...params });
    }
    
    static async create(data) {
        const client = new APIClient();
        return client.post('/ecommerce/products', data);
    }
    
    static async update(id, data) {
        const client = new APIClient();
        return client.put(`/ecommerce/products/${id}`, data);
    }
    
    static async delete(id) {
        const client = new APIClient();
        return client.delete(`/ecommerce/products/${id}`);
    }
}

// Cart API
class CartAPI {
    static async getOrCreate(sessionId) {
        const client = new APIClient();
        return client.post('/ecommerce/cart/get-or-create', { session_id: sessionId });
    }
    
    static async getById(cartId) {
        const client = new APIClient();
        return client.get(`/ecommerce/cart/${cartId}`);
    }
    
    static async addItem(cartId, itemData) {
        const client = new APIClient();
        return client.post(`/ecommerce/cart/${cartId}/items`, itemData);
    }
    
    static async updateItem(cartId, itemId, quantity) {
        const client = new APIClient();
        return client.put(`/ecommerce/cart/${cartId}/items/${itemId}`, { quantity });
    }
    
    static async removeItem(cartId, itemId) {
        const client = new APIClient();
        return client.delete(`/ecommerce/cart/${cartId}/items/${itemId}`);
    }
    
    static async clearCart(cartId) {
        const client = new APIClient();
        return client.delete(`/ecommerce/cart/${cartId}`);
    }
    
    static async mergeCarts(sessionId, userId) {
        const client = new APIClient();
        return client.post('/ecommerce/cart/merge', { session_id: sessionId, user_id: userId });
    }
}

// Orders API
class OrdersAPI {
    static async create(orderData) {
        const client = new APIClient();
        return client.post('/ecommerce/orders', orderData);
    }
    
    static async getById(orderId) {
        const client = new APIClient();
        return client.get(`/ecommerce/orders/${orderId}`);
    }
    
    static async getUserOrders(userId, params = {}) {
        const client = new APIClient();
        return client.get(`/ecommerce/orders/user/${userId}`, params);
    }
    
    static async updateStatus(orderId, status) {
        const client = new APIClient();
        return client.put(`/ecommerce/orders/${orderId}/status`, { status });
    }
    
    static async cancelOrder(orderId) {
        const client = new APIClient();
        return client.post(`/ecommerce/orders/${orderId}/cancel`);
    }
}

// Reviews API
class ReviewsAPI {
    static async getByProduct(productId, params = {}) {
        const client = new APIClient();
        return client.get(`/ecommerce/products/${productId}/reviews`, params);
    }
    
    static async create(productId, reviewData) {
        const client = new APIClient();
        return client.post(`/ecommerce/products/${productId}/reviews`, reviewData);
    }
    
    static async update(reviewId, reviewData) {
        const client = new APIClient();
        return client.put(`/ecommerce/reviews/${reviewId}`, reviewData);
    }
    
    static async delete(reviewId) {
        const client = new APIClient();
        return client.delete(`/ecommerce/reviews/${reviewId}`);
    }
}

// Wishlist API
class WishlistAPI {
    static async getByUser(userId) {
        const client = new APIClient();
        return client.get(`/ecommerce/wishlist/user/${userId}`);
    }
    
    static async addItem(userId, productId) {
        const client = new APIClient();
        return client.post(`/ecommerce/wishlist/user/${userId}/items`, { product_id: productId });
    }
    
    static async removeItem(userId, productId) {
        const client = new APIClient();
        return client.delete(`/ecommerce/wishlist/user/${userId}/items/${productId}`);
    }
    
    static async clearWishlist(userId) {
        const client = new APIClient();
        return client.delete(`/ecommerce/wishlist/user/${userId}`);
    }
}

// Analytics API
class AnalyticsAPI {
    static async getDashboard() {
        const client = new APIClient();
        return client.get('/ecommerce/analytics/dashboard');
    }
    
    static async getSalesReport(params = {}) {
        const client = new APIClient();
        return client.get('/ecommerce/analytics/sales', params);
    }
    
    static async getProductAnalytics(productId, params = {}) {
        const client = new APIClient();
        return client.get(`/ecommerce/analytics/products/${productId}`, params);
    }
}

// User API
class UserAPI {
    static async register(userData) {
        const client = new APIClient();
        return client.post('/auth/register', userData);
    }
    
    static async login(credentials) {
        const client = new APIClient();
        return client.post('/auth/login', credentials);
    }
    
    static async logout() {
        const client = new APIClient();
        return client.post('/auth/logout');
    }
    
    static async getProfile() {
        const client = new APIClient();
        return client.get('/auth/profile');
    }
    
    static async updateProfile(userData) {
        const client = new APIClient();
        return client.put('/auth/profile', userData);
    }
    
    static async changePassword(passwordData) {
        const client = new APIClient();
        return client.post('/auth/change-password', passwordData);
    }
}

// Export all APIs and utilities
window.APIUtils = APIUtils;
window.APIClient = APIClient;
window.CategoriesAPI = CategoriesAPI;
window.ProductsAPI = ProductsAPI;
window.CartAPI = CartAPI;
window.OrdersAPI = OrdersAPI;
window.ReviewsAPI = ReviewsAPI;
window.WishlistAPI = WishlistAPI;
window.AnalyticsAPI = AnalyticsAPI;
window.UserAPI = UserAPI;
