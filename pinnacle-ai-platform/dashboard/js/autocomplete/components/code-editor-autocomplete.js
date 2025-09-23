/**
 * Pinnacle AI Platform Dashboard - Code Editor Auto-Complete Component
 *
 * Provides intelligent code completion for code editors with syntax highlighting,
 * context-aware suggestions, and programming language support.
 */

class CodeEditorAutoComplete extends AutoCompleteBaseComponent {
    constructor(element, options = {}) {
        const defaultOptions = {
            classPrefix: 'code-editor-autocomplete',
            minQueryLength: 1,
            maxResults: 6,
            debounceDelay: 150,
            showImages: false,
            showDescriptions: true,
            allowCustomValues: false,
            placeholder: 'Start typing code...',
            noResultsText: 'No code suggestions found',
            loadingText: 'Analyzing code...',
            language: options.language || 'javascript',
            syntaxHighlighting: true,
            autoInsert: true,
            triggerChars: ['.', '(', ' ', '\n'],
            ...options
        };

        super(element, defaultOptions);

        this.language = this.options.language;
        this.syntaxHighlighter = null;
        this.currentContext = {
            line: 0,
            column: 0,
            scope: '',
            imports: [],
            variables: [],
            functions: []
        };

        this.initSyntaxHighlighter();
    }

    initSyntaxHighlighter() {
        // Initialize syntax highlighter based on language
        if (this.options.syntaxHighlighting) {
            this.syntaxHighlighter = this.getSyntaxHighlighter(this.language);
        }
    }

    getSyntaxHighlighter(language) {
        const highlighters = {
            javascript: (code) => this.highlightJavaScript(code),
            python: (code) => this.highlightPython(code),
            sql: (code) => this.highlightSQL(code),
            json: (code) => this.highlightJSON(code),
            html: (code) => this.highlightHTML(code),
            css: (code) => this.highlightCSS(code)
        };

        return highlighters[language] || ((code) => code);
    }

