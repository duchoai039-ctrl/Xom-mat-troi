// Live suggestions for the navbar search box. Without JS the form still submits to the results page.
(() => {
  const form = document.querySelector(".o-tim");
  const input = form.querySelector("input");
  const list = form.querySelector(".goi-y");
  let hen = null;
  let yeuCau = null;

  const dong = () => { list.hidden = true; };

  function hien(ketQua) {
    list.replaceChildren(...(ketQua.length ? ketQua.map((muc) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      const loai = document.createElement("small");
      a.href = muc.url;
      a.append(muc.ten);
      loai.textContent = muc.loai;
      a.append(loai);
      li.append(a);
      return li;
    }) : [Object.assign(document.createElement("li"), { className: "trong", textContent: "Chưa thấy thiên thể này trong xóm" })]));
    list.hidden = false;
  }

  input.addEventListener("input", () => {
    clearTimeout(hen);
    yeuCau?.abort();
    const q = input.value.trim();
    if (!q) return dong();
    hen = setTimeout(async () => {
      yeuCau = new AbortController();
      try {
        const res = await fetch(`${form.dataset.goiY}?q=${encodeURIComponent(q)}`, { signal: yeuCau.signal });
        if (!res.ok) return dong();
        hien((await res.json()).ket_qua);
      } catch (loi) {
        if (loi.name !== "AbortError") dong();
      }
    }, 180);
  });

  form.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { dong(); input.focus(); }
  });
  document.addEventListener("click", (e) => { if (!form.contains(e.target)) dong(); });
})();
