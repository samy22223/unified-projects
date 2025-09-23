/**
 * Pinnacle AI Boutique Storefront - Auto-Completion Integration
 *
 * Main integration file that initializes auto-completion components,
 * provides examples, and manages global storefront auto-completion functionality.
 */

// Global auto-completion instances
window.storefrontAutoComplete = null;
window.storefrontAutoCompleteInstances = new Map();

/**
 * Initialize auto-completion system for the storefront
 */
function initializeStorefrontAutoComplete(options = {}) {
    console.log('🛍️ Initializing Storefront Auto-Completion System...');

    // Initialize core system
    window.storefrontAutoComplete = new StorefrontAutoCompletionCore({
        baseUrl: '/api/v1/autocomplete',
        wsUrl: 'ws://' + window.location.host + '/ws/autocomplete',
        cacheEnabled: true,
        cacheSize: 50,
        debounceDelay: 200,
        maxRetries: 2,
        retryDelay: 800,
        requestTimeout: 3000,
        ...options
    });

    // Set up global event listeners
    setupGlobalEventListeners();

    // Initialize existing elements
    initializeExistingElements();

    // Set up storefront-specific integrations
    setupStorefrontIntegrations();

    console.log('✅ Storefront Auto-Completion System initialized');
}

/**
 * Set up global event listeners for auto-completion
 */
function setupGlobalEventListeners() {
    if (!window.storefrontAutoComplete) return;

    // Listen for WebSocket events
    window.storefrontAutoComplete.on('websocket:connected', () => {
        console.log('🔗 Storefront auto-completion WebSocket connected');
    });

    window.storefrontAutoComplete.on('websocket:disconnected', () => {
        console.log('🔌 Storefront auto-completion WebSocket disconnected');
    });

    window.storefrontAutoComplete.on('websocket:error', (error) => {
        console.error('Storefront auto-completion WebSocket error:', error);
    });

    // Listen for context updates
    window.storefrontAutoComplete.on('context:updated', (context) => {
        console.log('Storefront context updated:', context);
    });

    // Listen for product recommendations
    window.storefrontAutoComplete.on('product:recommendation', (data) => {
        console.log('Product recommendation received:', data);
        handleProductRecommendation(data);
    });

    // Listen for search suggestions
    window.storefrontAutoComplete.on('search:suggestion', (data) => {
        console.log('Search suggestion received:', data);
    });

    // Listen for cache events
    window.storefrontAutoComplete.on('cache:hit', (data) => {
        console.log('Cache hit for:', data.query);
    });

    // Listen for request events
    window.storefrontAutoComplete.on('request:completed', (data) => {
        console.log(`Storefront auto-completion request completed in ${data.responseTime}ms for:`, data.query);
    });

    window.storefrontAutoComplete.on('request:error', (data) => {
        console.error('Storefront auto-completion request failed:', data.error);
    });
}

/**
 * Initialize auto-completion on existing elements
 */
function initializeExistingElements() {
    // Initialize main search box
    const mainSearch = document.getElementById('searchInput') || document.querySelector('input[type="search"]');
    if (mainSearch && !mainSearch.hasAttribute('data-autocomplete-initialized')) {
        initializeProductSearchAutoComplete(mainSearch);
        mainSearch.setAttribute('data-autocomplete-initialized', 'true');
    }

    // Initialize category search boxes
    const categorySearches = document.querySelectorAll('.category-search input, .filter-search input');
    categorySearches.forEach(input => {
        if (!input.hasAttribute('data-autocomplete-initialized')) {
            initializeProductSearchAutoComplete(input, {
                placeholder: 'Search in this category...',
                showCategories: false
            });
            input.setAttribute('data-autocomplete-initialized', 'true');
        }
    });

    // Initialize product name inputs
    const productNameInputs = document.querySelectorAll('input[name="product_name"], input[name="product_search"]');
    productNameInputs.forEach(input => {
        if (!input.hasAttribute('data-autocomplete-initialized')) {
            initializeProductSearchAutoComplete(input, {
                placeholder: 'Enter product name...',
                maxResults: 4
            });
            input.setAttribute('data-autocomplete-initialized', 'true');
        }
    });
}

/**
 * Set up storefront-specific integrations
 */
function setupStorefrontIntegrations() {
    // Integrate with product grid search
    const productGridSearch = document.querySelector('.products-search input');
    if (productGridSearch && !productGridSearch.hasAttribute('data-autocomplete-initialized')) {
        initializeProductSearchAutoComplete(productGridSearch, {
            placeholder: 'Search products...',
            showAddToCart: false // Don't show add to cart in grid search
        });
    }

    // Integrate with navigation search
    const navSearch = document.querySelector('.nav-search input');
    if (navSearch && !navSearch.hasAttribute('data-autocomplete-initialized')) {
        initializeProductSearchAutoComplete(navSearch, {
            placeholder: 'Search...',
            maxResults: 3,
            showImages: false // Compact view for navigation
        });
    }

    // Integrate with filters
    const filterInputs = document.querySelectorAll('.filter-input input, .price-input input');
    filterInputs.forEach(input => {
        if (!input.hasAttribute('data-autocomplete-initialized')) {
            initializeProductSearchAutoComplete(input, {
                placeholder: 'Filter products...',
                maxResults: 5,
                showImages: false,
                showPrices: false
            });
            input.setAttribute('data-autocomplete-initialized', 'true');
        }
    });
}

