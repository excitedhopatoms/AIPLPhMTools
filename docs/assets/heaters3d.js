(function () {
  "use strict";

  var DATA = window.HEATER_3D || {};
  var canvas = document.getElementById("h3d-canvas");
  if (!canvas) return;
  var ctx = canvas.getContext("2d");
  var info = document.getElementById("h3d-info");
  var legend = document.getElementById("h3d-legend");
  var autoBox = document.getElementById("h3d-auto");
  var explodeInput = document.getElementById("h3d-explode");
  var resetBtn = document.getElementById("h3d-reset");
  var buttons = Array.prototype.slice.call(document.querySelectorAll(".h3d-item"));

  var keys = Object.keys(DATA);
  if (!keys.length) {
    if (info) info.textContent = "没有 3D 数据。请先运行 build_site.py。";
    return;
  }

  var query = new URLSearchParams(window.location.search).get("item");
  var current = DATA[query] ? query : keys[0];

  var yaw = -0.62;
  var pitch = 1.02;
  var zoom = 1.0;
  var explode = 1.0;
  var panX = 0;
  var panY = 0;
  var dragging = false;
  var dragMode = "rotate";
  var lastX = 0;
  var lastY = 0;
  var W = 1;
  var H = 1;

  function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
  }

  function shade(hex, factor) {
    var h = (hex || "#64748b").replace("#", "");
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var r = parseInt(h.slice(0, 2), 16);
    var g = parseInt(h.slice(2, 4), 16);
    var b = parseInt(h.slice(4, 6), 16);
    r = clamp(Math.round(r * factor), 0, 255);
    g = clamp(Math.round(g * factor), 0, 255);
    b = clamp(Math.round(b * factor), 0, 255);
    return "rgb(" + r + "," + g + "," + b + ")";
  }

  // 旋转 + 正交投影：x/y 是版图平面，z 是层叠方向（向上）
  function project(x, y, z) {
    var cy = Math.cos(yaw), sy = Math.sin(yaw);
    var cp = Math.cos(pitch), sp = Math.sin(pitch);
    var x1 = x * cy - y * sy;
    var y1 = x * sy + y * cy;
    var zz = z * explode;
    return [x1, -(y1 * cp + zz * sp)];
  }

  function layerThickness(layer) {
    // 层厚只做视觉提示，随 explode 轻微变化
    return layer.thickness * (0.75 + 0.25 * explode);
  }

  function allProjected(item) {
    var pts = [];
    item.layers.forEach(function (layer) {
      var z0 = layer.z * explode;
      var z1 = z0 + layerThickness(layer);
      layer.polygons.forEach(function (poly) {
        [poly.outer].concat(poly.holes || []).forEach(function (contour) {
          contour.forEach(function (p) {
            pts.push(project(p[0], p[1], z0));
            pts.push(project(p[0], p[1], z1));
          });
        });
      });
    });
    return pts;
  }

  function addContour(path, contour, z, tx, ty, scale) {
    for (var i = 0; i < contour.length; i++) {
      var q = project(contour[i][0], contour[i][1], z);
      var x = tx + q[0] * scale;
      var y = ty + q[1] * scale;
      if (i === 0) path.moveTo(x, y);
      else path.lineTo(x, y);
    }
    path.closePath();
  }

  function draw() {
    var item = DATA[current];
    if (!item) return;

    ctx.clearRect(0, 0, W, H);
    var pts = allProjected(item);
    if (!pts.length) return;
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    pts.forEach(function (p) {
      minX = Math.min(minX, p[0]); maxX = Math.max(maxX, p[0]);
      minY = Math.min(minY, p[1]); maxY = Math.max(maxY, p[1]);
    });
    var dx = Math.max(maxX - minX, 1e-6);
    var dy = Math.max(maxY - minY, 1e-6);
    var scale = Math.min((W - 100) / dx, (H - 92) / dy) * zoom;
    var tx = (W - dx * scale) / 2 - minX * scale + panX;
    var ty = (H - dy * scale) / 2 - minY * scale + panY;

    // 从下到上画：低层先画，高层覆盖上去；每层先侧壁再顶面
    item.layers.slice().sort(function (a, b) { return a.z - b.z; }).forEach(function (layer) {
      var z0 = layer.z * explode;
      var z1 = z0 + layerThickness(layer);
      var alpha = layer.alpha == null ? 0.95 : layer.alpha;

      // 只画顶面 + 可见侧壁；剔除背向相机的侧壁，避免投影里出现“阴影/第二层”
      var sy = Math.sin(yaw), cy = Math.cos(yaw), sp = Math.sin(pitch);
      ctx.globalAlpha = Math.min(1, alpha + 0.03);
      ctx.fillStyle = shade(layer.color, 0.88);
      var walls = new Path2D();
      function addWalls(contour, isHole) {
        var area2 = 0;
        for (var n = 0; n < contour.length; n++) {
          var q0 = contour[n], q1 = contour[(n + 1) % contour.length];
          area2 += q0[0] * q1[1] - q1[0] * q0[1];
        }
        var ccw = area2 > 0;
        for (var i = 0; i < contour.length; i++) {
          var a = contour[i];
          var b = contour[(i + 1) % contour.length];
          var dx = b[0] - a[0], dy = b[1] - a[1];
          var nx = ccw ? dy : -dy;
          var ny = ccw ? -dx : dx;
          if (isHole) { nx = -nx; ny = -ny; }
          if (nx * sy * sp + ny * cy * sp >= -1e-9) continue;
          var p0 = project(a[0], a[1], z0);
          var p1 = project(b[0], b[1], z0);
          var p2 = project(b[0], b[1], z1);
          var p3 = project(a[0], a[1], z1);
          walls.moveTo(tx + p0[0] * scale, ty + p0[1] * scale);
          walls.lineTo(tx + p1[0] * scale, ty + p1[1] * scale);
          walls.lineTo(tx + p2[0] * scale, ty + p2[1] * scale);
          walls.lineTo(tx + p3[0] * scale, ty + p3[1] * scale);
          walls.closePath();
        }
      }
      layer.polygons.forEach(function (poly) {
        addWalls(poly.outer, false);
        (poly.holes || []).forEach(function (hole) { addWalls(hole, true); });
      });
      ctx.fill(walls);

      // 顶面（evenodd 保留孔洞）
      ctx.globalAlpha = alpha;
      ctx.fillStyle = layer.color;
      var top = new Path2D();
      layer.polygons.forEach(function (poly) {
        addContour(top, poly.outer, z1, tx, ty, scale);
        (poly.holes || []).forEach(function (hole) {
          addContour(top, hole, z1, tx, ty, scale);
        });
      });
      ctx.fill(top, "evenodd");
      ctx.globalAlpha = Math.min(1, alpha + 0.15);
      ctx.strokeStyle = "rgba(255,255,255,.34)";
      ctx.lineWidth = 0.8;
      ctx.stroke(top);
    });

    ctx.globalAlpha = 1;
  }

  function resize() {
    var rect = canvas.getBoundingClientRect();
    var dpr = window.devicePixelRatio || 1;
    W = Math.max(1, rect.width);
    H = Math.max(1, rect.height);
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }

  function text(tag, cls, value) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (value != null) el.textContent = value;
    return el;
  }

  function renderInfo() {
    var item = DATA[current];
    if (!item || !info) return;
    info.innerHTML = "";
    var h = text("h3", null, item.title);
    info.appendChild(h);
    var p = text("p", "h3d-note", item.note || "");
    info.appendChild(p);
    var meta = text("p", "h3d-meta",
      "版图尺寸 " + item.size[0].toFixed(1) + " × " + item.size[1].toFixed(1) +
      " µm · " + item.layers.length + " 个图层 · z 间距为示意");
    info.appendChild(meta);
    var pre = document.createElement("pre");
    var code = document.createElement("code");
    code.textContent = "import AIPLPhMTools as ap\n\nc = " + item.code;
    pre.appendChild(code);
    info.appendChild(pre);
  }

  function renderLegend() {
    var item = DATA[current];
    if (!item || !legend) return;
    legend.innerHTML = "";
    item.layers.forEach(function (layer) {
      var chip = document.createElement("span");
      chip.className = "h3d-chip";
      var dot = document.createElement("i");
      dot.style.background = layer.color;
      chip.appendChild(dot);
      chip.appendChild(document.createTextNode(layer.name + "  " + layer.key + "  z=" + layer.z));
      legend.appendChild(chip);
    });
  }

  function select(key) {
    if (!DATA[key]) return;
    current = key;
    buttons.forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-id") === key);
    });
    renderInfo();
    renderLegend();
    draw();
  }

  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      select(b.getAttribute("data-id"));
      var url = new URL(window.location.href);
      url.searchParams.set("item", current);
      history.replaceState(null, "", url);
    });
  });

  canvas.addEventListener("pointerdown", function (e) {
    dragging = true;
    dragMode = (e.button === 2 || e.button === 1 || e.shiftKey) ? "pan" : "rotate";
    lastX = e.clientX; lastY = e.clientY;
    canvas.setPointerCapture(e.pointerId);
    canvas.style.cursor = dragMode === "pan" ? "move" : "grabbing";
  });
  canvas.addEventListener("pointermove", function (e) {
    if (!dragging) return;
    var dx = e.clientX - lastX;
    var dy = e.clientY - lastY;
    lastX = e.clientX; lastY = e.clientY;
    if (dragMode === "pan") {
      panX += dx;
      panY += dy;
    } else {
      yaw += dx * 0.008;
      pitch = clamp(pitch - dy * 0.007, 0.18, 1.45);
    }
    draw();
  });
  function endDrag() {
    dragging = false;
    canvas.style.cursor = "grab";
  }
  canvas.addEventListener("pointerup", endDrag);
  canvas.addEventListener("pointercancel", endDrag);
  canvas.addEventListener("contextmenu", function (e) { e.preventDefault(); });

  canvas.addEventListener("wheel", function (e) {
    e.preventDefault();
    zoom = clamp(zoom * Math.exp(-e.deltaY * 0.0012), 0.35, 6);
    draw();
  }, { passive: false });

  function resetView() {
    yaw = -0.62;
    pitch = 1.02;
    zoom = 1.0;
    panX = 0;
    panY = 0;
    draw();
  }
  canvas.addEventListener("dblclick", resetView);
  if (resetBtn) resetBtn.addEventListener("click", resetView);

  if (explodeInput) {
    explodeInput.addEventListener("input", function () {
      explode = parseFloat(explodeInput.value) || 1.0;
      draw();
    });
  }

  var raf = null;
  function tick() {
    if (!autoBox || !autoBox.checked) { raf = null; return; }
    yaw += 0.006;
    draw();
    raf = requestAnimationFrame(tick);
  }
  if (autoBox) {
    autoBox.addEventListener("change", function () {
      if (autoBox.checked && !raf) tick();
    });
  }

  window.addEventListener("resize", resize);
  resize();
  select(current);
})();
