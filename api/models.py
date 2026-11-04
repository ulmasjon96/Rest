from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from restaurant.models import validate_image


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Product(models.Model):
    name = models.CharField(_('Nomi'), max_length=200)
    description = models.TextField(_('Tavsif'), blank=True)
    price = models.DecimalField(_('Narxi (so‘m)'), max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField(_('Soni'), default=0)
    image = models.ImageField(_('Rasm'), upload_to='products/', blank=True, validators=[validate_image])
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='products', verbose_name=_('Yaratgan'),
    )
    created_at = models.DateTimeField(_('Yaratilgan sana'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Yangilangan sana'), auto_now=True)

    class Meta:
        verbose_name = _('Mahsulot')
        verbose_name_plural = _('Mahsulotlar')
        ordering = ['-created_at']

    def __str__(self):
        return self.name
