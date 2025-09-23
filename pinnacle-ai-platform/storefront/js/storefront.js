/**
 * Pinnacle AI Boutique - Main Storefront JavaScript
 *
 * This file contains the main storefront functionality including:
 * - Page initialization
 * - Dynamic content loading
 * - UI interactions
 * - Event handlers
 */

// Storefront State Management
const StorefrontState = {
    currentPage: 1,
    productsPerPage: 12,
    currentCategory: null,
    searchQuery: '',
    cart: {
        items: [],
        total: 0,
        itemCount: 0
    },
    user: null,
    loading: false
};

// Utility Functions
const StorefrontUtils = {
    // Show/hide loading overlay
    setLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
        StorefrontState.loading = show;
    },

    // Format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    // Format date
    formatDate(date) {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },

    // Debounce function for search
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

    // Show notification
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);

        // Auto-hide after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);

        // Close button functionality
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        });
    },

    // Update cart display
    updateCartDisplay() {
        const cartCount = document.getElementById('cartCount');
        const cartBtn = document.getElementById('cartBtn');

        if (cartCount) {
            cartCount.textContent = StorefrontState.cart.itemCount;
            cartCount.style.display = StorefrontState.cart.itemCount > 0 ? 'block' : 'none';
        }

        if (cartBtn) {
            cartBtn.classList.toggle('has-items', StorefrontState.cart.itemCount > 0);
        }
    }
};

