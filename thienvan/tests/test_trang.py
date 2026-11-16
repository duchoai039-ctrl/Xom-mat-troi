from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from thienvan.models import BaiViet, DanhGia, ThienThe, YeuThich
from thienvan.views import viet_khoi_luong, viet_nhiet_do, viet_so, viet_tu_quay

from .test_models import tao_hanh_tinh, tao_ve_tinh


class DuLieuMauTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hoa = tao_hanh_tinh(trong_luc=3.71, ban_kinh_km=3389.5)
        cls.kim = tao_hanh_tinh("Sao Kim", "Venus")
        cls.dat = tao_hanh_tinh("Trái Đất", "Earth")
        cls.phobos = tao_ve_tinh(cls.hoa)
        cls.trang = tao_ve_tinh(cls.dat, "Mặt Trăng", "Moon")
        cls.bai = BaiViet.objects.create(
            thien_the=cls.hoa, tieu_de="Hành tinh đỏ", noi_dung="Bụi đỏ khắp nơi", co_the_ban_chua_biet="Hoàng hôn màu xanh"
        )
        cls.user = User.objects.create_user("0912345678", password="x")
        cls.user2 = User.objects.create_user("0987654321", password="x")


class DinhDangSoTest(TestCase):
    def test_so_lon_co_dau_cham_ngan_cach(self):
        self.assertEqual(viet_so(3389.5), "3.389,5")
        self.assertEqual(viet_so(69911.0), "69.911")

    def test_so_nho_giu_du_chu_so(self):
        self.assertEqual(viet_so(0.0057), "0,0057")

    def test_nhiet_do_lam_tron_do_c(self):
        self.assertEqual(viet_nhiet_do(210), "210 K (-63 °C)")

    def test_khoi_luong_dang_khoa_hoc(self):
        self.assertEqual(viet_khoi_luong(6.417e23), "6,417 × 10²³ kg")

    def test_quay_nguoc_chieu(self):
        self.assertEqual(viet_tu_quay(-5832.5), "5.832,5 giờ, quay ngược chiều")


class DanhSachTest(DuLieuMauTest):
    def ten(self, **tham_so):
        phan_hoi = self.client.get(reverse("danh_sach"), tham_so)
        self.assertEqual(phan_hoi.status_code, 200)
        return {t.slug for t in phan_hoi.context["thien_the"]}

    def test_khong_loc_thay_tat_ca(self):
        self.assertEqual(len(self.ten()), 5)

    def test_loc_theo_loai(self):
        self.assertEqual(self.ten(loai="ve_tinh"), {"phobos", "moon"})

    def test_loc_theo_hanh_tinh_me(self):
        self.assertEqual(self.ten(hanh_tinh="mars"), {"phobos"})

    def test_tham_so_loc_sai_thi_bo_qua(self):
        self.assertEqual(len(self.ten(loai="sao-choi")), 5)

    def test_hanh_tinh_khong_co_ve_tinh_hien_thong_bao(self):
        phan_hoi = self.client.get(reverse("danh_sach"), {"hanh_tinh": "venus"})
        self.assertContains(phan_hoi, "Không có thiên thể nào")


class ChiTietTest(DuLieuMauTest):
    def test_hien_so_lieu_bai_viet_va_ve_tinh(self):
        phan_hoi = self.client.get(self.hoa.get_absolute_url())
        for chu in ("Bụi đỏ khắp nơi", "Hoàng hôn màu xanh", "Phobos", "3,71"):
            self.assertContains(phan_hoi, chu)

    def test_so_lieu_rong_hien_chua_co(self):
        self.assertContains(self.client.get(self.hoa.get_absolute_url()), "Chưa có")

    def test_chua_co_bai_viet_van_mo_duoc(self):
        phan_hoi = self.client.get(self.kim.get_absolute_url())
        self.assertContains(phan_hoi, "Bài về Sao Kim đang được viết")

    def test_slug_sai_tra_404(self):
        self.assertEqual(self.client.get("/thien-the/khong-co/").status_code, 404)

    def test_khach_khong_thay_form_cham_sao(self):
        phan_hoi = self.client.get(self.hoa.get_absolute_url())
        self.assertNotContains(phan_hoi, reverse("danh_gia", args=[self.bai.pk]))
        self.assertContains(phan_hoi, "Đăng nhập")


