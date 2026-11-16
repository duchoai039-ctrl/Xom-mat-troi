import unicodedata


def bo_dau(chuoi):
    """Chữ thường, không dấu, gộp khoảng trắng: 'MẶT  TRĂNG' -> 'mat trang'."""
    # đ is its own letter, NFD does not split it into d + a combining mark
    chuoi = chuoi.replace("đ", "d").replace("Đ", "d")
    khong_dau = "".join(c for c in unicodedata.normalize("NFD", chuoi) if not unicodedata.combining(c))
    return " ".join(khong_dau.lower().split())
