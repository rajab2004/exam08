from django.db import transaction
from django.db.models import F, Avg
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    SellerProfile, Category, Product, ProductImage,
    Favorite, Order, Review
)
from .permissions import IsSeller, IsOwnerProduct, IsOrderParty
from .filters import ProductFilter
from .serializers import (
    SellerPublicSerializer,
    CategoryTreeSerializer,
    ProductListSerializer, ProductDetailSerializer, ProductCreateUpdateSerializer,
    ProductImageSerializer,
    FavoriteSerializer,
    OrderListSerializer, OrderCreateSerializer, OrderUpdateSerializer,
    ReviewListSerializer, ReviewCreateSerializer,
)


# ---------------- CATEGORIES ----------------
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = CategoryTreeSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Category.objects.filter(is_active=True, parent__isnull=True).order_by("order_num", "id")

    @action(detail=True, methods=["get"], permission_classes=[AllowAny], url_path="products")
    def products(self, request, slug=None):
        category = self.get_object()
        qs = Product.objects.filter(status=Product.Status.ACTIVE, category=category).order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = ProductListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(ser.data)
        ser = ProductListSerializer(qs, many=True, context={"request": request})
        return Response(ser.data)


# ---------------- SELLERS (public) ----------------
class SellerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = SellerPublicSerializer
    queryset = SellerProfile.objects.select_related("user").all()

    @action(detail=True, methods=["get"], permission_classes=[AllowAny], url_path="products")
    def products(self, request, pk=None):
        profile = self.get_object()
        qs = Product.objects.filter(
            status=Product.Status.ACTIVE,
            seller_id=profile.user_id
        ).order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = ProductListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(ser.data)
        ser = ProductListSerializer(qs, many=True, context={"request": request})
        return Response(ser.data)


# ---------------- PRODUCTS ----------------
class ProductViewSet(viewsets.ModelViewSet):
    filterset_class = ProductFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "price", "view_count"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated(), IsSeller()]
        if self.action in ["update", "partial_update", "destroy", "publish", "archive", "sold"]:
            return [IsAuthenticated(), IsSeller(), IsOwnerProduct()]
        if self.action in ["add_image", "delete_image", "set_main_image"]:
            return [IsAuthenticated(), IsSeller(), IsOwnerProduct()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Product.objects.select_related("category").prefetch_related("images").all()
        if self.action == "list":
            return qs.filter(status=Product.Status.ACTIVE)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user, status=Product.Status.MOD)

    def perform_update(self, serializer):
        instance = self.get_object()
        obj = serializer.save()
        if instance.status == Product.Status.ACTIVE:
            obj.status = Product.Status.MOD
            obj.published_at = None
            obj.save(update_fields=["status", "published_at"])

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        Product.objects.filter(id=obj.id).update(view_count=F("view_count") + 1)
        obj.refresh_from_db(fields=["view_count"])
        ser = self.get_serializer(obj, context={"request": request})
        return Response(ser.data)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        product = self.get_object()
        if product.status == Product.Status.SOLD:
            return Response({"detail": "Mahsulot allaqachon sotilgan"}, status=400)
        product.publish()
        return Response({"message": "Mahsulot tasdiqlandi va aktiv holga keldi"}, status=200)

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        product = self.get_object()
        product.status = Product.Status.ARCHIVED
        product.save(update_fields=["status"])
        return Response({"message": "Mahsulot arxivlandi"}, status=200)

    @action(detail=True, methods=["post"], url_path="sold")
    def sold(self, request, pk=None):
        product = self.get_object()
        if product.status == Product.Status.SOLD:
            return Response({"detail": "Mahsulot allaqachon sotilgan"}, status=400)

        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=product.id)
            product.status = Product.Status.SOLD
            product.save(update_fields=["status"])
            SellerProfile.objects.filter(user_id=product.seller_id).update(total_sales=F("total_sales") + 1)

        return Response({"message": "Mahsulot sotilgan deb belgilandi"}, status=200)

    @action(detail=True, methods=["post"], url_path="images")
    def add_image(self, request, pk=None):
        product = self.get_object()
        ser = ProductImageSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)

        with transaction.atomic():
            img = ProductImage.objects.create(product=product, **ser.validated_data)
            if not ProductImage.objects.filter(product=product, is_main=True).exists():
                img.is_main = True
                img.save(update_fields=["is_main"])
        return Response(ProductImageSerializer(img, context={"request": request}).data, status=201)

    @action(detail=True, methods=["delete"], url_path=r"images/(?P<image_id>\d+)")
    def delete_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        img = get_object_or_404(ProductImage, id=image_id, product=product)
        img.delete()
        return Response(status=204)

    @action(detail=True, methods=["post"], url_path=r"images/(?P<image_id>\d+)/set-main")
    def set_main_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        img = get_object_or_404(ProductImage, id=image_id, product=product)

        with transaction.atomic():
            ProductImage.objects.filter(product=product, is_main=True).update(is_main=False)
            img.is_main = True
            img.save(update_fields=["is_main"])

        return Response({"message": "Asosiy rasm o'rnatildi"}, status=200)


