<?php
/**
 * Plugin Name: Automated Product Import
 * Plugin URI: https://github.com/your-username/free-ecommerce-store
 * Description: Automated product import from dropshipping suppliers (AliExpress, CJDropshipping, Spocket)
 * Version: 1.0.0
 * Author: Your Name
 * Author URI: https://your-website.com
 * License: GPL-2.0+
 * License URI: http://www.gnu.org/licenses/gpl-2.0.txt
 * Text Domain: product-import
 * Domain Path: /languages
 */

// If this file is called directly, abort.
if (!defined('WPINC')) {
    die;
}

/**
 * Currently plugin version.
 */
define('PRODUCT_IMPORT_VERSION', '1.0.0');

/**
 * The core plugin class.
 */
class Product_Import {

    /**
     * The single instance of the class.
     */
    private static $_instance = null;

    /**
     * Main Product_Import Instance.
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
        require_once plugin_dir_path(__FILE__) . 'includes/class-product-import-api.php';
        require_once plugin_dir_path(__FILE__) . 'includes/class-product-import-csv.php';
        require_once plugin_dir_path(__FILE__) . 'includes/class-product-import-suppliers.php';
        require_once plugin_dir_path(__FILE__) . 'admin/class-product-import-admin.php';
    }

    /**
     * Initialize hooks.
     */
    private function init_hooks() {
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));

        // Initialize admin functionality
        if (is_admin()) {
            new Product_Import_Admin();
        }

        // Add AJAX handlers
        add_action('wp_ajax_import_products', array($this, 'ajax_import_products'));
        add_action('wp_ajax_sync_products', array($this, 'ajax_sync_products'));
        add_action('wp_ajax_check_import_status', array($this, 'ajax_check_import_status'));

        // Add cron job for automatic sync
        add_action('product_import_auto_sync', array($this, 'auto_sync_products'));
    }

    /**
     * Plugin activation hook.
     */
    public function activate() {
        $this->create_tables();
        $this->schedule_cron_jobs();
        
        // Create necessary directories
        $upload_dir = wp_upload_dir();
        $import_dir = $upload_dir['basedir'] . '/product-import';
        if (!file_exists($import_dir)) {
            wp_mkdir_p($import_dir);
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
        
        $table_name = $wpdb->prefix . 'product_import_log';
        
        $sql = "CREATE TABLE $table_name (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            product_id bigint(20) NOT NULL,
            supplier varchar(50) NOT NULL,
            supplier_id varchar(100) NOT NULL,
            action varchar(20) NOT NULL,
            status varchar(20) NOT NULL,
            message text,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            KEY product_id (product_id),
            KEY supplier (supplier),
            KEY status (status)
        ) $charset_collate;";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
    }

    /**
     * Schedule cron jobs.
     */
    private function schedule_cron_jobs() {
        if (!wp_next_scheduled('product_import_auto_sync')) {
            wp_schedule_event(time(), 'hourly', 'product_import_auto_sync');
        }
    }

    /**
     * Unschedule cron jobs.
     */
    private function unschedule_cron_jobs() {
        wp_clear_scheduled_hook('product_import_auto_sync');
    }

    /**
     * AJAX handler for importing products.
     */
    public function ajax_import_products() {
        check_ajax_referer('product_import_nonce', 'nonce');
        
        if (!current_user_can('manage_woocommerce')) {
            wp_send_json_error('Permission denied');
        }

        $supplier = sanitize_text_field($_POST['supplier']);
        $csv_file = $_FILES['csv_file'];
        $auto_update = isset($_POST['auto_update']) ? true : false;

        $result = $this->import_products($supplier, $csv_file, $auto_update);
        
        wp_send_json_success($result);
    }

    /**
     * AJAX handler for syncing products.
     */
    public function ajax_sync_products() {
        check_ajax_referer('product_import_nonce', 'nonce');
        
        if (!current_user_can('manage_woocommerce')) {
            wp_send_json_error('Permission denied');
        }

        $supplier = sanitize_text_field($_POST['supplier']);
        $result = $this->sync_products($supplier);
        
        wp_send_json_success($result);
    }

    /**
     * AJAX handler for checking import status.
     */
    public function ajax_check_import_status() {
        check_ajax_referer('product_import_nonce', 'nonce');
        
        if (!current_user_can('manage_woocommerce')) {
            wp_send_json_error('Permission denied');
        }

        $status = $this->get_import_status();
        wp_send_json_success($status);
    }

    /**
     * Import products from supplier.
     */
    private function import_products($supplier, $csv_file, $auto_update = false) {
        $importer = new Product_Import_CSV();
        $result = $importer->import_from_csv($csv_file, $supplier, $auto_update);
        
        $this->log_import_activity('import', $supplier, $result);
        
        return $result;
    }

    /**
     * Sync products with supplier.
     */
    private function sync_products($supplier) {
        $api = new Product_Import_API();
        $result = $api->sync_with_supplier($supplier);
        
        $this->log_import_activity('sync', $supplier, $result);
        
        return $result;
    }

    /**
     * Auto sync products (cron job).
     */
    public function auto_sync_products() {
        $suppliers = array('aliexpress', 'cjdropshipping', 'spocket');
        
        foreach ($suppliers as $supplier) {
            $this->sync_products($supplier);
        }
    }

    /**
     * Get import status.
     */
    private function get_import_status() {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'product_import_log';
        
        $status = array(
            'total_imported' => $wpdb->get_var("SELECT COUNT(*) FROM $table_name WHERE action = 'import' AND status = 'success'"),
            'total_synced' => $wpdb->get_var("SELECT COUNT(*) FROM $table_name WHERE action = 'sync' AND status = 'success'"),
            'recent_activity' => $wpdb->get_results("SELECT * FROM $table_name ORDER BY created_at DESC LIMIT 10"),
        );
        
        return $status;
    }

    /**
     * Log import activity.
     */
    private function log_import_activity($action, $supplier, $result) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'product_import_log';
        
        foreach ($result['products'] as $product) {
            $wpdb->insert(
                $table_name,
                array(
                    'product_id' => $product['product_id'],
                    'supplier' => $supplier,
                    'supplier_id' => $product['supplier_id'],
                    'action' => $action,
                    'status' => $product['status'],
                    'message' => $product['message'],
                )
            );
        }
    }
}

// Initialize the plugin
function product_import() {
    return Product_Import::instance();
}

// Let's go!
product_import();
