/**
 * Pinnacle AI Boutique Storefront - Auto-Completion Base Component
 *
 * Base class for all storefront auto-completion UI components with e-commerce
 * specific functionality including product suggestions, cart integration, and
 * shopping context awareness.
 */

class StorefrontAutoCompleteBaseComponent {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            core: options.core || window.storefrontAutoComplete,
            minQueryLength: options.minQueryLength || 2,
            maxResults: options.maxResults || 6,
            debounceDelay: options.debounceDelay || 200,
            showImages: options.showImages !== false,
            showPrices: options.showPrices !== false,
            showStock: options.showStock !== false,
            allowCustomValues: options.allowCustomValues || false,
            placeholder: options.placeholder || 'Search products...',
            noResultsText: options.noResultsText || 'No products found',
            loadingText: options.loadingText || 'Searching...',
            classPrefix: options.classPrefix || 'storefront-autocomplete',
            theme: options.theme || 'storefront',
            position: options.position || 'bottom',
            width: options.width || 'auto',
            maxHeight: options.maxHeight || '400px',
            zIndex: options.zIndex || 1000,
            ...options
        };

        this.container = null;
        this.input = null;
        this.dropdown = null;
        this.resultsList = null;
        this.isOpen = false;
        this.isLoading = false;
        this.currentQuery = '';
        this.selectedIndex = -1;
        this.results = [];
        this.debounceTimer = null;

        this.init();
    }

    init() {
        this.createContainer();
        this.setupEventListeners();
        this.setupAccessibility();
        this.applyTheme();
        this.loadCartContext();
        console.log('🛍️ Storefront auto-completion base component initialized');
    }

    createContainer() {
        // Create main container
        this.container = document.createElement('div');
        this.container.className = `${this.options.classPrefix}-container`;
        this.container.style.position = 'relative';
        this.container.style.width = this.options.width;

        // Wrap the original element if it's an input
        if (this.element.tagName === 'INPUT') {
            this.input = this.element;
            this.input.classList.add(`${this.options.classPrefix}-input`);
            this.input.setAttribute('autocomplete', 'off');
            this.input.setAttribute('aria-expanded', 'false');
            this.input.setAttribute('aria-haspopup', 'listbox');
            this.input.setAttribute('aria-autocomplete', 'list');

            if (this.options.placeholder) {
                this.input.setAttribute('placeholder', this.options.placeholder);
            }

            this.container.appendChild(this.input);
        } else {
            // Create input if element is not an input
            this.input = document.createElement('input');
            this.input.type = 'text';
            this.input.className = `${this.options.classPrefix}-input`;
            this.input.setAttribute('autocomplete', 'off');
            this.input.setAttribute('aria-expanded', 'false');
            this.input.setAttribute('aria-haspopup', 'listbox');
            this.input.setAttribute('aria-autocomplete', 'list');

            if (this.options.placeholder) {
                this.input.setAttribute('placeholder', this.options.placeholder);
            }

            this.container.appendChild(this.input);

            // Hide original element
            this.element.style.display = 'none';
        }

        // Create dropdown container
        this.dropdown = document.createElement('div');
        this.dropdown.className = `${this.options.classPrefix}-dropdown`;
        this.dropdown.setAttribute('role', 'listbox');
        this.dropdown.style.display = 'none';
        this.dropdown.style.position = 'absolute';
        this.dropdown.style.zIndex = this.options.zIndex;
        this.dropdown.style.width = '100%';
        this.dropdown.style.maxHeight = this.options.maxHeight;
        this.dropdown.style.overflowY = 'auto';
        this.dropdown.style.backgroundColor = 'var(--bg-color, white)';
        this.dropdown.style.border = '1px solid var(--border-color, #e5e7eb)';
        this.dropdown.style.borderRadius = 'var(--border-radius, 8px)';
        this.dropdown.style.boxShadow = 'var(--shadow, 0 4px 12px rgba(0,0,0,0.15))';

        // Position dropdown
        this.positionDropdown();

        this.container.appendChild(this.dropdown);

        // Insert container after original element
        this.element.parentNode.insertBefore(this.container, this.element.nextSibling);
    }

    positionDropdown() {
        const inputRect = this.input.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const dropdownHeight = parseInt(this.options.maxHeight);

        if (this.options.position === 'top' ||
            (this.options.position === 'auto' && inputRect.bottom + dropdownHeight > viewportHeight)) {
            this.dropdown.style.bottom = '100%';
            this.dropdown.style.top = 'auto';
        } else {
            this.dropdown.style.top = '100%';
            this.dropdown.style.bottom = 'auto';
        }
    }

    setupEventListeners() {
        // Input events
        this.input.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
        });

        this.input.addEventListener('keydown', (e) => {
            this.handleKeyDown(e);
        });

        this.input.addEventListener('focus', () => {
            this.handleFocus();
        });

        this.input.addEventListener('blur', () => {
            // Delay to allow click events on dropdown items
            setTimeout(() => {
                this.handleBlur();
            }, 150);
        });

        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.close();
            }
        });

        // Window resize to reposition
        window.addEventListener('resize', () => {
            if (this.isOpen) {
                this.positionDropdown();
            }
        });

        // Scroll events to close dropdown
        window.addEventListener('scroll', () => {
            if (this.isOpen) {
                this.close();
            }
        }, { passive: true });

        // Listen for cart updates
        window.addEventListener('cart:updated', (e) => {
            this.handleCartUpdate(e.detail);
        });
    }

    setupAccessibility() {
        // Set up ARIA attributes
        this.input.setAttribute('aria-describedby', `${this.options.classPrefix}-results`);

        // Create live region for announcements
        const liveRegion = document.createElement('div');
        liveRegion.id = `${this.options.classPrefix}-announcements`;
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.style.position = 'absolute';
        liveRegion.style.left = '-10000px';
        liveRegion.style.width = '1px';
        liveRegion.style.height = '1px';
        liveRegion.style.overflow = 'hidden';

        this.container.appendChild(liveRegion);
        this.liveRegion = liveRegion;
    }

    applyTheme() {
        const themes = {
            storefront: {
                '--bg-color': '#ffffff',
                '--border-color': '#e5e7eb',
                '--border-radius': '8px',
                '--shadow': '0 4px 12px rgba(0, 0, 0, 0.15)',
                '--text-color': '#111827',
                '--text-color-muted': '#6b7280',
                '--hover-bg': '#f9fafb',
                '--selected-bg': '#eff6ff',
                '--selected-border': '#3b82f6',
                '--primary-color': '#3b82f6',
                '--price-color': '#059669',
                '--stock-color': '#059669',
                '--out-of-stock-color': '#dc2626'
            },
            dark: {
                '--bg-color': '#1f2937',
                '--border-color': '#374151',
                '--border-radius': '8px',
                '--shadow': '0 4px 12px rgba(0, 0, 0, 0.3)',
                '--text-color': '#f9fafb',
                '--text-color-muted': '#9ca3af',
                '--hover-bg': '#374151',
                '--selected-bg': '#1e3a8a',
                '--selected-border': '#60a5fa',
                '--primary-color': '#60a5fa',
                '--price-color': '#10b981',
                '--stock-color': '#10b981',
                '--out-of-stock-color': '#ef4444'
            }
        };

        const themeVars = themes[this.options.theme] || themes.storefront;

        Object.entries(themeVars).forEach(([property, value]) => {
            this.dropdown.style.setProperty(property, value);
        });
    }

    loadCartContext() {
        // Load cart context from localStorage or global state
        try {
            const cartData = JSON.parse(localStorage.getItem('cart_context') || '{}');
            this.cartContext = cartData;
        } catch (error) {
            this.cartContext = {};
        }
    }

    handleCartUpdate(cartData) {
        this.cartContext = cartData;
        this.emit('cart:updated', cartData);
    }

    handleInput(value) {
        this.currentQuery = value;

        if (value.length < this.options.minQueryLength) {
            this.close();
            return;
        }

        // Debounce the search
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.performSearch(value);
        }, this.options.debounceDelay);
    }

    async performSearch(query) {
        if (!this.options.core) {
            console.error('Storefront auto-completion core not available');
            return;
        }

        this.showLoading();

        try {
            const results = await this.options.core.requestProductCompletions(query, {
                maxResults: this.options.maxResults,
                context: this.getContext()
            });

            this.results = results.completions || [];
            this.renderResults();
            this.open();

        } catch (error) {
            console.error('Storefront auto-completion search failed:', error);
            this.showError('Search failed. Please try again.');
        }
    }

    getContext() {
        return {
            component_type: this.constructor.name,
            current_value: this.input.value,
            position: this.input.selectionStart,
            cart_context: this.cartContext,
            storefront_context: true
        };
    }

    renderResults() {
        if (this.results.length === 0) {
            this.showNoResults();
            return;
        }

        this.resultsList = document.createElement('div');
        this.resultsList.className = `${this.options.classPrefix}-results`;
        this.resultsList.id = `${this.options.classPrefix}-results`;

        this.results.forEach((result, index) => {
            const item = this.createResultItem(result, index);
            this.resultsList.appendChild(item);
        });

        this.dropdown.innerHTML = '';
        this.dropdown.appendChild(this.resultsList);
    }

    createResultItem(result, index) {
        const item = document.createElement('div');
        item.className = `${this.options.classPrefix}-item`;
        item.setAttribute('role', 'option');
        item.setAttribute('data-index', index);
        item.setAttribute('aria-selected', 'false');

        if (index === this.selectedIndex) {
            item.classList.add('selected');
            item.setAttribute('aria-selected', 'true');
        }

        item.innerHTML = this.renderResultContent(result);

        item.addEventListener('click', () => {
            this.selectItem(index);
        });

        item.addEventListener('mouseenter', () => {
            this.setSelectedIndex(index);
        });

        return item;
    }

    renderResultContent(result) {
        const content = [];

        // Product image
        if (this.options.showImages && result.image) {
            const image = document.createElement('div');
            image.className = `${this.options.classPrefix}-item-image`;
            image.innerHTML = `<img src="${result.image}" alt="${result.completion || result.text || result.name || ''}" loading="lazy">`;
            content.push(image.outerHTML);
        }

        // Main content
        const mainContent = document.createElement('div');
        mainContent.className = `${this.options.classPrefix}-item-content`;

        // Product name/title
        const title = document.createElement('div');
        title.className = `${this.options.classPrefix}-item-title`;
        title.textContent = result.completion || result.text || result.name || '';
        mainContent.appendChild(title);

        // Product description
        if (result.description) {
            const description = document.createElement('div');
            description.className = `${this.options.classPrefix}-item-description`;
            description.textContent = result.description;
            mainContent.appendChild(description);
        }

        // Price and stock info
        const metaInfo = document.createElement('div');
        metaInfo.className = `${this.options.classPrefix}-item-meta`;

        if (this.options.showPrices && result.price) {
            const price = document.createElement('span');
            price.className = `${this.options.classPrefix}-item-price`;
            price.textContent = `$${result.price}`;
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

        // Add to cart button for products
        if (result.type === 'product' && result.id) {
            const addToCart = document.createElement('div');
            addToCart.className = `${this.options.classPrefix}-item-action`;
            addToCart.innerHTML = `
                <button class="add-to-cart-btn" data-product-id="${result.id}">
                    <i class="fas fa-shopping-cart"></i>
                </button>
            `;

            // Add event listener for add to cart
            addToCart.querySelector('.add-to-cart-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.addToCart(result.id);
            });

            content.push(addToCart.outerHTML);
        }

        return content.join('');
    }

    async addToCart(productId) {
        try {
            // Use the global cart manager if available
            if (window.CartManager) {
                await window.CartManager.addToCart(productId);
                this.emit('product:added-to-cart', { productId });
            } else {
                console.warn('Cart manager not available');
            }
        } catch (error) {
            console.error('Failed to add product to cart:', error);
        }
    }

    showLoading() {
        this.isLoading = true;
        this.dropdown.innerHTML = `
            <div class="${this.options.classPrefix}-loading">
                <div class="${this.options.classPrefix}-loading-spinner"></div>
                <span>${this.options.loadingText}</span>
            </div>
        `;
        this.dropdown.style.display = 'block';
    }

    showNoResults() {
        this.dropdown.innerHTML = `
            <div class="${this.options.classPrefix}-no-results">
                ${this.options.noResultsText}
            </div>
        `;
        this.dropdown.style.display = 'block';
    }

    showError(message) {
        this.dropdown.innerHTML = `
            <div class="${this.options.classPrefix}-error">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
            </div>
        `;
        this.dropdown.style.display = 'block';
    }

    handleKeyDown(e) {
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.navigateDown();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.navigateUp();
                break;
            case 'Enter':
                e.preventDefault();
                this.selectCurrentItem();
                break;
            case 'Escape':
                e.preventDefault();
                this.close();
                break;
            case 'Tab':
                if (this.isOpen) {
                    e.preventDefault();
                    this.selectCurrentItem();
                }
                break;
        }
    }

    navigateDown() {
        if (!this.isOpen) return;

        const maxIndex = this.results.length - 1;
        this.setSelectedIndex(Math.min(this.selectedIndex + 1, maxIndex));
    }

    navigateUp() {
        if (!this.isOpen) return;

        this.setSelectedIndex(Math.max(this.selectedIndex - 1, -1));
    }

    setSelectedIndex(index) {
        // Remove previous selection
        const previousSelected = this.dropdown.querySelector('.selected');
        if (previousSelected) {
            previousSelected.classList.remove('selected');
            previousSelected.setAttribute('aria-selected', 'false');
        }

        this.selectedIndex = index;

        // Set new selection
        if (index >= 0) {
            const newSelected = this.dropdown.querySelector(`[data-index="${index}"]`);
            if (newSelected) {
                newSelected.classList.add('selected');
                newSelected.setAttribute('aria-selected', 'true');
                newSelected.scrollIntoView({ block: 'nearest' });
            }
        }

        this.announceSelection();
    }

    announceSelection() {
        if (this.selectedIndex >= 0 && this.results[this.selectedIndex]) {
            const result = this.results[this.selectedIndex];
            const text = result.completion || result.text || result.name || '';
            this.announce(`${text} selected`);
        }
    }

    announce(message) {
        if (this.liveRegion) {
            this.liveRegion.textContent = message;
        }
    }

    selectCurrentItem() {
        if (this.selectedIndex >= 0) {
            this.selectItem(this.selectedIndex);
        } else if (this.options.allowCustomValues && this.currentQuery) {
            this.selectCustomValue(this.currentQuery);
        }
    }

    selectItem(index) {
        const result = this.results[index];
        if (!result) return;

        const value = result.completion || result.text || result.name || '';
        this.setValue(value);
        this.close();

        this.emit('item:selected', { result, index, value });
    }

    selectCustomValue(value) {
        this.setValue(value);
        this.close();

        this.emit('custom:selected', { value });
    }

    setValue(value) {
        this.input.value = value;
        this.input.dispatchEvent(new Event('input', { bubbles: true }));
        this.input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    handleFocus() {
        this.emit('focus');
    }

    handleBlur() {
        this.emit('blur');
    }

    open() {
        if (this.isOpen) return;

        this.isOpen = true;
        this.dropdown.style.display = 'block';
        this.input.setAttribute('aria-expanded', 'true');

        this.emit('opened');
    }

    close() {
        if (!this.isOpen) return;

        this.isOpen = false;
        this.dropdown.style.display = 'none';
        this.input.setAttribute('aria-expanded', 'false');
        this.selectedIndex = -1;
        this.isLoading = false;

        this.emit('closed');
    }

    destroy() {
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }

        if (this.element && this.element.style.display === 'none') {
            this.element.style.display = '';
        }

        this.cleanup();
    }

    cleanup() {
        clearTimeout(this.debounceTimer);

        if (this.container) {
            this.container.remove();
        }
    }

    // Event system
    on(event, callback) {
        if (!this._events) this._events = {};
        if (!this._events[event]) this._events[event] = [];
        this._events[event].push(callback);
    }

    off(event, callback) {
        if (!this._events || !this._events[event]) return;
        const index = this._events[event].indexOf(callback);
        if (index > -1) {
            this._events[event].splice(index, 1);
        }
    }

    emit(event, data) {
        if (!this._events || !this._events[event]) return;
        this._events[event].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('Error in storefront auto-completion event listener:', error);
            }
        });
    }

    // Public API
    setOptions(options) {
        this.options = { ...this.options, ...options };
        this.applyTheme();
    }

    getValue() {
        return this.input.value;
    }

    setPlaceholder(placeholder) {
        this.options.placeholder = placeholder;
        if (this.input) {
            this.input.setAttribute('placeholder', placeholder);
        }
    }

    focus() {
        if (this.input) {
            this.input.focus();
        }
    }

    blur() {
        if (this.input) {
            this.input.blur();
        }
    }

    refresh() {
        if (this.currentQuery.length >= this.options.minQueryLength) {
            this.performSearch(this.currentQuery);
        }
    }
}

// Export for global use
window.StorefrontAutoCompleteBaseComponent = StorefrontAutoCompleteBaseComponent;</code>
</edit_file>