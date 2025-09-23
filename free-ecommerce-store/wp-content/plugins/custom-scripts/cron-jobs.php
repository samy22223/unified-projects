<?php
/**
 * Cron Jobs Manager for E-commerce Automation
 * Manages all automated tasks and scheduling
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Include WordPress functions
require_once('../../../wp-load.php');

class CronJobsManager {

    private $log_file;

    public function __construct() {
        $this->log_file = WP_CONTENT_DIR . '/logs/cron-jobs.log';
        $this->ensure_log_directory();
        $this->setup_cron_schedules();
    }

    private function ensure_log_directory() {
        $log_dir = dirname($this->log_file);
        if (!file_exists($log_dir)) {
            wp_mkdir_p($log_dir);
        }
    }

    private function log($message, $level = 'INFO') {
        $timestamp = date('Y-m-d H:i:s');
        $log_entry = "[$timestamp] [$level] $message\n";
        file_put_contents($this->log_file, $log_entry, FILE_APPEND);
    }

    /**
     * Setup custom cron schedules
     */
    private function setup_cron_schedules() {
        add_filter('cron_schedules', function($schedules) {
            $schedules['every_minute'] = [
                'interval' => 60,
                'display' => __('Every Minute')
            ];
            $schedules['every_5_minutes'] = [
                'interval' => 300,
                'display' => __('Every 5 Minutes')
            ];
            $schedules['every_15_minutes'] = [
                'interval' => 900,
                'display' => __('Every 15 Minutes')
            ];
            $schedules['twice_daily'] = [
                'interval' => 43200, // 12 hours
                'display' => __('Twice Daily')
            ];
            return $schedules;
        });
    }

    /**
     * Schedule all cron jobs
     */
    public function schedule_all_jobs() {
        $this->log("Scheduling all cron jobs");

        // Product import (hourly)
        if (!wp_next_scheduled('pinnacle_product_import')) {
            wp_schedule_event(time(), 'hourly', 'pinnacle_product_import');
            $this->log("Scheduled product import (hourly)");
        }

        // Stock sync (every 30 minutes)
        if (!wp_next_scheduled('pinnacle_stock_sync')) {
            wp_schedule_event(time(), 'every_30_minutes', 'pinnacle_stock_sync');
            $this->log("Scheduled stock sync (30 minutes)");
        }

        // Order fulfillment sync (every 15 minutes)
        if (!wp_next_scheduled('pinnacle_order_sync')) {
            wp_schedule_event(time(), 'every_15_minutes', 'pinnacle_order_sync');
            $this->log("Scheduled order sync (15 minutes)");
        }

        // AI agent daily tasks (daily at 2 AM)
        if (!wp_next_scheduled('pinnacle_ai_agent_daily')) {
            wp_schedule_event(strtotime('02:00:00'), 'daily', 'pinnacle_ai_agent_daily');
            $this->log("Scheduled AI agent daily tasks (2 AM)");
        }

        // Backup (weekly on Sunday at 3 AM)
        if (!wp_next_scheduled('pinnacle_weekly_backup')) {
            wp_schedule_event(strtotime('next Sunday 03:00:00'), 'weekly', 'pinnacle_weekly_backup');
            $this->log("Scheduled weekly backup (Sunday 3 AM)");
        }

        // Abandoned cart emails (every 6 hours)
        if (!wp_next_scheduled('pinnacle_abandoned_cart')) {
            wp_schedule_event(time(), 'every_6_hours', 'pinnacle_abandoned_cart');
            $this->log("Scheduled abandoned cart emails (6 hours)");
        }

        // Review request emails (daily at 10 AM)
        if (!wp_next_scheduled('pinnacle_review_requests')) {
            wp_schedule_event(strtotime('10:00:00'), 'daily', 'pinnacle_review_requests');
            $this->log("Scheduled review request emails (10 AM)");
        }

        // Clean old logs (weekly)
        if (!wp_next_scheduled('pinnacle_clean_logs')) {
            wp_schedule_event(strtotime('next Sunday 04:00:00'), 'weekly', 'pinnacle_clean_logs');
            $this->log("Scheduled log cleanup (Sunday 4 AM)");
        }

        $this->log("All cron jobs scheduled successfully");
    }

    /**
     * Unschedule all cron jobs
     */
    public function unschedule_all_jobs() {
        $this->log("Unscheduling all cron jobs");

        $jobs = [
            'pinnacle_product_import',
            'pinnacle_stock_sync',
            'pinnacle_order_sync',
            'pinnacle_ai_agent_daily',
            'pinnacle_weekly_backup',
            'pinnacle_abandoned_cart',
            'pinnacle_review_requests',
            'pinnacle_clean_logs'
        ];

        foreach ($jobs as $job) {
            $timestamp = wp_next_scheduled($job);
            if ($timestamp) {
                wp_unschedule_event($timestamp, $job);
                $this->log("Unscheduled $job");
            }
        }

        $this->log("All cron jobs unscheduled");
    }

    /**
     * Get cron jobs status
     */
    public function get_jobs_status() {
        $jobs = [
            'pinnacle_product_import' => 'Product Import',
            'pinnacle_stock_sync' => 'Stock Sync',
            'pinnacle_order_sync' => 'Order Sync',
            'pinnacle_ai_agent_daily' => 'AI Agent Daily',
            'pinnacle_weekly_backup' => 'Weekly Backup',
            'pinnacle_abandoned_cart' => 'Abandoned Cart',
            'pinnacle_review_requests' => 'Review Requests',
            'pinnacle_clean_logs' => 'Clean Logs'
        ];

        $status = [];

        foreach ($jobs as $hook => $name) {
            $next_run = wp_next_scheduled($hook);
            $status[$hook] = [
                'name' => $name,
                'next_run' => $next_run ? date('Y-m-d H:i:s', $next_run) : 'Not scheduled',
                'scheduled' => $next_run ? true : false
            ];
        }

        return $status;
    }

    /**
     * Run a specific job manually
     */
    public function run_job_manually($job_name) {
        $this->log("Running job manually: $job_name");

        switch ($job_name) {
            case 'product_import':
                $this->run_product_import();
                break;
            case 'stock_sync':
                $this->run_stock_sync();
                break;
            case 'order_sync':
                $this->run_order_sync();
                break;
            case 'ai_agent':
                $this->run_ai_agent();
                break;
            case 'backup':
                $this->run_backup();
                break;
            case 'abandoned_cart':
                $this->run_abandoned_cart();
                break;
            case 'review_requests':
                $this->run_review_requests();
                break;
            case 'clean_logs':
                $this->run_clean_logs();
                break;
            default:
                return ['error' => 'Unknown job name'];
        }

        return ['success' => true, 'job' => $job_name];
    }

    // Job execution methods
    private function run_product_import() {
        include_once WP_PLUGIN_DIR . '/custom-scripts/product-import.php';
        $importer = new ProductImporter();
        $result = $importer->run_import();
        $this->log("Product import completed: $result products imported");
    }

    private function run_stock_sync() {
        include_once WP_PLUGIN_DIR . '/custom-scripts/stock-sync.php';
        $sync = new StockSync();
        $result = $sync->run_sync();
        $this->log("Stock sync completed: " . json_encode($result));
    }

    private function run_order_sync() {
        include_once WP_PLUGIN_DIR . '/custom-scripts/order-fulfillment.php';
        $fulfillment = new OrderFulfillment();
        $result = $fulfillment->sync_tracking_info();
        $this->log("Order sync completed: $result orders updated");
    }

    private function run_ai_agent() {
        include_once WP_PLUGIN_DIR . '/custom-scripts/ai-agent.php';
        $ai_agent = new AIAgent();
        $ai_agent->run_daily_tasks();
        $this->log("AI agent daily tasks completed");
    }

    private function run_backup() {
        if (function_exists('updraft_backupnow_backup')) {
            updraft_backupnow_backup();
            $this->log("Backup initiated");
        } else {
            $this->log("UpdraftPlus not available for backup", 'WARNING');
        }
    }

    private function run_abandoned_cart() {
        // Send abandoned cart emails
        $this->send_abandoned_cart_emails();
        $this->log("Abandoned cart emails sent");
    }

    private function run_review_requests() {
        // Send review request emails for completed orders
        $this->send_review_request_emails();
        $this->log("Review request emails sent");
    }

    private function run_clean_logs() {
        // Clean old logs from various scripts
        include_once WP_PLUGIN_DIR . '/custom-scripts/stock-sync.php';
        $sync = new StockSync();
        $sync->clean_old_logs();

        // Clean other log files (keep last 30 days)
        $this->clean_old_log_files();
        $this->log("Old logs cleaned");
    }

    // Helper methods
    private function send_abandoned_cart_emails() {
        // Get carts abandoned in last 24 hours
        $abandoned_carts = $this->get_abandoned_carts(24);

        foreach ($abandoned_carts as $cart) {
            // Check if email already sent
            if (get_user_meta($cart['user_id'], 'abandoned_cart_email_sent', true)) {
                continue;
            }

            $this->send_abandoned_cart_email($cart);
            update_user_meta($cart['user_id'], 'abandoned_cart_email_sent', time());
        }
    }

    private function send_review_request_emails() {
        // Get completed orders from last 7 days that haven't received review requests
        $completed_orders = $this->get_completed_orders_for_review(7);

        foreach ($completed_orders as $order) {
            // Check if review email already sent
            if ($order->get_meta('review_email_sent')) {
                continue;
            }

            $this->send_review_request_email($order);
            $order->add_meta_data('review_email_sent', time());
            $order->save();
        }
    }

    private function get_abandoned_carts($hours) {
        // This would integrate with WooCommerce abandoned cart tracking
        // Simplified implementation
        return []; // Placeholder
    }

    private function get_completed_orders_for_review($days) {
        return wc_get_orders([
            'status' => 'completed',
            'date_completed' => '>' . strtotime("-{$days} days"),
            'meta_key' => 'review_email_sent',
            'meta_compare' => 'NOT EXISTS'
        ]);
    }

    private function send_abandoned_cart_email($cart) {
        // Implementation would send email using MailPoet or similar
        $this->log("Abandoned cart email sent to user {$cart['user_id']}");
    }

    private function send_review_request_email($order) {
        $email_template = file_get_contents(get_template_directory() . '/emails/review-request.html');
        $subject = 'How was your recent purchase?';

        $body = str_replace(
            ['{customer_name}', '{order_number}'],
            [$order->get_billing_first_name(), $order->get_order_number()],
            $email_template
        );

        wp_mail($order->get_billing_email(), $subject, $body, ['Content-Type: text/html; charset=UTF-8']);
    }

    private function clean_old_log_files() {
        $log_files = [
            WP_CONTENT_DIR . '/logs/product-import.log',
            WP_CONTENT_DIR . '/logs/order-fulfillment.log',
            WP_CONTENT_DIR . '/logs/ai-agent.log',
            $this->log_file
        ];

        $cutoff_time = strtotime('-30 days');

        foreach ($log_files as $log_file) {
            if (file_exists($log_file)) {
                $lines = file($log_file);
                $new_lines = [];

                foreach ($lines as $line) {
                    // Extract timestamp from log line
                    if (preg_match('/\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]/', $line, $matches)) {
                        $log_time = strtotime($matches[1]);
                        if ($log_time > $cutoff_time) {
                            $new_lines[] = $line;
                        }
                    } else {
                        $new_lines[] = $line; // Keep lines without timestamps
                    }
                }

                file_put_contents($log_file, implode('', $new_lines));
            }
        }
    }
}

