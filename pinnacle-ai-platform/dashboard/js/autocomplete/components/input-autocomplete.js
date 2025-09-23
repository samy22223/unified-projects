/**
 * Pinnacle AI Platform Dashboard - Input Auto-Complete Component
 *
 * Provides auto-completion functionality for text input fields with intelligent
 * suggestions based on context and user behavior.
 */

class InputAutoComplete extends AutoCompleteBaseComponent {
    constructor(element, options = {}) {
        const defaultOptions = {
            classPrefix: 'input-autocomplete',
            minQueryLength: 2,
            maxResults: 8,
            debounceDelay: 250,
            showImages: false,
            showDescriptions: true,
            allowCustomValues: true,
            placeholder: 'Start typing to search...',
            noResultsText: 'No suggestions found',
            loadingText: 'Searching...',
            highlightMatches: true,
            caseSensitive: false,
            ...options
        };

        super(element, defaultOptions);

        this.highlightClass = 'highlight';
        this.recentSelections = [];
        this.maxRecentSelections = 5;
    }

    getContext() {
        const baseContext = super.getContext();

        return {
            ...baseContext,
            input_type: 'text',
            recent_selections: this.recentSelections,
            allow_custom: this.options.allowCustomValues
        };
    }

    renderResultContent(result) {
        const content = [];

        // Text content container
        const textContent = document.createElement('div');
        textContent.className = `${this.options.classPrefix}-item-content`;

        // Title with highlighting
        const title = document.createElement('div');
        title.className = `${this.options.classPrefix}-item-title`;

        if (this.options.highlightMatches && this.currentQuery) {
            title.innerHTML = this.highlightText(result.completion || result.text || result.name || '', this.currentQuery);
        } else {
            title.textContent = result.completion || result.text || result.name || '';
        }

        textContent.appendChild(title);

        // Description
        if (this.options.showDescriptions && result.description) {
            const description = document.createElement('div');
            description.className = `${this.options.classPrefix}-item-description`;
            description.textContent = result.description;
            textContent.appendChild(description);
        }

        // Metadata/Score
        if (result.score !== undefined) {
            const metadata = document.createElement('div');
            metadata.className = `${this.options.classPrefix}-item-metadata`;
            metadata.innerHTML = `<span class="score">Score: ${Math.round(result.score * 100)}%</span>`;
            textContent.appendChild(metadata);
        }

        // Provider indicator
        if (result.provider) {
            const provider = document.createElement('div');
            provider.className = `${this.options.classPrefix}-item-provider`;
            provider.textContent = result.provider;
            textContent.appendChild(provider);
        }

        content.push(textContent.outerHTML);

        return content.join('');
    }

    highlightText(text, query) {
        if (!query || !text) return text;

        const regex = new RegExp(`(${this.escapeRegExp(query)})`, this.options.caseSensitive ? 'g' : 'gi');
        return text.replace(regex, `<span class="${this.highlightClass}">$1</span>`);
    }

    escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    selectItem(index) {
        const result = this.results[index];
        if (!result) return;

        const value = result.completion || result.text || result.name || '';

        // Add to recent selections
        this.addToRecentSelections(result);

        this.setValue(value);
        this.close();

        this.emit('item:selected', {
            result,
            index,
            value,
            isRecent: this.isRecentSelection(result)
        });
    }

    addToRecentSelections(result) {
        // Remove if already exists
        this.recentSelections = this.recentSelections.filter(item =>
            item.completion !== result.completion
        );

        // Add to beginning
        this.recentSelections.unshift({
            completion: result.completion,
            text: result.text,
            name: result.name,
            description: result.description,
            provider: result.provider,
            timestamp: Date.now()
        });

        // Keep only recent items
        this.recentSelections = this.recentSelections.slice(0, this.maxRecentSelections);

        // Persist to localStorage
        this.saveRecentSelections();
    }

    isRecentSelection(result) {
        return this.recentSelections.some(item =>
            item.completion === result.completion
        );
    }

    saveRecentSelections() {
        try {
            const key = `input-autocomplete-recent-${this.options.classPrefix}`;
            localStorage.setItem(key, JSON.stringify(this.recentSelections));
        } catch (error) {
            console.error('Failed to save recent selections:', error);
        }
    }

    loadRecentSelections() {
        try {
            const key = `input-autocomplete-recent-${this.options.classPrefix}`;
            const saved = localStorage.getItem(key);
            if (saved) {
                this.recentSelections = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Failed to load recent selections:', error);
        }
    }

    init() {
        super.init();
        this.loadRecentSelections();
    }

    performSearch(query) {
        // Add recent selections to results if query is short
        if (query.length < this.options.minQueryLength + 1 && this.recentSelections.length > 0) {
            const recentResults = this.recentSelections
                .filter(item => this.matchesQuery(item, query))
                .slice(0, 3)
                .map((item, index) => ({
                    completion: item.completion,
                    text: item.text,
                    name: item.name,
                    description: item.description,
                    provider: 'recent',
                    score: 0.9 - (index * 0.1),
                    metadata: { type: 'recent' }
                }));

            if (recentResults.length > 0) {
                this.results = recentResults;
                this.renderResults();
                this.open();
                return;
            }
        }

        // Perform full search
        super.performSearch(query);
    }

    matchesQuery(item, query) {
        if (!query) return true;

        const searchText = [
            item.completion,
            item.text,
            item.name,
            item.description
        ].filter(Boolean).join(' ').toLowerCase();

        return searchText.includes(query.toLowerCase());
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
            default:
                super.handleKeyDown(e);
        }
    }

    // Public API methods
    getRecentSelections() {
        return [...this.recentSelections];
    }

    clearRecentSelections() {
        this.recentSelections = [];
        const key = `input-autocomplete-recent-${this.options.classPrefix}`;
        localStorage.removeItem(key);
        this.emit('recent:cleared');
    }

    addCustomSuggestion(suggestion) {
        this.addToRecentSelections({
            completion: suggestion,
            text: suggestion,
            provider: 'custom',
            score: 1.0
        });
    }

    setSuggestions(suggestions) {
        this.results = suggestions.map((suggestion, index) => ({
            completion: suggestion.text || suggestion,
            text: suggestion.text || suggestion,
            description: suggestion.description || '',
            provider: suggestion.provider || 'custom',
            score: suggestion.score || 1.0,
            metadata: suggestion.metadata || {}
        }));

        this.renderResults();
        if (this.results.length > 0) {
            this.open();
        }
    }
}

// Export for global use
window.InputAutoComplete = InputAutoComplete;</code>
</edit_file>