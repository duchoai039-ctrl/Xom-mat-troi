from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from thienvan.forms import chuan_hoa_dinh_danh

MAT_KHAU = "sao-hoa-do-rực-2026"


def dang_ky(client, dinh_danh):
    return client.post(reverse("dang_ky"), {"username": dinh_danh, "password1": MAT_KHAU, "password2": MAT_KHAU})


class ChuanHoaTest(TestCase):
    def test_so_dien_thoai_hop_le(self):
        for nhap in ("0912345678", "+84912345678", "0912 345 678", "091-234-5678"):
            self.assertEqual(chuan_hoa_dinh_danh(nhap), "0912345678")

    def test_gmail_khong_phan_biet_hoa_thuong(self):
        self.assertEqual(chuan_hoa_dinh_danh(" Duc.Hoai@GMAIL.com "), "duc.hoai@gmail.com")

    def test_tu_choi_sai_dinh_dang(self):
        for sai in ("", "12345", "091234567a", "ban@outlook.com", "@gmail.com", "ten_dang_nhap"):
            with self.assertRaises(ValidationError):
                chuan_hoa_dinh_danh(sai)


class DangKyTest(TestCase):
    def test_dang_ky_bang_so_dien_thoai_thi_dang_nhap_luon(self):
        phan_hoi = dang_ky(self.client, "+84912345678")
        self.assertRedirects(phan_hoi, reverse("trang_chu"))
        user = User.objects.get(username="0912345678")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_dang_ky_bang_gmail(self):
        dang_ky(self.client, "Duc@Gmail.com")
        self.assertTrue(User.objects.filter(username="duc@gmail.com").exists())

    def test_trung_so_dang_viet_khac_van_bi_chan(self):
        dang_ky(self.client, "0912345678")
        self.client.logout()
        phan_hoi = dang_ky(self.client, "+84912345678")
        self.assertEqual(phan_hoi.status_code, 200)
        self.assertContains(phan_hoi, "đã được đăng ký")
        self.assertEqual(User.objects.count(), 1)

    def test_email_khac_gmail_bi_tu_choi(self):
        dang_ky(self.client, "ban@outlook.com")
        self.assertEqual(User.objects.count(), 0)


class DangNhapTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("0912345678", password=MAT_KHAU)

    def dang_nhap(self, dinh_danh):
        return self.client.post(reverse("dang_nhap"), {"username": dinh_danh, "password": MAT_KHAU})

    def test_dang_nhap_bang_cach_viet_khac_cua_cung_so(self):
        self.assertRedirects(self.dang_nhap("+84912345678"), reverse("trang_chu"))

    def test_sai_mat_khau_bao_loi_tieng_viet(self):
        phan_hoi = self.client.post(reverse("dang_nhap"), {"username": "0912345678", "password": "sai"})
        self.assertContains(phan_hoi, "không đúng")

    def test_tai_khoan_bi_chan_khong_dang_nhap_duoc(self):
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        self.assertEqual(self.dang_nhap("0912345678").status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_bi_chan_khi_dang_dang_nhap_thi_mat_phien(self):
        self.dang_nhap("0912345678")
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        phan_hoi = self.client.get(reverse("yeu_thich"))
        self.assertEqual(phan_hoi.status_code, 302)
        self.assertIn(reverse("dang_nhap"), phan_hoi.url)

    def test_dang_xuat(self):
        self.dang_nhap("0912345678")
        self.assertRedirects(self.client.post(reverse("dang_xuat")), reverse("trang_chu"))
        self.assertNotIn("_auth_user_id", self.client.session)
