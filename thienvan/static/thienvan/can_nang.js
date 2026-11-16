(() => {
  const G_TRAI_DAT = 9.81;
  const kg = document.getElementById("kg");
  const loi = document.getElementById("loi-can");
  const so = (x) => x.toLocaleString("vi-VN", { maximumFractionDigits: 1 });

  function hopLe(o) {
    const giaTri = Number(o.value);
    return o.value !== "" && giaTri >= Number(o.min) && giaTri <= Number(o.max);
  }

  function tinh() {
    const dung = hopLe(kg);
    loi.hidden = dung;
    loi.textContent = dung ? "" : "Nhập cân nặng từ 1 đến 500 kg nhé.";
    document.querySelectorAll("#bang-can tbody tr").forEach((dong) => {
      const g = Number(dong.dataset.g);
      dong.querySelector('[data-cot="kg"]').textContent = dung ? `${so((Number(kg.value) * g) / G_TRAI_DAT)} kg` : "";
    });
  }

  document.getElementById("form-can").addEventListener("submit", (e) => e.preventDefault());
  kg.addEventListener("input", tinh);
  tinh();
})();
