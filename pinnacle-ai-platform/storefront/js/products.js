/**
 * Pinnacle AI Boutique - Products Functionality
 * 
 * This file contains all product-related functionality including:
 * - Product display and filtering
 * - Product search
 * - Product modal management
 * - Product interactions (wishlist, compare, etc.)
 */

// Product Manager Class
class ProductManager {
    constructor() {
        this.products = [];
        this.categories = [];
        this.currentFilters = {
            category: null,
            search: '',
            priceRange: null,
            sortBy: 'name',
            sortOrder: 'asc'
        };
        this.pagination = {
            page: 1,
            limit: 12,
            total: 0,
            hasMore: true
        };
        
        this.bindEvents();
    }
    
    // Bind event listeners
    bindEvents() {
        // Product card interactions
        document.addEventListener('click', (event) => {
            const productCard = event.target.closest('.product-card');
            if (productCard) {
                const productId = productCard.dataset.productId;
                if (event.target.closest('.product-add-to-cart')) {
                    this.addToCart(productId);
                } else if (event.target.closest('.product-wishlist-btn')) {
                    this.toggleWishlist(productId);
                } else if (event.target.closest('.product-action-btn')) {
                    event.preventDefault();
                    this.showProductModal(productId);
                }
            }
            
            // Category card interactions
            const categoryCard = event.target.closest('.category-card');
            if (categoryCard) {
                const categoryId = categoryCard.dataset.categoryId;
                this.filterByCategory(categoryId);
            }
        });
        
        // Load more products
        const loadMoreBtn = document.getElementById('loadMoreProducts');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => {
                this.loadMoreProducts();
            });
        }
    }
    
    // Load products
    async loadProducts(reset = false) {
        if (reset) {
            this.pagination.page = 1;
            this.pagination.hasMore = true;
        }
        
        if (!this.pagination.hasMore && !reset) {
            return;
        }
        
        try {
            this.showLoading('Loading products...');
            
            const params = {
                category_id: this.currentFilters.category,
                search: this.currentFilters.search,
                limit: this.pagination.limit,
                offset: (this.pagination.page - 1) * this.pagination.limit,
                sort_by: this.currentFilters.sortBy,
                sort_order: this.currentFilters.sortOrder
            };
            
            const response = await ProductsAPI.getAll(params);
            
            if (reset) {
                this.products = response.products || [];
            } else {
                this.products = [...this.products, ...(response.products || [])];
            }
            
            this.pagination.total = response.total || 0;
            this.pagination.hasMore = this.products.length < this.pagination.total;
            
            this.renderProducts();
            this.updateLoadMoreButton();
            
        } catch (error) {
            console.error('Error loading products:', error);
            this.showMessage('Error loading products.', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    // Load categories
    async loadCategories() {
        try {
            this.categories = await CategoriesAPI.getAll();
            this.renderCategories();
        } catch (error) {
            console.error('Error loading categories:', error);
            this.showMessage('Error loading categories.', 'error');
        }
    }
    
    // Render products
    renderProducts() {
        const productsGrid = document.getElementById('productsGrid');
        if (!productsGrid) return;
        
        if (this.products.length === 0) {
            productsGrid.innerHTML = `
                <div class="no-products">
                    <i class="fas fa-box-open"></i>
                    <h3>No products found</h3>
                    <p>Try adjusting your search or filter criteria.</p>
                </div>
            `;
            return;
        }
        
        const productsHTML = this.products.map(product => this.createProductCard(product)).join('');
        productsGrid.innerHTML = productsHTML;
        
        // Add animation to new products
        if (this.pagination.page > 1) {
            const newCards = productsGrid.querySelectorAll('.product-card:nth-last-child(-n+' + this.pagination.limit + ')');
            newCards.forEach((card, index) => {
                setTimeout(() => {
                    card.classList.add('animate-in');
                }, index * 100);
            });
        }
    }
    
    // Create product card HTML
    createProductCard(product) {
        const isOnSale = product.compare_at_price && product.compare_at_price > product.price;
        const discountPercentage = isOnSale 
            ? Math.round(((product.compare_at_price - product.price) / product.compare_at_price) * 100)
            : 0;
        
        return `
            <div class="product-card" data-product-id="${product.id}">
                <div class="product-image">
                    <img src="${product.images?.[0] || 'https://via.placeholder.com/300x300'}" 
                         alt="${product.name}"
                         loading="lazy">
                    <div class="product-badges">
                        ${product.is_featured ? '<span class="product-badge featured">Featured</span>' : ''}
                        ${isOnSale ? `<span class="product-badge sale">-${discountPercentage}%</span>` : ''}
                        ${product.is_new ? '<span class="product-badge new">New</span>' : ''}
                    </div>
                    <div class="product-actions">
                        <button class="product-action-btn wishlist-btn" 
                                data-product-id="${product.id}"
                                title="Add to Wishlist">
                            <i class="far fa-heart"></i>
                        </button>
                        <button class="product-action-btn quick-view-btn" 
                                data-product-id="${product.id}"
                                title="Quick View">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>
                <div class="product-info">
                    <h3 class="product-title">
                        <a href="#" class="product-link" data-product-id="${product.id}">
                            ${product.name}
                        </a>
                    </h3>
                    <div class="product-price">
                        <span class="product-price-current">${APIUtils.formatCurrency(product.price)}</span>
                        ${isOnSale ? `<span class="product-price-compare">${APIUtils.formatCurrency(product.compare_at_price)}</span>` : ''}
                    </div>
                    <div class="product-rating">
                        <div class="product-stars">${this.generateStars(product.rating || 0)}</div>
                        <span class="product-rating-count">(${product.review_count || 0})</span>
                    </div>
                    <p class="product-description">${product.short_description || product.description?.substring(0, 100) + '...'}</p>
                    <div class="product-footer">
                        <button class="product-add-to-cart" data-product-id="${product.id}">
                            <i class="fas fa-shopping-cart"></i>
                            Add to Cart
                        </button>
                        <button class="product-wishlist-btn" data-product-id="${product.id}">
                            <i class="far fa-heart"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Generate star rating HTML
    generateStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 !== 0;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        
        let stars = '';
        
        for (let i = 0; i < fullStars; i++) {
            stars += '<i class="fas fa-star"></i>';
        }
        
        if (hasHalfStar) {
            stars += '<i class="fas fa-star-half-alt"></i>';
        }
        
        for (let i = 0; i < emptyStars; i++) {
            stars += '<i class="far fa-star"></i>';
        }
        
        return stars;
    }
    
    // Render categories
    renderCategories() {
        const categoriesGrid = document.getElementById('categoriesGrid');
        if (!categoriesGrid) return;
        
        if (this.categories.length === 0) {
            categoriesGrid.innerHTML = '<p class="no-data">No categories available.</p>';
            return;
        }
        
        const categoriesHTML = this.categories.map(category => `
            <div class="category-card" data-category-id="${category.id}">
                <div class="category-image">
                    <img src="${category.image_url || 'https://via.placeholder.com/300x200'}" 
                         alt="${category.name}"
                         loading="lazy">
                    <div class="category-overlay">
                        <h3 class="category-title">${category.name}</h3>
                    </div>
                </div>
                <div class="category-info">
                    <p class="category-description">${category.description || ''}</p>
                    <span class="category-product-count">${category.product_count || 0} products</span>
                </div>
            </div>
        `).join('');
        
        categoriesGrid.innerHTML = categoriesHTML;
    }
    
    // Update load more button
    updateLoadMoreButton() {
        const loadMoreBtn = document.getElementById('loadMoreProducts');
        if (loadMoreBtn) {
            if (this.pagination.hasMore) {
                loadMoreBtn.style.display = 'block';
                loadMoreBtn.textContent = 'Load More Products';
            } else {
                loadMoreBtn.style.display = 'none';
            }
        }
    }
    
    // Load more products
    async loadMoreProducts() {
        if (!this.pagination.hasMore) {
            return;
        }
        
        this.pagination.page++;
        await this.loadProducts(false);
    }
    
    // Filter by category
    async filterByCategory(categoryId) {
        this.currentFilters.category = categoryId;
        this.pagination.page = 1;
        
        // Update active category
        this.updateActiveCategory(categoryId);
        
        await this.loadProducts(true);
        this.scrollToProducts();
    }
    
    // Update active category
    updateActiveCategory(categoryId) {
        // Remove active class from all category cards
        const categoryCards = document.querySelectorAll('.category-card');
        categoryCards.forEach(card => {
            card.classList.remove('active');
        });
        
        // Add active class to selected category
        const activeCard = document.querySelector(`[data-category-id="${categoryId}"]`);
        if (activeCard) {
            activeCard.classList.add('active');
        }
    }
    
    // Search products
    async searchProducts(query) {
        this.currentFilters.search = query;
        this.pagination.page = 1;
        await this.loadProducts(true);
    }
    
    // Clear filters
    async clearFilters() {
        this.currentFilters = {
            category: null,
            search: '',
            priceRange: null,
            sortBy: 'name',
            sortOrder: 'asc'
        };
        
        this.pagination.page = 1;
        await this.loadProducts(true);
    }
    
    // Sort products
    async sortProducts(sortBy, sortOrder = 'asc') {
        this.currentFilters.sortBy = sortBy;
        this.currentFilters.sortOrder = sortOrder;
        this.pagination.page = 1;
        await this.loadProducts(true);
    }
    
    // Add to cart
    async addToCart(productId) {
        try {
            await cartManager.addItem(productId);
        } catch (error) {
            console.error('Error adding to cart:', error);
            this.showMessage('Error adding product to cart.', 'error');
        }
    }
    
    // Toggle wishlist
    async toggleWishlist(productId) {
        try {
            // This would integrate with wishlist functionality
            this.showMessage('Wishlist functionality coming soon!', 'info');
        } catch (error) {
            console.error('Error toggling wishlist:', error);
            this.showMessage('Error updating wishlist.', 'error');
        }
    }
    
    // Show product modal
    async showProductModal(productId) {
        try {
            const product = await ProductsAPI.getById(productId);
            this.renderProductModal(product);
            
            const modal = document.getElementById('productModal');
            if (modal) {
                modal.classList.add('show');
                document.body.style.overflow = 'hidden';
            }
        } catch (error) {
            console.error('Error loading product:', error);
            this.showMessage('Error loading product details.', 'error');
        }
    }
    
    // Render product modal
    renderProductModal(product) {
        const modalBody = document.getElementById('productModalBody');
        if (!modalBody) return;
        
        const isOnSale = product.compare_at_price && product.compare_at_price > product.price;
        const discountPercentage = isOnSale 
            ? Math.round(((product.compare_at_price - product.price) / product.compare_at_price) * 100)
            : 0;
        
        modalBody.innerHTML = `
            <div class="product-modal-content">
                <div class="product-modal-gallery">
                    <div class="product-modal-image-main">
                        <img src="${product.images?.[0] || 'https://via.placeholder.com/400x400'}" 
                             alt="${product.name}">
                        ${isOnSale ? `<span class="product-modal-badge sale">-${discountPercentage}%</span>` : ''}
                    </div>
                    ${product.images?.length > 1 ? `
                        <div class="product-modal-thumbnails">
                            ${product.images.map((image, index) => `
                                <img src="${image}" alt="${product.name}" 
                                     class="product-modal-thumbnail ${index === 0 ? 'active' : ''}"
                                     data-image-index="${index}">
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
                <div class="product-modal-info">
                    <h2 class="product-modal-title">${product.name}</h2>
                    
                    <div class="product-modal-price">
                        <span class="product-price-current">${APIUtils.formatCurrency(product.price)}</span>
                        ${isOnSale ? `<span class="product-price-compare">${APIUtils.formatCurrency(product.compare_at_price)}</span>` : ''}
                    </div>
                    
                    <div class="product-modal-rating">
                        <div class="product-stars">${this.generateStars(product.rating || 0)}</div>
                        <span class="product-rating-count">(${product.review_count || 0} reviews)</span>
                    </div>
                    
                    <div class="product-modal-description">
                        <p>${product.description}</p>
                    </div>
                    
                    <div class="product-modal-meta">
                        <div class="product-meta-item">
                            <span class="meta-label">SKU:</span>
                            <span class="meta-value">${product.sku}</span>
                        </div>
                        <div class="product-meta-item">
                            <span class="meta-label">Category:</span>
                            <span class="meta-value">${product.category_name || 'N/A'}</span>
                        </div>
                        <div class="product-meta-item">
                            <span class="meta-label">Stock:</span>
                            <span class="meta-value ${product.inventory_quantity > 0 ? 'in-stock' : 'out-of-stock'}">
                                ${product.inventory_quantity > 0 ? `${product.inventory_quantity} in stock` : 'Out of stock'}
                            </span>
                        </div>
                    </div>
                    
                    <div class="product-modal-actions">
                        <button class="btn btn-primary btn-large" 
                                onclick="productManager.addToCart('${product.id}')"
                                ${product.inventory_quantity <= 0 ? 'disabled' : ''}>
                            <i class="fas fa-shopping-cart"></i>
                            ${product.inventory_quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
                        </button>
                        <button class="btn btn-outline btn-large" 
                                onclick="productManager.toggleWishlist('${product.id}')">
                            <i class="far fa-heart"></i>
                            Add to Wishlist
                        </button>
                    </div>
                    
                    ${product.tags?.length ? `
                        <div class="product-modal-tags">
                            <h4>Tags:</h4>
                            <div class="product-tags">
                                ${product.tags.map(tag => `<span class="product-tag">${tag}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Add thumbnail click handlers
        const thumbnails = modalBody.querySelectorAll('.product-modal-thumbnail');
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.imageIndex);
                const mainImage = modalBody.querySelector('.product-modal-image-main img');
                const allThumbnails = modalBody.querySelectorAll('.product-modal-thumbnail');
                
                if (mainImage && product.images?.[index]) {
                    mainImage.src = product.images[index];
                    allThumbnails.forEach(thumb => thumb.classList.remove('active'));
                    e.target.classList.add('active');
                }
            });
        });
    }
    
    // Hide product modal
    hideProductModal() {
        const modal = document.getElementById('productModal');
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }
    
    // Scroll to products section
    scrollToProducts() {
        const productsSection = document.getElementById('products');
        if (productsSection) {
            productsSection.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
    
    // Show loading
    showLoading(message = 'Loading...') {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            const loadingText = loadingOverlay.querySelector('p');
            if (loadingText) {
                loadingText.textContent = message;
            }
            loadingOverlay.classList.add('show');
        }
    }
    
    // Hide loading
    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.classList.remove('show');
        }
    }
    
    // Show message
    showMessage(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <div class="toast-message">${message}</div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 100);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 4000);
    }
    
    // Initialize
    async init() {
        await Promise.all([
            this.loadCategories(),
            this.loadProducts(true)
        ]);
    }
}

// Create global product manager instance
const productManager = new ProductManager();

// Export for global access
window.productManager = productManager;
window.ProductManager = ProductManager;
