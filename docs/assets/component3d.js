(function () {
  "use strict";

  var DATA = window.VIEW3D;
  var root = document.querySelector(".c3d");
  if (!DATA || !root) return;

  var canvas = root.querySelector(".c3d-canvas");
  var stage = root.querySelector(".c3d-stage");
  var layerBox = root.querySelector(".c3d-layers");
  var metaBox = root.querySelector(".c3d-meta");
  var autoBox = root.querySelector(".c3d-auto");
  var resetBtn = root.querySelector(".c3d-reset");
  if (!canvas || !stage) return;
  var ctx = canvas.getContext("2d");

  var layers = (DATA.layers || []).slice().sort(function (a, b) {
    return (a.order == null ? 0 : a.order) - (b.order == null ? 0 : b.order);
  });
  if (!layers.length) return;

  var defaults = layers.map(function (l) {
    var d = (l.display == null ? 1.0 : l.display);
    return Math.max(0.2, Math.min(10, d));
  });
  var thickness = defaults.slice();

  var span = Math.max(DATA.size[0], DATA.size[1], 1);
  // 堆叠总高度控制为版图尺度的 6%，并限制在 2..40 之间，
  // 这样长条形器件不会变成一根超厚柱子。
  var targetStack = Math.max(2, Math.min(span * 0.06, 40));
  var zUnit = targetStack / (defaults.reduce(function (a, b) { return a + b; }, 0) || 1);
  var gapFactor = 0.15;

  var yaw = -0.62;
  var pitch = 1.02;
  var zoom = 1.0;
  var panX = 0, panY = 0;
  var W = 1, H = 1;
  var dragging = false, dragMode = "rotate", lastX = 0, lastY = 0;
  var raf = null;

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

  function shade(hex, factor) {
    var h = (hex || "#64748b").replace("#", "");
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var r = parseInt(h.slice(0, 2), 16);
    var g = parseInt(h.slice(2, 4), 16);
    var b = parseInt(h.slice(4, 6), 16);
    return "rgb(" + clamp(Math.round(r * factor), 0, 255) + "," +
      clamp(Math.round(g * factor), 0, 255) + "," +
      clamp(Math.round(b * factor), 0, 255) + ")";
  }

  function project(x, y, z) {
    var cy = Math.cos(yaw), sy = Math.sin(yaw);
    var cp = Math.cos(pitch), sp = Math.sin(pitch);
    var x1 = x * cy - y * sy;
    var y1 = x * sy + y * cy;
    return [x1, -(y1 * cp + z * sp)];
  }

  function zPositions() {
    var z = 0;
    return layers.map(function (l, i) {
      if (i > 0) z += gapFactor * zUnit;
      var z0 = z;
      z += thickness[i] * zUnit;
      return [z0, z];
    });
  }

  function projectedPoints(zs) {
    var out = [];
    layers.forEach(function (layer, i) {
      var z0 = zs[i][0], z1 = zs[i][1];
      layer.polygons.forEach(function (poly) {
        [poly.outer].concat(poly.holes || []).forEach(function (contour) {
          contour.forEach(function (p) {
            out.push(project(p[0], p[1], z0));
            out.push(project(p[0], p[1], z1));
          });
        });
      });
    });
    return out;
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
    ctx.clearRect(0, 0, W, H);
    var zs = zPositions();
    var pts = projectedPoints(zs);
    if (!pts.length) return;
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    pts.forEach(function (p) {
      if (p[0] < minX) minX = p[0];
      if (p[0] > maxX) maxX = p[0];
      if (p[1] < minY) minY = p[1];
      if (p[1] > maxY) maxY = p[1];
    });
    var dx = Math.max(maxX - minX, 1e-6);
    var dy = Math.max(maxY - minY, 1e-6);
    var scale = Math.min((W - 90) / dx, (H - 80) / dy) * zoom;
    var tx = (W - dx * scale) / 2 - minX * scale + panX;
    var ty = (H - dy * scale) / 2 - minY * scale + panY;

    layers.forEach(function (layer, i) {
      var z0 = zs[i][0], z1 = zs[i][1];
      var alpha = layer.alpha == null ? 0.95 : layer.alpha;

      // 只画顶面 + 可见侧壁；不画底面，且剔除背向相机的侧壁，
      // 避免远侧壁在投影里形成一圈“阴影/第二层”。
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
        for (var k = 0; k < contour.length; k++) {
          var a = contour[k];
          var b = contour[(k + 1) % contour.length];
          var dx = b[0] - a[0], dy = b[1] - a[1];
          // 外轮廓的朝外法向；孔洞再翻转一次
          var nx = ccw ? dy : -dy;
          var ny = ccw ? -dx : dx;
          if (isHole) { nx = -nx; ny = -ny; }
          // 相机方向 d=(sin(yaw)sin(pitch), cos(yaw)sin(pitch), -cos(pitch))
          // 法向朝向相机才画；背向相机的侧壁完全剔除
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

      // 顶面：evenodd 保留孔洞
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
      ctx.strokeStyle = "rgba(255,255,255,.35)";
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

  function makeEl(tag, cls, textValue) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (textValue != null) el.textContent = textValue;
    return el;
  }

  function buildLayerControls() {
    if (!layerBox) return;
    layerBox.innerHTML = "";
    layers.forEach(function (layer, i) {
      var row = makeEl("div", "c3d-layer");
      var dot = makeEl("span", "c3d-dot");
      dot.style.background = layer.color;
      row.appendChild(dot);
      var label = makeEl("span", "c3d-name");
      label.appendChild(makeEl("strong", null, layer.name));
      label.appendChild(makeEl("small", null, layer.key));
      row.appendChild(label);

      var range = document.createElement("input");
      range.type = "range";
      range.min = "0.2"; range.max = "6"; range.step = "0.1";
      range.value = String(thickness[i]);
      range.className = "c3d-range";
      row.appendChild(range);

      var num = document.createElement("input");
      num.type = "number";
      num.min = "0.2"; num.max = "20"; num.step = "0.1";
      num.value = thickness[i].toFixed(1);
      num.className = "c3d-num";
      row.appendChild(num);

      function apply(v) {
        v = Math.max(0.2, Math.min(20, parseFloat(v) || defaults[i]));
        thickness[i] = v;
        range.value = String(v);
        num.value = v.toFixed(1);
        draw();
      }
      range.addEventListener("input", function () { apply(range.value); });
      num.addEventListener("input", function () { apply(num.value); });
      layerBox.appendChild(row);
    });
    if (metaBox) {
      metaBox.textContent = "尺寸 " + DATA.size[0].toFixed(1) + " × " +
        DATA.size[1].toFixed(1) + " · " + layers.length + " 层 · 厚度为显示比例";
    }
  }

  function resetAll() {
    yaw = -0.62; pitch = 1.02; zoom = 1.0;
    panX = 0; panY = 0;
    thickness = defaults.slice();
    buildLayerControls();
    draw();
  }

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
    if (dragMode === "pan") {
      panX += dx;
      panY += dy;
    } else {
      yaw += dx * 0.008;
      pitch = clamp(pitch - dy * 0.007, 0.18, 1.45);
    }
    lastX = e.clientX; lastY = e.clientY;
    draw();
  });
  function endDrag() { dragging = false; canvas.style.cursor = "grab"; }
  canvas.addEventListener("pointerup", endDrag);
  canvas.addEventListener("pointercancel", endDrag);
  canvas.addEventListener("contextmenu", function (e) { e.preventDefault(); });
  canvas.addEventListener("wheel", function (e) {
    e.preventDefault();
    zoom = clamp(zoom * Math.exp(-e.deltaY * 0.0012), 0.35, 6);
    draw();
  }, { passive: false });
  canvas.addEventListener("dblclick", function () {
    yaw = -0.62; pitch = 1.02; zoom = 1.0;
    panX = 0; panY = 0;
    draw();
  });
  if (resetBtn) resetBtn.addEventListener("click", resetAll);
  if (autoBox) {
    autoBox.addEventListener("change", function () {
      if (autoBox.checked && !raf) tick();
    });
  }
  function tick() {
    if (!autoBox || !autoBox.checked) { raf = null; return; }
    yaw += 0.006;
    draw();
    raf = requestAnimationFrame(tick);
  }

  window.addEventListener("resize", resize);
  buildLayerControls();
  resize();
})();