class GoiYTest(DuLieuMauTest):
    def goi_y(self, q):
        return [m["ten"] for m in self.client.get(reverse("goi_y"), {"q": q}).json()["ket_qua"]]

    def test_khong_dau_va_hoa_thuong_deu_ra(self):
        for q in ("mat trang", "MẶT TRĂNG", "mặt   trăng", "Mặt"):
            self.assertEqual(self.goi_y(q), ["Mặt Trăng"], q)

    def test_hai_cach_bo_dau_deu_ra(self):
        for q in ("Sao Hỏa", "Sao Hoả"):
            self.assertEqual(self.goi_y(q), ["Sao Hỏa"], q)

    def test_tim_duoc_ten_tieng_anh(self):
        self.assertEqual(self.goi_y("moon"), ["Mặt Trăng"])

    def test_o_rong_khong_tra_gi(self):
        self.assertEqual(self.goi_y("   "), [])

    def test_trang_ket_qua_khong_can_javascript(self):
        phan_hoi = self.client.get(reverse("tim_kiem"), {"q": "mat trang"})
        self.assertContains(phan_hoi, "Mặt Trăng")
        self.assertNotContains(phan_hoi, "Phobos")

    def test_trang_ket_qua_khong_tim_thay(self):
        phan_hoi = self.client.get(reverse("tim_kiem"), {"q": "xyz"})
        self.assertContains(phan_hoi, "Chưa thấy")


class DanhGiaTest(DuLieuMauTest):
    def cham(self, so_sao):
        return self.client.post(reverse("danh_gia", args=[self.bai.pk]), {"so_sao": so_sao})

    def test_khach_bi_dua_den_dang_nhap(self):
        self.assertIn(reverse("dang_nhap"), self.cham(5).url)
        self.assertEqual(DanhGia.objects.count(), 0)

    def test_bieu_tuong_la_svg_khong_phu_thuoc_font_tung_may(self):
        self.client.force_login(self.user)
        phan_hoi = self.client.get(self.hoa.get_absolute_url())
        for ky_tu in ("★", "♥", "♡"):
            self.assertNotContains(phan_hoi, ky_tu)
        self.assertContains(phan_hoi, '<svg class="bieu-tuong"', count=6)

    def test_cham_sao(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.cham(4), self.hoa.get_absolute_url())
        self.assertEqual(DanhGia.objects.get().so_sao, 4)

    def test_cham_lai_thi_cap_nhat_khong_them_luot(self):
        self.client.force_login(self.user)
        self.cham(1)
        self.cham(5)
        self.assertEqual(DanhGia.objects.get().so_sao, 5)

    def test_so_sao_sai_bi_tu_choi(self):
        self.client.force_login(self.user)
        for sai in ("0", "6", "abc", ""):
            self.assertEqual(self.cham(sai).status_code, 400, sai)
        self.assertEqual(DanhGia.objects.count(), 0)

    def test_khong_nhan_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("danh_gia", args=[self.bai.pk])).status_code, 405)

    def test_diem_trung_binh(self):
        DanhGia.objects.create(nguoi_dung=self.user, bai_viet=self.bai, so_sao=5)
        DanhGia.objects.create(nguoi_dung=self.user2, bai_viet=self.bai, so_sao=2)
        phan_hoi = self.client.get(self.hoa.get_absolute_url())
        self.assertEqual(phan_hoi.context["diem_tb"], 3.5)
        self.assertEqual(phan_hoi.context["luot_cham"], 2)
        self.assertContains(phan_hoi, "3,5")

    def test_chua_ai_cham(self):
        self.assertContains(self.client.get(self.hoa.get_absolute_url()), "Chưa có ai chấm")


class YeuThichTest(DuLieuMauTest):
    def bam(self):
        return self.client.post(reverse("doi_yeu_thich", args=[self.bai.pk]))

    def test_khach_bi_dua_den_dang_nhap(self):
        self.assertIn(reverse("dang_nhap"), self.bam().url)
        self.assertEqual(YeuThich.objects.count(), 0)

    def test_luu_roi_hien_trong_danh_sach(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.bam(), self.hoa.get_absolute_url())
        self.assertContains(self.client.get(reverse("yeu_thich")), "Hành tinh đỏ")

    def test_bam_lan_hai_thi_bo_luu(self):
        self.client.force_login(self.user)
        self.bam()
        self.bam()
        self.assertEqual(YeuThich.objects.count(), 0)

    def test_chi_thay_bai_cua_minh(self):
        YeuThich.objects.create(nguoi_dung=self.user2, bai_viet=self.bai)
        self.client.force_login(self.user)
        self.assertNotContains(self.client.get(reverse("yeu_thich")), "Hành tinh đỏ")

    def test_danh_sach_rong(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("yeu_thich")), "Chưa lưu bài nào")


