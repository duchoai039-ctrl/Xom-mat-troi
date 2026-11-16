from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from thienvan.models import BaiViet, DanhGia, ThienThe, YeuThich

from .test_models import tao_hanh_tinh

TRANG_QUAN_TRI = ("them_bai", "them_bai_viet", "them_thien_the")


class CoSoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.quan_tri = User.objects.create_user("admin", password="x", is_staff=True)
        cls.thuong = User.objects.create_user("0912345678", password="x")
        cls.hoa = tao_hanh_tinh(thu_tu=1)
        cls.bai_chinh = BaiViet.objects.create(thien_the=cls.hoa, tieu_de="Bài chính", noi_dung="Nội dung chính")


class QuyenTest(CoSoTest):
    def test_khach_bi_dua_den_dang_nhap(self):
        for ten in TRANG_QUAN_TRI:
            phan_hoi = self.client.get(reverse(ten))
            self.assertEqual(phan_hoi.status_code, 302, ten)
            self.assertIn(reverse("dang_nhap"), phan_hoi.url)

    def test_nguoi_dung_thuong_bi_tu_choi(self):
        self.client.force_login(self.thuong)
        for ten in TRANG_QUAN_TRI:
            self.assertEqual(self.client.get(reverse(ten)).status_code, 403, ten)

    def test_nguoi_dung_thuong_khong_gui_duoc_form(self):
        self.client.force_login(self.thuong)
        self.client.post(reverse("them_bai_viet"), {"thien_the": self.hoa.pk, "tieu_de": "X", "noi_dung": "Y"})
        self.client.post(reverse("them_thien_the"), {"ten": "Ceres", "ten_en": "Ceres", "mau": "#123456"})
        self.assertEqual(BaiViet.objects.count(), 1)
        self.assertEqual(ThienThe.objects.count(), 1)

    def test_chi_admin_thay_muc_tren_menu(self):
        url = f'href="{reverse("them_bai")}"'
        self.assertNotContains(self.client.get(reverse("danh_sach")), url)
        self.client.force_login(self.thuong)
        self.assertNotContains(self.client.get(reverse("danh_sach")), url)
        self.client.force_login(self.quan_tri)
        self.assertContains(self.client.get(reverse("danh_sach")), url)


class TrangChonTest(CoSoTest):
    def test_co_hai_lua_chon(self):
        self.client.force_login(self.quan_tri)
        phan_hoi = self.client.get(reverse("them_bai"))
        self.assertContains(phan_hoi, f'href="{reverse("them_bai_viet")}"')
        self.assertContains(phan_hoi, f'href="{reverse("them_thien_the")}"')
        self.assertContains(phan_hoi, "beta")


class ThemBaiVietTest(CoSoTest):
    def setUp(self):
        self.client.force_login(self.quan_tri)

    def gui(self, **du_lieu):
        mac_dinh = {"thien_the": self.hoa.pk, "tieu_de": "Bão bụi", "noi_dung": "Bão phủ cả hành tinh", "co_the_ban_chua_biet": ""}
        return self.client.post(reverse("them_bai_viet"), {**mac_dinh, **du_lieu})

    def test_them_duoc_vao_thien_the_da_co_bai(self):
        phan_hoi = self.gui()
        bai = BaiViet.objects.get(tieu_de="Bão bụi")
        self.assertEqual(bai.thien_the, self.hoa)
        self.assertRedirects(phan_hoi, bai.get_absolute_url())

    def test_bai_cu_van_la_bai_chinh(self):
        self.gui()
        phan_hoi = self.client.get(self.hoa.get_absolute_url())
        self.assertEqual(phan_hoi.context["bai"], self.bai_chinh)
        self.assertContains(phan_hoi, "Nội dung chính")
        self.assertNotContains(phan_hoi, "Bão phủ cả hành tinh")

    def test_trang_thien_the_liet_ke_bai_khac(self):
        self.gui()
        bai = BaiViet.objects.get(tieu_de="Bão bụi")
        phan_hoi = self.client.get(self.hoa.get_absolute_url())
        self.assertContains(phan_hoi, f'href="{bai.get_absolute_url()}"')

    def test_thieu_tieu_de_bao_loi_va_giu_noi_dung_da_go(self):
        phan_hoi = self.gui(tieu_de="")
        self.assertEqual(phan_hoi.status_code, 200)
        self.assertEqual(BaiViet.objects.count(), 1)
        self.assertContains(phan_hoi, "Bão phủ cả hành tinh")

    def test_chon_san_thien_the_tu_lien_ket(self):
        phan_hoi = self.client.get(reverse("them_bai_viet"), {"thien_the": "mars"})
        self.assertEqual(phan_hoi.context["form"].initial["thien_the"], self.hoa)

    def test_lien_ket_chon_san_sai_khong_vo_trang(self):
        self.assertEqual(self.client.get(reverse("them_bai_viet"), {"thien_the": "khong-co"}).status_code, 200)

    def test_noi_dung_duoc_escape(self):
        self.gui(noi_dung="<script>alert(1)</script>")
        phan_hoi = self.client.get(BaiViet.objects.get(tieu_de="Bão bụi").get_absolute_url())
        self.assertNotContains(phan_hoi, "<script>alert(1)")


