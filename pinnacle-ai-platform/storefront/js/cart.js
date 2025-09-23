/**
 * Pinnacle AI Boutique - Cart Functionality
 * 
 * This file contains all cart-related functionality including:
 * - Cart state management
 * - Cart UI updates
 * - Cart persistence
 * - Checkout process
 */

// Cart Manager Class
class CartManager {
    constructor() {
        this.cart = {
            id: null,
            items: [],
            total: 0,
            itemCount: 0,
            currency: 'USD'
        };
        
        this.sessionId = this.getSessionId();
        this.loadCartFromStorage();
        this.bindEvents();
    }
    
    // Get session ID
    getSessionId() {
        let sessionId = localStorage.getItem('cart_session_id');
        if (!sessionId) {
            sessionId = APIUtils.generateSessionId();
            localStorage.setItem('cart_session_id', sessionId);
        }
        return sessionId;
    }
    
    // Load cart from localStorage
    loadCartFromStorage() {
        const savedCart = localStorage.getItem('cart');
        if (savedCart) {
            try {
                this.cart = JSON.parse(savedCart);
            } catch (error) {
                console.error('Error loading cart from storage:', error);
                this.cart = {
                    id: null,
                    items: [],
                    total: 0,
                    itemCount: 0,
                    currency: 'USD'
                };
            }
        }
    }
    
    // Save cart to localStorage
    saveCartToStorage() {
        localStorage.setItem('cart', JSON.stringify(this.cart));
    }
    
    // Bind event listeners
    bindEvents() {
        // Listen for cart updates
        document.addEventListener('cartUpdated', (event) => {
            this.updateCartDisplay();
        });
        
        // Handle cart icon clicks
        const cartBtn = document.getElementById('cartBtn');
        if (cartBtn) {
            cartBtn.addEventListener('click', () => {
                this.showCart();
            });
        }
    }
    
