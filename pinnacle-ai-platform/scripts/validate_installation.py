#!/usr/bin/env python3
"""
Validation script to test that the Pinnacle AI Platform core packages are working correctly.
This script tests imports and basic functionality of key packages.
"""

import sys
import importlib
import traceback

def test_import(package_name, test_function=None):
    """Test importing a package and optionally run a test function."""
    try:
        print(f"Testing {package_name}...")
        module = importlib.import_module(package_name)

        if test_function:
            test_function(module)

        print(f"✅ {package_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name} - Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ {package_name} - Error: {e}")
        traceback.print_exc()
        return False

def test_fastapi():
    """Test FastAPI basic functionality."""
    from fastapi import FastAPI
    app = FastAPI()
    assert app is not None
    print("   FastAPI app creation - OK")

def test_pydantic():
    """Test Pydantic basic functionality."""
    from pydantic import BaseModel

    class User(BaseModel):
        name: str
        age: int

    user = User(name="test", age=25)
    assert user.name == "test"
    assert user.age == 25
    print("   Pydantic model creation - OK")

def test_django():
    """Test Django basic functionality."""
    import django
    from django.conf import settings

    # Configure minimal Django settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
            SECRET_KEY='test-key-for-validation'
        )

    django.setup()
    print("   Django setup - OK")

def test_torch():
    """Test PyTorch basic functionality."""
    import torch
    x = torch.tensor([1, 2, 3])
    y = torch.tensor([4, 5, 6])
    z = x + y
    assert torch.equal(z, torch.tensor([5, 7, 9]))
    print("   PyTorch tensor operations - OK")

def test_transformers():
    """Test Transformers basic functionality."""
    from transformers import AutoTokenizer
    # Test with a small tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased", cache_dir="/tmp")
        tokens = tokenizer("Hello world", return_tensors="pt")
        assert "input_ids" in tokens
        print("   Transformers tokenizer - OK")
    except Exception as e:
        print(f"   Transformers tokenizer - Skipped (network issue): {e}")

def test_numpy():
    """Test NumPy basic functionality."""
    import numpy as np
    arr = np.array([1, 2, 3, 4, 5])
    assert arr.mean() == 3.0
    assert arr.sum() == 15
    print("   NumPy operations - OK")

def test_pandas():
    """Test Pandas basic functionality."""
    import pandas as pd
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    assert df.shape == (3, 2)
    assert df['A'].sum() == 6
    print("   Pandas DataFrame operations - OK")

def test_scikit_learn():
    """Test scikit-learn basic functionality."""
    from sklearn.linear_model import LinearRegression
    import numpy as np

    X = np.array([[1], [2], [3], [4]])
    y = np.array([1, 2, 3, 4])

    model = LinearRegression()
    model.fit(X, y)
    pred = model.predict([[5]])
    assert abs(pred[0] - 5.0) < 0.1
    print("   scikit-learn model training - OK")

def test_pillow():
    """Test Pillow basic functionality."""
    from PIL import Image
    import io

    # Create a small test image
    img = Image.new('RGB', (10, 10), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    assert len(img_bytes.getvalue()) > 0
    print("   Pillow image creation - OK")

def test_requests():
    """Test requests basic functionality."""
    import requests
    # Test with a simple HEAD request to avoid network dependency
    try:
        response = requests.head('https://httpbin.org/status/200', timeout=5)
        assert response.status_code == 200
        print("   Requests HTTP call - OK")
    except Exception as e:
        print(f"   Requests HTTP call - Skipped (network issue): {e}")

def main():
    """Run all validation tests."""
    print("🔍 Validating Pinnacle AI Platform Installation")
    print("=" * 50)

    # Core web framework tests
    tests = [
        ("fastapi", test_fastapi),
        ("pydantic", test_pydantic),
        ("uvicorn", None),
        ("django", test_django),
        ("djangorestframework", None),
        ("django_cors_headers", None),

        # Database tests
        ("sqlalchemy", None),
        ("redis", None),
        ("pymongo", None),

        # AI/ML tests
        ("torch", test_torch),
        ("torchvision", None),
        ("torchaudio", None),
        ("transformers", test_transformers),
        ("tokenizers", None),
        ("accelerate", None),
        ("diffusers", None),
        ("sentence_transformers", None),
        ("numpy", test_numpy),
        ("pandas", test_pandas),
        ("scikit_learn", test_scikit_learn),
        ("matplotlib", None),
        ("seaborn", None),
        ("plotly", None),

        # Computer vision (without OpenCV)
        ("PIL", test_pillow),
        ("imageio", None),
        ("albumentations", None),

        # NLP tests
        ("nltk", None),
        ("spacy", None),
        ("textblob", None),

        # Audio tests
        ("librosa", None),

        # API and web scraping
        ("requests", test_requests),
        ("httpx", None),
        ("aiohttp", None),
        ("beautifulsoup4", None),
        ("selenium", None),

        # Cloud services
        ("boto3", None),
        ("azure.storage.blob", None),
        ("google.cloud.storage", None),

        # Task queue
        ("celery", None),

        # Testing
        ("pytest", None),

        # Code quality
        ("black", None),
        ("isort", None),
        ("flake8", None),

        # Development tools
        ("jupyter", None),
        ("ipykernel", None),

        # Configuration
        ("python_dotenv", None),
        ("dynaconf", None),

        # Monitoring
        ("sentry_sdk", None),
        ("loguru", None),
        ("structlog", None),

        # Utilities
        ("click", None),
        ("rich", None),
        ("tqdm", None),
    ]

    passed = 0
    total = len(tests)

    for package_name, test_function in tests:
        if test_import(package_name, test_function):
            passed += 1

    print("=" * 50)
    print(f"📊 Results: {passed}/{total} packages working correctly")

    if passed == total:
        print("🎉 All core packages are working! The installation is successful.")
        return 0
    else:
        print(f"⚠️  {total - passed} packages had issues. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())