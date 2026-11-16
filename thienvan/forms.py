import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UsernameField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.text import slugify

from .models import BaiViet, ThienThe
from .utils import bo_dau

NHAN_DINH_DANH = "Số điện thoại hoặc Gmail"


def chuan_hoa_dinh_danh(chuoi):
    """Đưa số điện thoại và Gmail về một dạng duy nhất để so trùng và đăng nhập."""
    chuoi = chuoi.strip().lower()
    if "@" in chuoi:
        if re.fullmatch(r"[a-z0-9._%+-]+@gmail\.com", chuoi):
            return chuoi
        raise ValidationError("Chỉ nhận địa chỉ @gmail.com.")
    so = re.sub(r"[\s.-]", "", chuoi)
    if so.startswith("+84"):
        so = "0" + so[3:]
    if re.fullmatch(r"0\d{9}", so):
        return so
    raise ValidationError("Số điện thoại cần có 10 chữ số, ví dụ 0912345678.")


class BaiVietForm(forms.ModelForm):
    class Meta:
        model = BaiViet
        fields = ["thien_the", "tieu_de", "noi_dung", "co_the_ban_chua_biet"]
        widgets = {
            "noi_dung": forms.Textarea(attrs={"rows": 12}),
            "co_the_ban_chua_biet": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "noi_dung": "Cách đoạn bằng một dòng trống.",
            "co_the_ban_chua_biet": "1-2 câu vui, để trống thì không hiện.",
        }


class ThienTheMoiForm(forms.ModelForm):
    class Meta:
        model = ThienThe
        fields = [
            "ten", "ten_en", "mau", "ban_kinh_km", "khoi_luong_kg", "trong_luc",
            "chu_ky_quy_dao_ngay", "chu_ky_tu_quay_gio", "nhiet_do_tb_k",
        ]
        widgets = {"mau": forms.TextInput(attrs={"type": "color"})}
        help_texts = {
            "ten_en": "Dùng để tạo đường dẫn, ví dụ Ceres.",
            "khoi_luong_kg": "Có thể viết 9.4e20.",
            "chu_ky_tu_quay_gio": "Số âm nghĩa là quay ngược chiều.",
        }

    def clean_ten(self):
        ten = self.cleaned_data["ten"]
        if ThienThe.objects.filter(ten_khong_dau=bo_dau(ten)).exists():
            raise ValidationError("Đã có thiên thể tên này.")
        return ten

    def clean_ten_en(self):
        ten_en = self.cleaned_data["ten_en"]
        slug = slugify(ten_en)
        if not slug:
            raise ValidationError("Tên này không tạo được đường dẫn, hãy dùng chữ cái Latin.")
        if ThienThe.objects.filter(slug=slug).exists():
            raise ValidationError("Đã có thiên thể tên tiếng Anh này.")
        return ten_en

    def clean_mau(self):
        mau = self.cleaned_data["mau"]
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", mau):
            raise ValidationError("Màu cần có dạng #RRGGBB.")
        return mau

    def clean(self):
        du_lieu = super().clean()
        # rotation is left out: a negative period means the body spins backwards
        for truong in ("ban_kinh_km", "khoi_luong_kg", "trong_luc", "chu_ky_quy_dao_ngay", "nhiet_do_tb_k"):
            if du_lieu.get(truong) is not None and du_lieu[truong] <= 0:
                self.add_error(truong, "Giá trị này phải lớn hơn 0.")
        return du_lieu

    def save(self, commit=True):
        t = self.instance
        t.slug = slugify(t.ten_en)
        t.api_id = f"tu-them-{t.slug}"  # never in data/danh_sach.json, so nap_du_lieu leaves it alone
        t.loai = ThienThe.Loai.HANH_TINH
        cuoi = ThienThe.objects.filter(loai=ThienThe.Loai.HANH_TINH).aggregate(Max("thu_tu"))["thu_tu__max"]
        t.thu_tu = (cuoi or 0) + 1
        return super().save(commit)


class DangKyForm(UserCreationForm):
    username = forms.CharField(label=NHAN_DINH_DANH, max_length=150)

    def clean_username(self):
        dinh_danh = chuan_hoa_dinh_danh(self.cleaned_data["username"])
        if User.objects.filter(username=dinh_danh).exists():
            raise ValidationError("Số điện thoại hoặc Gmail này đã được đăng ký.")
        return dinh_danh


class DangNhapForm(AuthenticationForm):
    username = UsernameField(label=NHAN_DINH_DANH, widget=forms.TextInput(attrs={"autofocus": True}))
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Số điện thoại, Gmail hoặc mật khẩu không đúng.",
    }

    def clean(self):
        try:
            self.cleaned_data["username"] = chuan_hoa_dinh_danh(self.cleaned_data.get("username", ""))
        except ValidationError:
            pass  # the admin account has a plain username, so let authenticate() decide
        return super().clean()
