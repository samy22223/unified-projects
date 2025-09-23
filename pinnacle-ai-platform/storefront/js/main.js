/**
 * Pinnacle AI Boutique - Main Application
 * 
 * This is the main JavaScript file that initializes and coordinates
 * all the storefront functionality.
 */

// Main Storefront Application Class
class Storefront {
    constructor() {
        this.initialized = false;
        this.components = {};
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    // Initialize the application
    async init() {
        try {
            console.log('Initializing Pinnacle AI Boutique Storefront...');
            
            // Initialize components
            await this.initializeComponents();
            
            // Bind global events
            this.bindGlobalEvents();
            
            // Setup modals
            this.setupModals();
            
            // Setup loading overlay
            this.setupLoadingOverlay();
            
            // Setup toast notifications
            this.setupToastNotifications();
            
            // Initialize product manager
            await this.initializeProductManager();
            
            // Initialize cart manager
            this.initializeCartManager();
            
            // Setup search functionality
            this.setupSearch();
            
            // Setup navigation
            this.setupNavigation();
            
            // Setup responsive features
            this.setupResponsiveFeatures();
            
            this.initialized = true;
            console.log('Storefront initialized successfully');
            
            // Dispatch initialization event
            document.dispatchEvent(new CustomEvent('storefrontInitialized', {
                detail: { storefront: this }
            }));
            
        } catch (error) {
            console.error('Error initializing storefront:', error);
            this.showError('Failed to initialize storefront. Please refresh the page.');
        }
    }
    
    // Initialize components
    async initializeComponents() {
        console.log('Loading components...');
        
        // Load components in order
        this.components = {
            productManager: window.productManager,
            cartManager: window.cartManager
        };
        
        // Wait for components to be ready
        if (this.components.productManager && this.components.productManager.init) {
            await this.components.productManager.init();
        }
    }
    
    // Initialize product manager
    async initializeProductManager() {
        if (!this.components.productManager) {
            console.warn('Product manager not available');
            return;
        }
        
        try {
            await this.components.productManager.init();
            console.log('Product manager initialized');
        } catch (error) {
            console.error('Error initializing product manager:', error);
        }
    }
    
    // Initialize cart manager
    initializeCartManager() {
        if (!this.components.cartManager) {
            console.warn('Cart manager not available');
            return;
        }
        
        console.log('Cart manager initialized');
    }
    
    // Bind global events
    bindGlobalEvents() {
        // Handle modal close events
        document.addEventListener('click', (event) => {
            if (event.target.matches('.modal-backdrop, .modal-close, [data-dismiss="modal"]')) {
                this.closeAllModals();
            }
        });
        
        // Handle escape key for modals
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.closeAllModals();
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', APIUtils.debounce(() => {
            this.handleWindowResize();
        }, 250));
        
        // Handle scroll events
        window.addEventListener('scroll', APIUtils.debounce(() => {
            this.handleScroll();
        }, 100));
        
        // Handle form submissions
        document.addEventListener('submit', (event) => {
            if (event.target.matches('form')) {
                this.handleFormSubmission(event);
            }
        });
        
        // Handle clicks on elements with data attributes
        document.addEventListener('click', (event) => {
            this.handleDataAttributeClicks(event);
        });
    }
    
    // Setup modals
    setupModals() {
        // Add modal backdrop click handling
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('click', (event) => {
                if (event.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }
    
    // Setup loading overlay
    setupLoadingOverlay() {
        if (!document.getElementById('loadingOverlay')) {
            const loadingOverlay = document.createElement('div');
            loadingOverlay.id = 'loadingOverlay';
            loadingOverlay.className = 'loading-overlay';
            loadingOverlay.innerHTML = `
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <p>Loading...</p>
                </div>
            `;
            document.body.appendChild(loadingOverlay);
        }
    }
    
    // Setup toast notifications
    setupToastNotifications() {
        if (!document.getElementById('toastContainer')) {
            const toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
    }
    
    // Setup search functionality
    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        
        if (searchInput) {
            const debouncedSearch = APIUtils.debounce((query) => {
                if (query.length >= 2) {
                    this.performSearch(query);
                }
            }, 300);
            
            searchInput.addEventListener('input', (event) => {
                debouncedSearch(event.target.value);
            });
            
            searchInput.addEventListener('keydown', (event) => {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    this.performSearch(event.target.value);
                }
            });
        }
        
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                const query = searchInput ? searchInput.value : '';
                this.performSearch(query);
            });
        }
    }
    
    // Setup navigation
    setupNavigation() {
        // Mobile menu toggle
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        const mobileMenu = document.getElementById('mobileMenu');
        
        if (mobileMenuToggle && mobileMenu) {
            mobileMenuToggle.addEventListener('click', () => {
                mobileMenu.classList.toggle('show');
                mobileMenuToggle.classList.toggle('active');
            });
        }
        
        // Smooth scroll for anchor links
        document.addEventListener('click', (event) => {
            if (event.target.matches('a[href^="#"]')) {
                event.preventDefault();
                const targetId = event.target.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
        
        // Active navigation highlighting
        this.highlightActiveNavigation();
    }
    
    // Setup responsive features
    setupResponsiveFeatures() {
        // Add mobile class to body if needed
        const checkMobile = () => {
            const isMobile = window.innerWidth <= 768;
            document.body.classList.toggle('mobile', isMobile);
            document.body.classList.toggle('desktop', !isMobile);
        };
        
        checkMobile();
        
        // Handle orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(checkMobile, 100);
        });
    }
    
    // Handle window resize
    handleWindowResize() {
        // Update mobile menu state
        const mobileMenu = document.getElementById('mobileMenu');
        if (mobileMenu && window.innerWidth > 768) {
            mobileMenu.classList.remove('show');
            const mobileMenuToggle = document.getElementById('mobileMenuToggle');
            if (mobileMenuToggle) {
                mobileMenuToggle.classList.remove('active');
            }
        }
        
        // Update responsive classes
        this.setupResponsiveFeatures();
    }
    
    // Handle scroll events
    handleScroll() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add/remove scrolled class to header
        const header = document.querySelector('header');
        if (header) {
            header.classList.toggle('scrolled', scrollTop > 50);
        }
        
        // Show/hide scroll to top button
        const scrollToTopBtn = document.getElementById('scrollToTopBtn');
        if (scrollToTopBtn) {
            scrollToTopBtn.classList.toggle('visible', scrollTop > 300);
        }
    }
    
    // Handle form submissions
    handleFormSubmission(event) {
        const form = event.target;
        
        // Handle newsletter signup
        if (form.id === 'newsletterForm') {
            event.preventDefault();
            this.handleNewsletterSignup(form);
        }
        
        // Handle contact form
        if (form.id === 'contactForm') {
            event.preventDefault();
            this.handleContactForm(form);
        }
    }
    
    // Handle data attribute clicks
    handleDataAttributeClicks(event) {
        const target = event.target.closest('[data-action]');
        
        if (!target) return;
        
        const action = target.dataset.action;
        
        switch (action) {
            case 'scroll-to-top':
                this.scrollToTop();
                break;
            case 'toggle-theme':
                this.toggleTheme();
                break;
            case 'clear-cart':
                this.clearCart();
                break;
            case 'logout':
                this.logout();
                break;
        }
    }
    
    // Perform search
    async performSearch(query) {
        if (!query.trim()) {
            return;
        }
        
        try {
            this.showLoading('Searching...');
            
            if (this.components.productManager && this.components.productManager.searchProducts) {
                await this.components.productManager.searchProducts(query);
                this.scrollToProducts();
            }
        } catch (error) {
            console.error('Error performing search:', error);
            this.showError('Search failed. Please try again.');
        } finally {
            this.hideLoading();
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
    
    // Scroll to top
    scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
    
    // Toggle theme
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        this.showMessage(`Switched to ${newTheme} theme`, 'info');
    }
    
    // Clear cart
    clearCart() {
        if (confirm('Are you sure you want to clear your cart?')) {
            if (this.components.cartManager && this.components.cartManager.clearCart) {
                this.components.cartManager.clearCart();
            }
        }
    }
    
    // Logout
    logout() {
        if (confirm('Are you sure you want to logout?')) {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
            this.showMessage('Logged out successfully', 'success');
            // Redirect to home or reload
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        }
    }
    
    // Handle newsletter signup
    async handleNewsletterSignup(form) {
        const emailInput = form.querySelector('input[type="email"]');
        const email = emailInput ? emailInput.value : '';
        
        if (!email || !APIUtils.isValidEmail(email)) {
            this.showError('Please enter a valid email address');
            return;
        }
        
        try {
            // This would integrate with your newsletter API
            this.showMessage('Thank you for subscribing to our newsletter!', 'success');
            form.reset();
        } catch (error) {
            console.error('Error subscribing to newsletter:', error);
            this.showError('Failed to subscribe. Please try again.');
        }
    }
    
    // Handle contact form
    async handleContactForm(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        try {
            // This would integrate with your contact API
            this.showMessage('Thank you for your message. We\'ll get back to you soon!', 'success');
            form.reset();
        } catch (error) {
            console.error('Error submitting contact form:', error);
            this.showError('Failed to send message. Please try again.');
        }
    }
    
    // Highlight active navigation
    highlightActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('nav a[href]');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath || (currentPath === '/' && href === '/')) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
    
    // Show loading overlay
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
    
    // Hide loading overlay
    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.classList.remove('show');
        }
    }
    
    // Show message (toast notification)
    showMessage(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <div class="toast-message">${message}</div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.remove('show');
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 5000);
    }
    
    // Show error message
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    // Show success message
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    // Show info message
    showInfo(message) {
        this.showMessage(message, 'info');
    }
    
    // Show warning message
    showWarning(message) {
        this.showMessage(message, 'warning');
    }
    
    // Close all modals
    closeAllModals() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            this.closeModal(modal.id);
        });
    }
    
    // Close specific modal
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
            
            // Dispatch modal close event
            document.dispatchEvent(new CustomEvent('modalClosed', {
                detail: { modalId }
            }));
        }
    }
    
    // Open modal
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            // Dispatch modal open event
            document.dispatchEvent(new CustomEvent('modalOpened', {
                detail: { modalId }
            }));
        }
    }
    
    // Get component
    getComponent(name) {
        return this.components[name];
    }
    
    // Check if initialized
    isInitialized() {
        return this.initialized;
    }
}

// Create global storefront instance
const storefront = new Storefront();

// Export for global access
window.storefront = storefront;
window.Storefront = Storefront;
