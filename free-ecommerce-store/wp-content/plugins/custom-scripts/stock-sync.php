<?php
/**
 * Plugin Name: Automated Stock Synchronization
 * Plugin URI: https://github.com/your-username/free-ecommerce-store
 * Description: Automated inventory synchronization with dropshipping suppliers
 * Version: 1.0.0
 * Author: Your Name
 * Author URI: https://your-website.com
 * License: GPL-2.0+
 * License URI: http://www.gnu.org/licenses/gpl-2.0.txt
 * Text Domain: stock-sync
 * Domain Path: /languages
 */

// If this file is called directly, abort.
if (!defined('WPINC')) {
    die;
}

/**
 * Currently plugin version.
 */
define('STOCK_SYNC_VERSION', '1.0.0');

/**
 * The core plugin class.
 */
class Stock_Sync {

    /**
     * The single instance of the class.
     */
    private static $_instance = null;

    /**
     * Main Stock_Sync Instance.
     */
    public static function instance() {
        if (is_null(self::$_instance)) {
            self::$_instance = new self();
        }
        return self::$_instance;
    }

    /**
     * Constructor.
     */
    public function __construct() {
        $this->includes();
        $this->init_hooks();
    }

    /**
     * Include required core files.
     */
    private function includes() {
        require_once plugin_dir_path(__FILE__) . 'includes/class-stock-sync-api.php';
        require_once plugin_dir_path(__FILE__) . 'includes/class-stock-sync-suppliers.php';
        require_once plugin_dir_path(__FILE__) . 'includes/class-stock-sync-notifications.php';
        require_once plugin_dir_path(__FILE__) . 'admin/class-stock-sync-admin.php';
    }

