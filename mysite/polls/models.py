# 1 Category - категория
# 2 Product - продукт
# 3 CartProduct - продукт в корзине
# 4 Cart - корзина
# 5 Order - заказ
# ***************
# 6 Customer - покупатель
# 7 Specification - описание продукта
import sys
from PIL import Image

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse

from io import BytesIO

User = get_user_model()


def get_product_url(obj, viewname):
    ct_model = obj.__class__.meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


class MinResolutionErrorException(Exception):
    pass


class MaxResolutionErrorException(Exception):
    pass


class LatestProductsManager:

    @staticmethod
    def get_products_for_main_page(*args, **kwargs):

        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_models = ContentType.objects.filter(model = with_respect_to)
            if ct_models.exist():
                if with_respect_to in args:
                    return sorted(
                        products, key=lambda x: x.__class__.__meta__.model_name.startswith(with_respect_to), reverse=True
                        )

        return products


class LatestProducts:

    object = LatestProductsManager()


class Category(models.Model):

    name = models.CharField(max_length=255, verbose_name = 'Имя категории')
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):

    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (700, 400)
    MAX_IMAGE_SIZE = 3145728

    class Meta:
        abstract = True # abstract model, creating migration is not possible

    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name = 'Наименование')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение')
    description = models.TextField(verbose_name='Описание', null=True)
    price = models.PositiveIntegerField(verbose_name='Цена')


    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):

        # image = self.image
        # img = Image.open(image)
        # min_height, min_width = self.MIN_RESOLUTION
        # max_height, max_width = self.MAX_RESOLUTION
        # if img.height < min_height or img.width < min_width:
        #     raise MinResolutionErrorException('Разрешение изображения меньше минимального!')
        # if img.height > max_height or img.width > max_width:
        #     raise MaxResolutionErrorException('Разрешение изображения больше максимального!')
        image = self.image
        img = Image.open(image)
        new_img = img.convert('RGB')
        resized_new_img = new_img.resize((800, 700), Image.ANTIALIAS)
        filestream = BytesIO()
        resized_new_img.save(filestream, 'JPEG', quality=90)
        filestream.seek(0)
        name = '{}.{}'.format(*self.image.name.split('.'))
        self.image = InMemoryUploadedFile(
            filestream, 'ImageField', name, 'jpeg/image', sys.getsizeof(filestream), None
        )
        super().save(*args, **kwargs)


class Notebook(Product):

    diagonal = models.CharField(max_length = 255, verbose_name = 'Диагональ')
    display_type = models.CharField(max_length = 255, verbose_name = 'Тип дисплея')
    processor_freq = models.CharField(max_length = 255, verbose_name='Количество ядер процессора')
    ram = models.CharField(max_length = 255, verbose_name='Объём ОЗУ')
    video = models.CharField(max_length = 255, verbose_name='Видеокарта')
    time_without_charge = models.CharField(max_length = 255, verbose_name='Время автономной работы')

    def __str__(self):
        return '{}: {}'.format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class Smartphone(Product):

    diagonal = models.CharField(max_length = 255, verbose_name='Диагональ')
    display_type = models.CharField(max_length = 255, verbose_name='Тип дисплея')
    resolution = models.CharField(max_length = 255, verbose_name='Разрешение экрана')
    accum_volume = models.CharField(max_length = 255, verbose_name='Емкость аккумулятора')
    ram = models.CharField(max_length = 255, verbose_name='Объём ОЗУ')
    sd = models.BooleanField(default=True, verbose_name='Наличие SD карты')
    sd_volume_max = models.CharField(
        max_length = 255, null=True, blank=True, verbose_name='Максимальный объём SD карты'
                                    )
    main_cam_mp = models.CharField(max_length = 255, verbose_name='Задняя камера')
    frontal_cam_mp = models.CharField(max_length = 255, verbose_name='Фронтальная камера')

    def __str__(self):
        return '{}: {}'.format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')

    # @property
    # def sd(self):
    #     if self.sd:
    #         return 'Да'
    #     return 'Нет'

class CartProduct(models.Model):

    user = models.ForeignKey('Customer', verbose_name='Покупатель', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete = models.CASCADE) # micro framework whick determines in the amdin panel what models u have created
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')

def __str__(self):
        return 'Продукт: {} (для корзины)'.format(self.content_object.title)


class Cart(models.Model):

    owner = models.ForeignKey('Customer', verbose_name='Владелец', on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')
    email = models.CharField(max_length=255, verbose_name='Email')

    def __str__(self):
        return 'Покупатель {} {}'.format(self.user.first_name, self.user.last_name)





# class Specifacation(models.Model):
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.PositiveIntegerField()
#     name = models.CharField(max_length=255, verbose_name='Имя товара для характеристик')
#
#     def __str__(self):
#         return 'Характеристики для товара {}'.format(self.name)