class SoSanhTest(DuLieuMauTest):
    def so_sanh(self, **tham_so):
        return self.client.get(reverse("so_sanh"), tham_so)

    def test_co_hai_khung_3d_truoc_khi_bam_so_sanh(self):
        phan_hoi = self.so_sanh()
        self.assertContains(phan_hoi, 'class="san-khau"', count=2)
        self.assertContains(phan_hoi, 'type="importmap"', count=1)
        self.assertContains(phan_hoi, "thienvan/so_sanh_3d.js", count=1)

    def test_lua_chon_mang_du_thong_tin_de_ve_3d(self):
        phan_hoi = self.so_sanh()
        self.assertContains(phan_hoi, 'data-texture="/static/textures/mars.jpg"', count=2)
        # Solar System Scope has no texture for Phobos: it falls back to the CSS marble
        self.assertContains(phan_hoi, 'value="phobos" data-texture="" data-mau="#B8AEDB"', count=2)

    def test_chu_vs_nam_giua_hai_ben_va_khong_doc_cho_trinh_doc_man_hinh(self):
        html = self.so_sanh().content.decode()
        vi_tri_a, vi_tri_vs, vi_tri_b = (
            html.index('o-so-sanh--a'), html.index('<div class="chu-vs" aria-hidden="true">VS</div>'), html.index('o-so-sanh--b')
        )
        self.assertLess(vi_tri_a, vi_tri_vs)
        self.assertLess(vi_tri_vs, vi_tri_b)

    def test_giu_lua_chon_khi_mo_tu_trang_chi_tiet(self):
        phan_hoi = self.so_sanh(a="mars")
        self.assertContains(phan_hoi, 'value="mars" data-texture="/static/textures/mars.jpg" data-mau="#B8AEDB" selected', count=1)

    def test_hai_thien_the_co_bang_va_du_lieu_bieu_do(self):
        phan_hoi = self.so_sanh(a="mars", b="moon")
        self.assertEqual(phan_hoi.context["a"], self.hoa)
        self.assertEqual(phan_hoi.context["b"], self.trang)
        self.assertContains(phan_hoi, "Chưa có")

    def test_chon_trung_bao_loi(self):
        phan_hoi = self.so_sanh(a="mars", b="mars")
        self.assertContains(phan_hoi, "hai thiên thể khác nhau")
        self.assertIsNone(phan_hoi.context["a"])

    def test_slug_sai_khong_vo_trang(self):
        phan_hoi = self.so_sanh(a="mars", b="khong-co")
        self.assertEqual(phan_hoi.status_code, 200)
        self.assertIsNone(phan_hoi.context["a"])


class CanNangTest(DuLieuMauTest):
    def test_khong_con_phan_nhay_cao(self):
        phan_hoi = self.client.get(reverse("can_nang"))
        self.assertNotContains(phan_hoi, "hảy cao")
        self.assertNotContains(phan_hoi, 'id="cm"')
        self.assertNotContains(phan_hoi, 'data-cot="cm"')
        self.assertContains(phan_hoi, 'id="kg"', count=1)

    def test_chi_hien_hanh_tinh_co_trong_luc(self):
        phan_hoi = self.client.get(reverse("can_nang"))
        self.assertContains(phan_hoi, 'data-g="3.71"')
        self.assertNotContains(phan_hoi, "Sao Kim")


