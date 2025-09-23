<?php
/**
 * AI Agent for E-commerce Automation
 * Monitors security, generates content, analyzes trends
 * Runs via cron job or manual execution
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Include WordPress functions
require_once('../../../wp-load.php');

class AIAgent {

    private $openai_key;
    private $huggingface_key;
    private $log_file;

    public function __construct() {
        $this->openai_key = getenv('OPENAI_API_KEY') ?: OPENAI_API_KEY;
        $this->huggingface_key = getenv('HUGGINGFACE_API_KEY') ?: HUGGINGFACE_API_KEY;
        $this->log_file = WP_CONTENT_DIR . '/logs/ai-agent.log';
        $this->ensure_log_directory();
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
     * Main AI agent runner
     */
    public function run_daily_tasks() {
        $this->log("Starting daily AI agent tasks");

        try {
            // Security monitoring
            $this->monitor_security();

            // Content generation
            $this->generate_blog_content();

            // SEO optimization
            $this->optimize_seo();

            // Marketing analysis
            $this->analyze_marketing_performance();

            // Trend analysis
            $this->analyze_trends();

            $this->log("Daily AI agent tasks completed");

        } catch (Exception $e) {
            $this->log("AI agent error: " . $e->getMessage(), 'ERROR');
        }
    }

    /**
     * Monitor security and system health
     */
    private function monitor_security() {
        $this->log("Running security monitoring");

        // Check for suspicious file changes
        $suspicious_files = $this->scan_for_suspicious_files();
        if (!empty($suspicious_files)) {
            $this->alert_admin("Suspicious files detected", $suspicious_files);
        }

        // Check plugin vulnerabilities
        $vulnerable_plugins = $this->check_plugin_vulnerabilities();
        if (!empty($vulnerable_plugins)) {
            $this->alert_admin("Plugin vulnerabilities found", $vulnerable_plugins);
        }

        // Monitor failed login attempts
        $failed_logins = $this->get_failed_login_attempts();
        if ($failed_logins > 10) {
            $this->alert_admin("High number of failed login attempts", "Count: $failed_logins");
        }

        // Check for unauthorized admin users
        $unauthorized_admins = $this->check_unauthorized_admins();
        if (!empty($unauthorized_admins)) {
            $this->alert_admin("Unauthorized admin users detected", $unauthorized_admins);
        }
    }

    /**
     * Generate blog content for SEO
     */
    private function generate_blog_content() {
        $this->log("Generating blog content");

        // Get trending products
        $trending_products = $this->get_trending_products();

        foreach ($trending_products as $product) {
            $existing_post = $this->check_existing_blog_post($product['category']);

            if (!$existing_post) {
                $blog_content = $this->generate_blog_post($product);
                if ($blog_content) {
                    $this->create_blog_post($blog_content);
                }
            }
        }
    }

    /**
     * Optimize SEO for products and content
     */
    private function optimize_seo() {
        $this->log("Running SEO optimization");

        // Analyze product titles and descriptions
        $products = $this->get_products_needing_seo();
        foreach ($products as $product) {
            $seo_suggestions = $this->analyze_product_seo($product);
            if ($seo_suggestions) {
                $this->apply_seo_improvements($product, $seo_suggestions);
            }
        }

        // Check meta descriptions
        $this->optimize_meta_descriptions();

        // Generate internal linking suggestions
        $this->suggest_internal_links();
    }

    /**
     * Analyze marketing performance
     */
    private function analyze_marketing_performance() {
        $this->log("Analyzing marketing performance");

        // Analyze email campaign performance
        $email_performance = $this->analyze_email_campaigns();
        if ($email_performance['open_rate'] < 20) {
            $this->suggest_email_improvements($email_performance);
        }

        // Analyze abandoned cart patterns
        $cart_analysis = $this->analyze_abandoned_carts();
        $this->optimize_abandoned_cart_emails($cart_analysis);

        // Product recommendation analysis
        $this->analyze_product_recommendations();
    }

    /**
     * Analyze market trends
     */
    private function analyze_trends() {
        $this->log("Analyzing market trends");

        $categories = $this->get_product_categories();

        foreach ($categories as $category) {
            $trends = $this->get_category_trends($category);
            if ($trends) {
                $this->update_category_strategy($category, $trends);
            }
        }
    }

    // Security monitoring methods
    private function scan_for_suspicious_files() {
        $suspicious = [];
        $upload_dir = wp_upload_dir()['basedir'];

        // Scan for common malware patterns
        $suspicious_patterns = [
            'base64_decode',
            'eval(',
            'shell_exec',
            'system(',
            'passthru('
        ];

        $files = $this->scan_directory($upload_dir);
        foreach ($files as $file) {
            if (pathinfo($file, PATHINFO_EXTENSION) === 'php') {
                $content = file_get_contents($file);
                foreach ($suspicious_patterns as $pattern) {
                    if (strpos($content, $pattern) !== false) {
                        $suspicious[] = $file;
                        break;
                    }
                }
            }
        }

        return $suspicious;
    }

    private function check_plugin_vulnerabilities() {
        $vulnerable = [];

        if (!function_exists('get_plugins')) {
            require_once ABSPATH . 'wp-admin/includes/plugin.php';
        }

        $plugins = get_plugins();

        foreach ($plugins as $plugin_file => $plugin_data) {
            // Check against vulnerability database (simplified)
            $vulnerability_check = $this->check_vulnerability_database($plugin_data['Name'], $plugin_data['Version']);
            if ($vulnerability_check) {
                $vulnerable[] = [
                    'plugin' => $plugin_data['Name'],
                    'version' => $plugin_data['Version'],
                    'vulnerability' => $vulnerability_check
                ];
            }
        }

        return $vulnerable;
    }

    private function get_failed_login_attempts() {
        global $wpdb;
        $table_name = $wpdb->prefix . 'limit_login_attempts';

        if ($wpdb->get_var("SHOW TABLES LIKE '$table_name'") == $table_name) {
            return $wpdb->get_var("SELECT COUNT(*) FROM $table_name WHERE failed_attempts > 0");
        }

        return 0;
    }

    private function check_unauthorized_admins() {
        $unauthorized = [];

        $admins = get_users(['role' => 'administrator']);

        foreach ($admins as $admin) {
            // Check if admin was created recently and has suspicious activity
            $recent_posts = count_user_posts($admin->ID);
            $account_age = (time() - strtotime($admin->user_registered)) / (60*60*24); // days

            if ($account_age < 7 && $recent_posts > 10) {
                $unauthorized[] = $admin->user_login;
            }
        }

        return $unauthorized;
    }

    // Content generation methods
    private function get_trending_products() {
        // Get products with high views or sales in last 30 days
        $args = [
            'post_type' => 'product',
            'posts_per_page' => 5,
            'meta_query' => [
                [
                    'key' => 'total_sales',
                    'value' => '0',
                    'compare' => '>'
                ]
            ],
            'orderby' => 'meta_value_num',
            'meta_key' => 'total_sales',
            'order' => 'DESC'
        ];

        $products = get_posts($args);
        $trending = [];

        foreach ($products as $product) {
            $trending[] = [
                'id' => $product->ID,
                'title' => $product->post_title,
                'category' => wp_get_post_terms($product->ID, 'product_cat')[0]->name ?? 'General'
            ];
        }

        return $trending;
    }

    private function generate_blog_post($product) {
        $prompt = "Write a comprehensive blog post about {$product['title']} in the {$product['category']} category. Include SEO keywords, benefits, and buying guide. Make it engaging and informative.";

        $content = $this->call_ai_api($prompt, 800);

        if ($content) {
            return [
                'title' => "The Ultimate Guide to {$product['title']}",
                'content' => $content,
                'category' => $product['category'],
                'seo_title' => $this->generate_seo_title("Guide to {$product['title']}"),
                'meta_description' => substr($content, 0, 155) . '...'
            ];
        }

        return false;
    }

    private function create_blog_post($post_data) {
        $post_id = wp_insert_post([
            'post_title' => $post_data['title'],
            'post_content' => $post_data['content'],
            'post_status' => 'publish',
            'post_author' => 1,
            'post_category' => [get_cat_ID($post_data['category'])]
        ]);

        if ($post_id) {
            // Add SEO meta
            update_post_meta($post_id, '_yoast_wpseo_title', $post_data['seo_title']);
            update_post_meta($post_id, '_yoast_wpseo_metadesc', $post_data['meta_description']);

            $this->log("Created blog post: {$post_data['title']}");
        }
    }

    // AI API calls
    private function call_ai_api($prompt, $max_tokens = 500) {
        // Try OpenAI first
        if ($this->openai_key && $this->openai_key !== 'your_openai_key') {
            return $this->call_openai($prompt, $max_tokens);
        }

        // Fallback to Hugging Face
        if ($this->huggingface_key && $this->huggingface_key !== 'your_huggingface_key') {
            return $this->call_huggingface($prompt, $max_tokens);
        }

        return false;
    }

    private function call_openai($prompt, $max_tokens) {
        $data = [
            'model' => 'gpt-3.5-turbo',
            'messages' => [['role' => 'user', 'content' => $prompt]],
            'max_tokens' => $max_tokens,
            'temperature' => 0.7
        ];

        $response = wp_remote_post('https://api.openai.com/v1/chat/completions', [
            'headers' => [
                'Authorization' => 'Bearer ' . $this->openai_key,
                'Content-Type' => 'application/json'
            ],
            'body' => json_encode($data),
            'timeout' => 30
        ]);

        if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
            $body = json_decode(wp_remote_retrieve_body($response), true);
            return $body['choices'][0]['message']['content'];
        }

        return false;
    }

    private function call_huggingface($prompt, $max_length) {
        $response = wp_remote_post('https://api-inference.huggingface.co/models/gpt2', [
            'headers' => [
                'Authorization' => 'Bearer ' . $this->huggingface_key,
                'Content-Type' => 'application/json'
            ],
            'body' => json_encode([
                'inputs' => $prompt,
                'parameters' => [
                    'max_length' => $max_length,
                    'temperature' => 0.7
                ]
            ]),
            'timeout' => 30
        ]);

        if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
            $body = json_decode(wp_remote_retrieve_body($response), true);
            return is_array($body) ? $body[0]['generated_text'] : $body['generated_text'];
        }

        return false;
    }

    // Alert system
    private function alert_admin($subject, $details) {
        $admin_email = get_option('admin_email');
        $site_name = get_bloginfo('name');

        $message = "Alert from AI Agent at $site_name\n\n";
        $message .= "Subject: $subject\n\n";
        $message .= "Details:\n" . (is_array($details) ? json_encode($details, JSON_PRETTY_PRINT) : $details);
        $message .= "\n\nPlease review immediately.\n\nAI Agent";

        wp_mail($admin_email, "AI Agent Alert: $subject", $message);
        $this->log("Admin alert sent: $subject");
    }

    // Helper methods
    private function scan_directory($dir) {
        $files = [];
        if (is_dir($dir)) {
            $iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($dir));
            foreach ($iterator as $file) {
                if ($file->isFile()) {
                    $files[] = $file->getPathname();
                }
            }
        }
        return $files;
    }

    private function check_vulnerability_database($plugin_name, $version) {
        // Simplified vulnerability check - in real implementation, use WPScan API or similar
        return false; // Placeholder
    }

    private function check_existing_blog_post($category) {
        $args = [
            'post_type' => 'post',
            'category_name' => $category,
            'posts_per_page' => 1,
            'date_query' => [
                'after' => '1 week ago'
            ]
        ];

        $posts = get_posts($args);
        return !empty($posts);
    }

    private function generate_seo_title($base_title) {
        return $this->call_ai_api("Create an SEO-optimized title for: $base_title (under 60 characters)", 50);
    }
}

// Run daily tasks if called directly
if (isset($_GET['run_daily']) || defined('DOING_CRON')) {
    $ai_agent = new AIAgent();
    $ai_agent->run_daily_tasks();

    if (wp_doing_ajax()) {
        wp_send_json(['success' => true, 'message' => 'AI agent tasks completed']);
    } else {
        echo "AI agent daily tasks completed\n";
    }
}
?>