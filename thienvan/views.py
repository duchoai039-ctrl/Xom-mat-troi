from functools import wraps

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BaiVietForm, DangKyForm, ThienTheMoiForm
from .models import BaiViet, DanhGia, ThienThe, YeuThich
from .utils import bo_dau

CHUA_CO = "Chưa có"
SO_MU = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
# same order as bang_so_lieu: column, what the winner did, whether the higher number wins
LUAT_HIEP = [
    ("ban_kinh_km", "to gấp", True),
    ("khoi_luong_kg", "nặng gấp", True),
    ("trong_luc", "hút mạnh gấp", True),
    ("chu_ky_quy_dao_ngay", "đi hết một vòng nhanh gấp", False),
    ("chu_ky_tu_quay_gio", "tự quay nhanh gấp", False),
    ("nhiet_do_tb_k", "nóng gấp", True),
]
TRUONG_BIEU_DO = [
    ("ban_kinh_km", "Bán kính (km)"),
    ("khoi_luong_kg", "Khối lượng (kg)"),
    ("trong_luc", "Trọng lực (m/s²)"),
    ("chu_ky_quy_dao_ngay", "Một vòng quanh quỹ đạo (ngày)"),
    ("nhiet_do_tb_k", "Nhiệt độ trung bình (K)"),
]


def viet_so(so):
    so = round(so, 4)
    # Vietnamese numbers: 3.389,5 (the vi locale has no grouping size for number_format)
    return f"{int(so) if so == int(so) else so:,}".translate({ord(","): ".", ord("."): ","})


def viet_khoi_luong(kg):
    if kg is None:
        return CHUA_CO
    he_so, so_mu = f"{kg:.3e}".split("e")
    return f"{viet_so(float(he_so))} × 10{str(int(so_mu)).translate(SO_MU)} kg"


def viet_tu_quay(gio):
    if gio is None:
        return CHUA_CO
    return f"{viet_so(abs(gio))} giờ" + (", quay ngược chiều" if gio < 0 else "")


def viet_nhiet_do(k):
    return CHUA_CO if k is None else f"{viet_so(k)} K ({viet_so(round(k - 273.15))} °C)"


def viet_don_vi(so, don_vi):
    return CHUA_CO if so is None else f"{viet_so(so)} {don_vi}"


def bang_so_lieu(t):
    return [
        ("Bán kính", viet_don_vi(t.ban_kinh_km, "km")),
        ("Khối lượng", viet_khoi_luong(t.khoi_luong_kg)),
        ("Trọng lực", viet_don_vi(t.trong_luc, "m/s²")),
        ("Một vòng quanh quỹ đạo", viet_don_vi(t.chu_ky_quy_dao_ngay, "ngày")),
        ("Một vòng tự quay", viet_tu_quay(t.chu_ky_tu_quay_gio)),
        ("Nhiệt độ trung bình", viet_nhiet_do(t.nhiet_do_tb_k)),
    ]


def viet_lan(lan):
    if lan < 10:
        return viet_so(round(lan, 1))
    if lan < 1e6:
        return viet_so(round(lan))
    he_so, so_mu = f"{lan:.1e}".split("e")
    return f"{viet_so(float(he_so))} × 10{str(int(so_mu)).translate(SO_MU)}"


def chia_hiep(a, b):
    """Mỗi chỉ số là một hiệp: bên hơn được một điểm, kèm câu nói rõ hơn bao nhiêu lần."""
    hiep = []
    diem = {"a": 0, "b": 0}
    for (nhan, gia_tri_a), (_, gia_tri_b), (truong, dong_tu, cao_thang) in zip(bang_so_lieu(a), bang_so_lieu(b), LUAT_HIEP):
        so_a, so_b = getattr(a, truong), getattr(b, truong)
        if not so_a or not so_b:
            ben, ket_luan = None, "Chưa đủ số liệu"
        else:
            so_a, so_b = abs(so_a), abs(so_b)  # a negative rotation period only means spinning backwards
            lan = max(so_a, so_b) / min(so_a, so_b)
            if lan < 1.01:
                ben, ket_luan = "hoa", "Ngang nhau"
            else:
                ben = "a" if (so_a > so_b) == cao_thang else "b"
                diem[ben] += 1
                ket_luan = f"{(a if ben == 'a' else b).ten} {dong_tu} {viet_lan(lan)} lần"
        hiep.append({"nhan": nhan, "gia_tri_a": gia_tri_a, "gia_tri_b": gia_tri_b, "ben": ben, "ket_luan": ket_luan})

    ben_thang = "hoa" if diem["a"] == diem["b"] else max(diem, key=diem.get)
    return {
        "hiep": hiep,
        "diem_a": diem["a"],
        "diem_b": diem["b"],
        "diem_cao": max(diem.values()),
        "diem_thap": min(diem.values()),
        "ben_thang": ben_thang,
        "nguoi_thang": {"a": a, "b": b}.get(ben_thang),
        "co_so_lieu": any(h["ben"] for h in hiep),
    }


