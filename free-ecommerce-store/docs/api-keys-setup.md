# API Keys and Configuration Setup

## Required API Keys and Services

### 1. Supplier APIs

#### DSers
- **Website**: https://dsers.com
- **API Key**: Get from DSers dashboard → Settings → API
- **Configuration**: Add to `wp-config.php` as `DSERS_API_KEY`

#### CJDropshipping
- **Website**: https://cjdropshipping.com
- **API Key**: Get from CJDropshipping dashboard → API Settings
- **API Secret**: Required for authentication
- **Configuration**: Add to `wp-config.php` as `CJD_API_KEY` and `CJD_API_SECRET`

#### Spocket
- **Website**: https://spocket.co
- **API Key**: Get from Spocket dashboard → Integrations → API
- **Configuration**: Add to `wp-config.php` as `SPOCKET_API_KEY`

### 2. AI Services (Free Tiers)

#### OpenAI (Primary)
- **Website**: https://platform.openai.com
- **API Key**: Create account → API Keys → Create new key
- **Free Tier**: $5 credit for new accounts
- **Configuration**: Add to `wp-config.php` as `OPENAI_API_KEY`
- **Usage**: Product descriptions, SEO titles, marketing content

#### Hugging Face (Fallback)
- **Website**: https://huggingface.co
- **API Key**: Sign up → Settings → API Tokens
- **Free Tier**: Unlimited for public models
- **Configuration**: Add to `wp-config.php` as `HUGGINGFACE_API_KEY`
- **Usage**: Backup AI service when OpenAI quota exceeded

### 3. Google Services

#### Google Analytics 4
- **Website**: https://analytics.google.com
- **Tracking ID**: Create property → Admin → Data Streams → Web → Measurement ID
- **Configuration**: Add to `wp-config.php` as `GOOGLE_ANALYTICS_ID`

#### Google Search Console
- **Website**: https://search.google.com/search-console
- **Key**: Add property → Verify ownership → Get verification code
- **Configuration**: Add to `wp-config.php` as `GOOGLE_SEARCH_CONSOLE_KEY`

#### Google Drive (for Backups)
- **Website**: https://drive.google.com
- **Setup**: Create account → Enable API → Get credentials
- **Configuration**: Configure in UpdraftPlus plugin

### 4. Marketing Services

#### MailPoet
- **Website**: https://www.mailpoet.com
- **API Key**: Sign up → Settings → API Keys
- **Configuration**: Add to `wp-config.php` as `MAILPOET_API_KEY`

#### Tidio Chat
- **Website**: https://www.tidio.com
- **API Key**: Sign up → Settings → Developers → API Keys
- **Configuration**: Add to `wp-config.php` as `TIDIO_API_KEY`

### 5. Analytics Services

#### Hotjar
- **Website**: https://www.hotjar.com
- **API Key**: Sign up → Settings → Organizations → Sites → Get code
- **Free Plan**: 35 sessions/day, 3 heatmaps/month

## Configuration Steps

### 1. Update wp-config.php
```php
// Supplier APIs
define('DSERS_API_KEY', 'your_dsers_key_here');
define('CJD_API_KEY', 'your_cjd_key_here');
define('CJD_API_SECRET', 'your_cjd_secret_here');
define('SPOCKET_API_KEY', 'your_spocket_key_here');

// AI Services
define('OPENAI_API_KEY', 'your_openai_key_here');
define('HUGGINGFACE_API_KEY', 'your_huggingface_key_here');

// Google Services
define('GOOGLE_ANALYTICS_ID', 'GA-XXXXXXXXXX');
define('GOOGLE_SEARCH_CONSOLE_KEY', 'your_gsc_key_here');

// Marketing
define('MAILPOET_API_KEY', 'your_mailpoet_key_here');
define('TIDIO_API_KEY', 'your_tidio_key_here');
```

### 2. Plugin Configuration

#### WooCommerce
1. Install and activate WooCommerce
2. Run setup wizard
3. Configure store settings:
   - Store name and address
   - Currency: USD/EUR
   - Payment methods: PayPal/Stripe (test mode first)

#### Supplier Plugins
1. **DSers**: Enter API key in plugin settings
2. **CJDropshipping**: Configure API credentials
3. **Spocket**: Add API token and select regions

#### Security Plugins
1. **Wordfence**: Run initial scan, configure firewall
2. **Limit Login Attempts**: Set lockout thresholds

