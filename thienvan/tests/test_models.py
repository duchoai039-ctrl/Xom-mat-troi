from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from thienvan.models import BaiViet, DanhGia, ThienThe, YeuThich
from thienvan.utils import bo_dau


def tao_hanh_tinh(ten="Sao Hỏa", ten_en="Mars", **kw):
    return ThienThe.objects.create(
        ten=ten, ten_en=ten_en, api_id=ten_en.lower(), loai=ThienThe.Loai.HANH_TINH, **kw
    )


def tao_ve_tinh(me, ten="Phobos", ten_en="Phobos", **kw):
    return ThienThe.objects.create(
        ten=ten, ten_en=ten_en, api_id=ten_en.lower(), loai=ThienThe.Loai.VE_TINH, hanh_tinh_me=me, **kw
    )


class BoDauTest(TestCase):
    def test_bo_dau_va_chu_thuong(self):
        self.assertEqual(bo_dau("MẶT TRĂNG"), "mat trang")

    def test_hai_cach_bo_dau_cho_cung_ket_qua(self):
        self.assertEqual(bo_dau("Sao Hỏa"), bo_dau("Sao Hoả"))

    def test_chu_d_gach(self):
        self.assertEqual(bo_dau("Trái Đất"), "trai dat")

    def test_gop_khoang_trang(self):
        self.assertEqual(bo_dau("  mặt   trăng "), "mat trang")


class ThienTheTest(TestCase):
    def test_tu_tao_ten_khong_dau_va_slug(self):
        hoa = tao_hanh_tinh()
        self.assertEqual(hoa.ten_khong_dau, "sao hoa")
        self.assertEqual(hoa.slug, "mars")

    def test_ban_kinh_khong_duong_khong_lam_vo_trang(self):
        # admin can type any float, and the size formula takes a logarithm
        for sai in (-5, 0):
            self.assertEqual(ThienThe(ban_kinh_km=sai).co_hinh, 40)

    def test_hanh_tinh_khong_duoc_co_hanh_tinh_me(self):
        hoa = tao_hanh_tinh()
        with self.assertRaises(IntegrityError), transaction.atomic():
            tao_hanh_tinh("Sao Mộc", "Jupiter", hanh_tinh_me=hoa)

    def test_ngoi_sao_khong_duoc_co_hanh_tinh_me(self):
        hoa = tao_hanh_tinh()
        with self.assertRaises(IntegrityError), transaction.atomic():
            ThienThe.objects.create(ten="Mặt Trời", ten_en="Sun", api_id="soleil", loai="sao", hanh_tinh_me=hoa)

    def test_ngoi_sao_khong_co_hanh_tinh_me_thi_hop_le(self):
        ThienThe.objects.create(ten="Mặt Trời", ten_en="Sun", api_id="soleil", loai="sao")
        self.assertEqual(ThienThe.objects.filter(loai="sao").count(), 1)

    def test_ve_tinh_bat_buoc_co_hanh_tinh_me(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            tao_ve_tinh(None)

    def test_khong_xoa_duoc_hanh_tinh_con_ve_tinh(self):
        hoa = tao_hanh_tinh()
        tao_ve_tinh(hoa)
        with self.assertRaises(ProtectedError):
            hoa.delete()


class NhieuBaiVietTest(TestCase):
    def test_mot_thien_the_co_nhieu_bai_va_bai_dau_la_bai_chinh(self):
        hoa = tao_hanh_tinh()
        dau = BaiViet.objects.create(thien_the=hoa, tieu_de="A", noi_dung="N")
        sau = BaiViet.objects.create(thien_the=hoa, tieu_de="B", noi_dung="N")
        self.assertEqual(list(hoa.cac_bai.all()), [dau, sau])
        self.assertEqual(dau.get_absolute_url(), hoa.get_absolute_url())
        self.assertEqual(sau.get_absolute_url(), f"/bai-viet/{sau.pk}/")


class DanhGiaYeuThichTest(TestCase):
    def setUp(self):
        self.bai = BaiViet.objects.create(thien_the=tao_hanh_tinh(), tieu_de="T", noi_dung="N")
        self.user = User.objects.create_user("0912345678", password="x")

    def test_mot_nguoi_chi_co_mot_danh_gia_moi_bai(self):
        DanhGia.objects.create(nguoi_dung=self.user, bai_viet=self.bai, so_sao=5)
        with self.assertRaises(IntegrityError), transaction.atomic():
            DanhGia.objects.create(nguoi_dung=self.user, bai_viet=self.bai, so_sao=4)

    def test_so_sao_ngoai_1_den_5_bi_chan_o_database(self):
        for sai in (0, 6):
            with self.assertRaises(IntegrityError), transaction.atomic():
                DanhGia.objects.create(nguoi_dung=self.user, bai_viet=self.bai, so_sao=sai)

    def test_mot_nguoi_chi_luu_mot_lan_moi_bai(self):
        YeuThich.objects.create(nguoi_dung=self.user, bai_viet=self.bai)
        with self.assertRaises(IntegrityError), transaction.atomic():
            YeuThich.objects.create(nguoi_dung=self.user, bai_viet=self.bai)
