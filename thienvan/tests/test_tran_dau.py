from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from thienvan.models import ThienThe
from thienvan.views import chia_hiep, viet_lan

from .test_models import tao_hanh_tinh


def the(ten="A", **so_lieu):
    return ThienThe(ten=ten, **so_lieu)


def hiep(ket_qua, nhan):
    return next(h for h in ket_qua["hiep"] if h["nhan"] == nhan)


class VietLanTest(SimpleTestCase):
    def test_nho_giu_mot_so_le(self):
        self.assertEqual(viet_lan(2.84), "2,8")

    def test_lon_lam_tron(self):
        self.assertEqual(viet_lan(885.6), "886")
        self.assertEqual(viet_lan(61731.2), "61.731")

    def test_rat_lon_dung_luy_thua(self):
        self.assertEqual(viet_lan(1.87e14), "1,9 × 10¹⁴")


class ChiaHiepTest(SimpleTestCase):
    def test_ben_lon_hon_thang_va_ghi_ti_le(self):
        kq = chia_hiep(the("Sao Hỏa", ban_kinh_km=3389.5), the("Sao Thổ", ban_kinh_km=58232))
        h = hiep(kq, "Bán kính")
        self.assertEqual(h["ben"], "b")
        self.assertEqual(h["ket_luan"], "Sao Thổ to gấp 17 lần")

    def test_chu_ky_ngan_hon_thi_thang(self):
        kq = chia_hiep(the("Sao Thủy", chu_ky_quy_dao_ngay=88), the("Trái Đất", chu_ky_quy_dao_ngay=365))
        self.assertEqual(hiep(kq, "Một vòng quanh quỹ đạo")["ben"], "a")

    def test_quay_nguoc_chi_tinh_do_lon(self):
        kq = chia_hiep(the("Sao Kim", chu_ky_tu_quay_gio=-5832.5), the("Trái Đất", chu_ky_tu_quay_gio=24))
        h = hiep(kq, "Một vòng tự quay")
        self.assertEqual(h["ben"], "b")
        self.assertIn("Trái Đất tự quay nhanh gấp", h["ket_luan"])

    def test_gan_bang_nhau_la_hoa(self):
        kq = chia_hiep(the("Sao Kim", trong_luc=8.87), the("Sao Thiên Vương", trong_luc=8.87))
        h = hiep(kq, "Trọng lực")
        self.assertEqual((h["ben"], h["ket_luan"]), ("hoa", "Ngang nhau"))

    def test_thieu_so_lieu_khong_tinh_diem(self):
        kq = chia_hiep(the("A", nhiet_do_tb_k=100), the("B"))
        h = hiep(kq, "Nhiệt độ trung bình")
        self.assertEqual((h["ben"], h["ket_luan"]), (None, "Chưa đủ số liệu"))
        self.assertEqual((kq["diem_a"], kq["diem_b"]), (0, 0))

    def test_tinh_diem_va_nguoi_thang(self):
        a = the("A", ban_kinh_km=10, khoi_luong_kg=10, trong_luc=1)
        b = the("B", ban_kinh_km=1, khoi_luong_kg=1, trong_luc=5)
        kq = chia_hiep(a, b)
        self.assertEqual((kq["diem_a"], kq["diem_b"]), (2, 1))
        self.assertEqual(kq["nguoi_thang"], a)
        self.assertEqual(kq["diem_cao"], 2)
        self.assertEqual(kq["diem_thap"], 1)

    def test_bang_diem_thi_khong_co_nguoi_thang(self):
        kq = chia_hiep(the("A", ban_kinh_km=10, trong_luc=1), the("B", ban_kinh_km=1, trong_luc=5))
        self.assertIsNone(kq["nguoi_thang"])
        self.assertEqual(kq["ben_thang"], "hoa")


class TrangTranDauTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        tao_hanh_tinh(ban_kinh_km=3389.5)
        tao_hanh_tinh("Sao Thổ", "Saturn", ban_kinh_km=58232)

    def lay(self, **tham_so):
        return self.client.get(reverse("so_sanh"), tham_so)

    def test_hien_nguoi_thang_va_ti_le(self):
        phan_hoi = self.lay(a="mars", b="saturn")
        self.assertContains(phan_hoi, "Sao Thổ thắng 1-0")
        self.assertContains(phan_hoi, "Sao Thổ to gấp 17 lần")

    def test_luon_co_vung_ket_qua_de_cap_nhat_khong_tai_lai(self):
        self.assertContains(self.lay(), 'id="ket-qua"', count=1)
        self.assertContains(self.lay(a="mars"), 'id="ket-qua"', count=1)

    def test_vung_ket_qua_thong_bao_cho_trinh_doc_man_hinh(self):
        self.assertContains(self.lay(), 'aria-live="polite"')

    def test_lua_chon_mang_co_hinh_de_ve_dung_ti_le(self):
        sao_tho = ThienThe.objects.get(slug="saturn")
        self.assertContains(self.lay(), f'data-co="{sao_tho.co_hinh}"', count=2)

    def test_bieu_do_duoc_gom_vao_muc_mo_rong(self):
        self.assertContains(self.lay(a="mars", b="saturn"), '<details class="them-bieu-do">')

    def test_thu_vien_bieu_do_co_san_khi_chua_chon(self):
        self.assertContains(self.lay(), "vendor/chart.umd.min.js", count=1)

    def test_loi_nam_trong_vung_ket_qua(self):
        html = self.lay(a="mars", b="mars").content.decode()
        self.assertLess(html.index('id="ket-qua"'), html.index("hai thiên thể khác nhau"))
