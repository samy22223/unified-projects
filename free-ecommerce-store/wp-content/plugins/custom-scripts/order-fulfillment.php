<?php
/**
 * Plugin Name: Automated Order Fulfillment
 * Plugin URI: https://github.com/your-username/free-ecommerce-store
 * Description: Automated order fulfillment system for dropshipping suppliers with tracking integration
 * Version: 1.0.0
 * Author: Your Name
 * Author URI: https://your-website.com
 * License: GPL-2.0+
 * License URI: http://www.gnu.org/licenses/gpl-2.0.txt
 * Text Domain: order-fulfillment
 * Domain Path: /languages
 */

// If this file is called directly, abort.
if (!defined('WPINC')) {
    die;
}

/**
 * Currently plugin version.
 */
define('ORDER_FULFILLMENT_VERSION', '1.0.0');

/**
 * The core plugin class.
 */
class Order_Fulfillment {

    /**
     * The single instance of the class.
     */
    private static $_instance = null;

    /**
     * Main Order_Fulfillment Instance.
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
        require_once plugin_dir_path(__FILE__) . 'includes/class-order-fulfillment-api.php';
        require_once plugin_dir_path(__FILE__) . 'includes/class-order-fulfillment-suppliers.php';
        require_once plugin_dir_path(__FILE__) . 'includes/class-order-fulfillment-notifications.php';
        require_once plugin_dir_path(__FILE__) . 'admin/class-order-fulfillment-admin.php';
    }

    /**
     * Initialize hooks.
     */
    private function init_hooks() {
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));

        // Initialize admin functionality
        if (is_admin()) {
            new Order_Fulfillment_Admin();
        }

        // WooCommerce order hooks
        add_action('woocommerce_order_status_processing', array($this, 'process_order'), 10, 1);
        add_action('woocommerce_order_status_completed', array($this, 'complete_order'), 10, 1);
        add_action('woocommerce_order_status_cancelled', array($this, 'cancel_order'), 10, 1);
        add_action('woocommerce_order_status_refunded', array($this, 'refund_order'), 10, 1);

        // Add AJAX handlers
        add_action('wp_ajax_manual_fulfill_order', array($this, 'ajax_manual_fulfill_order'));
        add_action('wp_ajax_sync_tracking', array($this, 'ajax_sync_tracking'));
        add_action('wp_ajax_check_fulfillment_status', array($this, 'ajax_check_fulfillment_status'));

        // Add cron job for tracking sync
        add_action('order_fulfillment_sync_tracking', array($this, 'sync_all_tracking'));
        add_action('order_fulfillment_check_status', array($this, 'check_all_orders_status'));

        // Add custom order meta boxes
        add_action('add_meta_boxes_shop_order', array($this, 'add_fulfillment_meta_box'));

        // Add custom order columns
        add_filter('manage_edit-shop_order_columns', array($this, 'add_fulfillment_columns'));
        add_action('manage_shop_order_posts_custom_column', array($this, 'render_fulfillment_columns'), 10, 2);
    }

    /**
     * Plugin activation hook.
     */
    public function activate() {
        $this->create_tables();
        $this->schedule_cron_jobs();
        
        // Create necessary directories
        $upload_dir = wp_upload_dir();
        $fulfillment_dir = $upload_dir['basedir'] . '/order-fulfillment';
        if (!file_exists($fulfillment_dir)) {
            wp_mkdir_p($fulfillment_dir);
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
        
        // Fulfillment log table
        $table_name = $wpdb->prefix . 'order_fulfillment_log';
        
        $sql = "CREATE TABLE $table_name (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            order_id bigint(20) NOT NULL,
            supplier varchar(50) NOT NULL,
            supplier_order_id varchar(100) DEFAULT NULL,
            tracking_number varchar(100) DEFAULT NULL,
            tracking_url text DEFAULT NULL,
            status varchar(20) NOT NULL,
            action varchar(20) NOT NULL,
            message text,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            KEY order_id (order_id),
            KEY supplier (supplier),
            KEY status (status),
            KEY tracking_number (tracking_number)
        ) $charset_collate;";

        // Supplier orders table
        $table_name2 = $wpdb->prefix . 'supplier_orders';
        
        $sql .= "CREATE TABLE $table_name2 (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            order_id bigint(20) NOT NULL,
            supplier varchar(50) NOT NULL,
            supplier_order_id varchar(100) NOT NULL,
            supplier_product_id varchar(100) NOT NULL,
            quantity int(11) NOT NULL,
            unit_price decimal(10,2) NOT NULL,
            total_price decimal(10,2) NOT NULL,
            currency varchar(3) DEFAULT 'USD',
            status varchar(20) NOT NULL,
            tracking_number varchar(100) DEFAULT NULL,
            estimated_delivery date DEFAULT NULL,
            actual_delivery date DEFAULT NULL,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            updated_at datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY  (id),
            KEY order_id (order_id),
            KEY supplier (supplier),
            KEY supplier_order_id (supplier_order_id),
            KEY status (status)
        ) $charset_collate;";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
    }

    /**
     * Schedule cron jobs.
     */
    private function schedule_cron_jobs() {
        if (!wp_next_scheduled('order_fulfillment_sync_tracking')) {
            wp_schedule_event(time(), 'hourly', 'order_fulfillment_sync_tracking');
        }
        
        if (!wp_next_scheduled('order_fulfillment_check_status')) {
            wp_schedule_event(time(), 'twicedaily', 'order_fulfillment_check_status');
        }
    }

    /**
     * Unschedule cron jobs.
     */
    private function unschedule_cron_jobs() {
        wp_clear_scheduled_hook('order_fulfillment_sync_tracking');
        wp_clear_scheduled_hook('order_fulfillment_check_status');
    }

    /**
     * Process order when status changes to processing.
     */
    public function process_order($order_id) {
        $order = wc_get_order($order_id);
        if (!$order) {
            return false;
        }

        // Check if order is already being processed
        $fulfillment_status = $this->get_order_fulfillment_status($order_id);
        if ($fulfillment_status === 'processing') {
            return false;
        }

        // Get order items and group by supplier
        $items_by_supplier = $this->group_items_by_supplier($order);
        
        foreach ($items_by_supplier as $supplier => $items) {
            $this->process_supplier_order($order, $supplier, $items);
        }

        // Add order note
        $order->add_order_note('Order sent to supplier(s) for fulfillment.', false);

        return true;
    }

    /**
     * Complete order when all items are delivered.
     */
    public function complete_order($order_id) {
        $order = wc_get_order($order_id);
        if (!$order) {
            return false;
        }

        // Send completion notification
        $notifications = new Order_Fulfillment_Notifications();
        $notifications->send_order_completion_notification($order);

        // Log completion
        $this->log_fulfillment_activity($order_id, 'system', 'complete', 'Order completed successfully');

        return true;
    }

    /**
     * Cancel order with supplier.
     */
    public function cancel_order($order_id) {
        $order = wc_get_order($order_id);
        if (!$order) {
            return false;
        }

        // Get supplier orders for this order
        $supplier_orders = $this->get_supplier_orders($order_id);
        
        foreach ($supplier_orders as $supplier_order) {
            $this->cancel_supplier_order($order, $supplier_order);
        }

        // Add order note
        $order->add_order_note('Order cancellation requested from supplier(s).', false);

        return true;
    }

    /**
     * Process refund with supplier.
     */
    public function refund_order($order_id) {
        $order = wc_get_order($order_id);
        if (!$order) {
            return false;
        }

        // Get supplier orders for this order
        $supplier_orders = $this->get_supplier_orders($order_id);
        
        foreach ($supplier_orders as $supplier_order) {
            $this->process_supplier_refund($order, $supplier_order);
        }

        // Add order note
        $order->add_order_note('Refund processed with supplier(s).', false);

        return true;
    }

    /**
     * Process order with specific supplier.
     */
    private function process_supplier_order($order, $supplier, $items) {
        $api = new Order_Fulfillment_API();
        
        $result = $api->create_supplier_order($order, $supplier, $items);
        
        if ($result['success']) {
            // Save supplier order information
            $this->save_supplier_order($order->get_id(), $supplier, $items, $result);
            
            // Log success
            $this->log_fulfillment_activity(
                $order->get_id(),
                $supplier,
                'create',
                'Order created successfully with supplier',
                $result['supplier_order_id'],
                $result['tracking_number']
            );
        } else {
            // Log failure
            $this->log_fulfillment_activity(
                $order->get_id(),
                $supplier,
                'create',
                'Failed to create order with supplier: ' . $result['error']
            );
        }
    }

    /**
     * Group order items by supplier.
     */
    private function group_items_by_supplier($order) {
        $items_by_supplier = array();
        
        foreach ($order->get_items() as $item_id => $item) {
            $product = $item->get_product();
            $supplier = $product->get_meta('_supplier');
            
            if (!$supplier) {
                $supplier = 'default'; // Fallback supplier
            }
            
            if (!isset($items_by_supplier[$supplier])) {
                $items_by_supplier[$supplier] = array();
            }
            
            $items_by_supplier[$supplier][] = array(
                'item_id' => $item_id,
                'product_id' => $product->get_id(),
                'supplier_product_id' => $product->get_meta('_supplier_product_id'),
                'quantity' => $item->get_quantity(),
                'price' => $item->get_total(),
            );
        }
        
        return $items_by_supplier;
    }

    /**
     * Save supplier order information.
     */
    private function save_supplier_order($order_id, $supplier, $items, $result) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'supplier_orders';
        
        foreach ($items as $item) {
            $wpdb->insert(
                $table_name,
                array(
                    'order_id' => $order_id,
                    'supplier' => $supplier,
                    'supplier_order_id' => $result['supplier_order_id'],
                    'supplier_product_id' => $item['supplier_product_id'],
                    'quantity' => $item['quantity'],
                    'unit_price' => $item['price'] / $item['quantity'],
                    'total_price' => $item['price'],
                    'currency' => $order->get_currency(),
                    'status' => 'pending',
                    'estimated_delivery' => date('Y-m-d', strtotime('+14 days')), // Default 14 days
                )
            );
        }
    }

    /**
     * Get order fulfillment status.
     */
    private function get_order_fulfillment_status($order_id) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'supplier_orders';
        
        $status = $wpdb->get_var(
            $wpdb->prepare(
                "SELECT status FROM $table_name WHERE order_id = %d ORDER BY created_at DESC LIMIT 1",
                $order_id
            )
        );
        
        return $status ? $status : 'pending';
    }

    /**
     * Get supplier orders for an order.
     */
    private function get_supplier_orders($order_id) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'supplier_orders';
        
        return $wpdb->get_results(
            $wpdb->prepare(
                "SELECT * FROM $table_name WHERE order_id = %d",
                $order_id
            )
        );
    }

    /**
     * Log fulfillment activity.
     */
    private function log_fulfillment_activity($order_id, $supplier, $action, $message, $supplier_order_id = null, $tracking_number = null) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'order_fulfillment_log';
        
        $wpdb->insert(
            $table_name,
            array(
                'order_id' => $order_id,
                'supplier' => $supplier,
                'supplier_order_id' => $supplier_order_id,
                'tracking_number' => $tracking_number,
                'action' => $action,
                'status' => strpos($message, 'Failed') !== false ? 'error' : 'success',
                'message' => $message,
            )
        );
    }

    /**
     * Sync all tracking numbers (cron job).
     */
    public function sync_all_tracking() {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'supplier_orders';
        
        // Get orders that need tracking sync
        $orders = $wpdb->get_results(
            "SELECT DISTINCT order_id FROM $table_name 
            WHERE status IN ('pending', 'processing') 
            AND tracking_number IS NULL 
            AND created_at < DATE_SUB(NOW(), INTERVAL 1 HOUR)"
        );
        
        foreach ($orders as $order) {
            $this->sync_order_tracking($order->order_id);
        }
    }

    /**
     * Check all orders status (cron job).
     */
    public function check_all_orders_status() {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'supplier_orders';
        
        // Get active orders
        $orders = $wpdb->get_results(
            "SELECT DISTINCT order_id FROM $table_name 
            WHERE status IN ('pending', 'processing', 'shipped')"
        );
        
        foreach ($orders as $order) {
            $this->check_order_status($order->order_id);
        }
    }

    /**
     * Sync tracking for specific order.
     */
    private function sync_order_tracking($order_id) {
        $api = new Order_Fulfillment_API();
        $supplier_orders = $this->get_supplier_orders($order_id);
        
        foreach ($supplier_orders as $supplier_order) {
            $result = $api->get_tracking_info($supplier_order->supplier, $supplier_order->supplier_order_id);
            
            if ($result['success'] && !empty($result['tracking_number'])) {
                // Update tracking information
                $this->update_tracking_info($supplier_order->id, $result);
                
                // Send tracking notification
                $order = wc_get_order($order_id);
                $notifications = new Order_Fulfillment_Notifications();
                $notifications->send_tracking_notification($order, $result['tracking_number'], $result['tracking_url']);
            }
        }
    }

    /**
     * Check order status with suppliers.
     */
    private function check_order_status($order_id) {
        $api = new Order_Fulfillment_API();
        $supplier_orders = $this->get_supplier_orders($order_id);
        
        foreach ($supplier_orders as $supplier_order) {
            $result = $api->get_order_status($supplier_order->supplier, $supplier_order->supplier_order_id);
            
            if ($result['success']) {
                $this->update_supplier_order_status($supplier_order->id, $result['status']);
                
                // Send status change notifications
                if ($result['status'] !== $supplier_order->status) {
                    $order = wc_get_order($order_id);
                    $notifications = new Order_Fulfillment_Notifications();
                    $notifications->send_status_change_notification($order, $result['status']);
                }
            }
        }
    }

    /**
     * Update tracking information.
     */
    private function update_tracking_info($supplier_order_id, $tracking_info) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'supplier_orders';
        
        $wpdb->update(
            $table_name,
            array(
                'tracking_number' => $tracking_info['tracking_number'],
                'status' => 'shipped',
                'updated_at' => current_time('mysql'),
            ),
            array('id' => $supplier_order_id)
        );
    }

    /**
     * Update supplier order status.
     */
    private function update_supplier_order_status($supplier_order_id, $status) {
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'supplier_orders';
        
        $wpdb->update(
            $table_name,
            array(
                'status' => $status,
                'updated_at' => current_time('mysql'),
            ),
            array('id' => $supplier_order_id)
        );
    }

    /**
     * AJAX handler for manual order fulfillment.
     */
    public function ajax_manual_fulfill_order() {
        check_ajax_referer('order_fulfillment_nonce', 'nonce');
        
        if (!current_user_can('manage_woocommerce')) {
            wp_send_json_error('Permission denied');
        }

        $order_id = intval($_POST['order_id']);
        $supplier = sanitize_text_field($_POST['supplier']);
        
        $order = wc_get_order($order_id);
        if (!$order) {
            wp_send_json_error('Order not found');
        }

        $items_by_supplier = $this->group_items_by_supplier($order);
        
        if (!isset($items_by_supplier[$supplier])) {
            wp_send_json_error('No items found for this supplier');
        }

        $this->process_supplier_order($order, $supplier, $items_by_supplier[$supplier]);
        
        wp_send_json_success('Order fulfillment initiated');
    }

    /**
     * AJAX handler for syncing tracking.
     */
    public function ajax_sync_tracking() {
        check_ajax_referer('order_fulfillment_nonce', 'nonce');
        
        if (!current_user_can('manage_woocommerce')) {
            wp_send_json_error('Permission denied');
        }

        $order_id = intval($_POST['order_id']);
        $this->sync_order_tracking($order_id);
        
        wp_send_json_success('Tracking sync completed');
    }

    /**
     * AJAX handler for checking fulfillment status.
     */
    public function ajax_check_fulfillment_status() {
        check_ajax_referer('order_fulfillment_nonce', 'nonce');
        
        if (!current_user_can('manage_woocommerce')) {
            wp_send_json_error('Permission denied');
        }

        $order_id = intval($_POST['order_id']);
        $status = $this->get_order_fulfillment_status($order_id);
        $supplier_orders = $this->get_supplier_orders($order_id);
        
        wp_send_json_success(array(
            'status' => $status,
            'supplier_orders' => $supplier_orders,
        ));
    }

    /**
     * Add fulfillment meta box to order page.
     */
    public function add_fulfillment_meta_box() {
        add_meta_box(
            'order_fulfillment_meta_box',
            __('Order Fulfillment', 'order-fulfillment'),
            array($this, 'render_fulfillment_meta_box'),
            'shop_order',
            'normal',
            'high'
        );
    }

    /**
     * Render fulfillment meta box.
     */
    public function render_fulfillment_meta_box($post) {
        $order_id = $post->ID;
        $order = wc_get_order($order_id);
        
        if (!$order) {
            return;
        }

        $supplier_orders = $this->get_supplier_orders($order_id);
        $fulfillment_status = $this->get_order_fulfillment_status($order_id);
        
        include plugin_dir_path(__FILE__) . 'admin/templates/order-fulfillment-meta-box.php';
    }

    /**
     * Add fulfillment columns to orders list.
     */
    public function add_fulfillment_columns($columns) {
        $columns['fulfillment_status'] = __('Fulfillment', 'order-fulfillment');
        $columns['tracking_number'] = __('Tracking', 'order-fulfillment');
        return $columns;
    }

    /**
     * Render fulfillment columns.
     */
    public function render_fulfillment_columns($column, $post_id) {
        switch ($column) {
            case 'fulfillment_status':
                $status = $this->get_order_fulfillment_status($post_id);
                echo '<span class="fulfillment-status status-' . esc_attr($status) . '">' . esc_html(ucfirst($status)) . '</span>';
                break;
                
            case 'tracking_number':
                $supplier_orders = $this->get_supplier_orders($post_id);
                $tracking_numbers = array();
                
                foreach ($supplier_orders as $supplier_order) {
                    if (!empty($supplier_order->tracking_number)) {
                        $tracking_numbers[] = $supplier_order->tracking_number;
                    }
                }
                
                if (!empty($tracking_numbers)) {
                    echo implode(', ', array_map('esc_html', $tracking_numbers));
                } else {
                    echo '—';
                }
                break;
        }
    }
}

// Initialize the plugin
function order_fulfillment() {
    return Order_Fulfillment::instance();
}

// Let's go!
order_fulfillment();