// Product Management
const ProductManager = {
    // Load products
    async loadProducts(categoryId = null, searchQuery = '', page = 1) {
        try {
            StorefrontUtils.setLoading(true);

            const params = {
                limit: StorefrontState.productsPerPage,
                offset: (page - 1) * StorefrontState.productsPerPage
            };

            if (categoryId) {
                params.category_id = categoryId;
            }

            if (searchQuery) {
                params.search = searchQuery;
            }

            const products = await ProductsAPI.getAll(params);

            // Update state
            StorefrontState.currentPage = page;
            StorefrontState.currentCategory = categoryId;
            StorefrontState.searchQuery = searchQuery;

            return products;
        } catch (error) {
            console.error('Error loading products:', error);
            StorefrontUtils.showNotification('Failed to load products', 'error');
            return [];
        } finally {
            StorefrontUtils.setLoading(false);
        }
    },

    // Render products grid
    renderProducts(products) {
        const productsGrid = document.getElementById('productsGrid');
        if (!productsGrid) return;

        if (products.length === 0) {
            productsGrid.innerHTML = `
                <div class="no-products">
                    <i class="fas fa-box-open"></i>
                    <h3>No products found</h3>
                    <p>Try adjusting your search or filter criteria</p>
                </div>
            `;
            return;
        }

        productsGrid.innerHTML = products.map(product => `
            <div class="product-card" data-product-id="${product.id}">
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
        `).join('');

        // Add event listeners
        this.addProductEventListeners();
    },

    // Add product event listeners
    addProductEventListeners() {
        // Add to cart buttons
        document.querySelectorAll('.add-to-cart').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const productId = e.currentTarget.dataset.productId;
                this.addToCart(productId);
            });
        });

        // Quick view buttons
        document.querySelectorAll('.quick-view').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const productId = e.currentTarget.dataset.productId;
                this.showQuickView(productId);
            });
        });

        // Product card clicks (for navigation to detail page)
        document.querySelectorAll('.product-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.product-actions')) {
                    const productId = card.dataset.productId;
                    this.showProductDetail(productId);
                }
            });
        });
    },

    // Add product to cart
    async addToCart(productId) {
        try {
            // Get or create cart
            let cartId = localStorage.getItem('cart_id');
            if (!cartId) {
                const sessionId = APIUtils.generateSessionId();
                const cart = await CartAPI.getOrCreate(sessionId);
                cartId = cart.id;
                localStorage.setItem('cart_id', cartId);
                localStorage.setItem('cart_session_id', sessionId);
            }

            // Add item to cart
            const cartItem = {
                product_id: productId,
                quantity: 1
            };

            const updatedCart = await CartAPI.addItem(cartId, cartItem);

            // Update local state
            StorefrontState.cart = {
                items: updatedCart.items || [],
                total: updatedCart.total_price,
                itemCount: updatedCart.total_items
            };

            StorefrontUtils.updateCartDisplay();
            StorefrontUtils.showNotification('Product added to cart!', 'success');

        } catch (error) {
            console.error('Error adding to cart:', error);
            StorefrontUtils.showNotification('Failed to add product to cart', 'error');
        }
    },

    // Show quick view modal
    async showQuickView(productId) {
        try {
            const product = await ProductsAPI.getById(productId);
            const modal = document.getElementById('productModal');
            const modalBody = document.getElementById('productModalBody');

            if (!modal || !modalBody) return;

            modalBody.innerHTML = `
                <div class="quick-view-content">
                    <div class="quick-view-image">
                        <img src="${product.images[0] || 'images/placeholder.jpg'}" alt="${product.name}">
                    </div>
                    <div class="quick-view-info">
                        <h2>${product.name}</h2>
                        <div class="quick-view-price">
                            ${StorefrontUtils.formatCurrency(product.price)}
                            ${product.compare_at_price ? `<span class="original-price">${StorefrontUtils.formatCurrency(product.compare_at_price)}</span>` : ''}
                        </div>
                        <p class="quick-view-description">${product.description}</p>
                        <div class="quick-view-actions">
                            <button class="btn btn-primary add-to-cart" data-product-id="${product.id}">
                                <i class="fas fa-shopping-cart"></i>
                                Add to Cart
                            </button>
                            <button class="btn btn-outline" onclick="ProductManager.showProductDetail('${product.id}')">
                                <i class="fas fa-info-circle"></i>
                                View Details
                            </button>
                        </div>
                    </div>
                </div>
            `;

            modal.style.display = 'flex';

            // Add event listener for add to cart in modal
            const addToCartBtn = modalBody.querySelector('.add-to-cart');
            if (addToCartBtn) {
                addToCartBtn.addEventListener('click', () => {
                    this.addToCart(productId);
                    modal.style.display = 'none';
                });
            }

        } catch (error) {
            console.error('Error showing quick view:', error);
            StorefrontUtils.showNotification('Failed to load product details', 'error');
        }
    },

    // Show product detail page
    showProductDetail(productId) {
        // In a real application, this would navigate to a product detail page
        // For now, we'll just show the quick view
        this.showQuickView(productId);
    }
};

// Category Management
const CategoryManager = {
    // Load categories
    async loadCategories() {
        try {
            const categories = await CategoriesAPI.getAll();
            return categories;
        } catch (error) {
            console.error('Error loading categories:', error);
            return [];
        }
    },

    // Render categories
    renderCategories(categories) {
        const categoriesGrid = document.getElementById('categoriesGrid');
        if (!categoriesGrid) return;

        if (categories.length === 0) {
            categoriesGrid.innerHTML = '<p>No categories available</p>';
            return;
        }

        categoriesGrid.innerHTML = categories.map(category => `
            <div class="category-card" data-category-id="${category.id}">
                <div class="category-image">
                    <img src="${category.image_url || 'images/category-placeholder.jpg'}" alt="${category.name}">
                </div>
                <div class="category-info">
                    <h3 class="category-name">${category.name}</h3>
                    <p class="category-description">${category.description || ''}</p>
                    <button class="btn btn-outline view-category" data-category-id="${category.id}">
                        View Products
                    </button>
                </div>
            </div>
        `).join('');

        // Add event listeners
        this.addCategoryEventListeners();
    },

    // Add category event listeners
    addCategoryEventListeners() {
        document.querySelectorAll('.view-category').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const categoryId = e.currentTarget.dataset.categoryId;
                this.viewCategory(categoryId);
            });
        });
    },

    // View category products
    async viewCategory(categoryId) {
        try {
            // Update active category in navigation
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });

            // Load and display category products
            const products = await ProductManager.loadProducts(categoryId);
            ProductManager.renderProducts(products);

            // Scroll to products section
            const productsSection = document.getElementById('products');
            if (productsSection) {
                productsSection.scrollIntoView({ behavior: 'smooth' });
            }

        } catch (error) {
            console.error('Error viewing category:', error);
            StorefrontUtils.showNotification('Failed to load category products', 'error');
        }
    }
};

