import math

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import slugify

from .utils import bo_dau

# Solar System Scope only publishes textures for these bodies
TEXTURE = {
    "sun": "sun.jpg",
    "mercury": "mercury.jpg",
    "venus": "venus_surface.jpg",
    "earth": "earth_daymap.jpg",
    "mars": "mars.jpg",
    "jupiter": "jupiter.jpg",
    "saturn": "saturn.jpg",
    "uranus": "uranus.jpg",
    "neptune": "neptune.jpg",
    "moon": "moon.jpg",
}


class ThienThe(models.Model):
    class Loai(models.TextChoices):
        HANH_TINH = "hanh_tinh", "Hành tinh"
        VE_TINH = "ve_tinh", "Vệ tinh"
        SAO = "sao", "Ngôi sao"

    ten = models.CharField("tên", max_length=50)
    ten_en = models.CharField("tên tiếng Anh", max_length=50)
    ten_khong_dau = models.CharField(max_length=50, editable=False, db_index=True)
    slug = models.SlugField(unique=True, blank=True)
    api_id = models.CharField(max_length=50, unique=True)
    loai = models.CharField("loại", max_length=10, choices=Loai.choices)
    hanh_tinh_me = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True,
        related_name="ve_tinh", verbose_name="hành tinh mẹ",
    )
    thu_tu = models.PositiveSmallIntegerField("thứ tự", default=0)
    mau = models.CharField("màu đại diện", max_length=7, default="#B8AEDB")

    ban_kinh_km = models.FloatField("bán kính (km)", null=True, blank=True)
    khoi_luong_kg = models.FloatField("khối lượng (kg)", null=True, blank=True)
    trong_luc = models.FloatField("trọng lực (m/s²)", null=True, blank=True)
    chu_ky_quy_dao_ngay = models.FloatField("chu kỳ quỹ đạo (ngày)", null=True, blank=True)
    chu_ky_tu_quay_gio = models.FloatField("chu kỳ tự quay (giờ)", null=True, blank=True)
    nhiet_do_tb_k = models.FloatField("nhiệt độ trung bình (K)", null=True, blank=True)

    class Meta:
        verbose_name = "thiên thể"
        verbose_name_plural = "thiên thể"
        ordering = ["thu_tu", "ten"]
        constraints = [
            models.CheckConstraint(
                name="dung_quan_he_hanh_tinh_me",
                condition=Q(loai__in=["hanh_tinh", "sao"], hanh_tinh_me__isnull=True)
                | Q(loai="ve_tinh", hanh_tinh_me__isnull=False),
            ),
        ]

    def __str__(self):
        return self.ten

    def save(self, *args, **kwargs):
        self.ten_khong_dau = bo_dau(self.ten)
        if not self.slug:
            self.slug = slugify(self.ten_en)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("chi_tiet", args=[self.slug])

    @property
    def la_hanh_tinh(self):
        return self.loai == self.Loai.HANH_TINH

    @property
    def co_hinh(self):
        """Đường kính hình tròn (px): to nhỏ theo bán kính nhưng nén lại để Phobos vẫn nhìn thấy cạnh Sao Mộc."""
        if not self.ban_kinh_km or self.ban_kinh_km < 0:
            return 40
        return round(24 + ((math.log10(self.ban_kinh_km) - 0.8) / 4) ** 2 * 140)

    @property
    def texture_url(self):
        ten_file = TEXTURE.get(self.slug)
        return static(f"textures/{ten_file}") if ten_file else ""


class BaiViet(models.Model):
    thien_the = models.ForeignKey(ThienThe, on_delete=models.CASCADE, related_name="cac_bai", verbose_name="thiên thể")
    tieu_de = models.CharField("tiêu đề", max_length=120)
    noi_dung = models.TextField("nội dung")
    co_the_ban_chua_biet = models.TextField("có thể bạn chưa biết", blank=True)
    ngay_dang = models.DateTimeField("ngày đăng", auto_now_add=True)

    class Meta:
        verbose_name = "bài viết"
        verbose_name_plural = "bài viết"
        ordering = ["ngay_dang", "id"]

    def __str__(self):
        return self.tieu_de

    def get_absolute_url(self):
        # the oldest article is the main one and lives on the body's own page
        if self.thien_the.cac_bai.first() == self:
            return self.thien_the.get_absolute_url()
        return reverse("bai_viet", args=[self.pk])


class DanhGia(models.Model):
    nguoi_dung = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="người dùng")
    bai_viet = models.ForeignKey(BaiViet, on_delete=models.CASCADE, related_name="danh_gia", verbose_name="bài viết")
    so_sao = models.PositiveSmallIntegerField("số sao")

    class Meta:
        verbose_name = "đánh giá"
        verbose_name_plural = "đánh giá"
        constraints = [
            models.UniqueConstraint(fields=["nguoi_dung", "bai_viet"], name="moi_nguoi_mot_danh_gia"),
            models.CheckConstraint(name="so_sao_tu_1_den_5", condition=Q(so_sao__gte=1, so_sao__lte=5)),
        ]


class YeuThich(models.Model):
    nguoi_dung = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="người dùng")
    bai_viet = models.ForeignKey(BaiViet, on_delete=models.CASCADE, related_name="yeu_thich", verbose_name="bài viết")
    ngay_luu = models.DateTimeField("ngày lưu", auto_now_add=True)

    class Meta:
        verbose_name = "yêu thích"
        verbose_name_plural = "yêu thích"
        ordering = ["-ngay_luu"]
        constraints = [
            models.UniqueConstraint(fields=["nguoi_dung", "bai_viet"], name="moi_nguoi_luu_mot_lan"),
        ]
