/**
 * Pinnacle AI Platform Dashboard - Search Auto-Complete Component
 *
 * Provides enhanced search functionality with intelligent suggestions,
 * search history, and context-aware results.
 */

class SearchAutoComplete extends AutoCompleteBaseComponent {
    constructor(element, options = {}) {
        const defaultOptions = {
            classPrefix: 'search-autocomplete',
            minQueryLength: 1,
            maxResults: 7,
            debounceDelay: 200,
            showImages: true,
            showDescriptions: true,
            allowCustomValues: true,
            placeholder: 'Search agents, tasks, settings...',
            noResultsText: 'No search results found',
            loadingText: 'Searching...',
            searchHistory: true,
            maxHistoryItems: 10,
            categories: ['agents', 'tasks', 'settings', 'documentation', 'help'],
            highlightMatches: true,
            ...options
        };

        super(element, defaultOptions);

        this.searchHistory = [];
        this.categories = this.options.categories;
        this.currentCategory = 'all';
    }

    init() {
        super.init();
        this.loadSearchHistory();
    }

    getContext() {
        const baseContext = super.getContext();

        return {
            ...baseContext,
            search_type: 'dashboard',
            category: this.currentCategory,
            search_history: this.searchHistory.slice(0, 5),
            categories: this.categories
        };
    }

    renderResultContent(result) {
        const content = [];

        // Category indicator
        if (result.category) {
            const category = document.createElement('div');
            category.className = `${this.options.classPrefix}-item-category`;
            category.textContent = result.category;
            content.push(category.outerHTML);
        }

        // Main content container
        const mainContent = document.createElement('div');
        mainContent.className = `${this.options.classPrefix}-item-content`;

        // Title with highlighting
        const title = document.createElement('div');
        title.className = `${this.options.classPrefix}-item-title`;

        if (this.options.highlightMatches && this.currentQuery) {
            title.innerHTML = this.highlightText(result.completion || result.text || result.name || '', this.currentQuery);
        } else {
            title.textContent = result.completion || result.text || result.name || '';
        }

        mainContent.appendChild(title);

        // Description
        if (this.options.showDescriptions && result.description) {
            const description = document.createElement('div');
            description.className = `${this.options.classPrefix}-item-description`;
            description.textContent = result.description;
            mainContent.appendChild(description);
        }

        // Metadata
        if (result.metadata) {
            const metadata = document.createElement('div');
            metadata.className = `${this.options.classPrefix}-item-metadata`;

            const metaItems = [];
            if (result.metadata.type) metaItems.push(result.metadata.type);
            if (result.metadata.provider) metaItems.push(result.metadata.provider);
            if (result.metadata.score) metaItems.push(`${Math.round(result.metadata.score * 100)}%`);

            metadata.textContent = metaItems.join(' • ');
            mainContent.appendChild(metadata);
        }

        content.push(mainContent.outerHTML);

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
        // Show search history for short queries
        if (query.length < 2 && this.searchHistory.length > 0) {
            this.showSearchHistory(query);
            return;
        }

        // Show category suggestions for very short queries
        if (query.length === 1) {
            this.showCategorySuggestions(query);
            return;
        }

        // Perform full search
        super.performSearch(query);
    }

    showSearchHistory(query) {
        const historyResults = this.searchHistory
            .filter(item => this.matchesQuery(item, query))
            .slice(0, 5)
            .map((item, index) => ({
                completion: item.query,
                text: item.query,
                description: `Searched ${item.timestamp}`,
                category: 'Recent',
                provider: 'history',
                score: 0.9 - (index * 0.1),
                metadata: {
                    type: 'history',
                    timestamp: item.timestamp
                }
            }));

        if (historyResults.length > 0) {
            this.results = historyResults;
            this.renderResults();
            this.open();
        } else {
            super.performSearch(query);
        }
    }

    showCategorySuggestions(query) {
        const categoryResults = this.categories
            .filter(category => category.toLowerCase().includes(query.toLowerCase()))
            .map(category => ({
                completion: `${category}: `,
                text: `${category}: `,
                description: `Search in ${category}`,
                category: 'Category',
                provider: 'category',
                score: 0.8,
                metadata: { type: 'category' }
            }));

        if (categoryResults.length > 0) {
            this.results = categoryResults;
            this.renderResults();
            this.open();
        } else {
            super.performSearch(query);
        }
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

        // Add to search history
        this.addToSearchHistory(value);

        this.setValue(value);
        this.close();

        this.emit('search:selected', {
            result,
            index,
            value,
            category: result.category
        });
    }

    addToSearchHistory(query) {
        // Remove if already exists
        this.searchHistory = this.searchHistory.filter(item => item.query !== query);

        // Add to beginning
        this.searchHistory.unshift({
            query: query,
            timestamp: new Date().toISOString(),
            category: this.currentCategory
        });

        // Keep only recent items
        this.searchHistory = this.searchHistory.slice(0, this.options.maxHistoryItems);

        // Persist to localStorage
        this.saveSearchHistory();
    }

    saveSearchHistory() {
        try {
            localStorage.setItem('dashboard-search-history', JSON.stringify(this.searchHistory));
        } catch (error) {
            console.error('Failed to save search history:', error);
        }
    }

    loadSearchHistory() {
        try {
            const saved = localStorage.getItem('dashboard-search-history');
            if (saved) {
                this.searchHistory = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Failed to load search history:', error);
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
    setCategory(category) {
        this.currentCategory = category;
        this.emit('category:changed', category);
    }

    getSearchHistory() {
        return [...this.searchHistory];
    }

    clearSearchHistory() {
        this.searchHistory = [];
        localStorage.removeItem('dashboard-search-history');
        this.emit('history:cleared');
    }

    addSearchSuggestion(suggestion) {
        this.addToSearchHistory(suggestion);
    }

    setCategories(categories) {
        this.categories = categories;
        this.options.categories = categories;
    }

    searchInCategory(category, query) {
        this.setCategory(category);
        this.input.value = query;
        this.handleInput(query);
    }

    // Advanced search features
    getSuggestionsForCategory(category) {
        const categorySuggestions = {
            agents: [
                'agent create',
                'agent list',
                'agent status',
                'agent configure',
                'agent monitor'
            ],
            tasks: [
                'task create',
                'task list',
                'task status',
                'task schedule',
                'task history'
            ],
            settings: [
                'settings api',
                'settings database',
                'settings security',
                'settings performance',
                'settings preferences'
            ],
            documentation: [
                'docs api',
                'docs guide',
                'docs tutorial',
                'docs reference',
                'docs examples'
            ],
            help: [
                'help commands',
                'help shortcuts',
                'help troubleshooting',
                'help contact',
                'help about'
            ]
        };

        return categorySuggestions[category] || [];
    }

    showQuickActions() {
        const quickActions = [
            {
                completion: 'help',
                text: 'Show help and documentation',
                category: 'Quick Action',
                provider: 'system',
                score: 1.0
            },
            {
                completion: 'settings',
                text: 'Open settings panel',
                category: 'Quick Action',
                provider: 'system',
                score: 0.9
            },
            {
                completion: 'dashboard',
                text: 'Go to main dashboard',
                category: 'Quick Action',
                provider: 'system',
                score: 0.8
            }
        ];

        this.results = quickActions;
        this.renderResults();
        this.open();
    }
}

// Export for global use
window.SearchAutoComplete = SearchAutoComplete;</code>
</edit_file>