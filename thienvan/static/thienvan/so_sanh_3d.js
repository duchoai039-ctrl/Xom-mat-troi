// Live face-off: picking a body updates its 3D view, the relative sizes and the result, with no page reload.
import { moCanh3D } from "./hanh_tinh_3d.js";

// how much of the stage a body's sphere fills at scale 1 (Saturn's camera sits back to fit the rings)
const LAP_DAY = 0.83;
const LAP_DAY_SAO_THO = 0.36;

const form = document.querySelector(".chon--doi");
const ketQua = document.getElementById("ket-qua");
const cacBen = [...document.querySelectorAll(".o-so-sanh")].map((o) => ({
  chon: o.querySelector("select"),
  sanKhau: o.querySelector(".san-khau"),
  bi: o.querySelector(".bi"),
  trong: o.querySelector(".trong-san-khau"),
  goiY: o.querySelector(".goi-y-xoay"),
  dong: () => {},
}));
const dangChon = (ben) => ben.chon.selectedOptions[0];
let yeuCau = null;

function hienBen(ben) {
  ben.dong();
  ben.dong = () => {};
  ben.goiY.hidden = true;
  const { value: slug, dataset: { texture, mau } = {} } = dangChon(ben);
  ben.trong.hidden = Boolean(slug);
  ben.bi.hidden = !slug;
  if (!slug) return;

  // moons without a texture stay as the coloured marble
  ben.bi.className = `bi bi--${slug}`;
  ben.bi.style.setProperty("--mau", mau);
  if (texture) {
    ben.bi.style.setProperty("--anh", `url("${texture}")`);
    const { may, vanh } = ben.sanKhau.dataset;
    ben.dong = moCanh3D(ben.sanKhau, { slug, texture, may, vanh }, () => {
      ben.goiY.hidden = false;
    });
  } else {
    ben.bi.style.removeProperty("--anh");
  }
}

// Both sides drawn on one compressed size scale, so a bigger body really looks bigger.
function capNhatTiLe() {
  const chon = cacBen.map(dangChon).filter((o) => o.value);
  const coLonNhat = Math.max(...chon.map((o) => Number(o.dataset.co)));
  const saoTho = chon.find((o) => o.value === "saturn");
  // the whole pair shrinks when needed so Saturn's rings still fit its stage
  const coToiDa = saoTho ? Math.min(LAP_DAY, (LAP_DAY_SAO_THO * coLonNhat) / Number(saoTho.dataset.co)) : LAP_DAY;

  for (const ben of cacBen) {
    const o = dangChon(ben);
    const duKep = chon.length === 2 && o.value;
    const rong = duKep ? (Number(o.dataset.co) / coLonNhat) * coToiDa : null;
    const lapDay = o.value === "saturn" ? LAP_DAY_SAO_THO : LAP_DAY;
    ben.sanKhau.style.setProperty("--ti-le-3d", duKep ? rong / lapDay : 1);
    ben.sanKhau.style.setProperty("--ti-le-bi", duKep ? rong / LAP_DAY : 1);
  }
}

function khoaLuaChonTrung() {
  cacBen.forEach((ben, i) => {
    const benKia = dangChon(cacBen[1 - i]).value;
    for (const o of ben.chon.options) o.disabled = Boolean(o.value) && o.value === benKia;
  });
}

async function capNhatKetQua() {
  yeuCau?.abort();
  const thamSo = new URLSearchParams();
  for (const ben of cacBen) if (ben.chon.value) thamSo.set(ben.chon.name, ben.chon.value);
  history.replaceState(null, "", `?${thamSo}`);
  // never leave the previous pair's numbers under the new planets
  if (thamSo.size < 2) return ketQua.replaceChildren();

  yeuCau = new AbortController();
  try {
    const phanHoi = await fetch(`?${thamSo}`, { signal: yeuCau.signal });
    if (!phanHoi.ok) throw new Error(phanHoi.statusText);
    const trang = new DOMParser().parseFromString(await phanHoi.text(), "text/html");
    ketQua.replaceChildren(...trang.getElementById("ket-qua").childNodes);
    window.ganBieuDo();
  } catch (loi) {
    if (loi.name !== "AbortError") form.requestSubmit(); // no live update: a normal page load still works
  }
}

// the button is only for browsers without JavaScript
form.querySelector(".o-nut").hidden = true;

for (const ben of cacBen) {
  ben.chon.addEventListener("change", () => {
    hienBen(ben);
    capNhatTiLe();
    khoaLuaChonTrung();
    capNhatKetQua();
  });
}
// pageshow, not load: the browser restores the selection on Back before this fires
addEventListener("pageshow", () => {
  cacBen.forEach(hienBen);
  capNhatTiLe();
  khoaLuaChonTrung();
});