    // Add item to cart
    async addItem(productId, quantity = 1, variantId = null) {
        try {
            // Show loading
            this.showLoading('Adding to cart...');
            
            // Get or create cart
            if (!this.cart.id) {
                await this.createCart();
            }
            
            // Add item to cart via API
            const itemData = {
                product_id: productId,
                variant_id: variantId,
                quantity: quantity
            };
            
            const response = await CartAPI.addItem(this.cart.id, itemData);
            
            // Update local cart state
            this.cart = {
                id: response.id,
                items: response.items || [],
                total: response.total_price || 0,
                itemCount: response.total_items || 0,
                currency: response.currency || 'USD'
            };
            
            // Save to storage
            this.saveCartToStorage();
            
            // Update display
            this.updateCartDisplay();
            
            // Show success message
            this.showMessage('Product added to cart!', 'success');
            
            // Dispatch cart update event
            document.dispatchEvent(new CustomEvent('cartUpdated', {
                detail: { cart: this.cart }
            }));
            
        } catch (error) {
            console.error('Error adding item to cart:', error);
            this.showMessage('Error adding product to cart.', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    // Update cart item quantity
    async updateItemQuantity(itemId, newQuantity) {
        if (newQuantity <= 0) {
            await this.removeItem(itemId);
            return;
        }
        
        try {
            const response = await CartAPI.updateItem(this.cart.id, itemId, newQuantity);
            
            this.cart = {
                id: response.id,
                items: response.items || [],
                total: response.total_price || 0,
                itemCount: response.total_items || 0,
                currency: response.currency || 'USD'
            };
            
            this.saveCartToStorage();
            this.updateCartDisplay();
            
            document.dispatchEvent(new CustomEvent('cartUpdated', {
                detail: { cart: this.cart }
            }));
            
        } catch (error) {
            console.error('Error updating cart item:', error);
            this.showMessage('Error updating cart.', 'error');
        }
    }
    
    // Remove item from cart
    async removeItem(itemId) {
        try {
            const response = await CartAPI.removeItem(this.cart.id, itemId);
            
            this.cart = {
                id: response.id,
                items: response.items || [],
                total: response.total_price || 0,
                itemCount: response.total_items || 0,
                currency: response.currency || 'USD'
            };
            
            this.saveCartToStorage();
            this.updateCartDisplay();
            
            this.showMessage('Product removed from cart.', 'success');
            
            document.dispatchEvent(new CustomEvent('cartUpdated', {
                detail: { cart: this.cart }
            }));
            
        } catch (error) {
            console.error('Error removing item from cart:', error);
            this.showMessage('Error removing product from cart.', 'error');
        }
    }
    
    // Create new cart
    async createCart() {
        try {
            const cartData = await CartAPI.getOrCreate(this.sessionId);
            this.cart.id = cartData.id;
            this.saveCartToStorage();
            return cartData.id;
        } catch (error) {
            console.error('Error creating cart:', error);
            throw error;
        }
    }
    
    // Get cart data
    async getCart() {
        if (!this.cart.id) {
            return this.cart;
        }
        
        try {
            const cartData = await CartAPI.getById(this.cart.id);
            this.cart = {
                id: cartData.id,
                items: cartData.items || [],
                total: cartData.total_price || 0,
                itemCount: cartData.total_items || 0,
                currency: cartData.currency || 'USD'
            };
            
            this.saveCartToStorage();
            return this.cart;
        } catch (error) {
            console.error('Error getting cart:', error);
            return this.cart;
        }
    }
    
    // Update cart display
    updateCartDisplay() {
        const cartCountElements = document.querySelectorAll('#cartCount, .cart-count');
        cartCountElements.forEach(element => {
            if (element) {
                element.textContent = this.cart.itemCount;
            }
        });
        
        // Update cart icon
        const cartBtn = document.getElementById('cartBtn');
        if (cartBtn) {
            if (this.cart.itemCount > 0) {
                cartBtn.classList.add('has-items');
            } else {
                cartBtn.classList.remove('has-items');
            }
        }
    }
    
    // Show cart modal
    async showCart() {
        try {
            const cartData = await this.getCart();
            this.renderCart(cartData);
            
            const cartModal = document.getElementById('cartModal');
            if (cartModal) {
                cartModal.classList.add('show');
                document.body.style.overflow = 'hidden';
            }
        } catch (error) {
            console.error('Error showing cart:', error);
            this.showMessage('Error loading cart.', 'error');
        }
    }
    
    // Hide cart modal
    hideCart() {
        const cartModal = document.getElementById('cartModal');
        if (cartModal) {
            cartModal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }
    
    // Render cart modal
    renderCart(cartData) {
        const cartModalBody = document.getElementById('cartModalBody');
        if (!cartModalBody) return;
        
        if (!cartData.items || cartData.items.length === 0) {
            cartModalBody.innerHTML = `
                <div class="empty-cart">
                    <i class="fas fa-shopping-cart"></i>
                    <h3>Your cart is empty</h3>
                    <p>Add some products to get started!</p>
                    <button class="btn btn-primary" onclick="cartManager.hideCart()">
                        Continue Shopping
                    </button>
                </div>
            `;
            return;
        }
        
        const itemsHTML = cartData.items.map(item => `
            <div class="cart-item" data-item-id="${item.id}">
                <div class="cart-item-image">
                    <img src="${item.product_image || 'https://via.placeholder.com/80x80'}" 
                         alt="${item.product_name}">
                </div>
                <div class="cart-item-info">
                    <h4 class="cart-item-title">${item.product_name}</h4>
                    <p class="cart-item-price">${APIUtils.formatCurrency(item.price)}</p>
                    ${item.variant_name ? `<p class="cart-item-variant">${item.variant_name}</p>` : ''}
                </div>
                <div class="cart-item-actions">
                    <div class="cart-item-quantity">
                        <button class="cart-item-quantity-btn" 
                                onclick="cartManager.updateItemQuantity('${item.id}', ${item.quantity - 1})">
                            <i class="fas fa-minus"></i>
                        </button>
                        <span class="cart-item-quantity-value">${item.quantity}</span>
                        <button class="cart-item-quantity-btn" 
                                onclick="cartManager.updateItemQuantity('${item.id}', ${item.quantity + 1})">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                    <button class="cart-item-remove" 
                            onclick="cartManager.removeItem('${item.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        const cartSummaryHTML = `
            <div class="cart-summary">
                <div class="cart-summary-row">
                    <span>Subtotal (${cartData.itemCount} items)</span>
                    <span>${APIUtils.formatCurrency(cartData.total)}</span>
                </div>
                <div class="cart-summary-row">
                    <span>Shipping</span>
                    <span>Calculated at checkout</span>
                </div>
                <div class="cart-summary-row cart-total">
                    <span>Total</span>
                    <span>${APIUtils.formatCurrency(cartData.total)}</span>
                </div>
                <div class="cart-actions">
                    <button class="btn btn-outline btn-full" onclick="cartManager.hideCart()">
                        Continue Shopping
                    </button>
                    <button class="btn btn-primary btn-full" onclick="cartManager.proceedToCheckout()">
                        Proceed to Checkout
                    </button>
                </div>
            </div>
        `;
        
        cartModalBody.innerHTML = `
            <div class="cart-items">
                ${itemsHTML}
            </div>
            ${cartSummaryHTML}
        `;
    }
    
    // Proceed to checkout
    proceedToCheckout() {
        // Hide cart modal
        this.hideCart();
        
        // Show checkout modal or redirect to checkout page
        this.showMessage('Checkout functionality coming soon!', 'info');
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
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <div class="toast-message">${message}</div>
        `;
        
        document.body.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove after 4 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 4000);
    }
    
    // Clear cart
    async clearCart() {
        try {
            this.cart = {
                id: null,
                items: [],
                total: 0,
                itemCount: 0,
                currency: 'USD'
            };
            
            this.saveCartToStorage();
            this.updateCartDisplay();
            
            this.showMessage('Cart cleared.', 'success');
            
            document.dispatchEvent(new CustomEvent('cartUpdated', {
                detail: { cart: this.cart }
            }));
            
        } catch (error) {
            console.error('Error clearing cart:', error);
            this.showMessage('Error clearing cart.', 'error');
        }
    }
    
    // Get cart summary for checkout
    getCartSummary() {
        return {
            itemCount: this.cart.itemCount,
            total: this.cart.total,
            currency: this.cart.currency,
            items: this.cart.items.map(item => ({
                id: item.id,
                productId: item.product_id,
                name: item.product_name,
                price: item.price,
                quantity: item.quantity,
                total: item.price * item.quantity
            }))
        };
    }
}

// Create global cart manager instance
const cartManager = new CartManager();

// Export for global access
window.cartManager = cartManager;
window.CartManager = CartManager;