/**
 * Initialize Product Search Auto-Complete on an element
 */
function initializeProductSearchAutoComplete(element, options = {}) {
    if (!window.storefrontAutoComplete) {
        console.error('Storefront auto-completion core not initialized');
        return null;
    }

    const instance = new ProductSearchAutoComplete(element, {
        core: window.storefrontAutoComplete,
        minQueryLength: 1,
        maxResults: 5,
        debounceDelay: 150,
        showImages: true,
        showPrices: true,
        showStock: true,
        highlightMatches: true,
        showAddToCart: true,
        imageSize: '40px',
        ...options
    });

    // Store instance reference
    const id = 'product_search_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    window.storefrontAutoCompleteInstances.set(id, instance);

    // Set up event listeners
    instance.on('product:selected', (data) => {
        console.log('Product selected:', data);
        handleProductSelection(data);
    });

    instance.on('product:added-to-cart', (data) => {
        console.log('Product added to cart:', data);
        handleAddToCart(data);
    });

    instance.on('recent:cleared', () => {
        console.log('Recent searches cleared');
    });

    return instance;
}

/**
 * Handle product selection events
 */
function handleProductSelection(data) {
    // Navigate to product detail page
    if (data.productId && window.ProductManager) {
        window.ProductManager.showProductDetail(data.productId);
    }

    // Update search context
    if (window.storefrontAutoComplete) {
        window.storefrontAutoComplete.updateContext({
            last_product_search: data.value,
            last_selected_product: data.productId
        });
    }

    // Track analytics
    if (window.trackEvent) {
        window.trackEvent('product_search_select', {
            query: data.value,
            productId: data.productId,
            category: data.result.category
        });
    }
}

/**
 * Handle add to cart events
 */
function handleAddToCart(data) {
    // Update cart display
    if (window.StorefrontUtils) {
        window.StorefrontUtils.updateCartDisplay();
    }

    // Show success message
    if (window.StorefrontUtils) {
        window.StorefrontUtils.showNotification('Product added to cart!', 'success');
    }

    // Track analytics
    if (window.trackEvent) {
        window.trackEvent('product_added_to_cart', {
            productId: data.productId,
            source: 'autocomplete'
        });
    }
}

/**
 * Handle product recommendations
 */
function handleProductRecommendation(data) {
    // Display recommendations in appropriate location
    if (data.products && data.products.length > 0) {
        displayProductRecommendations(data.products, data.context);
    }
}

/**
 * Display product recommendations
 */
function displayProductRecommendations(products, context) {
    const recommendationsContainer = document.getElementById('product-recommendations');
    if (!recommendationsContainer) return;

    recommendationsContainer.innerHTML = products.map(product => `
        <div class="recommendation-item" data-product-id="${product.id}">
            <img src="${product.image}" alt="${product.name}" loading="lazy">
            <div class="recommendation-info">
                <h4>${product.name}</h4>
                <p class="price">$${product.price}</p>
                <button class="btn btn-sm btn-primary add-to-cart" data-product-id="${product.id}">
                    Add to Cart
                </button>
            </div>
        </div>
    `).join('');

    // Add event listeners
    recommendationsContainer.querySelectorAll('.add-to-cart').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const productId = e.currentTarget.dataset.productId;
            if (window.CartManager) {
                window.CartManager.addToCart(productId);
            }
        });
    });
}

/**
 * Create a new auto-complete instance programmatically
 */
function createStorefrontAutoComplete(element, type, options = {}) {
    switch (type) {
        case 'product-search':
            return initializeProductSearchAutoComplete(element, options);
        default:
            console.error('Unknown storefront auto-completion type:', type);
            return null;
    }
}

/**
 * Get all auto-completion instances
 */
function getStorefrontAutoCompleteInstances() {
    return Array.from(window.storefrontAutoCompleteInstances.entries());
}

/**
 * Get auto-completion instance by ID
 */
function getStorefrontAutoCompleteInstance(id) {
    return window.storefrontAutoCompleteInstances.get(id);
}

/**
 * Destroy auto-completion instance
 */
function destroyStorefrontAutoCompleteInstance(id) {
    const instance = window.storefrontAutoCompleteInstances.get(id);
    if (instance) {
        instance.destroy();
        window.storefrontAutoCompleteInstances.delete(id);
        return true;
    }
    return false;
}