def tim_thien_the(q):
    q = bo_dau(q)
    if not q:
        return ThienThe.objects.none()
    return ThienThe.objects.filter(Q(ten_khong_dau__contains=q) | Q(ten_en__icontains=q))


def trang_chu(request):
    bai_vui = BaiViet.objects.exclude(co_the_ban_chua_biet="").select_related("thien_the").order_by("?").first()
    return render(request, "thienvan/trang_chu.html", {
        "hanh_tinh": ThienThe.objects.filter(loai=ThienThe.Loai.HANH_TINH),
        "mat_troi": ThienThe.objects.filter(loai=ThienThe.Loai.SAO).first(),
        "bai_vui": bai_vui,
    })


def danh_sach(request):
    thien_the = ThienThe.objects.select_related("hanh_tinh_me")
    loai = request.GET.get("loai")
    hanh_tinh = request.GET.get("hanh_tinh")
    # unknown filter values are ignored rather than showing an empty page
    if loai in ThienThe.Loai.values:
        thien_the = thien_the.filter(loai=loai)
    else:
        loai = None
    hanh_tinh_me = ThienThe.objects.filter(loai=ThienThe.Loai.HANH_TINH)
    if hanh_tinh in {t.slug for t in hanh_tinh_me}:
        thien_the = thien_the.filter(hanh_tinh_me__slug=hanh_tinh)
    else:
        hanh_tinh = None
    return render(request, "thienvan/danh_sach.html", {
        "thien_the": thien_the,
        "cac_hanh_tinh": hanh_tinh_me,
        "loai": loai,
        "hanh_tinh": hanh_tinh,
    })


def chi_tiet(request, slug):
    thien_the = get_object_or_404(ThienThe.objects.select_related("hanh_tinh_me"), slug=slug)
    cac_bai = list(thien_the.cac_bai.all())
    ngu_canh = {
        "t": thien_the,
        "so_lieu": bang_so_lieu(thien_the),
        "ve_tinh": thien_the.ve_tinh.all(),
        "bai_khac": cac_bai[1:],
    }
    if cac_bai:
        ngu_canh.update(ngu_canh_bai(request, cac_bai[0]))
    return render(request, "thienvan/chi_tiet.html", ngu_canh)


def ngu_canh_bai(request, bai):
    tong_hop = bai.danh_gia.aggregate(tb=Avg("so_sao"), luot=Count("id"))
    ngu_canh = {"bai": bai, "cac_sao": [1, 2, 3, 4, 5], "diem_tb": tong_hop["tb"], "luot_cham": tong_hop["luot"]}
    if request.user.is_authenticated:
        cua_toi = bai.danh_gia.filter(nguoi_dung=request.user).first()
        ngu_canh.update(
            sao_cua_toi=cua_toi.so_sao if cua_toi else 0,
            da_luu=bai.yeu_thich.filter(nguoi_dung=request.user).exists(),
        )
    return ngu_canh


def bai_viet(request, pk):
    bai = get_object_or_404(BaiViet.objects.select_related("thien_the"), pk=pk)
    if bai.get_absolute_url() != request.path:
        return redirect(bai)
    return render(request, "thienvan/bai_viet.html", {"t": bai.thien_the, **ngu_canh_bai(request, bai)})


