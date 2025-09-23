# Deployment Guide for Pinnacle Free E-commerce Store

## Prerequisites

1. **Free Domain**: Register at [Freenom](https://www.freenom.com/) (.tk/.ml/.ga/.cf/.gq)
2. **Free Hosting**: Sign up at [InfinityFree](https://www.infinityfree.com/)
3. **Free Email**: Use Gmail or hosting-provided email
4. **Google Account**: For Google Drive backups and Analytics

## Step 1: Domain and Hosting Setup

### 1.1 Register Domain
1. Go to Freenom.com
2. Search for available domain (e.g., mystore.tk)
3. Register for free (12 months, renewable)

### 1.2 Sign Up for Hosting
1. Go to InfinityFree.com
2. Create account with your Freenom domain
3. Note down FTP credentials and control panel access

### 1.3 Point Domain to Hosting
1. In InfinityFree control panel, go to "Addon Domains"
2. Add your Freenom domain
3. Update nameservers at Freenom:
   - ns1.epizy.com
   - ns2.epizy.com

## Step 2: WordPress Installation

### 2.1 Upload WordPress Files
```bash
# Download WordPress
wget https://wordpress.org/latest.zip
unzip latest.zip

# Upload via FTP or InfinityFree File Manager
# Upload entire wordpress/ folder contents to public_html/
```

### 2.2 Database Setup
1. In InfinityFree control panel → MySQL Databases
2. Create new database: `yourdomain_wp`
3. Create user and grant permissions
4. Note down credentials

### 2.3 WordPress Configuration
1. Rename `wp-config-sample.php` to `wp-config.php`
2. Edit database settings:
```php
define('DB_NAME', 'yourdomain_wp');
define('DB_USER', 'yourdomain_user');
define('DB_PASSWORD', 'your_password');
define('DB_HOST', 'sqlxxx.epizy.com'); // From InfinityFree
```

3. Complete WordPress installation at yourdomain.epizy.com

## Step 3: WooCommerce Setup

### 3.1 Install WooCommerce
1. In WordPress admin → Plugins → Add New
2. Search "WooCommerce" → Install & Activate
3. Run setup wizard
4. Configure store settings (currency, location, etc.)

### 3.2 Install Required Free Plugins
Install these plugins via WordPress admin:

**Dropshipping:**
- DSers
- CJDropshipping
- Spocket

**Marketing:**
- MailPoet
- Tidio Chat
- Revive Old Posts

**Security:**
- Wordfence Security
- Limit Login Attempts Reloaded

**Performance:**
- WP Super Cache
- Smush
- Rank Math SEO

**Other:**
- UpdraftPlus
- WooCommerce PDF Invoices
- WooCommerce Table Rate Shipping (free)

## Step 4: Upload Custom Files

### 4.1 Upload Scripts
Upload these files to `wp-content/plugins/custom-scripts/`:
- `product-import.php`
- `order-fulfillment.php`
- `stock-sync.php`
- `ai-agent.php`
- `cron-jobs.php`

### 4.2 Upload Templates
- Email templates to `wp-content/themes/yourtheme/emails/`
- Invoice template to `wp-content/themes/yourtheme/invoices/`
- CSV template for reference

### 4.3 Upload Theme Customizations
Upload custom theme files to `wp-content/themes/yourtheme/`

## Step 5: API Keys and Configuration

### 5.1 Supplier API Keys
Configure in respective plugins:
- DSers: Get API key from DSers dashboard
- CJDropshipping: API credentials
- Spocket: API token

### 5.2 Google Services
- Google Analytics: Get tracking ID
- Google Drive: For UpdraftPlus backups
- Search Console: Verify domain

### 5.3 AI Services (Free Tiers)
- OpenAI: Free tier API key (if available)
- Alternative: Use free AI APIs or local models

### 5.4 Other Services
- Cloudflare: Sign up, add domain, enable SSL
- Hotjar: Free account for heatmaps

## Step 6: Cron Jobs Setup

### 6.1 InfinityFree Cron Jobs
In control panel → Cron Jobs:
```
# Product sync (hourly)
0 * * * * wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/stock-sync.php

# Order tracking sync (hourly)
30 * * * * wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/order-fulfillment.php

# AI content update (daily)
0 2 * * * wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/ai-agent.php?action=content

# Backup (weekly)
0 3 * * 0 wget -q -O /dev/null https://yourdomain.epizy.com/wp-admin/admin-ajax.php?action=updraft_backupnow&backupnow_nonce=xxx
```

## Step 7: Security Configuration

### 7.1 Wordfence Setup
1. Activate Wordfence
2. Run scan
3. Configure firewall rules
4. Set up login security

### 7.2 Cloudflare Configuration
1. Add domain to Cloudflare
2. Enable SSL (Full/Strict)
3. Configure firewall rules
4. Set up CDN

### 7.3 Additional Security
1. Change default admin username
2. Use strong passwords
3. Enable two-factor authentication
4. Configure backup encryption

## Step 8: Performance Optimization

### 8.1 Caching
1. Activate WP Super Cache
2. Configure caching rules

### 8.2 Image Optimization
1. Activate Smush
2. Bulk optimize existing images
3. Enable auto-optimization

### 8.3 SEO Setup
1. Activate Rank Math
2. Configure SEO settings
3. Submit sitemap to Google

## Step 9: Testing and Launch

### 9.1 Test Functionality
- Product import automation
- Order placement
- Payment processing (test mode)
- Email notifications
- Chatbot responses

### 9.2 Go Live
1. Switch payments to live mode
2. Update domain DNS if needed
3. Monitor initial orders
4. Set up customer support

## Troubleshooting

### Common Issues
1. **Plugin Conflicts**: Deactivate and test individually
2. **Cron Jobs Not Running**: Check InfinityFree logs
3. **API Errors**: Verify API keys and endpoints
4. **SSL Issues**: Ensure Cloudflare configuration

### Support Resources
- WordPress Codex
- WooCommerce Docs
- InfinityFree Forums
- Plugin documentation

## Maintenance

### Weekly Tasks
- Check security scans
- Review analytics
- Update plugins/themes
- Monitor backups

### Monthly Tasks
- Review performance metrics
- Optimize database
- Update API keys if needed
- Check supplier integrations