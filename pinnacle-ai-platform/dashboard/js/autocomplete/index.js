/**
 * Pinnacle AI Platform Dashboard - Auto-Completion Integration
 *
 * Main integration file that initializes auto-completion components,
 * provides examples, and manages global auto-completion functionality.
 */

// Global auto-completion instances
window.dashboardAutoComplete = null;
window.dashboardAutoCompleteInstances = new Map();

/**
 * Initialize auto-completion system for the dashboard
 */
function initializeDashboardAutoComplete(options = {}) {
    console.log('🚀 Initializing Dashboard Auto-Completion System...');

    // Initialize core system
    window.dashboardAutoComplete = new AutoCompletionCore({
        baseUrl: '/api/v1/autocomplete',
        wsUrl: 'ws://' + window.location.host + '/ws/autocomplete',
        cacheEnabled: true,
        cacheSize: 100,
        debounceDelay: 300,
        maxRetries: 3,
        retryDelay: 1000,
        requestTimeout: 5000,
        ...options
    });

    // Set up global event listeners
    setupGlobalEventListeners();

    // Initialize existing elements
    initializeExistingElements();

    // Set up dashboard-specific integrations
    setupDashboardIntegrations();

    console.log('✅ Dashboard Auto-Completion System initialized');
}

/**
 * Set up global event listeners for auto-completion
 */
function setupGlobalEventListeners() {
    if (!window.dashboardAutoComplete) return;

    // Listen for WebSocket events
    window.dashboardAutoComplete.on('websocket:connected', () => {
        console.log('🔗 Auto-completion WebSocket connected');
        showNotification('Auto-completion connected', 'success');
    });

    window.dashboardAutoComplete.on('websocket:disconnected', () => {
        console.log('🔌 Auto-completion WebSocket disconnected');
        showNotification('Auto-completion disconnected', 'warning');
    });

    window.dashboardAutoComplete.on('websocket:error', (error) => {
        console.error('Auto-completion WebSocket error:', error);
    });

    // Listen for context updates
    window.dashboardAutoComplete.on('context:updated', (context) => {
        console.log('Context updated:', context);
    });

    // Listen for cache events
    window.dashboardAutoComplete.on('cache:hit', (data) => {
        console.log('Cache hit for:', data.query);
    });

    // Listen for request events
    window.dashboardAutoComplete.on('request:completed', (data) => {
        console.log(`Auto-completion request completed in ${data.responseTime}ms for:`, data.query);
    });

    window.dashboardAutoComplete.on('request:error', (data) => {
        console.error('Auto-completion request failed:', data.error);
    });
}

/**
 * Initialize auto-completion on existing elements
 */
function initializeExistingElements() {
    // Initialize search boxes
    const searchBoxes = document.querySelectorAll('.search-box input, input[type="search"], .search-input');
    searchBoxes.forEach(input => {
        if (!input.hasAttribute('data-autocomplete-initialized')) {
            initializeSearchAutoComplete(input);
            input.setAttribute('data-autocomplete-initialized', 'true');
        }
    });

    // Initialize code editors
    const codeEditors = document.querySelectorAll('.code-editor, textarea.code, .monaco-editor');
    codeEditors.forEach(editor => {
        if (!editor.hasAttribute('data-autocomplete-initialized')) {
            initializeCodeEditorAutoComplete(editor);
            editor.setAttribute('data-autocomplete-initialized', 'true');
        }
    });

    // Initialize form inputs with auto-completion
    const autoCompleteInputs = document.querySelectorAll('input[data-autocomplete], .autocomplete-input');
    autoCompleteInputs.forEach(input => {
        if (!input.hasAttribute('data-autocomplete-initialized')) {
            initializeInputAutoComplete(input);
            input.setAttribute('data-autocomplete-initialized', 'true');
        }
    });
}

/**
 * Set up dashboard-specific integrations
 */
function setupDashboardIntegrations() {
    // Integrate with dashboard search
    const dashboardSearch = document.querySelector('.search-box input');
    if (dashboardSearch && !dashboardSearch.hasAttribute('data-autocomplete-initialized')) {
        initializeSearchAutoComplete(dashboardSearch);
    }

    // Integrate with agent creation forms
    const agentNameInputs = document.querySelectorAll('input[name="agent_name"], input[name="name"]');
    agentNameInputs.forEach(input => {
        if (!input.hasAttribute('data-autocomplete-initialized')) {
            initializeInputAutoComplete(input, {
                placeholder: 'Enter agent name...',
                providerTypes: ['ai_agent', 'search']
            });
        }
    });

    // Integrate with API endpoint inputs
    const apiEndpointInputs = document.querySelectorAll('input[name="endpoint"], input[name="api_endpoint"]');
    apiEndpointInputs.forEach(input => {
        if (!input.hasAttribute('data-autocomplete-initialized')) {
            initializeInputAutoComplete(input, {
                placeholder: 'Enter API endpoint...',
                providerTypes: ['api_endpoint', 'search']
            });
        }
    });

    // Integrate with command inputs
    const commandInputs = document.querySelectorAll('input[name="command"], .command-input, .cli-input');
    commandInputs.forEach(input => {
        if (!input.hasAttribute('data-autocomplete-initialized')) {
            initializeInputAutoComplete(input, {
                placeholder: 'Enter command...',
                providerTypes: ['cli', 'ai_agent']
            });
        }
    });
}

