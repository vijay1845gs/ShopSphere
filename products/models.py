from django.db import models
from django.urls import reverse


class ProductQuerySet(models.QuerySet):
    """
    Custom QuerySet attached to Product.
    Reusable filter chains — no repeated .filter() calls across views/services.
    """

    def active(self):
        return self.filter(is_active=True)

    def in_stock(self):
        return self.filter(stock__gt=0)

    def by_category(self, slug: str):
        return self.filter(category__slug=slug)

    def with_relations(self):
        """Standard select_related + prefetch for list views."""
        return self.select_related("category").prefetch_related("tags")


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def in_stock(self):
        return self.get_queryset().in_stock()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_list") + f"?category={self.slug}"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "category"]),
            models.Index(fields=["price"]),
            models.Index(fields=["stock"]),  # added for in_stock() filter performance
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})

    def is_in_stock(self) -> bool:
        return self.stock > 0

    def get_meta_title(self) -> str:
        return self.meta_title or self.name

    def get_meta_description(self) -> str:
        return self.meta_description or self.description[:160]

    def decrement_stock(self, quantity: int) -> None:
        """
        Decrement stock by quantity. Raises ValueError if insufficient.
        Should only be called inside a select_for_update() transaction.
        """
        if self.stock < quantity:
            raise ValueError(
                f"Insufficient stock for '{self.name}': "
                f"requested {quantity}, available {self.stock}."
            )
        self.stock -= quantity
        self.save(update_fields=["stock", "updated_at"])

    def restore_stock(self, quantity: int) -> None:
        """Restore stock on order cancellation."""
        self.stock += quantity
        self.save(update_fields=["stock", "updated_at"])
