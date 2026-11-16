from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import DangNhapForm

urlpatterns = [
    path("", views.trang_chu, name="trang_chu"),
    path("thien-the/", views.danh_sach, name="danh_sach"),
    path("thien-the/<slug:slug>/", views.chi_tiet, name="chi_tiet"),
    path("tim-kiem/", views.tim_kiem, name="tim_kiem"),
    path("tim-kiem/goi-y/", views.goi_y, name="goi_y"),
    path("bai-viet/<int:pk>/", views.bai_viet, name="bai_viet"),
    path("bai-viet/<int:pk>/danh-gia/", views.danh_gia, name="danh_gia"),
    path("bai-viet/<int:pk>/yeu-thich/", views.doi_yeu_thich, name="doi_yeu_thich"),
    path("yeu-thich/", views.yeu_thich, name="yeu_thich"),
    path("so-sanh/", views.so_sanh, name="so_sanh"),
    path("can-nang/", views.can_nang, name="can_nang"),
    path("them/", views.them_bai, name="them_bai"),
    path("them/bai-viet/", views.them_bai_viet, name="them_bai_viet"),
    path("them/hanh-tinh/", views.them_thien_the, name="them_thien_the"),
    path("dang-ky/", views.dang_ky, name="dang_ky"),
    path(
        "dang-nhap/",
        auth_views.LoginView.as_view(template_name="registration/dang_nhap.html", authentication_form=DangNhapForm),
        name="dang_nhap",
    ),
    path("dang-xuat/", auth_views.LogoutView.as_view(), name="dang_xuat"),
]
