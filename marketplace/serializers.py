from rest_framework import serializers
from django.db.models import Avg
from .models import (
    SellerProfile, Category, Product, ProductImage,
    Favorite, Order, Review
)


# ---------- SELLER ----------
class SellerPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = (
            "id", "shop_name", "shop_description", "shop_logo",
            "region", "district", "address",
            "rating", "total_sales", "created_at", "updated_at",
            "user",
        )


# ---------- CATEGORY ----------
class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "parent", "description", "icon", "order_num", "is_active", "children")

    def get_children(self, obj):
        qs = obj.children.filter(is_active=True).order_by("order_num", "id")
        return CategoryTreeSerializer(qs, many=True, context=self.context).data


# ---------- PRODUCT IMAGES ----------
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "order", "is_main", "created_at")


# ---------- PRODUCTS ----------
class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.slug", read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "title", "price", "price_type", "condition",
            "region", "district",
            "view_count", "favorite_count",
            "status", "created_at", "published_at", "expires_at",
            "category", "main_image",
        )

    def get_main_image(self, obj):
        main = obj.images.filter(is_main=True).order_by("order", "id").first()
        if not main:
            main = obj.images.order_by("order", "id").first()
        return main.image.url if main and main.image else None


class ProductDetailSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.slug", read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "seller", "category",
            "title", "description",
            "condition", "price", "price_type",
            "region", "district",
            "view_count", "favorite_count",
            "status",
            "created_at", "updated_at", "published_at", "expires_at",
            "images",
        )
        read_only_fields = ("seller", "view_count", "favorite_count", "status", "published_at", "expires_at")


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id", "category",
            "title", "description",
            "condition", "price", "price_type",
            "region", "district",
        )


# ---------- FAVORITES ----------
class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "product", "product_id", "created_at")

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product not found")
        return value


# ---------- ORDERS ----------
class OrderListSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "product",
            "buyer", "seller",
            "final_price", "status",
            "meeting_location", "meeting_time",
            "notes",
            "created_at", "updated_at",
        )
        read_only_fields = ("buyer", "seller", "final_price", "status")


class OrderCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_product_id(self, value):
        try:
            p = Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        if p.status != Product.Status.ACTIVE:
            raise serializers.ValidationError("Product is not active")
        return value


class OrderUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
    final_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    meeting_location = serializers.CharField(required=False, allow_blank=True)
    meeting_time = serializers.DateTimeField(required=False)

   


# ---------- REVIEWS ----------
class ReviewListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("id", "order", "reviewer", "seller", "rating", "comment", "created_at")
        read_only_fields = fields


class ReviewCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField()

    def validate_order_id(self, value):
        if not Order.objects.filter(id=value).exists():
            raise serializers.ValidationError("Order not found")
        return value