/**
 * Initialize Search Auto-Complete on an element
 */
function initializeSearchAutoComplete(element, options = {}) {
    if (!window.dashboardAutoComplete) {
        console.error('Auto-completion core not initialized');
        return null;
    }

    const instance = new SearchAutoComplete(element, {
        core: window.dashboardAutoComplete,
        minQueryLength: 1,
        maxResults: 7,
        debounceDelay: 200,
        searchHistory: true,
        categories: ['agents', 'tasks', 'settings', 'documentation', 'help'],
        ...options
    });

    // Store instance reference
    const id = 'search_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    window.dashboardAutoCompleteInstances.set(id, instance);

    // Set up event listeners
    instance.on('search:selected', (data) => {
        console.log('Search selected:', data);
        handleSearchSelection(data);
    });

    instance.on('category:changed', (category) => {
        console.log('Search category changed:', category);
    });

    return instance;
}

/**
 * Initialize Input Auto-Complete on an element
 */
function initializeInputAutoComplete(element, options = {}) {
    if (!window.dashboardAutoComplete) {
        console.error('Auto-completion core not initialized');
        return null;
    }

    const instance = new InputAutoComplete(element, {
        core: window.dashboardAutoComplete,
        minQueryLength: 2,
        maxResults: 8,
        debounceDelay: 250,
        allowCustomValues: true,
        highlightMatches: true,
        ...options
    });

    // Store instance reference
    const id = 'input_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    window.dashboardAutoCompleteInstances.set(id, instance);

    // Set up event listeners
    instance.on('item:selected', (data) => {
        console.log('Input item selected:', data);
        handleInputSelection(data);
    });

    instance.on('custom:selected', (data) => {
        console.log('Custom input selected:', data);
    });

    return instance;
}

/**
 * Initialize Code Editor Auto-Complete on an element
 */
function initializeCodeEditorAutoComplete(element, options = {}) {
    if (!window.dashboardAutoComplete) {
        console.error('Auto-completion core not initialized');
        return null;
    }

    const instance = new CodeEditorAutoComplete(element, {
        core: window.dashboardAutoComplete,
        minQueryLength: 1,
        maxResults: 6,
        debounceDelay: 150,
        language: options.language || 'javascript',
        syntaxHighlighting: true,
        autoInsert: true,
        triggerChars: ['.', '(', ' ', '\n'],
        ...options
    });

    // Store instance reference
    const id = 'code_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    window.dashboardAutoCompleteInstances.set(id, instance);

    // Set up event listeners
    instance.on('code:selected', (data) => {
        console.log('Code completion selected:', data);
        handleCodeSelection(data);
    });

    return instance;
}

/**
 * Handle search selection events
 */
function handleSearchSelection(data) {
    // Navigate to search results or perform action
    if (data.category === 'agents') {
        window.dashboard.navigateToPage('agents');
    } else if (data.category === 'tasks') {
        window.dashboard.navigateToPage('tasks');
    } else if (data.category === 'settings') {
        window.dashboard.navigateToPage('preferences');
    } else if (data.category === 'documentation') {
        window.open('/docs', '_blank');
    } else if (data.category === 'help') {
        window.dashboard.showNotification('Help system coming soon!', 'info');
    }

    // Update search context
    if (window.dashboardAutoComplete) {
        window.dashboardAutoComplete.updateContext({
            last_search: data.value,
            last_search_category: data.category
        });
    }
}

/**
 * Handle input selection events
 */
function handleInputSelection(data) {
    // Update context based on selection
    if (window.dashboardAutoComplete) {
        window.dashboardAutoComplete.updateContext({
            last_input_selection: data.value,
            last_input_provider: data.result.provider
        });
    }
}

/**
 * Handle code selection events
 */
function handleCodeSelection(data) {
    // Update code context
    if (window.dashboardAutoComplete) {
        window.dashboardAutoComplete.updateContext({
            last_code_completion: data.completion,
            last_code_context: data.context
        });
    }
}

