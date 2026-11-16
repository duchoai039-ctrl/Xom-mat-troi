// Charts live in a closed <details>: a canvas drawn while hidden has no size, so they are drawn on first open.
(() => {
  Chart.defaults.color = "#c6bce8";
  Chart.defaults.font.family = "'Be Vietnam Pro', sans-serif";

  const MU = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };

  // label whole powers of ten only, and few enough that a 27-decade axis stays readable
  const taoNhanTruc = (buoc) => (giaTri) => {
    const soMu = Math.round(Math.log10(giaTri));
    if (Math.abs(Math.log10(giaTri) - soMu) > 1e-9 || soMu % buoc) return "";
    if (Math.abs(soMu) < 5) return giaTri.toLocaleString("vi-VN", { maximumFractionDigits: 6 });
    return `10${[...String(soMu)].map((kyTu) => MU[kyTu]).join("")}`;
  };

  function ve(luoi) {
    const duLieu = JSON.parse(document.getElementById("du-lieu-bieu-do").textContent);
    for (const { nhan, a, b } of duLieu) {
      const coSo = [a, b].filter((x) => x !== null);
      if (!coSo.length) continue;
      const day = Math.floor(Math.log10(Math.min(...coSo))) - 1;
      const dinh = Math.ceil(Math.log10(Math.max(...coSo)));
      const hinh = document.createElement("figure");
      const canvas = document.createElement("canvas");
      canvas.setAttribute("role", "img");
      canvas.setAttribute("aria-label", `${nhan}: ${luoi.dataset.a} ${a ?? "chưa có"}, ${luoi.dataset.b} ${b ?? "chưa có"}`);
      hinh.append(canvas);
      luoi.append(hinh);
      new Chart(canvas, {
        type: "bar",
        data: {
          labels: [luoi.dataset.a, luoi.dataset.b],
          datasets: [{ data: [a, b], backgroundColor: ["#ff8a3d", "#4ed4c6"], borderRadius: 10 }],
        },
        options: {
          maintainAspectRatio: false,
          plugins: { legend: { display: false }, title: { display: true, text: nhan, color: "#f7f3ff" } },
          scales: {
            x: { grid: { display: false } },
            y: {
              type: "logarithmic",
              // bars grow from the axis floor, so the floor must sit below the smaller value
              min: 10 ** day,
              grid: { color: (nguCanh) => (nguCanh.tick?.label ? "#36286e" : "transparent") },
              ticks: { autoSkip: false, callback: taoNhanTruc(Math.max(1, Math.ceil((dinh - day) / 5))) },
            },
          },
        },
      });
    }
  }

  // also called by so_sanh_3d.js after it swaps in a new result
  window.ganBieuDo = () => {
    const chiTiet = document.querySelector(".them-bieu-do");
    chiTiet?.addEventListener("toggle", () => {
      const luoi = document.getElementById("bieu-do");
      if (chiTiet.open && !luoi.children.length) ve(luoi);
    });
  };
  window.ganBieuDo();
})();
