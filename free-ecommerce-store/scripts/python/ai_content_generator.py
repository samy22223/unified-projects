#!/usr/bin/env python3
"""
AI Content Generator for E-commerce Products
Uses free AI APIs to generate SEO-optimized content
"""

import requests
import json
import os
import logging
from typing import Dict, List, Optional

class AIContentGenerator:
    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY', 'your_openai_key')
        self.huggingface_key = os.getenv('HUGGINGFACE_API_KEY', 'your_huggingface_key')
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename='ai_generator.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def generate_seo_title(self, base_title: str) -> Optional[str]:
        """Generate SEO-optimized product title"""
        prompt = f"Create an SEO-optimized e-commerce product title based on: {base_title}. Make it compelling, include relevant keywords, and keep it under 60 characters."

        try:
            # Try OpenAI first
            title = self._call_openai(prompt, max_tokens=50)
            if title and len(title) <= 60:
                return title.strip()

            # Fallback to Hugging Face
            return self._call_huggingface(prompt, max_length=50)

        except Exception as e:
            logging.error(f"Title generation failed: {e}")
            return base_title

    def generate_product_description(self, product_data: Dict) -> Optional[str]:
        """Generate detailed product description"""
        prompt = f"""
        Create a compelling e-commerce product description for:
        Title: {product_data.get('title', '')}
        Category: {product_data.get('category', '')}
        Key Features: {', '.join(product_data.get('features', []))}

        Make it SEO-friendly, highlight benefits, and include relevant keywords.
        Keep it between 200-500 words.
        """

        try:
            description = self._call_openai(prompt, max_tokens=300)
            if description:
                return description.strip()

            return self._call_huggingface(prompt, max_length=300)

        except Exception as e:
            logging.error(f"Description generation failed: {e}")
            return product_data.get('description', '')

    def generate_short_description(self, title: str) -> Optional[str]:
        """Generate short product description"""
        prompt = f"Create a concise product summary (50-100 words) for: {title}"

        try:
            summary = self._call_openai(prompt, max_tokens=100)
            if summary:
                return summary.strip()

            return self._call_huggingface(prompt, max_length=100)

        except Exception as e:
            logging.error(f"Short description generation failed: {e}")
            return title

    def generate_seo_keywords(self, product_data: Dict) -> List[str]:
        """Generate SEO keywords"""
        prompt = f"Generate 10 relevant SEO keywords for this product: {product_data.get('title', '')} in category {product_data.get('category', '')}"

        try:
            response = self._call_openai(prompt, max_tokens=100)
            if response:
                keywords = [k.strip() for k in response.split(',') if k.strip()]
                return keywords[:10]

            return []

        except Exception as e:
            logging.error(f"Keyword generation failed: {e}")
            return []

    def _call_openai(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
        """Call OpenAI API"""
        if not self.openai_key or self.openai_key == 'your_openai_key':
            return None

        try:
            headers = {
                'Authorization': f'Bearer {self.openai_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': max_tokens,
                'temperature': 0.7
            }

            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()

        except Exception as e:
            logging.error(f"OpenAI API call failed: {e}")

        return None

    def _call_huggingface(self, prompt: str, max_length: int = 100) -> Optional[str]:
        """Call Hugging Face API (free inference)"""
        if not self.huggingface_key or self.huggingface_key == 'your_huggingface_key':
            return None

        try:
            headers = {
                'Authorization': f'Bearer {self.huggingface_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'inputs': prompt,
                'parameters': {
                    'max_length': max_length,
                    'temperature': 0.7,
                    'do_sample': True
                }
            }

            # Using a free text generation model
            response = requests.post(
                'https://api-inference.huggingface.co/models/gpt2',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and result:
                    return result[0].get('generated_text', '').strip()

        except Exception as e:
            logging.error(f"Hugging Face API call failed: {e}")

        return None

    def analyze_trends(self, category: str) -> Dict:
        """Analyze market trends for product category"""
        prompt = f"Analyze current e-commerce trends for {category} products. Provide insights on popular features, pricing strategies, and marketing approaches."

        try:
            analysis = self._call_openai(prompt, max_tokens=200)
            return {
                'category': category,
                'analysis': analysis or 'Analysis not available',
                'timestamp': str(datetime.now())
            }
        except Exception as e:
            logging.error(f"Trend analysis failed: {e}")
            return {'error': str(e)}

# Usage example
if __name__ == '__main__':
    generator = AIContentGenerator()

    # Test title generation
    title = generator.generate_seo_title("Wireless Bluetooth Headphones")
    print(f"Generated title: {title}")

    # Test description generation
    product_data = {
        'title': 'Wireless Bluetooth Headphones',
        'category': 'Electronics',
        'features': ['Noise cancelling', '20hr battery', 'Comfortable fit']
    }
    description = generator.generate_product_description(product_data)
    print(f"Generated description: {description[:200]}...")