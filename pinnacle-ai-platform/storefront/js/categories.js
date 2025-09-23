/**
 * Pinnacle AI Boutique - Categories JavaScript
 *
 * This file contains category-specific functionality including:
 * - Category filtering and navigation
 * - Category-based product loading
 * - Category management
 */

// Category State Management
const CategoryState = {
    currentCategory: null,
    categoryPath: [],
    subcategories: [],
    categoryProducts: [],
    loading: false
};

// Category Manager
const CategoryManager = {
    // Initialize categories
    async initialize() {
        try {
            await this.loadCategories();
            this.setupCategoryNavigation();
            this.setupCategoryFilters();
        } catch (error) {
            console.error('Error initializing categories:', error);
        }
    },

    // Load all categories
    async loadCategories() {
        try {
            const categories = await CategoriesAPI.getAll();
            this.renderCategoryTree(categories);
            this.setupBreadcrumbNavigation();
            return categories;
        } catch (error) {
            console.error('Error loading categories:', error);
            throw error;
        }
    },

    // Render category tree
    renderCategoryTree(categories) {
        const categoryTree = this.buildCategoryTree(categories);
        const categoryNav = document.querySelector('.category-nav');

        if (categoryNav) {
            categoryNav.innerHTML = this.generateCategoryHTML(categoryTree);
            this.addCategoryTreeEventListeners();
        }
    },

    // Build category tree structure
    buildCategoryTree(categories) {
        const categoryMap = {};
        const tree = [];

        // Create category map
        categories.forEach(category => {
            categoryMap[category.id] = {
                ...category,
                children: [],
                level: 0
            };
        });

        // Build tree structure
        categories.forEach(category => {
            if (category.parent_id && categoryMap[category.parent_id]) {
                categoryMap[category.parent_id].children.push(categoryMap[category.id]);
                categoryMap[category.id].level = categoryMap[category.parent_id].level + 1;
            } else {
                tree.push(categoryMap[category.id]);
            }
        });

        return tree;
    },

    // Generate category HTML
    generateCategoryHTML(categories, level = 0) {
        if (!categories.length) return '';

        return categories.map(category => `
            <div class="category-item" data-category-id="${category.id}" data-level="${level}">
                <div class="category-header">
                    <span class="category-name">${category.name}</span>
                    ${category.children.length > 0 ? '<span class="category-toggle"><i class="fas fa-chevron-right"></i></span>' : ''}
                </div>
                ${category.children.length > 0 ? `
                    <div class="category-children" style="display: none;">
                        ${this.generateCategoryHTML(category.children, level + 1)}
                    </div>
                ` : ''}
            </div>
        `).join('');
    },

    // Add category tree event listeners
    addCategoryTreeEventListeners() {
        const categoryItems = document.querySelectorAll('.category-item');

        categoryItems.forEach(item => {
            const header = item.querySelector('.category-header');
            const toggle = item.querySelector('.category-toggle');

            if (header) {
                header.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.selectCategory(item.dataset.categoryId);
                });
            }

            if (toggle) {
                toggle.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleCategory(item);
                });
            }
        });
    },

    // Toggle category expansion
    toggleCategory(categoryItem) {
        const children = categoryItem.querySelector('.category-children');
        const toggle = categoryItem.querySelector('.category-toggle i');

        if (children && toggle) {
            const isOpen = children.style.display !== 'none';
            children.style.display = isOpen ? 'none' : 'block';
            toggle.className = isOpen ? 'fas fa-chevron-right' : 'fas fa-chevron-down';
        }
    },

    // Select category
    async selectCategory(categoryId) {
        try {
            CategoryState.loading = true;
            this.showCategoryLoading();

            // Update active category
            this.setActiveCategory(categoryId);

            // Load category details
            const category = await CategoriesAPI.getById(categoryId);
            if (category) {
                CategoryState.currentCategory = category;
                await this.loadCategoryProducts(categoryId);
                this.updateBreadcrumb(category);
                this.showCategoryInfo(category);
            }

        } catch (error) {
            console.error('Error selecting category:', error);
            StorefrontUtils.showNotification('Failed to load category', 'error');
        } finally {
            CategoryState.loading = false;
            this.hideCategoryLoading();
        }
    },

    // Set active category in navigation
    setActiveCategory(categoryId) {
        // Remove active class from all categories
        document.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
        });

        // Add active class to selected category
        const activeItem = document.querySelector(`[data-category-id="${categoryId}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    },

    // Load category products
    async loadCategoryProducts(categoryId) {
        try {
            const products = await ProductsAPI.getAll({ category_id: categoryId });
            CategoryState.categoryProducts = products;
            this.renderCategoryProducts(products);
        } catch (error) {
            console.error('Error loading category products:', error);
            throw error;
        }
    },

    // Render category products
    renderCategoryProducts(products) {
        const productsContainer = document.querySelector('.category-products');
        if (!productsContainer) return;

        if (products.length === 0) {
            productsContainer.innerHTML = `
                <div class="no-products">
                    <i class="fas fa-box-open"></i>
                    <h3>No products in this category</h3>
                    <p>This category doesn't have any products yet.</p>
                </div>
            `;
            return;
        }

        productsContainer.innerHTML = `
            <div class="category-products-header">
                <h2>Products in ${CategoryState.currentCategory.name}</h2>
                <span class="product-count">${products.length} products</span>
            </div>
            <div class="products-grid">
                ${products.map(product => `
                    <div class="product-card" data-product-id="${product.id}">
                        <div class="product-image">
                            <img src="${product.images[0] || 'images/placeholder.jpg'}" alt="${product.name}">
                            ${product.is_featured ? '<span class="product-badge">Featured</span>' : ''}
                        </div>
                        <div class="product-info">
                            <h3 class="product-title">${product.name}</h3>
                            <p class="product-description">${product.short_description || product.description.substring(0, 100)}...</p>
                            <div class="product-price">
                                <span class="current-price">${StorefrontUtils.formatCurrency(product.price)}</span>
                            </div>
                            <div class="product-actions">
                                <button class="btn btn-primary add-to-cart" data-product-id="${product.id}">
                                    <i class="fas fa-shopping-cart"></i>
                                    Add to Cart
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Add event listeners to product cards
        this.addProductCardEventListeners();
    },

    // Add product card event listeners
    addProductCardEventListeners() {
        const addToCartBtns = document.querySelectorAll('.category-products .add-to-cart');
        addToCartBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const productId = e.currentTarget.dataset.productId;
                ProductManager.addToCart(productId);
            });
        });
    },

    // Setup breadcrumb navigation
    setupBreadcrumbNavigation() {
        const breadcrumbContainer = document.querySelector('.breadcrumb');
        if (breadcrumbContainer) {
            breadcrumbContainer.addEventListener('click', (e) => {
                if (e.target.classList.contains('breadcrumb-link')) {
                    e.preventDefault();
                    const categoryId = e.target.dataset.categoryId;
                    if (categoryId) {
                        this.selectCategory(categoryId);
                    }
                }
            });
        }
    },

    // Update breadcrumb
    updateBreadcrumb(category) {
        const breadcrumbContainer = document.querySelector('.breadcrumb');
        if (!breadcrumbContainer) return;

        const breadcrumb = this.buildBreadcrumb(category);
        breadcrumbContainer.innerHTML = breadcrumb;
    },

    // Build breadcrumb
    buildBreadcrumb(category) {
        const breadcrumb = [
            { name: 'Home', id: null },
            { name: category.name, id: category.id }
        ];

        let currentCategory = category;
        while (currentCategory.parent_id) {
            // In a real implementation, you'd fetch the parent category
            // For now, we'll just show the current category
            break;
        }

        return breadcrumb.map((crumb, index) => `
            <span class="breadcrumb-item">
                ${index > 0 ? '<span class="breadcrumb-separator">/</span>' : ''}
                ${crumb.id ?
                    `<a href="#" class="breadcrumb-link" data-category-id="${crumb.id}">${crumb.name}</a>` :
                    `<span class="breadcrumb-current">${crumb.name}</span>`
                }
            </span>
        `).join('');
    },

    // Show category info
    showCategoryInfo(category) {
        const categoryInfo = document.querySelector('.category-info');
        if (!categoryInfo) return;

        categoryInfo.innerHTML = `
            <div class="category-details">
                <h1>${category.name}</h1>
                ${category.description ? `<p class="category-description">${category.description}</p>` : ''}
                <div class="category-meta">
                    <span class="category-product-count">
                        <i class="fas fa-box"></i>
                        ${CategoryState.categoryProducts.length} products
                    </span>
                </div>
            </div>
        `;
    },

    // Setup category navigation
    setupCategoryNavigation() {
        const categoryNavToggle = document.querySelector('.category-nav-toggle');
        const categoryNav = document.querySelector('.category-nav');

        if (categoryNavToggle && categoryNav) {
            categoryNavToggle.addEventListener('click', () => {
                categoryNav.classList.toggle('open');
            });
        }
    },

    // Setup category filters
    setupCategoryFilters() {
        const sortSelect = document.querySelector('.category-sort');
        const filterSelect = document.querySelector('.category-filter');

        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.applySort(e.target.value);
            });
        }

        if (filterSelect) {
            filterSelect.addEventListener('change', (e) => {
                this.applyFilter(e.target.value);
            });
        }
    },

    // Apply sorting
    applySort(sortBy) {
        if (!CategoryState.categoryProducts.length) return;

        let sortedProducts = [...CategoryState.categoryProducts];

        switch (sortBy) {
            case 'price-low':
                sortedProducts.sort((a, b) => a.price - b.price);
                break;
            case 'price-high':
                sortedProducts.sort((a, b) => b.price - a.price);
                break;
            case 'name':
                sortedProducts.sort((a, b) => a.name.localeCompare(b.name));
                break;
            case 'newest':
                sortedProducts.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                break;
            default:
                // Default sorting (featured first, then by name)
                sortedProducts.sort((a, b) => {
                    if (a.is_featured && !b.is_featured) return -1;
                    if (!a.is_featured && b.is_featured) return 1;
                    return a.name.localeCompare(b.name);
                });
        }

        this.renderCategoryProducts(sortedProducts);
    },

    // Apply filtering
    applyFilter(filterBy) {
        if (!CategoryState.categoryProducts.length) return;

        let filteredProducts = [...CategoryState.categoryProducts];

        switch (filterBy) {
            case 'featured':
                filteredProducts = filteredProducts.filter(p => p.is_featured);
                break;
            case 'on-sale':
                filteredProducts = filteredProducts.filter(p => p.compare_at_price);
                break;
            case 'in-stock':
                filteredProducts = filteredProducts.filter(p => p.inventory_quantity > 0);
                break;
            case 'all':
            default:
                // Show all products
                break;
        }

        this.renderCategoryProducts(filteredProducts);
    },

    // Show category loading state
    showCategoryLoading() {
        const productsContainer = document.querySelector('.category-products');
        if (productsContainer) {
            productsContainer.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading category products...</p>
                </div>
            `;
        }
    },

    // Hide category loading state
    hideCategoryLoading() {
        const loadingState = document.querySelector('.loading-state');
        if (loadingState) {
            loadingState.remove();
        }
    },

    // Search within category
    async searchInCategory(query) {
        if (!CategoryState.currentCategory) return;

        try {
            CategoryState.loading = true;
            this.showCategoryLoading();

            const products = await ProductsAPI.search(query, {
                category_id: CategoryState.currentCategory.id
            });

            CategoryState.categoryProducts = products;
            this.renderCategoryProducts(products);

        } catch (error) {
            console.error('Error searching in category:', error);
            StorefrontUtils.showNotification('Search failed', 'error');
        } finally {
            CategoryState.loading = false;
            this.hideCategoryLoading();
        }
    }
};