    highlightJavaScript(code) {
        // Basic JavaScript syntax highlighting
        return code
            .replace(/\b(function|const|let|var|if|else|for|while|return|class|import|export)\b/g, '<span class="keyword">$1</span>')
            .replace(/"([^"]*)"/g, '<span class="string">"$1"</span>')
            .replace(/'([^']*)'/g, '<span class="string">\'$1\'</span>')
            .replace(/\b(\d+)\b/g, '<span class="number">$1</span>')
            .replace(/\/\/(.*)$/gm, '<span class="comment">//$1</span>')
            .replace(/\/\*([\s\S]*?)\*\//g, '<span class="comment">/*$1*/</span>');
    }

    highlightPython(code) {
        return code
            .replace(/\b(def|class|if|elif|else|for|while|import|from|return|and|or|not|in|is)\b/g, '<span class="keyword">$1</span>')
            .replace(/#[^\n]*/g, '<span class="comment">$&</span>')
            .replace(/"""([\s\S]*?)"""/g, '<span class="string">"""$1"""</span>')
            .replace(/'''([\s\S]*?)'''/g, '<span class="string">\'\'\'$1\'\'\'</span>')
            .replace(/("([^"]*)")/g, '<span class="string">$1</span>')
            .replace(/('([^']*)')/g, '<span class="string">$1</span>')
            .replace(/\b(\d+)\b/g, '<span class="number">$1</span>');
    }

    highlightSQL(code) {
        return code
            .replace(/\b(SELECT|FROM|WHERE|JOIN|INNER|LEFT|RIGHT|OUTER|ON|GROUP|BY|HAVING|ORDER|INSERT|UPDATE|DELETE|CREATE|TABLE|INDEX|DROP|ALTER|PRIMARY|KEY|FOREIGN|REFERENCES|UNIQUE|NOT|NULL|DEFAULT|AUTO_INCREMENT)\b/gi, '<span class="keyword">$1</span>')
            .replace(/('([^']*)')/g, '<span class="string">$1</span>')
            .replace(/("([^"]*)")/g, '<span class="string">$1</span>')
            .replace(/(--.*$)/gm, '<span class="comment">$1</span>')
            .replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="comment">$1</span>')
            .replace(/\b(\d+)\b/g, '<span class="number">$1</span>');
    }

    highlightJSON(code) {
        return code
            .replace(/("([^"]*)")/g, '<span class="string">$1</span>')
            .replace(/\b(true|false|null)\b/g, '<span class="keyword">$1</span>')
            .replace(/\b(\d+)\b/g, '<span class="number">$1</span>');
    }

    highlightHTML(code) {
        return code
            .replace(/(&lt;[^&gt;]+&gt;)/g, '<span class="bracket">$1</span>')
            .replace(/(class|id|href|src)=/g, '<span class="attribute">$1=</span>')
            .replace(/("([^"]*)")/g, '<span class="string">$1</span>')
            .replace(/('([^']*)')/g, '<span class="string">$1</span>');
    }

    highlightCSS(code) {
        return code
            .replace(/([.#][a-zA-Z][a-zA-Z0-9-_]*)/g, '<span class="selector">$1</span>')
            .replace(/([a-z-]+)\s*:/g, '<span class="property">$1:</span>')
            .replace(/(#[0-9a-fA-F]{3,6}|rgb\([^)]+\)|[a-z]+)\s*([;])/g, '<span class="value">$1</span>$2')
            .replace(/\/\*[\s\S]*?\*\//g, '<span class="comment">$&</span>');
    }

    getContext() {
        const baseContext = super.getContext();

        return {
            ...baseContext,
            language: this.language,
            code_context: this.currentContext,
            syntax_highlighting: this.options.syntaxHighlighting
        };
    }

    renderResultContent(result) {
        const content = [];

        // Code content container
        const codeContent = document.createElement('div');
        codeContent.className = `${this.options.classPrefix}-item-content`;

        // Code text with syntax highlighting
        const codeText = document.createElement('div');
        codeText.className = `${this.options.classPrefix}-item-code`;

        if (this.options.syntaxHighlighting && this.syntaxHighlighter) {
            codeText.innerHTML = this.syntaxHighlighter(result.completion || result.text || result.name || '');
        } else {
            codeText.textContent = result.completion || result.text || result.name || '';
        }

        codeContent.appendChild(codeText);

        // Description/Help text
        if (this.options.showDescriptions && result.description) {
            const description = document.createElement('div');
            description.className = `${this.options.classPrefix}-item-description`;
            description.textContent = result.description;
            codeContent.appendChild(description);
        }

        // Type information
        if (result.type) {
            const typeInfo = document.createElement('div');
            typeInfo.className = `${this.options.classPrefix}-item-type`;
            typeInfo.textContent = result.type;
            codeContent.appendChild(typeInfo);
        }

        // Parameters for functions
        if (result.parameters) {
            const params = document.createElement('div');
            params.className = `${this.options.classPrefix}-item-parameters`;
            params.textContent = `(${result.parameters.join(', ')})`;
            codeContent.appendChild(params);
        }

        // Provider indicator
        if (result.provider) {
            const provider = document.createElement('div');
            provider.className = `${this.options.classPrefix}-item-provider`;
            provider.textContent = result.provider;
            codeContent.appendChild(provider);
        }

        content.push(codeContent.outerHTML);

        return content.join('');
    }

    handleInput(value) {
        // Update cursor context
        this.updateCursorContext();

        // Check for trigger characters
        if (this.shouldTriggerCompletion(value)) {
            super.handleInput(value);
        }
    }

    shouldTriggerCompletion(value) {
        const lastChar = value.slice(-1);
        return this.options.triggerChars.includes(lastChar) ||
               value.length >= this.options.minQueryLength;
    }

    updateCursorContext() {
        const textarea = this.input;
        const cursorPosition = textarea.selectionStart;

        if (textarea.scrollHeight > textarea.clientHeight) {
            // Multi-line context
            const lines = textarea.value.substring(0, cursorPosition).split('\n');
            this.currentContext.line = lines.length;
            this.currentContext.column = lines[lines.length - 1].length + 1;

            // Analyze current scope
            this.currentContext.scope = this.analyzeScope(textarea.value, cursorPosition);
        } else {
            // Single line context
            this.currentContext.line = 1;
            this.currentContext.column = cursorPosition + 1;
            this.currentContext.scope = this.analyzeScope(textarea.value, cursorPosition);
        }
    }

    analyzeScope(code, cursorPosition) {
        // Basic scope analysis - can be enhanced with proper parsing
        const lines = code.substring(0, cursorPosition).split('\n');
        const currentLine = lines[lines.length - 1];

        // Detect common patterns
        if (currentLine.includes('function') || currentLine.includes('=>')) {
            return 'function';
        }
        if (currentLine.includes('class')) {
            return 'class';
        }
        if (currentLine.includes('import') || currentLine.includes('from')) {
            return 'import';
        }
        if (currentLine.includes('SELECT') || currentLine.includes('FROM')) {
            return 'query';
        }

        return 'general';
    }

    performSearch(query) {
        // Enhanced context for code completion
        const context = {
            ...this.getContext(),
            cursor_context: this.currentContext,
            language: this.language,
            scope: this.currentContext.scope
        };

        if (!this.options.core) {
            console.error('Auto-completion core not available');
            return;
        }

        this.showLoading();

        try {
            this.options.core.requestCompletions(query, {
                maxResults: this.options.maxResults,
                context: context,
                providerTypes: ['ai_agent', 'api_endpoint', 'config'], // Code-focused providers
                metadata: {
                    language: this.language,
                    code_context: this.currentContext,
                    syntax_highlighting: this.options.syntaxHighlighting
                }
            }).then(result => {
                this.results = result.completions || [];
                this.renderResults();
                this.open();
            }).catch(error => {
                console.error('Code completion search failed:', error);
                this.showError('Code completion failed. Please try again.');
            });

        } catch (error) {
            console.error('Auto-completion search failed:', error);
            this.showError('Search failed. Please try again.');
        }
    }

    selectItem(index) {
        const result = this.results[index];
        if (!result) return;

        const completion = result.completion || result.text || result.name || '';

        if (this.options.autoInsert) {
            this.insertCompletion(completion);
        } else {
            this.setValue(completion);
        }

        this.close();

        this.emit('code:selected', {
            result,
            index,
            completion,
            context: this.currentContext
        });
    }

    insertCompletion(completion) {
        const textarea = this.input;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const beforeCursor = textarea.value.substring(0, start);
        const afterCursor = textarea.value.substring(end);

        // Find the start of the current word/token
        const beforeMatch = beforeCursor.match(/\b\w*$/);
        const tokenStart = beforeMatch ? start - beforeMatch[0].length : start;

        // Replace from token start to cursor end
        const newValue = beforeCursor.substring(0, tokenStart) + completion + afterCursor;
        textarea.value = newValue;

        // Set cursor position after the inserted completion
        const newCursorPos = tokenStart + completion.length;
        textarea.setSelectionRange(newCursorPos, newCursorPos);

        // Trigger input event
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Enhanced keyboard handling for code editing
    handleKeyDown(e) {
        switch (e.key) {
            case 'Tab':
                if (this.isOpen && this.selectedIndex >= 0) {
                    e.preventDefault();
                    this.selectCurrentItem();
                } else if (e.shiftKey) {
                    // Shift+Tab for reverse tab behavior
                    e.preventDefault();
                    this.insertText('    '); // Insert 4 spaces
                }
                break;
            case 'Enter':
                if (e.ctrlKey || e.metaKey) {
                    // Ctrl/Cmd+Enter to select completion
                    e.preventDefault();
                    this.selectCurrentItem();
                } else {
                    super.handleKeyDown(e);
                }
                break;
            case '.':
            case '(':
            case ' ':
                // Trigger completion on these characters
                setTimeout(() => {
                    if (this.input.value.length >= this.options.minQueryLength) {
                        this.handleInput(this.input.value);
                    }
                }, 10);
                break;
            default:
                super.handleKeyDown(e);
        }
    }

    insertText(text) {
        const textarea = this.input;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;

        const newValue = textarea.value.substring(0, start) + text + textarea.value.substring(end);
        textarea.value = newValue;
        textarea.setSelectionRange(start + text.length, start + text.length);

        textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Public API methods
    setLanguage(language) {
        this.language = language;
        this.syntaxHighlighter = this.getSyntaxHighlighter(language);
        this.options.language = language;
    }

    getCurrentContext() {
        return { ...this.currentContext };
    }

    insertSnippet(snippet) {
        this.insertText(snippet);
    }

    formatCode() {
        // Basic code formatting - can be enhanced with proper formatters
        const code = this.input.value;
        const formatted = this.formatCodeByLanguage(code, this.language);
        this.input.value = formatted;
        this.input.dispatchEvent(new Event('input', { bubbles: true }));
    }

    formatCodeByLanguage(code, language) {
        // Basic formatting - replace with proper formatter
        return code.replace(/\s+/g, ' ').trim();
    }
}

// Export for global use
window.CodeEditorAutoComplete = CodeEditorAutoComplete;</code>
</edit_file>