def chi_quan_tri(view):
    @wraps(view)
    @login_required
    def boc(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return boc


@chi_quan_tri
def them_bai(request):
    return render(request, "thienvan/them_bai.html")


@chi_quan_tri
def them_bai_viet(request):
    co_san = ThienThe.objects.filter(slug=request.GET.get("thien_the", "")).first()
    form = BaiVietForm(request.POST or None, initial={"thien_the": co_san})
    if request.method == "POST" and form.is_valid():
        return redirect(form.save())
    return render(request, "thienvan/form_quan_tri.html", {
        "form": form, "tieu_de": "Thêm bài viết vào hành tinh đã có sẵn", "nut": "Đăng bài viết",
    })


@chi_quan_tri
def them_thien_the(request):
    form = ThienTheMoiForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        return redirect(form.save())
    return render(request, "thienvan/form_quan_tri.html", {
        "form": form, "tieu_de": "Thêm hành tinh mới", "beta": True, "nut": "Tạo hành tinh",
    })


def goi_y(request):
    ket_qua = tim_thien_the(request.GET.get("q", ""))[:8]
    return JsonResponse({"ket_qua": [
        {"ten": t.ten, "loai": t.get_loai_display(), "url": t.get_absolute_url()} for t in ket_qua
    ]})


def tim_kiem(request):
    q = request.GET.get("q", "").strip()
    return render(request, "thienvan/tim_kiem.html", {"q": q, "ket_qua": tim_thien_the(q)})


@require_POST
def danh_gia(request, pk):
    bai = get_object_or_404(BaiViet.objects.select_related("thien_the"), pk=pk)
    # login's next must be the article: this URL only accepts POST
    if not request.user.is_authenticated:
        return redirect_to_login(bai.get_absolute_url())
    so_sao = request.POST.get("so_sao", "")
    if so_sao not in {"1", "2", "3", "4", "5"}:
        return HttpResponseBadRequest("Số sao phải từ 1 đến 5.")
    DanhGia.objects.update_or_create(nguoi_dung=request.user, bai_viet=bai, defaults={"so_sao": int(so_sao)})
    return redirect(bai)


@require_POST
def doi_yeu_thich(request, pk):
    bai = get_object_or_404(BaiViet.objects.select_related("thien_the"), pk=pk)
    if not request.user.is_authenticated:
        return redirect_to_login(bai.get_absolute_url())
    da_luu, moi_tao = YeuThich.objects.get_or_create(nguoi_dung=request.user, bai_viet=bai)
    if not moi_tao:
        da_luu.delete()
    return redirect(bai)


@login_required
def yeu_thich(request):
    da_luu = YeuThich.objects.filter(nguoi_dung=request.user).select_related("bai_viet__thien_the")
    return render(request, "thienvan/yeu_thich.html", {"da_luu": da_luu})


def so_sanh(request):
    chon_a, chon_b = request.GET.get("a", ""), request.GET.get("b", "")
    tat_ca = ThienThe.objects.all()
    theo_slug = {t.slug: t for t in tat_ca}
    a, b, loi, ket_qua, bieu_do = None, None, "", None, []
    if chon_a and chon_b:
        if chon_a == chon_b:
            loi = "Chọn hai thiên thể khác nhau để so sánh nhé."
        elif chon_a in theo_slug and chon_b in theo_slug:
            a, b = theo_slug[chon_a], theo_slug[chon_b]
            ket_qua = chia_hiep(a, b)
            bieu_do = [
                {"nhan": nhan, "a": getattr(a, truong), "b": getattr(b, truong)}
                for truong, nhan in TRUONG_BIEU_DO
            ]
        else:
            loi = "Không tìm thấy thiên thể này, bạn chọn lại trong danh sách nhé."
    return render(request, "thienvan/so_sanh.html", {
        "tat_ca": tat_ca, "chon_a": chon_a, "chon_b": chon_b,
        "a": a, "b": b, "loi": loi, "ket_qua": ket_qua, "bieu_do": bieu_do,
    })


def can_nang(request):
    hanh_tinh = ThienThe.objects.filter(loai=ThienThe.Loai.HANH_TINH, trong_luc__isnull=False)
    return render(request, "thienvan/can_nang.html", {"hanh_tinh": hanh_tinh})


def dang_ky(request):
    form = DangKyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        return redirect("trang_chu")
    return render(request, "registration/dang_ky.html", {"form": form})