class TrangChuTest(DuLieuMauTest):
    def test_hien_cac_hanh_tinh(self):
        phan_hoi = self.client.get(reverse("trang_chu"))
        self.assertContains(phan_hoi, "Sao Hỏa")
        self.assertNotContains(phan_hoi, "Phobos")

    def test_ten_web_moi(self):
        phan_hoi = self.client.get(reverse("trang_chu"))
        self.assertContains(phan_hoi, "<title>Xóm Mặt Trời</title>")
        self.assertNotContains(phan_hoi, "Web Thiên Văn")

    def test_trang_chu_khong_co_ten_web_tren_header(self):
        self.assertNotContains(self.client.get(reverse("trang_chu")), "navbar-brand")

    def test_trang_khac_van_co_ten_web_de_ve_trang_chu(self):
        for url in (reverse("danh_sach"), self.hoa.get_absolute_url(), reverse("so_sanh"), reverse("dang_nhap")):
            self.assertContains(self.client.get(url), '<a class="navbar-brand" href="/">Xóm Mặt Trời</a>', html=True)

    def test_da_xoa_ba_o_trung_voi_menu(self):
        phan_hoi = self.client.get(reverse("trang_chu"))
        for chu in ("Gặp các vệ tinh", "Cho hai thiên thể đọ sức", "Lên sao Mộc bạn nặng bao nhiêu?"):
            self.assertNotContains(phan_hoi, chu)

    def test_co_ba_ngoi_sao_trang_tri_khong_doc_len_cho_trinh_doc_man_hinh(self):
        self.assertContains(self.client.get(reverse("trang_chu")), 'aria-hidden="true" class="sao-tu', count=3)

    def test_danh_sach_dat_thien_the_trong_khung(self):
        phan_hoi = self.client.get(reverse("danh_sach"))
        self.assertContains(phan_hoi, 'class="khung-bi"', count=5)
        self.assertContains(phan_hoi, 'class="nhan-ten"', count=5)

    def test_cac_trang_khac_cung_dung_khung(self):
        self.client.force_login(self.user)
        YeuThich.objects.create(nguoi_dung=self.user, bai_viet=self.bai)
        for url, so_khung in (
            (self.hoa.get_absolute_url(), 1),  # Phobos
            (reverse("tim_kiem") + "?q=mat", 1),  # Mặt Trăng
            (reverse("yeu_thich"), 1),
        ):
            self.assertContains(self.client.get(url), 'class="khung-bi"', count=so_khung)

    def test_co_anh_phi_hanh_gia_luu_tai_cho_va_co_mo_ta(self):
        phan_hoi = self.client.get(reverse("trang_chu"))
        self.assertContains(phan_hoi, 'src="/static/thienvan/phi-hanh-gia.jpg"')
        self.assertContains(phan_hoi, 'alt="Phi hành gia trôi lơ lửng phía trên Trái Đất"')
        self.assertNotContains(phan_hoi, "unsplash.com/photo")
        self.assertIsNotNone(finders.find("thienvan/phi-hanh-gia.jpg"))

    def test_loi_chao_co_quy_dao_trang_tri_va_van_doc_duoc_chu(self):
        phan_hoi = self.client.get(reverse("trang_chu"))
        self.assertContains(phan_hoi, '<svg class="quy-dao" aria-hidden="true"', count=1)
        self.assertContains(phan_hoi, 'class="ve-tinh-nho', count=3)
        self.assertContains(phan_hoi, '<h1 lang="en">Welcome To Spaceeee</h1>', count=1)
        self.assertNotContains(phan_hoi, "Chào mừng đến")

    def test_da_xoa_cau_gioi_thieu(self):
        self.assertNotContains(self.client.get(reverse("trang_chu")), "cả đống chuyện lạ")

    def test_chua_co_mat_troi_trong_database_van_mo_duoc(self):
        phan_hoi = self.client.get(reverse("trang_chu"))
        self.assertEqual(phan_hoi.status_code, 200)
        self.assertNotContains(phan_hoi, 'href="/thien-the/sun/"')


class MatTroiTest(DuLieuMauTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mat_troi = ThienThe.objects.create(
            ten="Mặt Trời", ten_en="Sun", api_id="soleil", loai=ThienThe.Loai.SAO, trong_luc=274, ban_kinh_km=695700
        )

    def test_trang_chu_co_mat_troi_ghi_ten_va_bam_duoc(self):
        phan_hoi = self.client.get(reverse("trang_chu"))
        self.assertContains(
            phan_hoi, f'<a class="mat-troi" href="{self.mat_troi.get_absolute_url()}"><span>Mặt Trời</span></a>', html=True
        )

    def test_mat_troi_khong_nam_trong_hang_hanh_tinh(self):
        self.assertNotIn(self.mat_troi, self.client.get(reverse("trang_chu")).context["hanh_tinh"])

    def test_trang_chi_tiet_ghi_dung_la_ngoi_sao(self):
        phan_hoi = self.client.get(self.mat_troi.get_absolute_url())
        self.assertContains(phan_hoi, "Ngôi sao")
        self.assertNotContains(phan_hoi, "Hành tinh trong hệ Mặt Trời")

    def test_trang_chi_tiet_khong_co_muc_ve_tinh(self):
        self.assertNotContains(self.client.get(self.mat_troi.get_absolute_url()), "Vệ tinh của")

    def test_danh_sach_ghi_dung_loai(self):
        phan_hoi = self.client.get(reverse("danh_sach"))
        self.assertContains(phan_hoi, "ngôi sao")

    def test_loc_theo_loai_sao(self):
        phan_hoi = self.client.get(reverse("danh_sach"), {"loai": "sao"})
        self.assertEqual([t.slug for t in phan_hoi.context["thien_the"]], ["sun"])

    def test_tim_duoc_mat_troi(self):
        ket_qua = self.client.get(reverse("goi_y"), {"q": "mat troi"}).json()["ket_qua"]
        self.assertEqual([(m["ten"], m["loai"]) for m in ket_qua], [("Mặt Trời", "Ngôi sao")])

    def test_so_sanh_duoc_voi_hanh_tinh(self):
        self.assertEqual(self.client.get(reverse("so_sanh"), {"a": "sun", "b": "mars"}).context["a"], self.mat_troi)

    def test_khong_nam_trong_trang_can_nang(self):
        self.assertNotIn(self.mat_troi, self.client.get(reverse("can_nang")).context["hanh_tinh"])