# ---------------- FAVORITES ----------------
class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.select_related(
            "product", "product__category"
        ).prefetch_related("product__images").filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        ser = FavoriteSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        product_id = ser.validated_data["product_id"]

        with transaction.atomic():
            fav, created = Favorite.objects.get_or_create(user=request.user, product_id=product_id)
            if created:
                Product.objects.filter(id=product_id).update(favorite_count=F("favorite_count") + 1)

        fav.refresh_from_db()
        out = FavoriteSerializer(fav, context={"request": request})
        return Response(out.data, status=201)

    def destroy(self, request, *args, **kwargs):
        fav = self.get_object()
        product_id = fav.product_id
        with transaction.atomic():
            fav.delete()
            Product.objects.filter(id=product_id, favorite_count__gt=0).update(
                favorite_count=F("favorite_count") - 1
            )
        return Response(status=204)


# ---------------- ORDERS ----------------
class OrderViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
):
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.select_related(
        "product", "buyer", "seller"
    ).prefetch_related("product__images", "product__category")

    def get_permissions(self):
        if self.action in ["retrieve", "partial_update", "update"]:
            return [IsAuthenticated(), IsOrderParty()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action in ["update", "partial_update"]:
            return OrderUpdateSerializer
        return OrderListSerializer

    def list(self, request, *args, **kwargs):
        role = request.query_params.get("role")  # buyer|seller
        qs = self.get_queryset()

        if role == "seller":
            qs = qs.filter(seller=request.user)
        else:
            qs = qs.filter(buyer=request.user)

        qs = qs.order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = OrderListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(ser.data)
        ser = OrderListSerializer(qs, many=True, context={"request": request})
        return Response(ser.data)

    def create(self, request, *args, **kwargs):
        if request.user.role != "customer":
            return Response({"detail": "Faqat xaridorlar buyurtma bera oladi"}, status=403)

        ser = OrderCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        product = get_object_or_404(Product, id=ser.validated_data["product_id"])
        if product.seller_id == request.user.id:
            return Response({"detail": "O'z mahsulotingizga buyurtma bera olmaysiz"}, status=400)

        order = Order.objects.create(
            product=product,
            buyer=request.user,
            seller=product.seller,
            final_price=product.price,
            status=Order.Status.KUTILYAPTI,
            notes=ser.validated_data.get("notes", ""),
        )
        out = OrderListSerializer(order, context={"request": request})
        return Response(out.data, status=201)

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        ser = OrderUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        new_status = data.get("status")
        if not new_status:
            return Response({"detail": "status majburiy"}, status=400)

        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order.id)

            is_seller = (request.user.id == order.seller_id)
            is_buyer = (request.user.id == order.buyer_id)

            if is_seller:
                if order.status == Order.Status.KUTILYAPTI and new_status in [
                    Order.Status.KELISHILGAN, Order.Status.BEKOR
                ]:
                    pass
                else:
                    return Response({"detail": "Sotuvchi bu statusni o'rnatolmaydi"}, status=403)

            elif is_buyer:
                if order.status == Order.Status.KELISHILGAN and new_status in [
                    Order.Status.SOTIB_OLINGAN, Order.Status.BEKOR
                ]:
                    pass
                else:
                    return Response({"detail": "Xaridor bu statusni o'rnatolmaydi"}, status=403)
            else:
                return Response({"detail": "Ruxsat yo'q"}, status=403)

            if "final_price" in data and is_seller and new_status == Order.Status.KELISHILGAN:
                order.final_price = data["final_price"]
            if "meeting_location" in data and is_seller and new_status == Order.Status.KELISHILGAN:
                order.meeting_location = data["meeting_location"]
            if "meeting_time" in data and is_seller and new_status == Order.Status.KELISHILGAN:
                order.meeting_time = data["meeting_time"]

            order.status = new_status
            order.save()

            if new_status == Order.Status.SOTIB_OLINGAN:
                Product.objects.filter(id=order.product_id).update(status=Product.Status.SOLD)
                SellerProfile.objects.filter(user_id=order.seller_id).update(
                    total_sales=F("total_sales") + 1
                )

        out = OrderListSerializer(order, context={"request": request})
        return Response(out.data, status=200)


# ---------------- REVIEWS ----------------
class ReviewViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
):
    queryset = Review.objects.select_related("order", "reviewer", "seller").all()

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return ReviewCreateSerializer
        return ReviewListSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().order_by("-created_at")
        seller_id = request.query_params.get("seller_id")
        if seller_id and str(seller_id).isdigit():
            qs = qs.filter(seller_id=int(seller_id))

        page = self.paginate_queryset(qs)
        if page is not None:
            ser = ReviewListSerializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = ReviewListSerializer(qs, many=True)
        return Response(ser.data)

    def create(self, request, *args, **kwargs):
        ser = ReviewCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        order_id = ser.validated_data["order_id"]

        with transaction.atomic():
            order = get_object_or_404(Order, id=order_id)

            if order.buyer_id != request.user.id:
                return Response({"detail": "Faqat xaridor izoh qoldira oladi"}, status=403)
            if order.status != Order.Status.SOTIB_OLINGAN:
                return Response({"detail": "Buyurtma 'sotib olingan' bo'lishi kerak"}, status=400)
            if Review.objects.filter(order=order).exists():
                return Response({"detail": "Bu buyurtma uchun izoh allaqachon mavjud"}, status=400)

            review = Review.objects.create(
                order=order,
                reviewer=request.user,
                seller=order.seller,
                rating=ser.validated_data["rating"],
                comment=ser.validated_data["comment"],
            )

            avg_rating = Review.objects.filter(seller=order.seller).aggregate(a=Avg("rating"))["a"] or 0
            SellerProfile.objects.filter(user_id=order.seller_id).update(rating=avg_rating)

        return Response(ReviewListSerializer(review).data, status=201)
