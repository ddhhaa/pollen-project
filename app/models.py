from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    age = models.PositiveIntegerField(null=True, blank=True)

    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Аллергены пользователя
    allergens = models.ManyToManyField(
        'PollenType',
        through='UserAllergy',
        related_name='profiles',
        verbose_name="Аллергены пользователя",
        blank=True
    )

    def __str__(self):
        return f"Профиль: {self.user.username}"
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class PollenType(models.Model):
    """Типы пыльцы (растения)"""
    POLLEN_CATEGORIES = [
        ('tree', 'Дерево'),
        ('grass', 'Трава'),
        ('weed', 'Сорняк'),
    ]
    
    # Основные поля
    name = models.CharField(max_length=100, verbose_name="Название")  # "Берёза", "Амброзия"

    # Код для Open-Meteo API
    openmeteo_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Код в Open-Meteo",
        help_text="Например: birch_pollen, grass_pollen"
    )
    
    # Категория
    category = models.CharField(
        max_length=10,
        choices=POLLEN_CATEGORIES,
        verbose_name="Категория"
    )
    
    # Аллергенность
    ALLERGENICITY_CHOICES = [
        (0.2, 'Очень низкая'),
        (0.4, 'Низкая'),
        (0.7, 'Средняя'),
        (1.0, 'Высокая'),
        (1.3, 'Очень высокая'),
    ]
    
    allergenicity = models.FloatField(
        choices=ALLERGENICITY_CHOICES,
        default=0.7,
        verbose_name="Коэффициент аллергенности",
        help_text="1.0 = береза (эталон)"
    )
    
    # Цвет для отображения
    color = models.CharField(
        max_length=7,
        default='#FF0000',
        verbose_name="Цвет на графике"
    )
    
    class Meta:
        verbose_name = "Тип пыльцы"
        verbose_name_plural = "Типы пыльцы"
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

class PollenData(models.Model):
    """Данные о концентрации пыльцы"""
    
    # Связь с типом пыльцы вместо прямого выбора
    pollen_type = models.ForeignKey(
        PollenType,
        on_delete=models.CASCADE,
        related_name='data',
        verbose_name="Тип пыльцы"
    )
    
    # Локация
    city = models.CharField(max_length=100, verbose_name="Город")
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    
    # Время
    date = models.DateField(verbose_name="Дата")
    hour = models.IntegerField(
        null=True, blank=True,
        verbose_name="Час",
        help_text="Час измерения (0-23), если есть"
    )
    
    # Данные
    concentration = models.FloatField(
        verbose_name="Концентрация (grains/m³)",
        help_text="Концентрация пыльцы в grains на кубический метр"
    )
    
    class Meta:
        verbose_name = "Данные о пыльце"
        verbose_name_plural = "Данные о пыльце"
        indexes = [
            models.Index(fields=['date', 'pollen_type']),
            models.Index(fields=['city']),
            models.Index(fields=['latitude', 'longitude']),
        ]
        ordering = ['-date', '-hour']
    
    def __str__(self):
        return f"{self.city} | {self.pollen_type.name} | {self.date} | {self.concentration} grains/m³"

class UserAllergy(models.Model):
    """Какие типы пыльцы вызывают аллергию у пользователя"""
    
    SENSITIVITY_CHOICES = [
        (1, 'Очень низкая'),
        (2, 'Низкая'),
        (3, 'Средняя'),
        (4, 'Высокая'),
        (5, 'Очень высокая'),
    ]
    
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='allergies',
        verbose_name="Пользователь"
    )
    
    pollen_type = models.ForeignKey(
        PollenType,
        on_delete=models.CASCADE,
        related_name='allergic_users',
        verbose_name="Тип пыльцы"
    )
    
    sensitivity = models.IntegerField(
        choices=SENSITIVITY_CHOICES,
        default=3,
        verbose_name="Чувствительность"
    )
    class Meta:
        verbose_name = "Аллергия пользователя"
        verbose_name_plural = "Аллергии пользователей"
        unique_together = ['user', 'pollen_type']  # Одна запись на пару пользователь-аллерген
    
    def __str__(self):
        return f"{self.user} - аллергия на {self.pollen_type.name}"

class Recommendation(models.Model):
    """Рекомендации для аллергиков"""
    
    CATEGORY_CHOICES = [
        ('prevention', 'Профилактика'),
        ('medication', 'Лекарства'),
        ('lifestyle', 'Образ жизни'),
        ('home', 'Дом'),
        ('outdoor', 'На улице'),
        ('emergency', 'Экстренные случаи'),
    ]
    
    # Категория рекомендации
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='lifestyle',
        verbose_name="Категория"
    )
    
    # Для какого типа пыльцы (необязательно)
    pollen_type = models.ForeignKey(
        PollenType,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Тип пыльцы"
    )
    
    # Текст рекомендации
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст рекомендации")
    

    # Особые отметки
    # for_asthma = models.BooleanField(default=False, verbose_name="Для астматиков")
    
    # Активность
    # is_active = models.BooleanField(default=True, verbose_name="Активно")
    
    class Meta:
        verbose_name = "Рекомендация"
        verbose_name_plural = "Рекомендации"
        ordering = ['category']
    
    def __str__(self):
        return self.title

