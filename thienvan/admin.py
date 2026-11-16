from django.contrib import admin

from .models import BaiViet, DanhGia, ThienThe, YeuThich


@admin.register(ThienThe)
class ThienTheAdmin(admin.ModelAdmin):
    list_display = ["ten", "ten_en", "loai", "hanh_tinh_me", "thu_tu"]
    list_filter = ["loai", "hanh_tinh_me"]
    search_fields = ["ten", "ten_en"]


@admin.register(BaiViet)
class BaiVietAdmin(admin.ModelAdmin):
    list_display = ["tieu_de", "thien_the", "ngay_dang"]
    list_filter = ["thien_the"]
    search_fields = ["tieu_de"]


@admin.register(DanhGia)
class DanhGiaAdmin(admin.ModelAdmin):
    list_display = ["bai_viet", "nguoi_dung", "so_sao"]


@admin.register(YeuThich)
class YeuThichAdmin(admin.ModelAdmin):
    list_display = ["bai_viet", "nguoi_dung", "ngay_luu"]
