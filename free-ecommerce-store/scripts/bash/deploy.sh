#!/bin/bash

# Pinnacle Free E-commerce Store Deployment Script
# This script automates the deployment of the entire e-commerce system

set -e  # Exit on any error

# Configuration - Update these values
DOMAIN="yourdomain.epizy.com"
DB_NAME="yourdomain_wp"
DB_USER="yourdomain_user"
DB_PASS="your_password"
DB_HOST="sqlxxx.epizy.com"
WP_ADMIN_USER="admin"
WP_ADMIN_PASS="secure_password_123"
WP_ADMIN_EMAIL="admin@yourdomain.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v wget &> /dev/null; then
        error "wget is required but not installed. Please install wget."
        exit 1
    fi

    if ! command -v unzip &> /dev/null; then
        error "unzip is required but not installed. Please install unzip."
        exit 1
    fi

    log "Prerequisites check passed."
}

# Create project directory structure
create_directory_structure() {
    log "Creating directory structure..."

    mkdir -p free-ecommerce-store
    cd free-ecommerce-store

    # Create all necessary directories
    mkdir -p wp-content/plugins/custom-scripts
    mkdir -p wp-content/themes/custom-theme
    mkdir -p wp-content/themes/custom-theme/templates
    mkdir -p wp-content/themes/custom-theme/emails
    mkdir -p wp-content/themes/custom-theme/invoices
    mkdir -p wp-content/uploads
    mkdir -p wp-content/mu-plugins
    mkdir -p scripts/python
    mkdir -p scripts/bash
    mkdir -p templates/emails
    mkdir -p templates/invoices
    mkdir -p templates/csv
    mkdir -p config
    mkdir -p docs

    log "Directory structure created."
}

