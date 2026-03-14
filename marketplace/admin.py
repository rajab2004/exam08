from django.contrib import admin
from .models import SellerProfile, Category, Product, ProductImage, Favorite, Order, Review


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "shop_name", "user", "region", "district", "rating", "total_sales", "created_at")
    search_fields = ("shop_name", "user__username", "region")
    list_filter = ("region",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "parent", "is_active", "order_num")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "seller", "category", "price", "status", "condition", "created_at")
    list_filter = ("status", "condition", "price_type")
    search_fields = ("title", "description", "seller__username")
    inlines = [ProductImageInline]
    actions = ["approve_products", "reject_products"]

    def approve_products(self, request, queryset):
        for product in queryset:
            product.publish()
        self.message_user(request, f"{queryset.count()} mahsulot tasdiqlandi.")
    approve_products.short_description = "Tanlangan mahsulotlarni tasdiqlash (publish)"

    def reject_products(self, request, queryset):
        queryset.update(status=Product.Status.REJECTED)
        self.message_user(request, f"{queryset.count()} mahsulot rad etildi.")
    reject_products.short_description = "Tanlangan mahsulotlarni rad etish"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "buyer", "seller", "final_price", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("buyer__username", "seller__username")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "reviewer", "seller", "rating", "created_at")
    list_filter = ("rating",)