class TrangBaiVietTest(CoSoTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.bai_phu = BaiViet.objects.create(
            thien_the=cls.hoa, tieu_de="Bão bụi", noi_dung="Bão phủ cả hành tinh", co_the_ban_chua_biet="Vui vui"
        )

    def test_hien_noi_dung_va_quay_lai_thien_the(self):
        phan_hoi = self.client.get(self.bai_phu.get_absolute_url())
        self.assertContains(phan_hoi, "Bão phủ cả hành tinh")
        self.assertContains(phan_hoi, "Vui vui")
        self.assertContains(phan_hoi, f'href="{self.hoa.get_absolute_url()}"')

    def test_bai_chinh_chuyen_ve_trang_thien_the(self):
        phan_hoi = self.client.get(reverse("bai_viet", args=[self.bai_chinh.pk]))
        self.assertRedirects(phan_hoi, self.hoa.get_absolute_url())

    def test_bai_khong_ton_tai_tra_404(self):
        self.assertEqual(self.client.get(reverse("bai_viet", args=[9999])).status_code, 404)

    def test_cham_sao_rieng_tung_bai_va_quay_lai_dung_trang(self):
        self.client.force_login(self.thuong)
        phan_hoi = self.client.post(reverse("danh_gia", args=[self.bai_phu.pk]), {"so_sao": "2"})
        self.assertRedirects(phan_hoi, self.bai_phu.get_absolute_url())
        self.assertEqual(DanhGia.objects.get().bai_viet, self.bai_phu)
        self.assertEqual(self.client.get(self.bai_phu.get_absolute_url()).context["diem_tb"], 2)
        self.assertIsNone(self.client.get(self.hoa.get_absolute_url()).context["diem_tb"])

    def test_luu_bai_phu_va_mo_dung_bai_tu_danh_sach(self):
        self.client.force_login(self.thuong)
        self.assertRedirects(
            self.client.post(reverse("doi_yeu_thich", args=[self.bai_phu.pk])), self.bai_phu.get_absolute_url()
        )
        self.assertEqual(YeuThich.objects.get().bai_viet, self.bai_phu)
        self.assertContains(self.client.get(reverse("yeu_thich")), f'href="{self.bai_phu.get_absolute_url()}"')

    def test_khach_cham_sao_dang_nhap_xong_quay_lai_dung_bai(self):
        phan_hoi = self.client.post(reverse("danh_gia", args=[self.bai_phu.pk]), {"so_sao": "2"})
        self.assertIn(self.bai_phu.get_absolute_url().replace("/", "%2F"), phan_hoi.url.replace("/", "%2F"))

    def test_xoa_bai_chinh_thi_bai_tiep_theo_len_lam_bai_chinh(self):
        self.bai_chinh.delete()
        self.assertEqual(self.client.get(self.hoa.get_absolute_url()).context["bai"], self.bai_phu)


class ThemThienTheTest(CoSoTest):
    def setUp(self):
        self.client.force_login(self.quan_tri)

    def gui(self, **du_lieu):
        return self.client.post(reverse("them_thien_the"), {"ten": "Sao Ceres", "ten_en": "Ceres", "mau": "#123456", **du_lieu})

    def loi(self, truong, **du_lieu):
        phan_hoi = self.gui(**du_lieu)
        self.assertEqual(phan_hoi.status_code, 200)
        self.assertIn(truong, phan_hoi.context["form"].errors)
        self.assertEqual(ThienThe.objects.count(), 1)

    def test_tao_hanh_tinh_moi_roi_mo_trang_cua_no(self):
        phan_hoi = self.gui(ban_kinh_km="473", trong_luc="0.28")
        moi = ThienThe.objects.get(slug="ceres")
        self.assertRedirects(phan_hoi, moi.get_absolute_url())
        self.assertEqual((moi.loai, moi.hanh_tinh_me, moi.ban_kinh_km), ("hanh_tinh", None, 473))
        self.assertEqual(moi.ten_khong_dau, "sao ceres")

    def test_hien_tren_trang_chu_sau_cac_hanh_tinh_co_san(self):
        self.gui()
        ds = list(self.client.get(reverse("trang_chu")).context["hanh_tinh"])
        self.assertEqual([t.slug for t in ds], ["mars", "ceres"])

    def test_chua_co_bai_thi_admin_co_loi_tat_them_bai(self):
        self.gui()
        phan_hoi = self.client.get(ThienThe.objects.get(slug="ceres").get_absolute_url())
        self.assertContains(phan_hoi, f'{reverse("them_bai_viet")}?thien_the=ceres')

    def test_khach_khong_thay_loi_tat_them_bai(self):
        self.client.logout()
        self.assertNotContains(self.client.get(self.hoa.get_absolute_url()), reverse("them_bai_viet"))

    def test_trung_ten_tieng_anh_bi_tu_choi(self):
        self.loi("ten_en", ten_en="Mars")

    def test_trung_ten_tieng_viet_du_khac_cach_bo_dau(self):
        self.loi("ten", ten="Sao Hoả")

    def test_ten_tieng_anh_khong_tao_duoc_duong_dan(self):
        self.loi("ten_en", ten_en="火星")

    def test_so_khong_duong_bi_tu_choi(self):
        for truong in ("ban_kinh_km", "khoi_luong_kg", "trong_luc", "chu_ky_quy_dao_ngay", "nhiet_do_tb_k"):
            self.loi(truong, **{truong: "-1"})

    def test_chu_ky_tu_quay_am_hop_le(self):
        self.gui(chu_ky_tu_quay_gio="-10")
        self.assertEqual(ThienThe.objects.get(slug="ceres").chu_ky_tu_quay_gio, -10)

    def test_mau_sai_dinh_dang_bi_tu_choi(self):
        self.loi("mau", mau="red;x")
