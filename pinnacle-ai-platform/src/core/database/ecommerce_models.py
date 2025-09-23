"""
E-commerce Database Models

This module contains all database models for the e-commerce functionality
including products, categories, cart, orders, reviews, and wishlist.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CategoryModel(Base):
    """Database model for product categories."""
    __tablename__ = "categories"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(String, ForeignKey("categories.id"), nullable=True)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)


class ProductModel(Base):
    """Database model for products."""
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    description = Column(Text)
    short_description = Column(Text, nullable=True)
    price = Column(Float)
    compare_at_price = Column(Float, nullable=True)
    cost_price = Column(Float, nullable=True)
    sku = Column(String, unique=True, index=True)
    category_id = Column(String, ForeignKey("categories.id"))
    images = Column(JSON, default=list)  # List of image URLs
    inventory_quantity = Column(Integer, default=0)
    inventory_policy = Column(String, default="deny")  # deny, allow_backorder
    weight = Column(Float, nullable=True)
    dimensions = Column(JSON, nullable=True)  # width, height, depth
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_digital = Column(Boolean, default=False)
    tags = Column(JSON, default=list)
    seo_title = Column(String, nullable=True)
    seo_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)


class ProductVariantModel(Base):
    """Database model for product variants (size, color, etc.)."""
    __tablename__ = "product_variants"

    id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"))
    name = Column(String)  # e.g., "Color", "Size"
    value = Column(String)  # e.g., "Red", "Large"
    price_modifier = Column(Float, default=0.0)
    sku = Column(String, nullable=True)
    inventory_quantity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CartModel(Base):
    """Database model for shopping carts."""
    __tablename__ = "carts"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # None for guest carts
    session_id = Column(String, index=True)  # For guest users
    status = Column(String, default="active")  # active, abandoned, converted
    total_items = Column(Integer, default=0)
    total_price = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    metadata = Column(JSON, default=dict)


class CartItemModel(Base):
    """Database model for cart items."""
    __tablename__ = "cart_items"

    id = Column(String, primary_key=True, index=True)
    cart_id = Column(String, ForeignKey("carts.id"))
    product_id = Column(String, ForeignKey("products.id"))
    variant_id = Column(String, ForeignKey("product_variants.id"), nullable=True)
    quantity = Column(Integer, default=1)
    price = Column(Float)  # Price at time of adding to cart
    total_price = Column(Float)  # quantity * price
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class OrderModel(Base):
    """Database model for orders."""
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    order_number = Column(String, unique=True, index=True)
    status = Column(String, default="pending")  # pending, confirmed, processing, shipped, delivered, cancelled, refunded
    payment_status = Column(String, default="pending")  # pending, paid, failed, refunded
    fulfillment_status = Column(String, default="unfulfilled")  # unfulfilled, partially_fulfilled, fulfilled

    # Customer information
    customer_email = Column(String)
    customer_name = Column(String)
    customer_phone = Column(String, nullable=True)

    # Shipping information
    shipping_address = Column(JSON)
    shipping_method = Column(String, default="standard")
    shipping_cost = Column(Float, default=0.0)

    # Billing information
    billing_address = Column(JSON)

    # Order totals
    subtotal = Column(Float)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float)

    # Payment information
    payment_method = Column(String)
    payment_id = Column(String, nullable=True)  # Stripe/PayPal transaction ID
    currency = Column(String, default="USD")

    # Notes and metadata
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)


class OrderItemModel(Base):
    """Database model for order items."""
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"))
    product_id = Column(String, ForeignKey("products.id"))
    variant_id = Column(String, ForeignKey("product_variants.id"), nullable=True)
    product_name = Column(String)  # Snapshot of product name at time of order
    variant_name = Column(String, nullable=True)  # Snapshot of variant info
    quantity = Column(Integer)
    price = Column(Float)  # Price at time of order
    total_price = Column(Float)  # quantity * price
    sku = Column(String)
    weight = Column(Float, nullable=True)
    requires_shipping = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReviewModel(Base):
    """Database model for product reviews."""
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"))
    user_id = Column(String, ForeignKey("users.id"))
    order_id = Column(String, ForeignKey("orders.id"), nullable=True)  # Verified purchase
    rating = Column(Integer)  # 1-5 stars
    title = Column(String, nullable=True)
    content = Column(Text)
    is_verified_purchase = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)
    helpful_votes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)


class WishlistModel(Base):
    """Database model for user wishlists."""
    __tablename__ = "wishlists"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, default="Default Wishlist")
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class WishlistItemModel(Base):
    """Database model for wishlist items."""
    __tablename__ = "wishlist_items"

    id = Column(String, primary_key=True, index=True)
    wishlist_id = Column(String, ForeignKey("wishlists.id"))
    product_id = Column(String, ForeignKey("products.id"))
    variant_id = Column(String, ForeignKey("product_variants.id"), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)


class AddressModel(Base):
    """Database model for user addresses."""
    __tablename__ = "addresses"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    type = Column(String, default="shipping")  # shipping, billing
    is_default = Column(Boolean, default=False)

    # Address fields
    first_name = Column(String)
    last_name = Column(String)
    company = Column(String, nullable=True)
    address_line_1 = Column(String)
    address_line_2 = Column(String, nullable=True)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    country = Column(String)
    phone = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class PromotionModel(Base):
    """Database model for promotions and discounts."""
    __tablename__ = "promotions"

    id = Column(String, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    type = Column(String)  # percentage, fixed_amount, free_shipping
    value = Column(Float)
    minimum_amount = Column(Float, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class InventoryTransactionModel(Base):
    """Database model for inventory transactions."""
    __tablename__ = "inventory_transactions"

    id = Column(String, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"))
    variant_id = Column(String, ForeignKey("product_variants.id"), nullable=True)
    type = Column(String)  # stock_in, stock_out, adjustment, sale, return
    quantity = Column(Integer)
    previous_quantity = Column(Integer)
    new_quantity = Column(Integer)
    reference_id = Column(String, nullable=True)  # order_id, po_id, etc.
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)</code>
</edit_file>