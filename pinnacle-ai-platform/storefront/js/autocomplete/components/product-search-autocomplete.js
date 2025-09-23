/**
 * Pinnacle AI Boutique Storefront - Product Search Auto-Complete Component
 *
 * Provides intelligent product search with images, prices, stock information,
 * and direct add-to-cart functionality for enhanced shopping experience.
 */

class ProductSearchAutoComplete extends StorefrontAutoCompleteBaseComponent {
    constructor(element, options = {}) {
        const defaultOptions = {
            classPrefix: 'product-search-autocomplete',
            minQueryLength: 1,
            maxResults: 5,
            debounceDelay: 150,
            showImages: true,
            showPrices: true,
            showStock: true,
            allowCustomValues: true,
            placeholder: 'Search for products...',
            noResultsText: 'No products found',
            loadingText: 'Searching products...',
            highlightMatches: true,
            showCategories: true,
            showAddToCart: true,
            imageSize: '40px',
            ...options
        };

        super(element, defaultOptions);

        this.productCache = new Map();
        this.recentSearches = [];
        this.maxRecentSearches = 5;
    }

    init() {
        super.init();
        this.loadRecentSearches();
    }

    getContext() {
        const baseContext = super.getContext();

        return {
            ...baseContext,
            search_type: 'product',
            show_images: this.options.showImages,
            show_prices: this.options.showPrices,
            show_stock: this.options.showStock,
            recent_searches: this.recentSearches.slice(0, 3)
        };
    }

    renderResultContent(result) {
        const content = [];

        // Product image
        if (this.options.showImages && result.image) {
            const image = document.createElement('div');
            image.className = `${this.options.classPrefix}-item-image`;
            image.innerHTML = `<img src="${result.image}" alt="${result.completion || result.text || result.name || ''}" loading="lazy" style="width: ${this.options.imageSize}; height: ${this.options.imageSize};">`;
            content.push(image.outerHTML);
        }

        // Main content
        const mainContent = document.createElement('div');
        mainContent.className = `${this.options.classPrefix}-item-content`;

        // Product name/title with highlighting
        const title = document.createElement('div');
        title.className = `${this.options.classPrefix}-item-title`;

        if (this.options.highlightMatches && this.currentQuery) {
            title.innerHTML = this.highlightText(result.completion || result.text || result.name || '', this.currentQuery);
        } else {
            title.textContent = result.completion || result.text || result.name || '';
        }

        mainContent.appendChild(title);

        // Product description
        if (result.description) {
            const description = document.createElement('div');
            description.className = `${this.options.classPrefix}-item-description`;
            description.textContent = result.description;
            mainContent.appendChild(description);
        }

        // Category
        if (this.options.showCategories && result.category) {
            const category = document.createElement('div');
            category.className = `${this.options.classPrefix}-item-category`;
            category.textContent = result.category;
            mainContent.appendChild(category);
        }

        // Price and stock info
        const metaInfo = document.createElement('div');
        metaInfo.className = `${this.options.classPrefix}-item-meta`;

        if (this.options.showPrices && result.price) {
            const price = document.createElement('span');
            price.className = `${this.options.classPrefix}-item-price`;
            price.textContent = `$${result.price}`;

            // Show sale price if available
            if (result.sale_price && result.sale_price < result.price) {
                price.innerHTML = `<span class="original-price">$${result.price}</span> <span class="sale-price">$${result.sale_price}</span>`;
            }

            metaInfo.appendChild(price);
        }

        if (this.options.showStock && result.stock !== undefined) {
            const stock = document.createElement('span');
            stock.className = `${this.options.classPrefix}-item-stock ${result.stock > 0 ? 'in-stock' : 'out-of-stock'}`;
            stock.textContent = result.stock > 0 ? `In Stock (${result.stock})` : 'Out of Stock';
            metaInfo.appendChild(stock);
        }

        if (metaInfo.children.length > 0) {
            mainContent.appendChild(metaInfo);
        }

        content.push(mainContent.outerHTML);

        // Add to cart button
        if (this.options.showAddToCart && result.type === 'product' && result.id) {
            const addToCart = document.createElement('div');
            addToCart.className = `${this.options.classPrefix}-item-action`;
            addToCart.innerHTML = `
                <button class="add-to-cart-btn" data-product-id="${result.id}" title="Add to Cart">
                    <i class="fas fa-shopping-cart"></i>
                </button>
            `;

            // Add event listener for add to cart
            addToCart.querySelector('.add-to-cart-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.addToCart(result.id, result);
            });

            content.push(addToCart.outerHTML);
        }