// Hook into WordPress cron system
add_action('pinnacle_product_import', function() {
    $cron = new CronJobsManager();
    $cron->run_product_import();
});

add_action('pinnacle_stock_sync', function() {
    $cron = new CronJobsManager();
    $cron->run_stock_sync();
});

add_action('pinnacle_order_sync', function() {
    $cron = new CronJobsManager();
    $cron->run_order_sync();
});

add_action('pinnacle_ai_agent_daily', function() {
    $cron = new CronJobsManager();
    $cron->run_ai_agent();
});

add_action('pinnacle_weekly_backup', function() {
    $cron = new CronJobsManager();
    $cron->run_backup();
});

add_action('pinnacle_abandoned_cart', function() {
    $cron = new CronJobsManager();
    $cron->run_abandoned_cart();
});

add_action('pinnacle_review_requests', function() {
    $cron = new CronJobsManager();
    $cron->run_review_requests();
});

add_action('pinnacle_clean_logs', function() {
    $cron = new CronJobsManager();
    $cron->run_clean_logs();
});

// Admin interface functions
function pinnacle_cron_admin_page() {
    if (isset($_POST['schedule_jobs'])) {
        $cron = new CronJobsManager();
        $cron->schedule_all_jobs();
        echo '<div class="notice notice-success"><p>All cron jobs scheduled successfully!</p></div>';
    }

    if (isset($_POST['unschedule_jobs'])) {
        $cron = new CronJobsManager();
        $cron->unschedule_all_jobs();
        echo '<div class="notice notice-success"><p>All cron jobs unscheduled!</p></div>';
    }

    if (isset($_POST['run_job']) && isset($_POST['job_name'])) {
        $cron = new CronJobsManager();
        $result = $cron->run_job_manually($_POST['job_name']);
        if (isset($result['success'])) {
            echo '<div class="notice notice-success"><p>Job executed successfully!</p></div>';
        } else {
            echo '<div class="notice notice-error"><p>Job execution failed: ' . $result['error'] . '</p></div>';
        }
    }

    $cron = new CronJobsManager();
    $status = $cron->get_jobs_status();

    ?>
    <div class="wrap">
        <h1>Cron Jobs Manager</h1>

        <form method="post">
            <input type="submit" name="schedule_jobs" class="button button-primary" value="Schedule All Jobs">
            <input type="submit" name="unschedule_jobs" class="button button-secondary" value="Unschedule All Jobs">
        </form>

        <h2>Job Status</h2>
        <table class="wp-list-table widefat fixed striped">
            <thead>
                <tr>
                    <th>Job Name</th>
                    <th>Next Run</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($status as $hook => $job): ?>
                <tr>
                    <td><?php echo esc_html($job['name']); ?></td>
                    <td><?php echo esc_html($job['next_run']); ?></td>
                    <td>
                        <span class="dashicons dashicons-<?php echo $job['scheduled'] ? 'yes' : 'no'; ?>"></span>
                        <?php echo $job['scheduled'] ? 'Scheduled' : 'Not Scheduled'; ?>
                    </td>
                    <td>
                        <form method="post" style="display: inline;">
                            <input type="hidden" name="job_name" value="<?php echo esc_attr(str_replace('pinnacle_', '', $hook)); ?>">
                            <input type="submit" name="run_job" class="button button-small" value="Run Now">
                        </form>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
    <?php
}

// Add admin menu
add_action('admin_menu', function() {
    add_submenu_page(
        'tools.php',
        'Cron Jobs Manager',
        'Cron Jobs',
        'manage_options',
        'pinnacle-cron-jobs',
        'pinnacle_cron_admin_page'
    );
});

// Run setup if called directly
if (isset($_GET['setup_cron'])) {
    $cron = new CronJobsManager();
    $cron->schedule_all_jobs();

    if (wp_doing_ajax()) {
        wp_send_json(['success' => true, 'message' => 'Cron jobs scheduled']);
    } else {
        echo "Cron jobs scheduled successfully\n";
    }
}
?>