import json
import os
from http.client import IncompleteRead, RemoteDisconnected
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch
from urllib.error import HTTPError

from django.core.management import call_command
from django.test import TestCase

from thienvan.models import BaiViet, ThienThe

URLOPEN = "thienvan.management.commands.nap_du_lieu.urlopen"


def nap(**env):
    with patch.dict(os.environ, env, clear=False):
        if "SOLAR_API_KEY" not in env:
            os.environ.pop("SOLAR_API_KEY", None)
        out = StringIO()
        call_command("nap_du_lieu", stdout=out, stderr=out)
    return out.getvalue()


def phan_hoi_api(**truong):
    return BytesIO(json.dumps(truong).encode())


class KhongCoKhoaTest(TestCase):
    def test_nap_du_39_thien_the(self):
        nap()
        self.assertEqual(ThienThe.objects.filter(loai="hanh_tinh").count(), 8)
        self.assertEqual(ThienThe.objects.filter(loai="ve_tinh").count(), 30)

    def test_mat_troi_la_ngoi_sao(self):
        nap()
        mat_troi = ThienThe.objects.get(slug="sun")
        self.assertEqual((mat_troi.ten, mat_troi.loai, mat_troi.hanh_tinh_me), ("Mặt Trời", "sao", None))

    def test_khong_goi_mang(self):
        with patch(URLOPEN) as urlopen:
            nap()
        urlopen.assert_not_called()

    def test_ve_tinh_gan_dung_hanh_tinh_me(self):
        nap()
        self.assertEqual(ThienThe.objects.get(slug="moon").hanh_tinh_me.slug, "earth")
        self.assertEqual(ThienThe.objects.get(slug="titan").hanh_tinh_me.slug, "saturn")

    def test_chay_lai_khong_tao_trung(self):
        nap()
        nap()
        self.assertEqual(ThienThe.objects.count(), 39)

    def test_chay_lai_khong_dung_bai_viet(self):
        nap()
        hoa = ThienThe.objects.get(slug="mars")
        BaiViet.objects.create(thien_the=hoa, tieu_de="Của Đức", noi_dung="Bài tự viết")
        nap()
        self.assertEqual(BaiViet.objects.get(thien_the=hoa).noi_dung, "Bài tự viết")


class ChayLaiGiuDuLieuTest(TestCase):
    def setUp(self):
        with patch(URLOPEN, side_effect=lambda req, timeout: phan_hoi_api(meanRadius=1111.0)):
            nap(SOLAR_API_KEY="abc")

    def ban_kinh_sao_hoa(self):
        return ThienThe.objects.get(slug="mars").ban_kinh_km

    def test_khong_co_khoa_khong_ghi_de_so_lieu_api(self):
        nap()
        self.assertEqual(self.ban_kinh_sao_hoa(), 1111.0)

    def test_api_loi_khong_ghi_de_so_lieu_api(self):
        with patch(URLOPEN, side_effect=HTTPError("u", 500, "Loi", {}, None)):
            nap(SOLAR_API_KEY="abc")
        self.assertEqual(self.ban_kinh_sao_hoa(), 1111.0)

    def test_giu_ten_va_mau_admin_da_sua(self):
        hoa = ThienThe.objects.get(slug="mars")
        hoa.ten, hoa.mau = "Hoả Tinh", "#123456"
        hoa.save()
        nap()
        hoa.refresh_from_db()
        self.assertEqual((hoa.ten, hoa.mau, hoa.ten_khong_dau), ("Hoả Tinh", "#123456", "hoa tinh"))


class ApiTraVeLaTest(TestCase):
    def test_du_lieu_la_khong_lam_vo_lenh_va_khong_duoc_luu(self):
        cac_phan_hoi = [
            b"[]", b"null", b'"x"', b"{", b"\xff",
            b'{"mass": "x"}', b'{"mass": {"massValue": "5.97", "massExponent": 24}}',
            b'{"mass": {"massValue": 5.97}}', b'{"mass": {"massValue": 5.97, "massExponent": "24"}}',
            b'{"mass": {"massValue": 5.97, "massExponent": 400}}',
            b'{"meanRadius": "abc"}', b'{"meanRadius": true}', b'{"meanRadius": -5}',
            b'{"sideralRotation": "abc"}', b'{"avgTemp": -1}',
        ]
        for than in cac_phan_hoi:
            with self.subTest(than=than):
                with patch(URLOPEN, side_effect=lambda req, timeout: BytesIO(than)):
                    nap(SOLAR_API_KEY="abc")
                hoa = ThienThe.objects.get(slug="mars")
                self.assertEqual(ThienThe.objects.count(), 39)
                self.assertEqual(hoa.ban_kinh_km, 3389.5)
                self.assertEqual(hoa.khoi_luong_kg, 6.417e23)
                self.assertEqual(hoa.nhiet_do_tb_k, 210)

    def test_loi_ket_noi_khong_lam_vo_lenh(self):
        for loi in (ConnectionResetError(), RemoteDisconnected(), IncompleteRead(b""), TimeoutError()):
            with self.subTest(loi=type(loi).__name__):
                with patch(URLOPEN, side_effect=loi):
                    out = nap(SOLAR_API_KEY="abc")
                self.assertEqual(ThienThe.objects.count(), 39)
                self.assertIn("mars", out)

    def test_nhan_chu_ky_quay_am_cua_api(self):
        with patch(URLOPEN, side_effect=lambda req, timeout: phan_hoi_api(sideralRotation=-5832.5)):
            nap(SOLAR_API_KEY="abc")
        self.assertEqual(ThienThe.objects.get(slug="mars").chu_ky_tu_quay_gio, -5832.5)


class ManHinhWindowsTest(TestCase):
    def test_in_tieng_viet_ra_cp1252_khong_lam_vo_lenh(self):
        # piping output on Windows gives a cp1252 stream, which has no Vietnamese letters
        man_hinh = TextIOWrapper(BytesIO(), encoding="cp1252")
        os.environ.pop("SOLAR_API_KEY", None)
        with patch("sys.stdout", man_hinh), patch("sys.stderr", man_hinh):
            call_command("nap_du_lieu")
        self.assertEqual(ThienThe.objects.count(), 39)


class CoKhoaTest(TestCase):
    def test_gui_khoa_va_ghi_so_lieu_api(self):
        def tra_loi(req, timeout):
            self.assertEqual(req.get_header("Authorization"), "Bearer abc")
            return phan_hoi_api(meanRadius=1111.0, mass={"massValue": 2.0, "massExponent": 23})

        with patch(URLOPEN, side_effect=tra_loi):
            nap(SOLAR_API_KEY="abc")
        hoa = ThienThe.objects.get(slug="mars")
        self.assertEqual(hoa.ban_kinh_km, 1111.0)
        self.assertEqual(hoa.khoi_luong_kg, 2e23)

    def test_api_thieu_truong_giu_so_lieu_du_phong(self):
        # the API reports unknown values as 0
        with patch(URLOPEN, side_effect=lambda req, timeout: phan_hoi_api(gravity=0)):
            nap(SOLAR_API_KEY="abc")
        self.assertEqual(ThienThe.objects.get(slug="mars").trong_luc, 3.71)

    def test_api_loi_van_nap_du_va_co_canh_bao(self):
        loi = HTTPError("u", 401, "Unauthorized", {}, None)
        with patch(URLOPEN, side_effect=loi):
            out = nap(SOLAR_API_KEY="sai")
        self.assertEqual(ThienThe.objects.count(), 39)
        self.assertIn("mars", out)
