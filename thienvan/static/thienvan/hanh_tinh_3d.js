import * as THREE from "three";
import { OrbitControls } from "./../vendor/OrbitControls.js";

const DO_NGHIENG = { sun: 7.25, earth: 23.4, mars: 25.2, jupiter: 3.1, saturn: 26.7, uranus: 97.8, neptune: 28.3, moon: 6.7 };
// rocky bodies: the colour map doubles as a bump map; gas giants have no surface to bump
const DA = new Set(["mercury", "mars", "moon"]);
const KHI_QUYEN = { sun: "#ffb05a", earth: "#6fb7ff", venus: "#ffd9a0", mars: "#ff9b6b", uranus: "#a9eef0", neptune: "#7c9bff" };
const BOT_CHUYEN_DONG = matchMedia("(prefers-reduced-motion: reduce)").matches;

function vienKhiQuyen(mauSac) {
  return new THREE.Mesh(
    new THREE.SphereGeometry(1.07, 48, 48),
    new THREE.ShaderMaterial({
      uniforms: { mau: { value: new THREE.Color(mauSac) } },
      vertexShader: `varying vec3 n; varying vec3 v;
        void main() { n = normalize(normalMatrix * normal); vec4 p = modelViewMatrix * vec4(position, 1.0); v = normalize(-p.xyz); gl_Position = projectionMatrix * p; }`,
      fragmentShader: `uniform vec3 mau; varying vec3 n; varying vec3 v;
        void main() { float a = pow(clamp(-dot(n, v) * 2.2, 0.0, 1.0), 2.0) * 0.8; gl_FragColor = vec4(mau, a); }`,
      side: THREE.BackSide,
      transparent: true,
      depthWrite: false,
    }),
  );
}

function vanhSaoTho(taiAnh, vanh) {
  const hinh = new THREE.RingGeometry(1.25, 2.27, 128);
  // map the ring texture radially instead of across a square
  const vi_tri = hinh.attributes.position;
  const v = new THREE.Vector3();
  for (let i = 0; i < vi_tri.count; i++) {
    v.fromBufferAttribute(vi_tri, i);
    hinh.attributes.uv.setXY(i, (v.length() - 1.25) / 1.02, 0.5);
  }
  const vat = new THREE.Mesh(hinh, new THREE.MeshStandardMaterial({
    map: taiAnh.load(vanh), side: THREE.DoubleSide, transparent: true, depthWrite: false, color: "#efe3c2",
  }));
  vat.rotation.x = Math.PI / 2;
  return vat;
}

function dungCanh(khung, { slug, texture, may, vanh }, khiSan) {
  let daDong = false;
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));

  const canh = new THREE.Scene();
  const mayQuay = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
  // Saturn is viewed from above, level with its equator the rings shrink to a line
  mayQuay.position.set(0, slug === "saturn" ? 3.2 : 0, slug === "saturn" ? 8.2 : 3.8);

  const taiAnh = new THREE.TextureLoader();
  const nhom = new THREE.Group();
  nhom.rotation.z = THREE.MathUtils.degToRad(DO_NGHIENG[slug] ?? 0);
  canh.add(nhom);

  const beMat = taiAnh.load(texture, () => {
    // the viewer may have picked another body while this image was still loading
    if (daDong) return;
    // show the canvas only once the texture is really there, the CSS marble stays until then
    khung.append(renderer.domElement);
    khung.classList.add("da-3d");
    khiSan();
  });
  beMat.colorSpace = THREE.SRGBColorSpace;
  beMat.anisotropy = renderer.capabilities.getMaxAnisotropy();

  // the sun makes its own light, so scene lighting must not shade it
  const chatLieu = slug === "sun"
    ? new THREE.MeshBasicMaterial({ map: beMat })
    : new THREE.MeshStandardMaterial({ map: beMat, color: "#ffffff", roughness: 0.95, metalness: 0 });
  if (DA.has(slug)) {
    chatLieu.bumpMap = beMat;
    chatLieu.bumpScale = 1.4;
  }
  const qua = new THREE.Mesh(new THREE.SphereGeometry(1, 64, 64), chatLieu);
  nhom.add(qua);

  let may_bay = null;
  if (slug === "earth") {
    const anhMay = taiAnh.load(may);
    may_bay = new THREE.Mesh(
      new THREE.SphereGeometry(1.012, 64, 64),
      new THREE.MeshStandardMaterial({ alphaMap: anhMay, transparent: true, depthWrite: false, color: "#ffffff" }),
    );
    nhom.add(may_bay);
  }
  if (slug === "saturn") nhom.add(vanhSaoTho(taiAnh, vanh));
  if (KHI_QUYEN[slug]) canh.add(vienKhiQuyen(KHI_QUYEN[slug]));

  canh.add(new THREE.AmbientLight("#ffffff", 0.35));
  // light from the left, where the sun sits on the home page
  const nangMatTroi = new THREE.DirectionalLight("#fff4e2", 2.8);
  nangMatTroi.position.set(-4, 1.5, 3.5);
  canh.add(nangMatTroi);

  const dieuKhien = new OrbitControls(mayQuay, renderer.domElement);
  dieuKhien.enablePan = false;
  dieuKhien.enableZoom = false; // the wheel must keep scrolling the page
  dieuKhien.enableDamping = true;

  const quanSat = new ResizeObserver(() => {
    const co = khung.clientWidth;
    renderer.setSize(co, co, false);
    mayQuay.updateProjectionMatrix();
  });
  quanSat.observe(khung);

  renderer.setAnimationLoop(() => {
    if (!BOT_CHUYEN_DONG) {
      qua.rotation.y += 0.0022;
      if (may_bay) may_bay.rotation.y += 0.0029;
    }
    dieuKhien.update();
    renderer.render(canh, mayQuay);
  });

  // browsers cap live WebGL contexts, so switching bodies must release the old one for real
  return () => {
    daDong = true;
    renderer.setAnimationLoop(null);
    quanSat.disconnect();
    dieuKhien.dispose();
    canh.traverse((vat) => {
      vat.geometry?.dispose();
      vat.material?.map?.dispose();
      vat.material?.alphaMap?.dispose();
      vat.material?.dispose();
    });
    renderer.dispose();
    renderer.forceContextLoss();
    renderer.domElement.remove();
    khung.classList.remove("da-3d");
  };
}

// Returns a function that closes the scene. No WebGL: the CSS marble underneath stays as the static fallback.
export function moCanh3D(khung, thongTin, khiSan = () => {}) {
  try {
    return dungCanh(khung, thongTin, khiSan);
  } catch (loi) {
    console.warn("Không dùng được 3D:", loi);
    return () => {};
  }
}

const khungChiTiet = document.getElementById("san-khau-3d");
if (khungChiTiet) {
  moCanh3D(khungChiTiet, khungChiTiet.dataset, () => {
    document.getElementById("goi-y-xoay").hidden = false;
  });
}