// Search Management
const SearchManager = {
    // Initialize search
    init() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            const debouncedSearch = StorefrontUtils.debounce(this.performSearch.bind(this), 300);
            searchInput.addEventListener('input', debouncedSearch);
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.performSearch(e.target.value);
                }
            });
        }
    },

    // Perform search
    async performSearch(query) {
        if (query.length < 2) return;

        try {
            const products = await ProductManager.loadProducts(null, query);
            ProductManager.renderProducts(products);

            // Scroll to products section
            const productsSection = document.getElementById('products');
            if (productsSection) {
                productsSection.scrollIntoView({ behavior: 'smooth' });
            }

        } catch (error) {
            console.error('Error performing search:', error);
            StorefrontUtils.showNotification('Search failed', 'error');
        }
    }
};

// Cart Management
const CartManager = {
    // Show cart modal
    showCartModal() {
        const modal = document.getElementById('cartModal');
        const modalBody = document.getElementById('cartModalBody');

        if (!modal || !modalBody) return;

        this.loadCartItems();
        modal.style.display = 'flex';
    },

    // Hide cart modal
    hideCartModal() {
        const modal = document.getElementById('cartModal');
        if (modal) {
            modal.style.display = 'none';
        }
    },

    // Load cart items
    async loadCartItems() {
        try {
            const cartId = localStorage.getItem('cart_id');
            if (!cartId) {
                this.renderEmptyCart();
                return;
            }

            const cart = await CartAPI.getById(cartId);
            this.renderCartItems(cart);

        } catch (error) {
            console.error('Error loading cart items:', error);
            this.renderEmptyCart();
        }
    },

    // Render cart items
    renderCartItems(cart) {
        const modalBody = document.getElementById('cartModalBody');
        if (!modalBody) return;

        if (!cart.items || cart.items.length === 0) {
            this.renderEmptyCart();
            return;
        }

        modalBody.innerHTML = `
            <div class="cart-items">
                ${cart.items.map(item => `
                    <div class="cart-item">
                        <div class="cart-item-image">
                            <img src="${item.product_image || 'images/placeholder.jpg'}" alt="${item.product_name}">
                        </div>
                        <div class="cart-item-info">
                            <h4 class="cart-item-name">${item.product_name}</h4>
                            <div class="cart-item-price">${StorefrontUtils.formatCurrency(item.price)}</div>
                            <div class="cart-item-quantity">
                                <button class="quantity-btn" onclick="CartManager.updateQuantity('${item.id}', ${item.quantity - 1})">-</button>
                                <span class="quantity-value">${item.quantity}</span>
                                <button class="quantity-btn" onclick="CartManager.updateQuantity('${item.id}', ${item.quantity + 1})">+</button>
                            </div>
                        </div>
                        <div class="cart-item-total">
                            ${StorefrontUtils.formatCurrency(item.total_price)}
                        </div>
                        <button class="cart-item-remove" onclick="CartManager.removeItem('${item.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `).join('')}
            </div>
            <div class="cart-summary">
                <div class="cart-total">
                    <span>Total: ${StorefrontUtils.formatCurrency(cart.total_price)}</span>
                </div>
                <div class="cart-actions">
                    <button class="btn btn-outline" onclick="CartManager.hideCartModal()">Continue Shopping</button>
                    <button class="btn btn-primary" onclick="CartManager.checkout()">Checkout</button>
                </div>
            </div>
        `;
    },

    // Render empty cart
    renderEmptyCart() {
        const modalBody = document.getElementById('cartModalBody');
        if (!modalBody) return;

        modalBody.innerHTML = `
            <div class="empty-cart">
                <i class="fas fa-shopping-cart"></i>
                <h3>Your cart is empty</h3>
                <p>Add some products to get started!</p>
                <button class="btn btn-primary" onclick="CartManager.hideCartModal()">Continue Shopping</button>
            </div>
        `;
    },

    // Update item quantity
    async updateQuantity(itemId, newQuantity) {
        if (newQuantity < 1) {
            this.removeItem(itemId);
            return;
        }

        try {
            const cartId = localStorage.getItem('cart_id');
            if (!cartId) return;

            await CartAPI.updateItem(cartId, itemId, newQuantity);
            await this.loadCartItems();

        } catch (error) {
            console.error('Error updating quantity:', error);
            StorefrontUtils.showNotification('Failed to update quantity', 'error');
        }
    },

    // Remove item from cart
    async removeItem(itemId) {
        try {
            const cartId = localStorage.getItem('cart_id');
            if (!cartId) return;

            await CartAPI.removeItem(cartId, itemId);
            await this.loadCartItems();

            // Update cart display
            const cart = await CartAPI.getById(cartId);
            StorefrontState.cart = {
                items: cart.items || [],
                total: cart.total_price,
                itemCount: cart.total_items
            };
            StorefrontUtils.updateCartDisplay();

        } catch (error) {
            console.error('Error removing item:', error);
            StorefrontUtils.showNotification('Failed to remove item', 'error');
        }
    },

    // Checkout process
    checkout() {
        // In a real application, this would redirect to checkout page
        StorefrontUtils.showNotification('Checkout functionality coming soon!', 'info');
    }
};

// User Management
const UserManager = {
    // Show user dropdown
    toggleUserDropdown() {
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) {
            dropdown.classList.toggle('show');
        }
    },

    // Hide user dropdown
    hideUserDropdown() {
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) {
            dropdown.classList.remove('show');
        }
    },

    // Handle user menu clicks
    handleUserMenuClick(action) {
        this.hideUserDropdown();

        switch (action) {
            case 'signin':
                this.showSignInModal();
                break;
            case 'signup':
                this.showSignUpModal();
                break;
            case 'wishlist':
                this.showWishlist();
                break;
            case 'orders':
                this.showOrderHistory();
                break;
        }
    },

    // Show sign in modal
    showSignInModal() {
        StorefrontUtils.showNotification('Sign in functionality coming soon!', 'info');
    },

    // Show sign up modal
    showSignUpModal() {
        StorefrontUtils.showNotification('Sign up functionality coming soon!', 'info');
    },

    // Show wishlist
    showWishlist() {
        StorefrontUtils.showNotification('Wishlist functionality coming soon!', 'info');
    },

    // Show order history
    showOrderHistory() {
        StorefrontUtils.showNotification('Order history functionality coming soon!', 'info');
    }
};

// Newsletter Management
const NewsletterManager = {
    // Handle newsletter form submission
    async handleSubmit(e) {
        e.preventDefault();

        const emailInput = e.target.querySelector('input[type="email"]');
        const email = emailInput.value.trim();

        if (!APIUtils.isValidEmail(email)) {
            StorefrontUtils.showNotification('Please enter a valid email address', 'error');
            return;
        }

        try {
            // In a real application, this would call an API
            StorefrontUtils.showNotification('Thank you for subscribing!', 'success');
            emailInput.value = '';

        } catch (error) {
            console.error('Error subscribing to newsletter:', error);
            StorefrontUtils.showNotification('Failed to subscribe. Please try again.', 'error');
        }
    }
};

// Initialize storefront when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🏪 Initializing Pinnacle AI Boutique Storefront...');

    // Initialize search
    SearchManager.init();

    // Load initial data
    await StorefrontManager.initialize();

    // Add event listeners
    StorefrontManager.addEventListeners();

    console.log('✅ Storefront initialized successfully');
});

// Main Storefront Manager
const StorefrontManager = {
    // Initialize storefront
    async initialize() {
        try {
            // Load categories
            const categories = await CategoryManager.loadCategories();
            CategoryManager.renderCategories(categories);

            // Load featured products
            const products = await ProductManager.loadProducts();
            ProductManager.renderProducts(products);

            // Initialize cart display
            StorefrontUtils.updateCartDisplay();

        } catch (error) {
            console.error('Error initializing storefront:', error);
            StorefrontUtils.showNotification('Failed to initialize storefront', 'error');
        }
    },

    // Add event listeners
    addEventListeners() {
        // Cart button
        const cartBtn = document.getElementById('cartBtn');
        if (cartBtn) {
            cartBtn.addEventListener('click', () => CartManager.showCartModal());
        }

        // Close cart modal
        const closeCartModal = document.getElementById('closeCartModal');
        if (closeCartModal) {
            closeCartModal.addEventListener('click', () => CartManager.hideCartModal());
        }

        // Close product modal
        const closeProductModal = document.getElementById('closeProductModal');
        if (closeProductModal) {
            closeProductModal.addEventListener('click', () => {
                const modal = document.getElementById('productModal');
                if (modal) modal.style.display = 'none';
            });
        }

        // User menu
        const userBtn = document.getElementById('userBtn');
        if (userBtn) {
            userBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                UserManager.toggleUserDropdown();
            });
        }

        // User dropdown items
        document.querySelectorAll('#userDropdown .dropdown-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const action = e.target.textContent.toLowerCase().replace(' ', '');
                UserManager.handleUserMenuClick(action);
            });
        });

        // Newsletter form
        const newsletterForm = document.getElementById('newsletterForm');
        if (newsletterForm) {
            newsletterForm.addEventListener('submit', NewsletterManager.handleSubmit.bind(NewsletterManager));
        }

        // Mobile menu toggle
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', this.toggleMobileMenu);
        }

        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            // Close user dropdown
            if (!e.target.closest('.user-menu')) {
                UserManager.hideUserDropdown();
            }

            // Close modals
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });

        // Load more products
        const loadMoreBtn = document.getElementById('loadMoreProducts');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', this.loadMoreProducts);
        }
    },

    // Toggle mobile menu
    toggleMobileMenu() {
        const nav = document.querySelector('.nav');
        if (nav) {
            nav.classList.toggle('mobile-open');
        }
    },

    // Load more products
    async loadMoreProducts() {
        try {
            StorefrontState.currentPage++;
            const products = await ProductManager.loadProducts(
                StorefrontState.currentCategory,
                StorefrontState.searchQuery,
                StorefrontState.currentPage
            );

            if (products.length > 0) {
                const productsGrid = document.getElementById('productsGrid');
                if (productsGrid) {
                    productsGrid.innerHTML += ProductManager.renderProducts(products);
                }
            } else {
                StorefrontUtils.showNotification('No more products to load', 'info');
                StorefrontState.currentPage--;
            }

        } catch (error) {
            console.error('Error loading more products:', error);
            StorefrontUtils.showNotification('Failed to load more products', 'error');
            StorefrontState.currentPage--;
        }
    }
};

// Export for global use
window.StorefrontUtils = StorefrontUtils;
window.ProductManager = ProductManager;
window.CategoryManager = CategoryManager;
window.SearchManager = SearchManager;
window.CartManager = CartManager;
window.UserManager = UserManager;
window.StorefrontManager = StorefrontManager;