# Download and setup WordPress
setup_wordpress() {
    log "Setting up WordPress..."

    # Download WordPress
    if [ ! -f "latest.zip" ]; then
        wget https://wordpress.org/latest.zip
    fi

    # Extract WordPress
    unzip -q latest.zip

    # Move WordPress files to current directory
    mv wordpress/* .
    rm -rf wordpress latest.zip

    # Create wp-config.php
    cp config/wp-config-sample.php wp-config.php

    # Update wp-config.php with database details
    sed -i "s/database_name_here/$DB_NAME/" wp-config.php
    sed -i "s/username_here/$DB_USER/" wp-config.php
    sed -i "s/password_here/$DB_PASS/" wp-config.php
    sed -i "s/localhost/$DB_HOST/" wp-config.php

    # Add custom configurations
    cat >> wp-config.php << 'EOF'

// Custom configurations for Pinnacle Store
define('WP_AUTO_UPDATE_CORE', true);
define('DISALLOW_FILE_EDIT', true);
define('FORCE_SSL_ADMIN', true);

// API Keys (update with your actual keys)
define('DSERS_API_KEY', 'your_dsers_api_key');
define('CJD_API_KEY', 'your_cjd_api_key');
define('CJD_API_SECRET', 'your_cjd_api_secret');
define('SPOCKET_API_KEY', 'your_spocket_api_key');
define('OPENAI_API_KEY', 'your_openai_api_key');
define('HUGGINGFACE_API_KEY', 'your_huggingface_api_key');

// WooCommerce settings
define('WC_MAX_LINKED_VARIATIONS', 50);

// Performance settings
define('WP_CACHE', true);
define('DISABLE_WP_EMOJI', true);
define('DISABLE_WP_EMBED', true);
EOF

    log "WordPress setup completed."
}

# Copy custom files
copy_custom_files() {
    log "Copying custom files..."

    # Copy custom scripts
    cp wp-content/plugins/custom-scripts/*.php wp-content/plugins/custom-scripts/

    # Copy theme files
    cp wp-content/themes/custom-theme/* wp-content/themes/custom-theme/

    # Copy email templates
    cp templates/emails/* wp-content/themes/custom-theme/emails/

    # Copy invoice templates
    cp templates/invoices/* wp-content/themes/custom-theme/invoices/

    # Copy CSV template
    cp templates/csv/* .

    # Copy configuration files
    cp config/.htaccess .
    cp config/robots.txt .

    log "Custom files copied."
}

# Install required plugins
install_plugins() {
    log "Installing required plugins..."

    # Create plugins directory if it doesn't exist
    mkdir -p wp-content/plugins

    # Note: In a real deployment, you would download these plugins
    # For now, we'll create placeholders and instructions

    cat > wp-content/plugins/README.md << 'EOF'
# Required Plugins Installation

Install these plugins via WordPress admin or manually:

## Free Plugins (Required)
1. WooCommerce - https://wordpress.org/plugins/woocommerce/
2. DSers - Download from DSers website
3. CJDropshipping - Download from CJDropshipping website
4. Spocket - Download from Spocket website
5. MailPoet - https://wordpress.org/plugins/mailpoet/
6. Tidio Chat - https://wordpress.org/plugins/tidio-chat/
7. Revive Old Posts - https://wordpress.org/plugins/tweet-old-post/
8. Wordfence Security - https://wordpress.org/plugins/wordfence/
9. Limit Login Attempts Reloaded - https://wordpress.org/plugins/limit-login-attempts-reloaded/
10. WP Super Cache - https://wordpress.org/plugins/wp-super-cache/
11. Smush - https://wordpress.org/plugins/wp-smushit/
12. Rank Math SEO - https://wordpress.org/plugins/seo-by-rank-math/
13. UpdraftPlus - https://wordpress.org/plugins/updraftplus/
14. WooCommerce PDF Invoices - https://wordpress.org/plugins/woocommerce-pdf-invoices/
15. WooCommerce Table Rate Shipping - https://wordpress.org/plugins/table-rate-shipping-for-woocommerce/

## Installation Steps:
1. Download each plugin
2. Upload to wp-content/plugins/ via FTP
3. Activate in WordPress admin
4. Configure API keys and settings
EOF

    log "Plugin installation instructions created."
}

# Setup cron jobs
setup_cron_jobs() {
    log "Setting up cron jobs..."

    # Create cron setup script
    cat > setup-cron.sh << 'EOF'
#!/bin/bash
# Cron Jobs Setup for InfinityFree

# Product import (hourly)
wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/product-import.php?run_import=1

# Stock sync (every 30 minutes)
wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/stock-sync.php?run_sync=1

# Order fulfillment (every 15 minutes)
wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/order-fulfillment.php?sync_tracking=1

# AI agent daily tasks (daily at 2 AM)
wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/ai-agent.php?run_daily=1

# Abandoned cart emails (every 6 hours)
wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/cron-jobs.php?run_abandoned_cart=1

# Review requests (daily at 10 AM)
wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/cron-jobs.php?run_review_requests=1

# Weekly backup (Sunday at 3 AM)
wget -q -O /dev/null https://yourdomain.epizy.com/wp-admin/admin-ajax.php?action=updraft_backupnow&backupnow_nonce=xxx

# Clean logs (weekly Sunday at 4 AM)
wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/cron-jobs.php?run_clean_logs=1
EOF

    chmod +x setup-cron.sh

    log "Cron jobs setup script created."
}

# Create deployment package
create_deployment_package() {
    log "Creating deployment package..."

    # Create tar archive of all files
    cd ..
    tar -czf free-ecommerce-store-deployment.tar.gz free-ecommerce-store/

    log "Deployment package created: free-ecommerce-store-deployment.tar.gz"
}

# Generate final instructions
generate_instructions() {
    log "Generating final deployment instructions..."

    cat > DEPLOYMENT_INSTRUCTIONS.md << 'EOF'
# Final Deployment Instructions

## 1. Upload Files to Hosting
1. Extract `free-ecommerce-store-deployment.tar.gz`
2. Upload all files to your InfinityFree public_html directory
3. Set proper permissions (755 for directories, 644 for files)

## 2. Complete WordPress Installation
1. Visit yourdomain.epizy.com
2. Complete WordPress installation
3. Set admin username/password as configured

## 3. Install and Configure Plugins
1. Install all required plugins listed in wp-content/plugins/README.md
2. Configure WooCommerce store settings
3. Set up API keys for suppliers and services

## 4. Configure Domain and SSL
1. Point your Freenom domain to InfinityFree nameservers
2. Enable Cloudflare SSL and CDN
3. Update site URL in WordPress settings

## 5. Set Up Cron Jobs
1. In InfinityFree control panel, go to Cron Jobs
2. Add the cron commands from setup-cron.sh
3. Test cron jobs manually first

## 6. Import Initial Products
1. Use the product-import.py script or CSV import
2. Configure supplier integrations
3. Test product sync

## 7. Configure AI Services
1. Set up OpenAI or Hugging Face API keys
2. Test AI content generation
3. Configure automated tasks

## 8. Security Setup
1. Enable Wordfence firewall
2. Configure backup settings
3. Set up monitoring alerts

## 9. Testing
1. Test product purchases
2. Verify order fulfillment
3. Check email notifications
4. Test all automated features

## 10. Go Live
1. Switch to live payment methods
2. Enable all cron jobs
3. Monitor system performance
4. Set up customer support

## Important Notes
- Keep all API keys secure
- Regularly update WordPress and plugins
- Monitor server resources on InfinityFree
- Backup regularly using UpdraftPlus
- Test all features before going live

## Support
- Check logs in wp-content/logs/
- Monitor cron job execution
- Use WordPress debug mode for troubleshooting
EOF

    log "Deployment instructions generated."
}

# Main deployment function
main() {
    echo "========================================"
    echo "Pinnacle Free E-commerce Store Deployment"
    echo "========================================"

    check_prerequisites
    create_directory_structure
    setup_wordpress
    copy_custom_files
    install_plugins
    setup_cron_jobs
    create_deployment_package
    generate_instructions

    echo ""
    log "Deployment preparation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Upload the deployment package to your hosting"
    echo "2. Follow DEPLOYMENT_INSTRUCTIONS.md"
    echo "3. Configure API keys and settings"
    echo "4. Test all functionality"
    echo ""
    warning "Remember to update all placeholder values with your actual credentials!"
}

# Run main function
main "$@"