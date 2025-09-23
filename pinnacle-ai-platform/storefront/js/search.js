/**
 * Pinnacle AI Boutique - Search JavaScript
 *
 * This file contains search functionality including:
 * - Product search
 * - Search suggestions
 * - Search filters
 * - Search results management
 */

// Search State Management
const SearchState = {
    currentQuery: '',
    searchResults: [],
    suggestions: [],
    filters: {
        category: null,
        minPrice: null,
        maxPrice: null,
        inStock: false,
        onSale: false,
        sortBy: 'relevance'
    },
    pagination: {
        currentPage: 1,
        totalPages: 1,
        totalResults: 0,
        resultsPerPage: 12
    },
    loading: false,
    searchHistory: []
};

// Search Manager
const SearchManager = {
    // Initialize search functionality
    initialize() {
        this.loadSearchHistory();
        this.setupSearchInput();
        this.setupSearchSuggestions();
        this.setupAdvancedFilters();
        this.setupSearchResults();
    },

    // Load search history from localStorage
    loadSearchHistory() {
        const history = localStorage.getItem('search_history');
        if (history) {
            SearchState.searchHistory = JSON.parse(history);
            this.renderSearchHistory();
        }
    },

    // Save search query to history
    saveSearchHistory(query) {
        if (!query.trim()) return;

        // Remove if already exists
        SearchState.searchHistory = SearchState.searchHistory.filter(item => item !== query);

        // Add to beginning
        SearchState.searchHistory.unshift(query);

        // Keep only last 10 searches
        SearchState.searchHistory = SearchState.searchHistory.slice(0, 10);

        // Save to localStorage
        localStorage.setItem('search_history', JSON.stringify(SearchState.searchHistory));

        this.renderSearchHistory();
    },

    // Render search history
    renderSearchHistory() {
        const historyContainer = document.querySelector('.search-history');
        if (!historyContainer) return;

        if (SearchState.searchHistory.length === 0) {
            historyContainer.style.display = 'none';
            return;
        }

        historyContainer.style.display = 'block';
        historyContainer.innerHTML = `
            <div class="search-history-header">
                <span>Recent Searches</span>
                <button class="clear-history" onclick="SearchManager.clearSearchHistory()">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="search-history-items">
                ${SearchState.searchHistory.map(query => `
                    <div class="search-history-item" onclick="SearchManager.performSearchFromHistory('${query}')">
                        <i class="fas fa-history"></i>
                        <span>${query}</span>
                    </div>
                `).join('')}
            </div>
        `;
    },

    // Clear search history
    clearSearchHistory() {
        SearchState.searchHistory = [];
        localStorage.removeItem('search_history');
        this.renderSearchHistory();
    },

    // Setup search input functionality
    setupSearchInput() {
        const searchInput = document.getElementById('searchInput');
        if (!searchInput) return;

        // Real-time search suggestions
        const debouncedSuggestions = StorefrontUtils.debounce((query) => {
            if (query.length >= 2) {
                this.getSearchSuggestions(query);
            } else {
                this.hideSearchSuggestions();
            }
        }, 300);

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value;
            SearchState.currentQuery = query;
            debouncedSuggestions(query);
        });

        searchInput.addEventListener('focus', () => {
            if (SearchState.searchHistory.length > 0) {
                this.renderSearchHistory();
            }
        });

        searchInput.addEventListener('blur', () => {
            // Delay hiding to allow clicking on suggestions
            setTimeout(() => this.hideSearchSuggestions(), 200);
        });

        // Handle enter key
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch(searchInput.value);
            }
        });
    },

    // Setup search suggestions
    setupSearchSuggestions() {
        const suggestionsContainer = document.querySelector('.search-suggestions');
        if (!suggestionsContainer) return;

        // Create suggestions dropdown if it doesn't exist
        if (!document.querySelector('.search-suggestions-dropdown')) {
            const dropdown = document.createElement('div');
            dropdown.className = 'search-suggestions-dropdown';
            dropdown.style.display = 'none';
            suggestionsContainer.appendChild(dropdown);
        }
    },

    // Get search suggestions
    async getSearchSuggestions(query) {
        try {
            const suggestions = await ProductsAPI.search(query, { limit: 5 });
            SearchState.suggestions = suggestions.map(product => ({
                type: 'product',
                text: product.name,
                product: product
            }));

            this.renderSearchSuggestions();
        } catch (error) {
            console.error('Error getting search suggestions:', error);
        }
    },

    // Render search suggestions
    renderSearchSuggestions() {
        const dropdown = document.querySelector('.search-suggestions-dropdown');
        if (!dropdown) return;

        if (SearchState.suggestions.length === 0) {
            this.hideSearchSuggestions();
            return;
        }

        dropdown.innerHTML = SearchState.suggestions.map(suggestion => `
            <div class="search-suggestion" onclick="SearchManager.selectSuggestion('${suggestion.product.id}')">
                <i class="fas fa-search"></i>
                <span>${suggestion.text}</span>
            </div>
        `).join('');

        dropdown.style.display = 'block';
    },

    // Hide search suggestions
    hideSearchSuggestions() {
        const dropdown = document.querySelector('.search-suggestions-dropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    },

    // Select suggestion
    selectSuggestion(productId) {
        const product = SearchState.suggestions.find(s => s.product.id === productId);
        if (product) {
            // Fill search input with product name
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.value = product.text;
                SearchState.currentQuery = product.text;
            }

            // Perform search
            this.performSearch(product.text);
            this.hideSearchSuggestions();
        }
    },

    // Perform search from history
    performSearchFromHistory(query) {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = query;
            SearchState.currentQuery = query;
        }
        this.performSearch(query);
    },

    // Perform main search
    async performSearch(query) {
        if (!query.trim()) return;

        try {
            SearchState.loading = true;
            this.showSearchLoading();

            // Save to history
            this.saveSearchHistory(query);

            // Perform search
            const results = await ProductsAPI.search(query, {
                category_id: SearchState.filters.category,
                min_price: SearchState.filters.minPrice,
                max_price: SearchState.filters.maxPrice,
                limit: SearchState.pagination.resultsPerPage,
                offset: (SearchState.pagination.currentPage - 1) * SearchState.pagination.resultsPerPage
            });

            SearchState.searchResults = results;
            SearchState.pagination.totalResults = results.length; // In real implementation, get from API
            SearchState.pagination.totalPages = Math.ceil(SearchState.pagination.totalResults / SearchState.pagination.resultsPerPage);

            this.renderSearchResults();
            this.updateSearchInfo();
            this.showSearchResults();

        } catch (error) {
            console.error('Error performing search:', error);
            StorefrontUtils.showNotification('Search failed. Please try again.', 'error');
        } finally {
            SearchState.loading = false;
            this.hideSearchLoading();
        }
    },

    // Show search loading state
    showSearchLoading() {
        const searchResults = document.querySelector('.search-results');
        if (searchResults) {
            searchResults.innerHTML = `
                <div class="search-loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Searching for "${SearchState.currentQuery}"...</p>
                </div>
            `;
        }
    },

    // Hide search loading state
    hideSearchLoading() {
        const loadingState = document.querySelector('.search-loading');
        if (loadingState) {
            loadingState.remove();
        }
    },

    // Render search results
    renderSearchResults() {
        const searchResults = document.querySelector('.search-results');
        if (!searchResults) return;

        if (SearchState.searchResults.length === 0) {
            searchResults.innerHTML = `
                <div class="no-search-results">
                    <i class="fas fa-search"></i>
                    <h3>No results found</h3>
                    <p>We couldn't find any products matching "${SearchState.currentQuery}"</p>
                    <div class="search-suggestions">
                        <h4>Try:</h4>
                        <ul>
                            <li>Checking your spelling</li>
                            <li>Using more general terms</li>
                            <li>Searching in a different category</li>
                        </ul>
                    </div>
                </div>
            `;
            return;
        }

        searchResults.innerHTML = `
            <div class="search-results-grid">
                ${SearchState.searchResults.map(product => `
                    <div class="product-card search-result" data-product-id="${product.id}">
                        <div class="product-image">
                            <img src="${product.images[0] || 'images/placeholder.jpg'}" alt="${product.name}">
                            ${product.is_featured ? '<span class="product-badge">Featured</span>' : ''}
                            ${product.compare_at_price ? '<span class="product-badge sale">Sale</span>' : ''}
                        </div>
                        <div class="product-info">
                            <h3 class="product-title">${product.name}</h3>
                            <p class="product-description">${product.short_description || product.description.substring(0, 100)}...</p>
                            <div class="product-price">
                                <span class="current-price">${StorefrontUtils.formatCurrency(product.price)}</span>
                                ${product.compare_at_price ? `<span class="original-price">${StorefrontUtils.formatCurrency(product.compare_at_price)}</span>` : ''}
                            </div>
                            <div class="product-actions">
                                <button class="btn btn-primary add-to-cart" data-product-id="${product.id}">
                                    <i class="fas fa-shopping-cart"></i>
                                    Add to Cart
                                </button>
                                <button class="btn btn-outline quick-view" data-product-id="${product.id}">
                                    <i class="fas fa-eye"></i>
                                    Quick View
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Add event listeners
        this.addSearchResultEventListeners();
    },

    // Add search result event listeners
    addSearchResultEventListeners() {
        // Add to cart buttons
        document.querySelectorAll('.search-result .add-to-cart').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const productId = e.currentTarget.dataset.productId;
                ProductManager.addToCart(productId);
            });
        });

        // Quick view buttons
        document.querySelectorAll('.search-result .quick-view').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const productId = e.currentTarget.dataset.productId;
                ProductManager.showQuickView(productId);
            });
        });
    },

    // Update search info
    updateSearchInfo() {
        const searchInfo = document.querySelector('.search-info');
        if (!searchInfo) return;

        searchInfo.innerHTML = `
            <div class="search-query">
                <span>Search results for:</span>
                <strong>"${SearchState.currentQuery}"</strong>
            </div>
            <div class="search-count">
                ${SearchState.pagination.totalResults} results found
            </div>
        `;
    },

    // Show search results section
    showSearchResults() {
        const searchSection = document.querySelector('.search-section');
        const productsSection = document.querySelector('.featured-products');

        if (searchSection) {
            searchSection.style.display = 'block';
        }

        if (productsSection) {
            productsSection.style.display = 'none';
        }

        // Scroll to search results
        if (searchSection) {
            searchSection.scrollIntoView({ behavior: 'smooth' });
        }
    },

    // Hide search results section
    hideSearchResults() {
        const searchSection = document.querySelector('.search-section');
        const productsSection = document.querySelector('.featured-products');

        if (searchSection) {
            searchSection.style.display = 'none';
        }

        if (productsSection) {
            productsSection.style.display = 'block';
        }
    },

    // Setup advanced filters
    setupAdvancedFilters() {
        const filterToggle = document.querySelector('.search-filters-toggle');
        const filterPanel = document.querySelector('.search-filters-panel');

        if (filterToggle && filterPanel) {
            filterToggle.addEventListener('click', () => {
                filterPanel.classList.toggle('open');
            });
        }

        // Category filter
        const categoryFilter = document.querySelector('.category-filter-select');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', (e) => {
                SearchState.filters.category = e.target.value || null;
                this.applyFilters();
            });
        }

        // Price range filters
        const minPriceInput = document.querySelector('.min-price-input');
        const maxPriceInput = document.querySelector('.max-price-input');

        if (minPriceInput) {
            minPriceInput.addEventListener('input', StorefrontUtils.debounce(() => {
                SearchState.filters.minPrice = minPriceInput.value ? parseFloat(minPriceInput.value) : null;
                this.applyFilters();
            }, 500));
        }

        if (maxPriceInput) {
            maxPriceInput.addEventListener('input', StorefrontUtils.debounce(() => {
                SearchState.filters.maxPrice = maxPriceInput.value ? parseFloat(maxPriceInput.value) : null;
                this.applyFilters();
            }, 500));
        }

        // Checkbox filters
        const inStockFilter = document.querySelector('.in-stock-filter');
        const onSaleFilter = document.querySelector('.on-sale-filter');

        if (inStockFilter) {
            inStockFilter.addEventListener('change', (e) => {
                SearchState.filters.inStock = e.target.checked;
                this.applyFilters();
            });
        }

        if (onSaleFilter) {
            onSaleFilter.addEventListener('change', (e) => {
                SearchState.filters.onSale = e.target.checked;
                this.applyFilters();
            });
        }

        // Sort filter
        const sortFilter = document.querySelector('.search-sort-select');
        if (sortFilter) {
            sortFilter.addEventListener('change', (e) => {
                SearchState.filters.sortBy = e.target.value;
                this.applySort();
            });
        }

        // Clear filters button
        const clearFiltersBtn = document.querySelector('.clear-filters-btn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearFilters();
            });
        }
    },

    // Apply filters to current search
    async applyFilters() {
        if (!SearchState.currentQuery) return;

        try {
            SearchState.loading = true;
            this.showSearchLoading();

            const results = await ProductsAPI.search(SearchState.currentQuery, {
                category_id: SearchState.filters.category,
                min_price: SearchState.filters.minPrice,
                max_price: SearchState.filters.maxPrice,
                limit: SearchState.pagination.resultsPerPage,
                offset: 0
            });

            // Apply client-side filters
            let filteredResults = results;

            if (SearchState.filters.inStock) {
                filteredResults = filteredResults.filter(p => p.inventory_quantity > 0);
            }

            if (SearchState.filters.onSale) {
                filteredResults = filteredResults.filter(p => p.compare_at_price);
            }

            SearchState.searchResults = filteredResults;
            this.renderSearchResults();

        } catch (error) {
            console.error('Error applying filters:', error);
            StorefrontUtils.showNotification('Failed to apply filters', 'error');
        } finally {
            SearchState.loading = false;
            this.hideSearchLoading();
        }
    },

    // Apply sorting
    applySort() {
        if (!SearchState.searchResults.length) return;

        let sortedResults = [...SearchState.searchResults];

        switch (SearchState.filters.sortBy) {
            case 'price-low':
                sortedResults.sort((a, b) => a.price - b.price);
                break;
            case 'price-high':
                sortedResults.sort((a, b) => b.price - a.price);
                break;
            case 'name':
                sortedResults.sort((a, b) => a.name.localeCompare(b.name));
                break;
            case 'newest':
                sortedResults.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                break;
            case 'relevance':
            default:
                // Keep original order for relevance
                break;
        }

        SearchState.searchResults = sortedResults;
        this.renderSearchResults();
    },

    // Clear all filters
    clearFilters() {
        SearchState.filters = {
            category: null,
            minPrice: null,
            maxPrice: null,
            inStock: false,
            onSale: false,
            sortBy: 'relevance'
        };

        // Reset form elements
        const categoryFilter = document.querySelector('.category-filter-select');
        const minPriceInput = document.querySelector('.min-price-input');
        const maxPriceInput = document.querySelector('.max-price-input');
        const inStockFilter = document.querySelector('.in-stock-filter');
        const onSaleFilter = document.querySelector('.on-sale-filter');
        const sortFilter = document.querySelector('.search-sort-select');

        if (categoryFilter) categoryFilter.value = '';
        if (minPriceInput) minPriceInput.value = '';
        if (maxPriceInput) maxPriceInput.value = '';
        if (inStockFilter) inStockFilter.checked = false;
        if (onSaleFilter) onSaleFilter.checked = false;
        if (sortFilter) sortFilter.value = 'relevance';

        this.applyFilters();
    },

    // Setup search results functionality
    setupSearchResults() {
        // Pagination
        const prevBtn = document.querySelector('.search-pagination .prev');
        const nextBtn = document.querySelector('.search-pagination .next');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (SearchState.pagination.currentPage > 1) {
                    SearchState.pagination.currentPage--;
                    this.performSearch(SearchState.currentQuery);
                }
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (SearchState.pagination.currentPage < SearchState.pagination.totalPages) {
                    SearchState.pagination.currentPage++;
                    this.performSearch(SearchState.currentQuery);
                }
            });
        }
    }
};