/**
 * Create a new auto-complete instance programmatically
 */
function createAutoComplete(element, type, options = {}) {
    switch (type) {
        case 'search':
            return initializeSearchAutoComplete(element, options);
        case 'input':
            return initializeInputAutoComplete(element, options);
        case 'code':
            return initializeCodeEditorAutoComplete(element, options);
        default:
            console.error('Unknown auto-completion type:', type);
            return null;
    }
}

/**
 * Get all auto-completion instances
 */
function getAutoCompleteInstances() {
    return Array.from(window.dashboardAutoCompleteInstances.entries());
}

/**
 * Get auto-completion instance by ID
 */
function getAutoCompleteInstance(id) {
    return window.dashboardAutoCompleteInstances.get(id);
}

/**
 * Destroy auto-completion instance
 */
function destroyAutoCompleteInstance(id) {
    const instance = window.dashboardAutoCompleteInstances.get(id);
    if (instance) {
        instance.destroy();
        window.dashboardAutoCompleteInstances.delete(id);
        return true;
    }
    return false;
}

/**
 * Destroy all auto-completion instances
 */
function destroyAllAutoCompleteInstances() {
    window.dashboardAutoCompleteInstances.forEach((instance, id) => {
        instance.destroy();
    });
    window.dashboardAutoCompleteInstances.clear();
}

/**
 * Update auto-completion context
 */
function updateAutoCompleteContext(updates) {
    if (window.dashboardAutoComplete) {
        window.dashboardAutoComplete.updateContext(updates);
    }
}

/**
 * Get auto-completion statistics
 */
function getAutoCompleteStats() {
    if (window.dashboardAutoComplete) {
        return window.dashboardAutoComplete.getStats();
    }
    return null;
}

/**
 * Perform health check on auto-completion system
 */
async function healthCheckAutoComplete() {
    if (window.dashboardAutoComplete) {
        try {
            const health = await window.dashboardAutoComplete.healthCheck();
            console.log('Auto-completion health check:', health);
            return health;
        } catch (error) {
            console.error('Auto-completion health check failed:', error);
            return { status: 'unhealthy', error: error.message };
        }
    }
    return { status: 'not_initialized' };
}

/**
 * Show notification helper
 */
function showNotification(message, type = 'info') {
    if (window.dashboard && window.dashboard.showNotification) {
        window.dashboard.showNotification(message, type);
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

/**
 * Example usage and demonstrations
 */
function demonstrateAutoComplete() {
    console.log('🎯 Auto-Completion Examples:');

    console.log('1. Search Auto-Complete:');
    console.log('   const search = new SearchAutoComplete(document.getElementById("search"));');

    console.log('2. Input Auto-Complete:');
    console.log('   const input = new InputAutoComplete(document.getElementById("input"));');

    console.log('3. Code Editor Auto-Complete:');
    console.log('   const code = new CodeEditorAutoComplete(document.getElementById("code"), { language: "python" });');

    console.log('4. Global functions:');
    console.log('   - createAutoComplete(element, type, options)');
    console.log('   - getAutoCompleteInstances()');
    console.log('   - updateAutoCompleteContext(updates)');
    console.log('   - healthCheckAutoComplete()');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Auto-initialize if core is not already initialized
    if (!window.dashboardAutoComplete) {
        initializeDashboardAutoComplete();
    }

    // Add global functions to window
    window.initializeDashboardAutoComplete = initializeDashboardAutoComplete;
    window.createAutoComplete = createAutoComplete;
    window.getAutoCompleteInstances = getAutoCompleteInstances;
    window.getAutoCompleteInstance = getAutoCompleteInstance;
    window.destroyAutoCompleteInstance = destroyAutoCompleteInstance;
    window.destroyAllAutoCompleteInstances = destroyAllAutoCompleteInstances;
    window.updateAutoCompleteContext = updateAutoCompleteContext;
    window.getAutoCompleteStats = getAutoCompleteStats;
    window.healthCheckAutoComplete = healthCheckAutoComplete;
    window.demonstrateAutoComplete = demonstrateAutoComplete;

    console.log('🔧 Dashboard Auto-Completion system loaded and ready!');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeDashboardAutoComplete,
        createAutoComplete,
        getAutoCompleteInstances,
        getAutoCompleteInstance,
        destroyAutoCompleteInstance,
        destroyAllAutoCompleteInstances,
        updateAutoCompleteContext,
        getAutoCompleteStats,
        healthCheckAutoComplete,
        demonstrateAutoComplete
    };
}</code>
</edit_file>