from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL

class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="seller_profile")
    shop_name = models.CharField(max_length=120, unique=True)
    shop_description = models.TextField(blank=True)
    shop_logo = models.ImageField(upload_to="shop_logos/", blank=True, null=True)
    region = models.CharField(max_length=120)
    district = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    rating = models.FloatField(default=0)
    total_sales = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    icon = models.ImageField(upload_to="category_icons/", blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order_num = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug

class Product(models.Model):
    class Condition(models.TextChoices):
        YANGI = "yangi", "yangi"
        IDEAL = "ideal", "ideal"
        YAXSHI = "yaxshi", "yaxshi"
        QONIQARLI = "qoniqarli", "qoniqarli"

    class PriceType(models.TextChoices):
        QATIY = "qat'iy", "qat'iy"
        KELISHILADI = "kelishiladi", "kelishiladi"
        BEPUL = "bepul", "bepul"
        AYIRBOSHLASH = "ayirboshlash", "ayirboshlash"

    class Status(models.TextChoices):
        MOD = "moderatsiyada", "moderatsiyada"
        ACTIVE = "aktiv", "aktiv"
        REJECTED = "rad etilgan", "rad etilgan"
        SOLD = "sotilgan", "sotilgan"
        ARCHIVED = "arxivlangan", "arxivlangan"

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    title = models.CharField(max_length=200)
    description = models.TextField()
    condition = models.CharField(max_length=20, choices=Condition.choices)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    price_type = models.CharField(max_length=30, choices=PriceType.choices)
    region = models.CharField(max_length=120)
    district = models.CharField(max_length=120)
    view_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.MOD)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def publish(self):
        self.status = self.Status.ACTIVE
        self.published_at = timezone.now()
        self.expires_at = timezone.now() + timedelta(days=30)
        self.save(update_fields=["status", "published_at", "expires_at"])

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/")
    order = models.PositiveIntegerField(default=0)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

class Order(models.Model):
    class Status(models.TextChoices):
        KUTILYAPTI = "kutilyapti", "kutilyapti"
        KELISHILGAN = "kelishilgan", "kelishilgan"
        SOTIB_OLINGAN = "sotib olingan", "sotib olingan"
        BEKOR = "bekor qilingan", "bekor qilingan"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orders")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders_as_buyer")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders_as_seller")
    final_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.KUTILYAPTI)
    meeting_location = models.CharField(max_length=255, blank=True)
    meeting_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="review")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews_left")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews_received")
    rating = models.PositiveSmallIntegerField()  # 1..5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)