// Category Filter Widget
const CategoryFilterWidget = {
    // Initialize filter widget
    initialize() {
        this.createFilterWidget();
        this.setupFilterEvents();
    },

    // Create filter widget HTML
    createFilterWidget() {
        const filterContainer = document.querySelector('.category-filters');
        if (!filterContainer) return;

        filterContainer.innerHTML = `
            <div class="filter-widget">
                <div class="filter-group">
                    <label for="category-sort">Sort by:</label>
                    <select id="category-sort" class="filter-select">
                        <option value="featured">Featured</option>
                        <option value="name">Name A-Z</option>
                        <option value="price-low">Price: Low to High</option>
                        <option value="price-high">Price: High to Low</option>
                        <option value="newest">Newest First</option>
                    </select>
                </div>

                <div class="filter-group">
                    <label for="category-filter">Filter:</label>
                    <select id="category-filter" class="filter-select">
                        <option value="all">All Products</option>
                        <option value="featured">Featured Only</option>
                        <option value="on-sale">On Sale</option>
                        <option value="in-stock">In Stock</option>
                    </select>
                </div>

                <div class="filter-group">
                    <label for="category-search">Search in category:</label>
                    <input type="text" id="category-search" class="filter-input" placeholder="Search products...">
                </div>
            </div>
        `;
    },

    // Setup filter events
    setupFilterEvents() {
        const categorySearch = document.getElementById('category-search');
        if (categorySearch) {
            const debouncedSearch = StorefrontUtils.debounce((query) => {
                if (query.length >= 2) {
                    CategoryManager.searchInCategory(query);
                } else if (query.length === 0) {
                    // Reload original category products
                    CategoryManager.renderCategoryProducts(CategoryState.categoryProducts);
                }
            }, 300);

            categorySearch.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    CategoryManager.initialize();
    CategoryFilterWidget.initialize();
});

// Export for global use
window.CategoryManager = CategoryManager;
window.CategoryFilterWidget = CategoryFilterWidget;