        return content.join('');
    }

    highlightText(text, query) {
        if (!query || !text) return text;

        const regex = new RegExp(`(${this.escapeRegExp(query)})`, 'gi');
        return text.replace(regex, `<span class="highlight">$1</span>`);
    }

    escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    performSearch(query) {
        // Show recent searches for short queries
        if (query.length < 2 && this.recentSearches.length > 0) {
            this.showRecentSearches(query);
            return;
        }

        // Show popular products for empty query
        if (query.length === 0) {
            this.showPopularProducts();
            return;
        }

        // Perform full search
        super.performSearch(query);
    }

    showRecentSearches(query) {
        const recentResults = this.recentSearches
            .filter(item => this.matchesQuery(item, query))
            .slice(0, 3)
            .map((item, index) => ({
                completion: item.query,
                text: item.query,
                description: `Searched ${this.formatTimeAgo(item.timestamp)}`,
                category: 'Recent Search',
                provider: 'history',
                score: 0.9 - (index * 0.1),
                metadata: {
                    type: 'recent_search',
                    timestamp: item.timestamp
                }
            }));

        if (recentResults.length > 0) {
            this.results = recentResults;
            this.renderResults();
            this.open();
        } else {
            super.performSearch(query);
        }
    }

    showPopularProducts() {
        // Show popular/trending products
        const popularProducts = [
            {
                completion: 'Premium AI Agent',
                text: 'Premium AI Agent',
                description: 'Advanced AI assistant for professional use',
                category: 'Popular',
                image: '/images/products/ai-agent.jpg',
                price: 299,
                stock: 15,
                id: 'popular_1',
                provider: 'popular',
                score: 1.0
            },
            {
                completion: 'Data Analytics Suite',
                text: 'Data Analytics Suite',
                description: 'Comprehensive data analysis and visualization tools',
                category: 'Popular',
                image: '/images/products/analytics.jpg',
                price: 199,
                stock: 8,
                id: 'popular_2',
                provider: 'popular',
                score: 0.9
            }
        ];

        this.results = popularProducts;
        this.renderResults();
        this.open();
    }

    matchesQuery(item, query) {
        if (!query) return true;

        const searchText = [
            item.query,
            item.text,
            item.description,
            item.category
        ].filter(Boolean).join(' ').toLowerCase();

        return searchText.includes(query.toLowerCase());
    }

    selectItem(index) {
        const result = this.results[index];
        if (!result) return;

        const value = result.completion || result.text || result.name || '';

        // Add to recent searches
        this.addToRecentSearches(value);

        this.setValue(value);
        this.close();

        this.emit('product:selected', {
            result,
            index,
            value,
            productId: result.id
        });

        // Navigate to product page if it's a product
        if (result.type === 'product' && result.id) {
            this.navigateToProduct(result.id);
        }
    }

    addToRecentSearches(query) {
        // Remove if already exists
        this.recentSearches = this.recentSearches.filter(item => item.query !== query);

        // Add to beginning
        this.recentSearches.unshift({
            query: query,
            timestamp: Date.now(),
            category: 'product_search'
        });

        // Keep only recent items
        this.recentSearches = this.recentSearches.slice(0, this.maxRecentSearches);

        // Persist to localStorage
        this.saveRecentSearches();
    }

    saveRecentSearches() {
        try {
            localStorage.setItem('storefront-product-search-history', JSON.stringify(this.recentSearches));
        } catch (error) {
            console.error('Failed to save recent searches:', error);
        }
    }

    loadRecentSearches() {
        try {
            const saved = localStorage.getItem('storefront-product-search-history');
            if (saved) {
                this.recentSearches = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Failed to load recent searches:', error);
        }
    }

    formatTimeAgo(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
        if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        return 'Just now';
    }

    async addToCart(productId, productData) {
        try {
            // Use the global cart manager if available
            if (window.CartManager) {
                await window.CartManager.addToCart(productId);

                // Show success feedback
                this.showAddToCartFeedback(productData);

                this.emit('product:added-to-cart', { productId, productData });
            } else {
                console.warn('Cart manager not available');
                this.showNotification('Cart system not available', 'warning');
            }
        } catch (error) {
            console.error('Failed to add product to cart:', error);
            this.showNotification('Failed to add product to cart', 'error');
        }
    }

    showAddToCartFeedback(productData) {
        // Create a temporary feedback element
        const feedback = document.createElement('div');
        feedback.className = 'add-to-cart-feedback';
        feedback.innerHTML = `
            <i class="fas fa-check"></i>
            <span>Added ${productData.completion || productData.text || productData.name} to cart!</span>
        `;

        document.body.appendChild(feedback);

        // Position feedback
        const rect = this.container.getBoundingClientRect();
        feedback.style.position = 'fixed';
        feedback.style.top = `${rect.top - 50}px`;
        feedback.style.left = `${rect.left + rect.width / 2}px`;
        feedback.style.transform = 'translateX(-50%)';
        feedback.style.zIndex = '9999';

        // Animate in
        setTimeout(() => feedback.classList.add('show'), 100);

        // Remove after delay
        setTimeout(() => {
            feedback.classList.remove('show');
            setTimeout(() => {
                if (feedback.parentNode) {
                    feedback.parentNode.removeChild(feedback);
                }
            }, 300);
        }, 2000);
    }

    navigateToProduct(productId) {
        // Navigate to product detail page
        if (window.ProductManager && window.ProductManager.showProductDetail) {
            window.ProductManager.showProductDetail(productId);
        } else {
            console.log('Navigating to product:', productId);
        }
    }

    showNotification(message, type = 'info') {
        if (window.StorefrontUtils && window.StorefrontUtils.showNotification) {
            window.StorefrontUtils.showNotification(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    // Enhanced keyboard navigation
    handleKeyDown(e) {
        switch (e.key) {
            case 'ArrowRight':
                if (this.input.selectionStart === this.input.value.length && this.selectedIndex >= 0) {
                    e.preventDefault();
                    this.selectCurrentItem();
                }
                break;
            case 'Enter':
                if (e.shiftKey) {
                    // Shift+Enter for new line in search
                    e.preventDefault();
                    this.insertText('\n');
                } else {
                    super.handleKeyDown(e);
                }
                break;
            default:
                super.handleKeyDown(e);
        }
    }

    insertText(text) {
        const input = this.input;
        const start = input.selectionStart;
        const end = input.selectionEnd;

        const newValue = input.value.substring(0, start) + text + input.value.substring(end);
        input.value = newValue;
        input.setSelectionRange(start + text.length, start + text.length);

        input.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Public API methods
    getRecentSearches() {
        return [...this.recentSearches];
    }

    clearRecentSearches() {
        this.recentSearches = [];
        localStorage.removeItem('storefront-product-search-history');
        this.emit('recent:cleared');
    }

    addPopularProduct(product) {
        this.productCache.set(product.id, product);
    }

    setCategories(categories) {
        this.options.categories = categories;
    }

    // Advanced search features
    searchInCategory(category, query) {
        this.input.value = query;
        this.handleInput(query);

        // Update context
        this.emit('category:search', { category, query });
    }

    getSuggestionsForCategory(category) {
        const categorySuggestions = {
            'ai-agents': [
                'AI Agent Professional',
                'AI Agent Enterprise',
                'AI Agent Developer'
            ],
            'data-tools': [
                'Data Analytics Suite',
                'Business Intelligence Platform',
                'Data Visualization Tools'
            ],
            'automation': [
                'Workflow Automation',
                'Process Orchestrator',
                'Task Scheduler'
            ]
        };

        return categorySuggestions[category] || [];
    }
}

// Export for global use
window.ProductSearchAutoComplete = ProductSearchAutoComplete;</code>
</edit_file>