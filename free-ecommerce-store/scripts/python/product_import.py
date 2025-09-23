#!/usr/bin/env python3
"""
Automated Product Import Script
Imports products from CSV and syncs with WooCommerce
"""

import csv
import requests
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import time

class WooCommerceAPI:
    def __init__(self, site_url: str, consumer_key: str, consumer_secret: str):
        self.site_url = site_url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.session = requests.Session()
        self.session.auth = (consumer_key, consumer_secret)

    def get(self, endpoint: str, params: Dict = None) -> Dict:
        url = f"{self.site_url}/wp-json/wc/v3/{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Dict) -> Dict:
        url = f"{self.site_url}/wp-json/wc/v3/{endpoint}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def put(self, endpoint: str, data: Dict) -> Dict:
        url = f"{self.site_url}/wp-json/wc/v3/{endpoint}"
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()

class ProductImporter:
    def __init__(self, csv_file: str, site_url: str, consumer_key: str, consumer_secret: str):
        self.csv_file = csv_file
        self.wc_api = WooCommerceAPI(site_url, consumer_key, consumer_secret)
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename='product_import.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def import_products(self) -> Dict[str, int]:
        """Import products from CSV file"""
        logging.info("Starting product import from CSV")

        if not os.path.exists(self.csv_file):
            raise FileNotFoundError(f"CSV file not found: {self.csv_file}")

        products_imported = 0
        products_updated = 0
        errors = 0

        try:
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    try:
                        if self.product_exists(row['sku']):
                            self.update_product(row)
                            products_updated += 1
                        else:
                            self.create_product(row)
                            products_imported += 1

                        # Rate limiting
                        time.sleep(0.5)

                    except Exception as e:
                        logging.error(f"Error processing product {row.get('sku', 'unknown')}: {e}")
                        errors += 1

        except Exception as e:
            logging.error(f"Error reading CSV file: {e}")
            raise

        result = {
            'imported': products_imported,
            'updated': products_updated,
            'errors': errors
        }

        logging.info(f"Import completed: {result}")
        return result

    def product_exists(self, sku: str) -> Optional[int]:
        """Check if product exists by SKU"""
        try:
            products = self.wc_api.get('products', {'sku': sku})
            return products[0]['id'] if products else None
        except:
            return None

    def create_product(self, product_data: Dict) -> int:
        """Create new WooCommerce product"""
        logging.info(f"Creating product: {product_data['title']}")

        # Prepare product data
        product = {
            'name': product_data['title'],
            'type': 'simple',
            'sku': product_data['sku'],
            'description': product_data.get('description', ''),
            'short_description': product_data.get('short_description', ''),
            'regular_price': str(product_data['price']),
            'sale_price': str(product_data['sale_price']) if product_data.get('sale_price') else '',
            'manage_stock': True,
            'stock_quantity': int(product_data['stock']),
            'in_stock': int(product_data['stock']) > 0,
            'categories': self.get_categories(product_data.get('category', '')),
            'images': self.process_images(product_data.get('images', '')),
            'meta_data': [
                {'key': '_supplier', 'value': product_data.get('supplier', '')},
                {'key': '_supplier_sku', 'value': product_data.get('supplier_sku', '')},
                {'key': '_eco_friendly', 'value': 'yes' if product_data.get('eco_friendly', '').lower() == 'true' else 'no'}
            ]
        }

        # Add eco-friendly badge
        if product_data.get('eco_friendly', '').lower() == 'true':
            product['meta_data'].append({'key': '_eco_badge', 'value': 'yes'})

        # Create product
        result = self.wc_api.post('products', product)
        product_id = result['id']

        logging.info(f"Created product {product_id}: {product_data['title']}")
        return product_id

    def update_product(self, product_data: Dict) -> None:
        """Update existing WooCommerce product"""
        product_id = self.product_exists(product_data['sku'])
        if not product_id:
            return

        logging.info(f"Updating product {product_id}: {product_data['title']}")

        # Prepare update data
        update_data = {
            'regular_price': str(product_data['price']),
            'sale_price': str(product_data['sale_price']) if product_data.get('sale_price') else '',
            'stock_quantity': int(product_data['stock']),
            'in_stock': int(product_data['stock']) > 0
        }

        self.wc_api.put(f'products/{product_id}', update_data)
        logging.info(f"Updated product {product_id}")

    def get_categories(self, category_string: str) -> List[Dict]:
        """Get or create product categories"""
        if not category_string:
            return []

        categories = []
        category_names = [cat.strip() for cat in category_string.split(',')]

        for category_name in category_names:
            category_id = self.get_or_create_category(category_name)
            if category_id:
                categories.append({'id': category_id})

        return categories

    def get_or_create_category(self, category_name: str) -> Optional[int]:
        """Get existing category or create new one"""
        try:
            # Check if category exists
            categories = self.wc_api.get('products/categories', {'search': category_name})
            for category in categories:
                if category['name'].lower() == category_name.lower():
                    return category['id']

            # Create new category
            result = self.wc_api.post('products/categories', {'name': category_name})
            return result['id']

        except Exception as e:
            logging.error(f"Error handling category '{category_name}': {e}")
            return None

    def process_images(self, images_string: str) -> List[Dict]:
        """Process product images"""
        if not images_string:
            return []

        images = []
        image_urls = [url.strip() for url in images_string.split('|')]

        for i, url in enumerate(image_urls[:5]):  # Max 5 images
            try:
                # Download and upload image to WordPress
                image_data = self.upload_image_to_wordpress(url)
                if image_data:
                    images.append({
                        'src': image_data['source_url'],
                        'position': i
                    })
            except Exception as e:
                logging.error(f"Error processing image {url}: {e}")

        return images

    def upload_image_to_wordpress(self, image_url: str) -> Optional[Dict]:
        """Upload image to WordPress media library"""
        try:
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Get filename from URL
            filename = os.path.basename(image_url.split('?')[0])
            if not filename:
                filename = f"product-image-{int(time.time())}.jpg"

            # Prepare upload data
            files = {'file': (filename, response.content, response.headers.get('content-type', 'image/jpeg'))}

            # Upload to WordPress
            upload_url = f"{self.wc_api.site_url}/wp-json/wp/v2/media"
            upload_response = self.wc_api.session.post(upload_url, files=files)
            upload_response.raise_for_status()

            return upload_response.json()

        except Exception as e:
            logging.error(f"Error uploading image {image_url}: {e}")
            return None

def main():
    # Configuration - replace with your values
    CSV_FILE = 'product-import-template.csv'
    SITE_URL = os.getenv('WP_SITE_URL', 'https://yourdomain.epizy.com')
    CONSUMER_KEY = os.getenv('WC_CONSUMER_KEY', 'your_consumer_key')
    CONSUMER_SECRET = os.getenv('WC_CONSUMER_SECRET', 'your_consumer_secret')

    try:
        importer = ProductImporter(CSV_FILE, SITE_URL, CONSUMER_KEY, CONSUMER_SECRET)
        result = importer.import_products()

        print(f"Import completed successfully!")
        print(f"Products imported: {result['imported']}")
        print(f"Products updated: {result['updated']}")
        print(f"Errors: {result['errors']}")

    except Exception as e:
        print(f"Import failed: {e}")
        logging.error(f"Import failed: {e}")
        exit(1)

if __name__ == '__main__':
    main()