// Advanced Search Features
const AdvancedSearch = {
    // Initialize advanced search
    initialize() {
        this.setupVoiceSearch();
        this.setupImageSearch();
        this.setupSearchAnalytics();
    },

    // Setup voice search
    setupVoiceSearch() {
        const voiceBtn = document.querySelector('.voice-search-btn');
        if (!voiceBtn) return;

        voiceBtn.addEventListener('click', () => {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                this.startVoiceSearch();
            } else {
                StorefrontUtils.showNotification('Voice search is not supported in your browser', 'warning');
            }
        });
    },

    // Start voice search
    startVoiceSearch() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();

        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        const searchInput = document.getElementById('searchInput');

        recognition.onstart = () => {
            searchInput.placeholder = 'Listening...';
            searchInput.classList.add('listening');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            searchInput.value = transcript;
            SearchState.currentQuery = transcript;
            SearchManager.performSearch(transcript);
        };

        recognition.onerror = (event) => {
            console.error('Voice search error:', event.error);
            StorefrontUtils.showNotification('Voice search failed. Please try again.', 'error');
        };

        recognition.onend = () => {
            searchInput.placeholder = 'Search products...';
            searchInput.classList.remove('listening');
        };

        recognition.start();
    },

    // Setup image search
    setupImageSearch() {
        const imageBtn = document.querySelector('.image-search-btn');
        if (!imageBtn) return;

        imageBtn.addEventListener('click', () => {
            this.showImageSearchModal();
        });
    },

    // Show image search modal
    showImageSearchModal() {
        StorefrontUtils.showNotification('Image search functionality coming soon!', 'info');
    },

    // Setup search analytics
    setupSearchAnalytics() {
        // Track search queries
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('focus', () => {
                // Track search focus event
                this.trackEvent('search_focus');
            });
        }
    },

    // Track search event
    trackEvent(eventType, data = {}) {
        // In a real implementation, this would send analytics data
        console.log('Search Analytics:', { eventType, ...data, timestamp: new Date().toISOString() });
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    SearchManager.initialize();
    AdvancedSearch.initialize();
});

// Export for global use
window.SearchManager = SearchManager;
window.AdvancedSearch = AdvancedSearch;