#### Performance Plugins
1. **WP Super Cache**: Enable caching
2. **Smush**: Enable automatic compression
3. **Rank Math**: Connect Google services

#### Marketing Plugins
1. **MailPoet**: Configure SMTP settings
2. **Tidio**: Set up chatbot responses
3. **Revive Old Posts**: Configure social media accounts

### 3. Cron Jobs Setup

In InfinityFree control panel → Cron Jobs:

```
# Product import (hourly)
0 * * * * wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/product-import.php?run_import=1

# Stock sync (every 30 minutes)
*/30 * * * * wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/stock-sync.php?run_sync=1

# Order fulfillment (every 15 minutes)
*/15 * * * * wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/order-fulfillment.php?sync_tracking=1

# AI agent daily tasks (daily at 2 AM)
0 2 * * * wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/ai-agent.php?run_daily=1

# Abandoned cart emails (every 6 hours)
0 */6 * * * wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/cron-jobs.php?run_abandoned_cart=1

# Review requests (daily at 10 AM)
0 10 * * * wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/cron-jobs.php?run_review_requests=1

# Weekly backup (Sunday at 3 AM)
0 3 * * 0 wget -q -O /dev/null https://yourdomain.epizy.com/wp-admin/admin-ajax.php?action=updraft_backupnow&backupnow_nonce=xxx

# Clean logs (weekly Sunday at 4 AM)
0 4 * * 0 wget -q -O /dev/null https://yourdomain.epizy.com/wp-content/plugins/custom-scripts/cron-jobs.php?run_clean_logs=1
```

### 4. Testing API Connections

#### Test Supplier APIs
```bash
# Test DSers connection
curl -H "Authorization: Bearer YOUR_DSERS_KEY" https://api.dsers.com/v1/products?limit=1

# Test CJD connection
curl -H "Authorization: Bearer YOUR_CJD_KEY" -H "X-Timestamp: $(date +%s)" -H "X-Signature: YOUR_SIGNATURE" https://api.cjdropshipping.com/v1/products?limit=1

# Test Spocket connection
curl -H "Authorization: Bearer YOUR_SPOCKET_KEY" https://api.spocket.co/v1/products?limit=1
```

#### Test AI APIs
```bash
# Test OpenAI
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_OPENAI_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'

# Test Hugging Face
curl -X POST https://api-inference.huggingface.co/models/gpt2 \
  -H "Authorization: Bearer YOUR_HF_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello world", "parameters": {"max_length": 20}}'
```

### 5. Security Best Practices

1. **API Key Security**
   - Never commit API keys to version control
   - Use environment variables when possible
   - Rotate keys regularly
   - Monitor API usage for anomalies

2. **WordPress Security**
   - Keep WordPress and plugins updated
   - Use strong passwords
   - Enable two-factor authentication
   - Regular security scans with Wordfence

3. **Server Security**
   - Use HTTPS everywhere
   - Configure Cloudflare WAF rules
   - Monitor for suspicious activity
   - Regular backups

### 6. Monitoring and Alerts

#### AI Agent Monitoring
The AI agent automatically monitors:
- Security threats
- Plugin vulnerabilities
- Failed login attempts
- Unauthorized admin access
- System performance

#### Manual Monitoring
- Check cron job logs regularly
- Monitor Google Analytics
- Review WooCommerce reports
- Check server resource usage

### 7. Troubleshooting

#### Common Issues

**API Connection Failed**
- Verify API keys are correct
- Check API rate limits
- Confirm service status

**Cron Jobs Not Running**
- Check InfinityFree cron logs
- Verify script URLs are accessible
- Test scripts manually first

**Plugin Conflicts**
- Deactivate plugins one by one
- Check WordPress debug logs
- Update all plugins

**AI Content Generation Failed**
- Check API quotas
- Switch to fallback AI service
- Reduce content generation frequency

## Support Resources

- **WordPress**: https://wordpress.org/support/
- **WooCommerce**: https://woocommerce.com/docs/
- **InfinityFree**: https://forum.infinityfree.com/
- **Supplier APIs**: Check respective documentation
- **AI Services**: OpenAI/Hugging Face documentation

## Cost Summary

- **Domain**: Free (Freenom)
- **Hosting**: Free (InfinityFree)
- **SSL/CDN**: Free (Cloudflare)
- **AI Services**: Free tiers available
- **All Plugins**: Free versions
- **Total Cost**: $0/month

The system is designed to operate completely free while providing enterprise-level e-commerce functionality.