# Free E-commerce Dropshipping Store

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![WordPress](https://img.shields.io/badge/WordPress-5.8+-blue.svg)
![WooCommerce](https://img.shields.io/badge/WooCommerce-6.0+-96588a.svg)
![PHP](https://img.shields.io/badge/PHP-7.4+-777bb4.svg)

A 100% free, fully autonomous, fully automated dropshipping online store built with WordPress + WooCommerce, featuring AI-powered automation and zero-cost infrastructure.

## Architecture Overview

### Infrastructure
- **Hosting**: InfinityFree (free PHP/MySQL hosting)
- **Domain**: Freenom (.tk/.ml/.ga/.cf/.gq)
- **SSL**: Cloudflare Free
- **CMS**: WordPress + WooCommerce
- **Database**: MySQL (provided by InfinityFree)
- **CDN**: Cloudflare Free
- **Backups**: UpdraftPlus Free (Google Drive)

### Automation Components
- **Product Import**: DSers, CJDropshipping, Spocket Free
- **Order Fulfillment**: Webhook PHP scripts → Supplier APIs
- **Marketing**: MailPoet Free, Tidio Free Chatbot, Revive Old Posts
- **Security**: Wordfence Free, Limit Login Attempts
- **Performance**: WP Super Cache, Smush Free, Rank Math Free
- **Analytics**: Google Analytics 4, Hotjar Free

### AI Agents (Free Implementation)
- Product selection and content generation using free AI APIs
- SEO optimization recommendations
- Customer support automation
- Marketing campaign suggestions

## Folder Structure

```
free-ecommerce-store/
├── wp-content/
│   ├── plugins/
│   │   ├── custom-scripts/
│   │   │   ├── product-import.php
│   │   │   ├── order-fulfillment.php
│   │   │   ├── stock-sync.php
│   │   │   ├── ai-agent.php
│   │   │   └── cron-jobs.php
│   │   └── (free plugins installed via WordPress)
│   ├── themes/
│   │   └── custom-theme/
│   │       ├── functions.php
│   │       ├── style.css
│   │       └── templates/
│   ├── uploads/
│   └── mu-plugins/
│       └── eco-commerce.php
├── scripts/
│   ├── python/
│   │   ├── product_import.py
│   │   ├── ai_content_generator.py
│   │   └── analytics_analyzer.py
│   └── bash/
│       └── deploy.sh
├── templates/
│   ├── emails/
│   │   ├── order-confirmation.html
│   │   ├── shipment-notification.html
│   │   └── review-request.html
│   ├── invoices/
│   │   └── invoice-template.html
│   └── csv/
│       └── product-import-template.csv
├── config/
│   ├── wp-config-sample.php
│   ├── .htaccess
│   └── robots.txt
├── docs/
│   ├── deployment-guide.md
│   ├── api-keys-setup.md
│   ├── cron-setup.md
│   └── security-best-practices.md
└── README.md
```

## Key Features

1. **Fully Automated Product Import**
   - CSV/API integration with AliExpress, CJDropshipping, Spocket
   - Auto stock/price updates
   - AI-generated product descriptions and SEO

2. **Order Fulfillment Automation**
   - Webhook triggers on WooCommerce orders
   - Automatic supplier API calls
   - Tracking number sync and customer notifications

3. **Marketing Automation**
   - Abandoned cart emails
   - AI-powered product recommendations
   - Social media auto-posting
   - Chatbot support

4. **Security & Monitoring**
   - Firewall and malware protection
   - Auto backups
   - AI security monitoring

5. **Eco-Commerce Features**
   - Carbon footprint calculations
   - Sustainable supplier prioritization
   - Eco-friendly badges

## Deployment Steps

1. Register free domain at Freenom
2. Sign up for InfinityFree hosting
3. Point domain to InfinityFree nameservers
4. Upload WordPress files
5. Install required plugins
6. Configure API keys and settings
7. Set up cron jobs
8. Enable Cloudflare SSL/CDN

See `docs/deployment-guide.md` for detailed instructions.

## 📋 Prerequisites

- **PHP** (7.4 or higher)
- **MySQL** (5.6 or higher)
- **WordPress** (5.8 or higher)
- **WooCommerce** (6.0 or higher)
- Free hosting account (InfinityFree recommended)
- Free domain (.tk/.ml/.ga/.cf/.gq from Freenom)

## 🛠 Installation & Setup

### 1. Domain & Hosting Setup
1. Register free domain at [Freenom](https://www.freenom.com/)
2. Sign up for [InfinityFree](https://www.infinityfree.net/) hosting
3. Point domain to InfinityFree nameservers

### 2. WordPress Installation
1. Download WordPress from [wordpress.org](https://wordpress.org/download/)
2. Upload files to your hosting via FTP
3. Run WordPress installation wizard

### 3. Environment Configuration
Copy the example environment file:
```bash
cp .env.example .env
```

Configure your settings in `.env`:
```env
DB_HOST=localhost
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
WP_DEBUG=false
# Add other variables as needed
```

### 4. Plugin Installation
Install required free plugins via WordPress admin:
- WooCommerce
- Wordfence Security
- UpdraftPlus
- Rank Math SEO
- WP Super Cache

### 5. API Configuration
Set up API keys in `wp-config.php` or via WordPress admin:
- Google Analytics
- MailPoet SMTP
- Supplier APIs (DSers, CJDropshipping, etc.)

## 🚀 Usage

### Basic Operations
1. **Product Import**: Use automated scripts or manual CSV upload
2. **Order Management**: Monitor orders in WooCommerce dashboard
3. **Fulfillment**: Automatic webhook triggers handle supplier orders
4. **Marketing**: Configure automated email campaigns
5. **Analytics**: Monitor performance with Google Analytics

### Automation Scripts
Run Python automation scripts:
```bash
cd scripts/python
python product_import.py
python ai_content_generator.py
```

### Deployment
See `docs/deployment-guide.md` for detailed deployment instructions.

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add some feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

### Development Guidelines
- Follow WordPress coding standards
- Test plugins on staging environment first
- Update documentation for new features
- Use descriptive commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with WordPress and WooCommerce
- Powered by free hosting and services
- Thanks to the open-source community for automation scripts and plugins

## 📞 Support

For support, please check the documentation in the `docs/` folder or open an issue on GitHub.

## Zero Cost Guarantee

All components use free services and open-source software:
- No paid hosting or domains
- No premium plugins
- Free supplier integrations
- Open-source automation scripts