    /**
     * Initialize hooks.
     */
    private function init_hooks() {
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));

        // Initialize admin functionality
        if (is_admin()) {
            new Stock_Sync_Admin();
        }

        // WooCommerce product hooks
        add_action('woocommerce_product_set_stock', array($this, 'on_stock_change'), 10, 2);
        add_action('woocommerce_variation_set_stock', array($this, 'on_variation_stock_change'), 10, 2);
        add_action('woocommerce_product_before_save', array($this, 'before_product_save'), 10, 1);

        // Add AJAX handlers
        add_action('wp_ajax_sync_product_stock', array($this, 'ajax_sync_product_stock'));
        add_action('wp_ajax_sync_all_stock', array($this, 'ajax_sync_all_stock'));
        add_action('wp_ajax_check_sync_status', array($this, 'ajax_check_sync_status'));
        add_action('wp_ajax_manual_stock_update', array($this, 'ajax_manual_stock_update'));

        // Add cron job for automatic sync
        add_action('stock_sync_auto_sync', array($this, 'auto_sync_stock'));
        add_action('stock_sync_low_stock_check', array($this, 'check_low_stock'));
        add_action('stock_sync_price_update', array($this, 'update_prices'));

        // Add custom product meta boxes
        add_action('add_meta_boxes', array($this, 'add_stock_sync_meta_box'));

        // Add custom product columns
        add_filter('manage_edit-product_columns', array($this, 'add_stock_sync_columns'));
        add_action('manage_product_posts_custom_column', array($this, 'render_stock_sync_columns'), 10, 2);

        // Add bulk actions
        add_filter('bulk_actions-edit-product', array($this, 'add_bulk_actions'));
        add_filter('handle_bulk_actions-edit-product', array($this, 'handle_bulk_actions'), 10, 3);

        // Add product data tab
        add_filter('woocommerce_product_data_tabs', array($this, 'add_stock_sync_tab'));
        add_action('woocommerce_product_data_panels', array($this, 'add_stock_sync_panel'));

        // Add scheduled stock update filter
        add_filter('cron_schedules', array($this, 'add_custom_cron_schedules'));
    }

    /**
     * Plugin activation hook.
     */
    public function activate() {
        $this->create_tables();
        $this->schedule_cron_jobs();
        
        // Create necessary directories
        $upload_dir = wp_upload_dir();
        $stock_sync_dir = $upload_dir['basedir'] . '/stock-sync';
        if (!file_exists($stock_sync_dir)) {
            wp_mkdir_p($stock_sync_dir);
        }
    }

    /**
     * Plugin deactivation hook.
     */
    public function deactivate() {
        $this->unschedule_cron_jobs();
    }

    /**
     * Create required database tables.
     */
    private function create_tables() {
        global $wpdb;
        
        $charset_collate = $wpdb->get_charset_collate();
        
        // Stock sync log table
        $table_name = $wpdb->prefix . 'stock_sync_log';
        
        $sql = "CREATE TABLE $table_name (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            product_id bigint(20) NOT NULL,
            supplier varchar(50) NOT NULL,
            supplier_product_id varchar(100) NOT NULL,
            action varchar(20) NOT NULL,
            old_stock int(11) DEFAULT NULL,
            new_stock int(11) DEFAULT NULL,
            old_price decimal(10,2) DEFAULT NULL,
            new_price decimal(10,2) DEFAULT NULL,
            status varchar(20) NOT NULL,
            message text,
            sync_type varchar(20) DEFAULT 'auto',
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            KEY product_id (product_id),
            KEY supplier (supplier),
            KEY status (status),
            KEY sync_type (sync_type),
            KEY created_at (created_at)
        ) $charset_collate;";

        // Product supplier mapping table
        $table_name2 = $wpdb->prefix . 'product_supplier_mapping';
        
        $sql .= "CREATE TABLE $table_name2 (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            product_id bigint(20) NOT NULL,
            supplier varchar(50) NOT NULL,
            supplier_product_id varchar(100) NOT NULL,
            supplier_sku varchar(100) DEFAULT NULL,
            last_sync datetime DEFAULT NULL,
            sync_enabled tinyint(1) DEFAULT 1,
            price_sync_enabled tinyint(1) DEFAULT 1,
            stock_sync_enabled tinyint(1) DEFAULT 1,
            min_stock_level int(11) DEFAULT 0,
            max_stock_level int(11) DEFAULT 1000,
            price_adjustment decimal(5,2) DEFAULT 0.00,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            UNIQUE KEY product_supplier (product_id, supplier),
            KEY supplier_product_id (supplier_product_id),
            KEY supplier (supplier)
        ) $charset_collate;";

        // Low stock alerts table
        $table_name3 = $wpdb->prefix . 'low_stock_alerts';
        
        $sql .= "CREATE TABLE $table_name3 (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            product_id bigint(20) NOT NULL,
            supplier varchar(50) NOT NULL,
            current_stock int(11) NOT NULL,
            min_stock_level int(11) NOT NULL,
            alert_sent tinyint(1) DEFAULT 0,
            alert_sent_at datetime DEFAULT NULL,
            resolved_at datetime DEFAULT NULL,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            KEY product_id (product_id),
            KEY supplier (supplier),
            KEY alert_sent (alert_sent),
            KEY created_at (created_at)
        ) $charset_collate;";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
    }

    /**
     * Schedule cron jobs.
     */
    private function schedule_cron_jobs() {
        if (!wp_next_scheduled('stock_sync_auto_sync')) {
            wp_schedule_event(time(), 'hourly', 'stock_sync_auto_sync');
        }
        
        if (!wp_next_scheduled('stock_sync_low_stock_check')) {
            wp_schedule_event(time(), 'twicedaily', 'stock_sync_low_stock_check');
        }
        
        if (!wp_next_scheduled('stock_sync_price_update')) {
            wp_schedule_event(time(), 'daily', 'stock_sync_price_update');
        }
    }

    /**
     * Unschedule cron jobs.
     */
    private function unschedule_cron_jobs() {
        wp_clear_scheduled_hook('stock_sync_auto_sync');
        wp_clear_scheduled_hook('stock_sync_low_stock_check');
        wp_clear_scheduled_hook('stock_sync_price_update');
    }

    /**
     * Add custom cron schedules.
     */
    public function add_custom_cron_schedules($schedules) {
        $schedules['every_15_minutes'] = array(
            'interval' => 15 * 60,
            'display' => __('Every 15 Minutes', 'stock-sync')
        );
        
        $schedules['every_30_minutes'] = array(
            'interval' => 30 * 60,
            'display' => __('Every 30 Minutes', 'stock-sync')
        );
        
        return $schedules;
    }

    /**
     * Handle stock change events.
     */
    public function on_stock_change($product, $stock_quantity) {
        $this->handle_stock_update($product, $stock_quantity);
    }

    /**
     * Handle variation stock change events.
     */
    public function on_variation_stock_change($product, $stock_quantity) {
        $this->handle_stock_update($product, $stock_quantity);
    }

    /**
     * Handle stock update.
     */
    private function handle_stock_update($product, $stock_quantity) {
        $product_id = $product->get_id();
        $old_stock = $product->get_stock_quantity();
        
        // Get supplier mappings for this product
        $mappings = $this->get_product_supplier_mappings($product_id);
        
        foreach ($mappings as $mapping) {
            if ($mapping->stock_sync_enabled) {
                $this->sync_stock_to_supplier($product, $mapping, $old_stock, $stock_quantity);
            }
        }
        
        // Check for low stock
        $this->check_product_low_stock($product_id);
    }

    /**
     * Before product save hook.
     */
    public function before_product_save($product) {
        // Check if price or stock has changed
        if ($product->get_id()) {
            $old_product = wc_get_product($product->get_id());
            if ($old_product) {
                $old_price = $old_product->get_price();
                $new_price = $product->get_price();
                
                if ($old_price != $new_price) {
                    $this->handle_price_change($product, $old_price, $new_price);
                }
            }
        }
    }

    /**
     * Handle price change.
     */
    private function handle_price_change($product, $old_price, $new_price) {
        $product_id = $product->get_id();
        
        // Get supplier mappings for this product
        $mappings = $this->get_product_supplier_mappings($product_id);
        
        foreach ($mappings as $mapping) {
            if ($mapping->price_sync_enabled) {
                $this->sync_price_to_supplier($product, $mapping, $old_price, $new_price);
            }
        }
    }

    /**
     * Get product supplier mappings.
     */
    private function get_product_supplier_mappings($product_id) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'product_supplier_mapping';
        
        return $wpdb->get_results(
            $wpdb->prepare(
                "SELECT * FROM $table_name WHERE product_id = %d AND sync_enabled = 1",
                $product_id
            )
        );
    }

    /**
     * Sync stock to supplier.
     */
    private function sync_stock_to_supplier($product, $mapping, $old_stock, $new_stock) {
        $api = new Stock_Sync_API();
        
        $result = $api->update_supplier_stock($mapping->supplier, $mapping->supplier_product_id, $new_stock);
        
        $this->log_sync_activity(
            $product->get_id(),
            $mapping->supplier,
            $mapping->supplier_product_id,
            'stock_update',
            $old_stock,
            $new_stock,
            null,
            null,
            $result['success'] ? 'success' : 'error',
            $result['message'],
            'manual'
        );
    }

    /**
     * Sync price to supplier.
     */
    private function sync_price_to_supplier($product, $mapping, $old_price, $new_price) {
        $api = new Stock_Sync_API();
        
        // Apply price adjustment
        $adjusted_price = $new_price * (1 + ($mapping->price_adjustment / 100));
        
        $result = $api->update_supplier_price($mapping->supplier, $mapping->supplier_product_id, $adjusted_price);
        
        $this->log_sync_activity(
            $product->get_id(),
            $mapping->supplier,
            $mapping->supplier_product_id,
            'price_update',
            null,
            null,
            $old_price,
            $new_price,
            $result['success'] ? 'success' : 'error',
            $result['message'],
            'manual'
        );
    }

    /**
     * Check product low stock.
     */
    private function check_product_low_stock($product_id) {
        $product = wc_get_product($product_id);
        $current_stock = $product->get_stock_quantity();
        
        $mappings = $this->get_product_supplier_mappings($product_id);
        
        foreach ($mappings as $mapping) {
            if ($current_stock <= $mapping->min_stock_level) {
                $this->create_low_stock_alert($product_id, $mapping, $current_stock);
            }
        }
    }

    /**
     * Create low stock alert.
     */
    private function create_low_stock_alert($product_id, $mapping, $current_stock) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'low_stock_alerts';
        
        // Check if alert already exists
        $existing = $wpdb->get_row(
            $wpdb->prepare(
                "SELECT * FROM $table_name WHERE product_id = %d AND supplier = %s AND resolved_at IS NULL",
                $product_id,
                $mapping->supplier
            )
        );
        
        if (!$existing) {
            $wpdb->insert(
                $table_name,
                array(
                    'product_id' => $product_id,
                    'supplier' => $mapping->supplier,
                    'current_stock' => $current_stock,
                    'min_stock_level' => $mapping->min_stock_level,
                )
            );
            
            // Send low stock notification
            $notifications = new Stock_Sync_Notifications();
            $notifications->send_low_stock_alert($product_id, $mapping, $current_stock);
        }
    }

    /**
     * Auto sync stock (cron job).
     */
    public function auto_sync_stock() {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'product_supplier_mapping';
        
        // Get products that need sync
        $mappings = $wpdb->get_results(
            "SELECT * FROM $table_name 
            WHERE sync_enabled = 1 AND stock_sync_enabled = 1
            AND (last_sync IS NULL OR last_sync < DATE_SUB(NOW(), INTERVAL 1 HOUR))"
        );
        
        foreach ($mappings as $mapping) {
            $this->sync_product_from_supplier($mapping);
        }
    }

    /**
     * Check low stock (cron job).
     */
    public function check_low_stock() {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'low_stock_alerts';
        
        // Get unresolved low stock alerts
        $alerts = $wpdb->get_results(
            "SELECT * FROM $table_name WHERE resolved_at IS NULL"
        );
        
        foreach ($alerts as $alert) {
            $product = wc_get_product($alert->product_id);
            $current_stock = $product->get_stock_quantity();
            
            if ($current_stock > $alert->min_stock_level) {
                // Stock has been replenished
                $wpdb->update(
                    $table_name,
<?php
/**
 * Plugin Name: Automated Stock Synchronization
 * Plugin URI: https://github.com/your-username/free-ecommerce-store
 * Description: Automated inventory synchronization with dropshipping suppliers
 * Version: 1.0.0
 * Author: Your Name
 * Author URI: https://your-website.com
 * License: GPL-2.0+
 * License URI: http://www.gnu.org/licenses/gpl-2.0.txt
 * Text Domain: stock-sync
 * Domain Path: /languages
 */

// If this file is called directly, abort.
if (!defined('WPINC')) {
    die;
}

/**
 * Currently plugin version.
 */
define('STOCK_SYNC_VERSION', '1.0.0');

/**
 * The core plugin class.
 */
class Stock_Sync {

    /**
     * The single instance of the class.
     */
    private static $_instance = null;

    /**
     * Main Stock_Sync Instance.
     */
    public static function instance() {
        if (is_null(self::$_instance)) {
            self::$_instance = new self();
        }
        return self::$_instance;
    }

    /**
     * Constructor.
     */
    public function __construct() {
        $this->includes();
        $this->init_hooks();
    }

    /**
     * Include required core files.
     */
    private function includes() {
        require_once plugin_dir_path(__FILE__) . 'includes/class-stock-sync-api.php';
        require_once plugin_dir_path(__FILE__) . 'includes/class-stock-sync-suppliers.php';
        require_once plugin_dir_path(__FILE__) . 'includes/class-stock-sync-notifications.php';
        require_once plugin_dir_path(__FILE__) . 'admin/class-stock-sync-admin.php';
    }

    /**
     * Initialize hooks.
     */
    private function init_hooks() {
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));

        // Initialize admin functionality
        if (is_admin()) {
            new Stock_Sync_Admin();
        }

        // WooCommerce product hooks
        add_action('woocommerce_product_set_stock', array($this, 'on_stock_change'), 10, 2);
        add_action('woocommerce_variation_set_stock', array($this, 'on_variation_stock_change'), 10, 2);
        add_action('woocommerce_product_before_save', array($this, 'before_product_save'), 10, 1);

        // Add AJAX handlers
        add_action('wp_ajax_sync_product_stock', array($this, 'ajax_sync_product_stock'));
        add_action('wp_ajax_sync_all_stock', array($this, 'ajax_sync_all_stock'));
        add_action('wp_ajax_check_sync_status', array($this, 'ajax_check_sync_status'));
        add_action('wp_ajax_manual_stock_update', array($this, 'ajax_manual_stock_update'));

        // Add cron job for automatic sync
        add_action('stock_sync_auto_sync', array($this, 'auto_sync_stock'));
        add_action('stock_sync_low_stock_check', array($this, 'check_low_stock'));
        add_action('stock_sync_price_update', array($this, 'update_prices'));

        // Add custom product meta boxes
        add_action('add_meta_boxes', array($this, 'add_stock_sync_meta_box'));

        // Add custom product columns
        add_filter('manage_edit-product_columns', array($this, 'add_stock_sync_columns'));
        add_action('manage_product_posts_custom_column', array($this, 'render_stock_sync_columns'), 10, 2);

        // Add bulk actions
        add_filter('bulk_actions-edit-product', array($this, 'add_bulk_actions'));
        add_filter('handle_bulk_actions-edit-product', array($this, 'handle_bulk_actions'), 10, 3);

        // Add product data tab
        add_filter('woocommerce_product_data_tabs', array($this, 'add_stock_sync_tab'));
        add_action('woocommerce_product_data_panels', array($this, 'add_stock_sync_panel'));

        // Add scheduled stock update filter
        add_filter('cron_schedules', array($this, 'add_custom_cron_schedules'));
    }

    /**
     * Plugin activation hook.
     */
    public function activate() {
        $this->create_tables();
        $this->schedule_cron_jobs();
        
        // Create necessary directories
        $upload_dir = wp_upload_dir();
        $stock_sync_dir = $upload_dir['basedir'] . '/stock-sync';
        if (!file_exists($stock_sync_dir)) {
            wp_mkdir_p($stock_sync_dir);
        }
    }

    /**
     * Plugin deactivation hook.
     */
    public function deactivate() {
        $this->unschedule_cron_jobs();
    }

    /**
     * Create required database tables.
     */
    private function create_tables() {
        global $wpdb;
        
        $charset_collate = $wpdb->get_charset_collate();
        
        // Stock sync log table
        $table_name = $wpdb->prefix . 'stock_sync_log';
        
        $sql = "CREATE TABLE $table_name (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            product_id bigint(20) NOT NULL,
            supplier varchar(50) NOT NULL,
            supplier_product_id varchar(100) NOT NULL,
            action varchar(20) NOT NULL,
            old_stock int(11) DEFAULT NULL,
            new_stock int(11) DEFAULT NULL,
            old_price decimal(10,2) DEFAULT NULL,
            new_price decimal(10,2) DEFAULT NULL,
            status varchar(20) NOT NULL,
            message text,
            sync_type varchar(20) DEFAULT 'auto',
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            KEY product_id (product_id),
            KEY supplier (supplier),
            KEY status (status),
            KEY sync_type (sync_type),
            KEY created_at (created_at)
        ) $charset_collate;";

        // Product supplier mapping table
        $table_name2 = $wpdb->prefix . 'product_supplier_mapping';
        
        $sql .= "CREATE TABLE $table_name2 (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            product_id bigint(20) NOT NULL,
            supplier varchar(50) NOT NULL,
            supplier_product_id varchar(100) NOT NULL,
            supplier_sku varchar(100) DEFAULT NULL,
            last_sync datetime DEFAULT NULL,
            sync_enabled tinyint(1) DEFAULT 1,
            price_sync_enabled tinyint(1) DEFAULT 1,
            stock_sync_enabled tinyint(1) DEFAULT 1,
            min_stock_level int(11) DEFAULT 0,
            max_stock_level int(11) DEFAULT 1000,
            price_adjustment decimal(5,2) DEFAULT 0.00,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            UNIQUE KEY product_supplier (product_id, supplier),
            KEY supplier_product_id (supplier_product_id),
            KEY supplier (supplier)
        ) $charset_collate;";

        // Low stock alerts table
        $table_name3 = $wpdb->prefix . 'low_stock_alerts';
        
        $sql .= "CREATE TABLE $table_name3 (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            product_id bigint(20) NOT NULL,
            supplier varchar(50) NOT NULL,
            current_stock int(11) NOT NULL,
            min_stock_level int(11) NOT NULL,
            alert_sent tinyint(1) DEFAULT 0,
            alert_sent_at datetime DEFAULT NULL,
            resolved_at datetime DEFAULT NULL,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            KEY product_id (product_id),
            KEY supplier (supplier),
            KEY alert_sent (alert_sent),
            KEY created_at (created_at)
        ) $charset_collate;";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
    }

    /**
     * Schedule cron jobs.
     */
    private function schedule_cron_jobs() {
        if (!wp_next_scheduled('stock_sync_auto_sync')) {
            wp_schedule_event(time(), 'hourly', 'stock_sync_auto_sync');
        }
        
        if (!wp_next_scheduled('stock_sync_low_stock_check')) {
            wp_schedule_event(time(), 'twicedaily', 'stock_sync_low_stock_check');
        }
        
        if (!wp_next_scheduled('stock_sync_price_update')) {
            wp_schedule_event(time(), 'daily', 'stock_sync_price_update');
        }
    }

    /**
     * Unschedule cron jobs.
     */
    private function unschedule_cron_jobs() {
        wp_clear_scheduled_hook('stock_sync_auto_sync');
        wp_clear_scheduled_hook('stock_sync_low_stock_check');
        wp_clear_scheduled_hook('stock_sync_price_update');
    }

    /**
     * Add custom cron schedules.
     */
    public function add_custom_cron_schedules($schedules) {
        $schedules['every_15_minutes'] = array(
            'interval' => 15 * 60,
            'display' => __('Every 15 Minutes', 'stock-sync')
        );
        
        $schedules['every_30_minutes'] = array(
            'interval' => 30 * 60,
            'display' => __('Every 30 Minutes', 'stock-sync')
        );
        
        return $schedules;
    }

    /**
     * Handle stock change events.
     */
    public function on_stock_change($product, $stock_quantity) {
        $this->handle_stock_update($product, $stock_quantity);
    }

    /**
     * Handle variation stock change events.
     */
    public function on_variation_stock_change($product, $stock_quantity) {
        $this->handle_stock_update($product, $stock_quantity);
    }

    /**
     * Handle stock update.
     */
    private function handle_stock_update($product, $stock_quantity) {
        $product_id = $product->get_id();
        $old_stock = $product->get_stock_quantity();
        
        // Get supplier mappings for this product
        $mappings = $this->get_product_supplier_mappings($product_id);
        
        foreach ($mappings as $mapping) {
            if ($mapping->stock_sync_enabled) {
                $this->sync_stock_to_supplier($product, $mapping, $old_stock, $stock_quantity);
            }
        }
        
        // Check for low stock
        $this->check_product_low_stock($product_id);
    }

    /**
     * Before product save hook.
     */
    public function before_product_save($product) {
        // Check if price or stock has changed
        if ($product->get_id()) {
            $old_product = wc_get_product($product->get_id());
            if ($old_product) {
                $old_price = $old_product->get_price();
                $new_price = $product->get_price();
                
                if ($old_price != $new_price) {
                    $this->handle_price_change($product, $old_price, $new_price);
                }
            }
        }
    }

    /**
     * Handle price change.
     */
    private function handle_price_change($product, $old_price, $new_price) {
        $product_id = $product->get_id();
        
        // Get supplier mappings for this product
        $mappings = $this->get_product_supplier_mappings($product_id);
        
        foreach ($mappings as $mapping) {
            if ($mapping->price_sync_enabled) {
                $this->sync_price_to_supplier($product, $mapping, $old_price, $new_price);
            }
        }
    }

    /**
     * Get product supplier mappings.
     */
    private function get_product_supplier_mappings($product_id) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'product_supplier_mapping';
        
        return $wpdb->get_results(
            $wpdb->prepare(
                "SELECT * FROM $table_name WHERE product_id = %d AND sync_enabled = 1",
                $product_id
            )
        );
    }

    /**
     * Sync stock to supplier.
     */
    private function sync_stock_to_supplier($product, $mapping, $old_stock, $new_stock) {
        $api = new Stock_Sync_API();
        
        $result = $api->update_supplier_stock($mapping->supplier, $mapping->supplier_product_id, $new_stock);
        
        $this->log_sync_activity(
            $product->get_id(),
            $mapping->supplier,
            $mapping->supplier_product_id,
            'stock_update',
            $old_stock,
            $new_stock,
            null,
            null,
            $result['success'] ? 'success' : 'error',
            $result['message'],
            'manual'
        );
    }

    /**
     * Sync price to supplier.
     */
    private function sync_price_to_supplier($product, $mapping, $old_price, $new_price) {
        $api = new Stock_Sync_API();
        
        // Apply price adjustment
        $adjusted_price = $new_price * (1 + ($mapping->price_adjustment / 100));
