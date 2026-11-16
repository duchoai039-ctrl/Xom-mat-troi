import json
import math
import os
import sys
from http.client import HTTPException
from pathlib import Path
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from thienvan.models import ThienThe

API = "https://api.le-systeme-solaire.net/rest/bodies/"
DANH_SACH = Path(settings.BASE_DIR) / "data" / "danh_sach.json"
TRUONG_SO_LIEU = [
    "ban_kinh_km", "khoi_luong_kg", "trong_luc",
    "chu_ky_quy_dao_ngay", "chu_ky_tu_quay_gio", "nhiet_do_tb_k",
]


def goi_api(api_id, khoa):
    yeu_cau = Request(API + api_id, headers={"Authorization": f"Bearer {khoa}"})
    with urlopen(yeu_cau, timeout=20) as phan_hoi:
        return json.load(phan_hoi)


def so_hop_le(gia_tri, am_duoc=False):
    # the API reports unknown values as 0; bool is a subclass of int
    if not isinstance(gia_tri, (int, float)) or isinstance(gia_tri, bool) or not math.isfinite(gia_tri):
        return False
    return gia_tri > 0 or (am_duoc and gia_tri != 0)


def doi_so_lieu(du_lieu):
    """Đổi trường của API sang cột trong database; bỏ giá trị thiếu hoặc không hợp lệ."""
    if not isinstance(du_lieu, dict):
        raise ValueError("phản hồi không phải object JSON")
    so_lieu = {
        truong: du_lieu.get(khoa)
        for truong, khoa in [
            ("ban_kinh_km", "meanRadius"),
            ("trong_luc", "gravity"),
            ("chu_ky_quy_dao_ngay", "sideralOrbit"),
            ("nhiet_do_tb_k", "avgTemp"),
        ]
        if so_hop_le(du_lieu.get(khoa))
    }
    # negative means the body spins backwards
    if so_hop_le(du_lieu.get("sideralRotation"), am_duoc=True):
        so_lieu["chu_ky_tu_quay_gio"] = du_lieu["sideralRotation"]
    khoi_luong = du_lieu.get("mass")
    if isinstance(khoi_luong, dict):
        he_so, so_mu = khoi_luong.get("massValue"), khoi_luong.get("massExponent")
        if so_hop_le(he_so) and type(so_mu) is int and abs(so_mu) <= 100:
            so_lieu["khoi_luong_kg"] = he_so * 10 ** so_mu
    return so_lieu


class Command(BaseCommand):
    help = (
        "Nạp các thiên thể trong data/danh_sach.json vào database. Có SOLAR_API_KEY thì cập nhật số liệu từ API. "
        "Thiên thể đã có chỉ đổi số liệu lấy được từ API; không đụng vào tên, màu và bài viết."
    )

    def handle(self, *args, **options):
        # a Windows pipe is cp1252: a garbled log line must not abort the import
        for luong in (sys.stdout, sys.stderr):
            if hasattr(luong, "reconfigure"):
                luong.reconfigure(errors="replace")

        khoa = os.environ.get("SOLAR_API_KEY")
        if not khoa:
            self.stdout.write("Chưa có SOLAR_API_KEY: thiên thể mới dùng số liệu dự phòng, thiên thể đã có giữ nguyên.")

        danh_sach = json.loads(DANH_SACH.read_text(encoding="utf-8"))
        tu_api = {}
        if khoa:
            for muc in danh_sach:
                try:
                    tu_api[muc["api_id"]] = doi_so_lieu(goi_api(muc["api_id"], khoa))
                except (OSError, HTTPException, ValueError, OverflowError) as loi:
                    self.stderr.write(f"{muc['ten_en'].lower()}: không lấy được từ API, giữ số liệu hiện có ({loi})")

        # network calls stay outside: the transaction only guards the writes
        with transaction.atomic():
            # planets come first in the file, so a moon's parent already exists
            for thu_tu, muc in enumerate(danh_sach):
                moi = tu_api.get(muc["api_id"], {})
                me = ThienThe.objects.get(api_id=muc["me"]) if muc.get("me") else None
                ThienThe.objects.update_or_create(
                    api_id=muc["api_id"],
                    defaults=moi,
                    create_defaults={
                        "api_id": muc["api_id"],
                        "ten": muc["ten"],
                        "ten_en": muc["ten_en"],
                        "mau": muc["mau"],
                        "thu_tu": thu_tu,
                        "loai": muc.get("loai") or (ThienThe.Loai.VE_TINH if me else ThienThe.Loai.HANH_TINH),
                        "hanh_tinh_me": me,
                        **{truong: muc.get(truong) for truong in TRUONG_SO_LIEU},
                        **moi,
                    },
                )
        self.stdout.write(self.style.SUCCESS(f"Đã nạp {ThienThe.objects.count()} thiên thể."))