/**
 * Destroy all auto-completion instances
 */
function destroyAllStorefrontAutoCompleteInstances() {
    window.storefrontAutoCompleteInstances.forEach((instance, id) => {
        instance.destroy();
    });
    window.storefrontAutoCompleteInstances.clear();
}

/**
 * Update auto-completion context
 */
function updateStorefrontAutoCompleteContext(updates) {
    if (window.storefrontAutoComplete) {
        window.storefrontAutoComplete.updateContext(updates);
    }
}

/**
 * Get auto-completion statistics
 */
function getStorefrontAutoCompleteStats() {
    if (window.storefrontAutoComplete) {
        return window.storefrontAutoComplete.getStats();
    }
    return null;
}

/**
 * Perform health check on auto-completion system
 */
async function healthCheckStorefrontAutoComplete() {
    if (window.storefrontAutoComplete) {
        try {
            const health = await window.storefrontAutoComplete.healthCheck();
            console.log('Storefront auto-completion health check:', health);
            return health;
        } catch (error) {
            console.error('Storefront auto-completion health check failed:', error);
            return { status: 'unhealthy', error: error.message };
        }
    }
    return { status: 'not_initialized' };
}

/**
 * Search for products programmatically
 */
async function searchProducts(query, options = {}) {
    if (!window.storefrontAutoComplete) {
        console.error('Storefront auto-completion not initialized');
        return [];
    }

    try {
        const results = await window.storefrontAutoComplete.requestProductCompletions(query, {
            maxResults: options.maxResults || 5,
            ...options
        });

        return results.completions || [];
    } catch (error) {
        console.error('Product search failed:', error);
        return [];
    }
}

/**
 * Get product recommendations
 */
async function getProductRecommendations(context = {}) {
    if (!window.storefrontAutoComplete) {
        console.error('Storefront auto-completion not initialized');
        return [];
    }

    try {
        // This would typically call a recommendation API
        const recommendations = await window.storefrontAutoComplete.requestCompletions('recommendations', {
            maxResults: 4,
            context: context,
            providerTypes: ['search', 'database']
        });

        return recommendations.completions || [];
    } catch (error) {
        console.error('Failed to get recommendations:', error);
        return [];
    }
}

/**
 * Example usage and demonstrations
 */
function demonstrateStorefrontAutoComplete() {
    console.log('🛍️ Storefront Auto-Completion Examples:');

    console.log('1. Product Search Auto-Complete:');
    console.log('   const search = new ProductSearchAutoComplete(document.getElementById("search"));');

    console.log('2. Global functions:');
    console.log('   - createStorefrontAutoComplete(element, type, options)');
    console.log('   - searchProducts(query, options)');
    console.log('   - getProductRecommendations(context)');
    console.log('   - getStorefrontAutoCompleteInstances()');
    console.log('   - updateStorefrontAutoCompleteContext(updates)');
    console.log('   - healthCheckStorefrontAutoComplete()');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Auto-initialize if core is not already initialized
    if (!window.storefrontAutoComplete) {
        initializeStorefrontAutoComplete();
    }

    // Add global functions to window
    window.initializeStorefrontAutoComplete = initializeStorefrontAutoComplete;
    window.createStorefrontAutoComplete = createStorefrontAutoComplete;
    window.getStorefrontAutoCompleteInstances = getStorefrontAutoCompleteInstances;
    window.getStorefrontAutoCompleteInstance = getStorefrontAutoCompleteInstance;
    window.destroyStorefrontAutoCompleteInstance = destroyStorefrontAutoCompleteInstance;
    window.destroyAllStorefrontAutoCompleteInstances = destroyAllStorefrontAutoCompleteInstances;
    window.updateStorefrontAutoCompleteContext = updateStorefrontAutoCompleteContext;
    window.getStorefrontAutoCompleteStats = getStorefrontAutoCompleteStats;
    window.healthCheckStorefrontAutoComplete = healthCheckStorefrontAutoComplete;
    window.searchProducts = searchProducts;
    window.getProductRecommendations = getProductRecommendations;
    window.demonstrateStorefrontAutoComplete = demonstrateStorefrontAutoComplete;

    console.log('🛍️ Storefront Auto-Completion system loaded and ready!');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeStorefrontAutoComplete,
        createStorefrontAutoComplete,
        getStorefrontAutoCompleteInstances,
        getStorefrontAutoCompleteInstance,
        destroyStorefrontAutoCompleteInstance,
        destroyAllStorefrontAutoCompleteInstances,
        updateStorefrontAutoCompleteContext,
        getStorefrontAutoCompleteStats,
        healthCheckStorefrontAutoComplete,
        searchProducts,
        getProductRecommendations,
        demonstrateStorefrontAutoComplete
    };
}</code>
</edit_file>