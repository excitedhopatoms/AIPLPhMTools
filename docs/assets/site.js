(function () {
  "use strict";

  // ---------- sidebar search ----------
  var search = document.getElementById("nav-search");
  var empty = document.querySelector(".nav-empty");
  var groups = Array.prototype.slice.call(document.querySelectorAll(".nav-group"));
  var links = Array.prototype.slice.call(document.querySelectorAll(".nav-links .nav-link"));

  function normalize(s) {
    return (s || "").toLowerCase().trim();
  }

  function filterNav() {
    var q = normalize(search ? search.value : "");
    var shown = 0;
    links.forEach(function (a) {
      var hay = normalize(a.getAttribute("data-name") + " " + (a.getAttribute("data-keywords") || ""));
      var hit = !q || hay.indexOf(q) !== -1;
      a.hidden = !hit;
      if (hit) shown++;
    });
    groups.forEach(function (g) {
      var visible = g.querySelectorAll(".nav-links .nav-link:not([hidden])").length;
      g.hidden = visible === 0;
      if (q) g.open = true;
    });
    if (empty) empty.style.display = shown === 0 ? "block" : "none";
  }

  if (search) {
    search.addEventListener("input", filterNav);
    search.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { search.value = ""; filterNav(); search.blur(); }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== search) {
        e.preventDefault(); search.focus(); search.select();
      }
    });
  }

  // ---------- mobile sidebar ----------
  var menu = document.querySelector(".menu-btn");
  var sidebar = document.querySelector(".sidebar");
  if (menu && sidebar) {
    menu.addEventListener("click", function () { sidebar.classList.toggle("open"); });
  }

  // ---------- copy buttons ----------
  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); } catch (e) { /* ignore */ }
    document.body.removeChild(ta);
  }
  Array.prototype.slice.call(document.querySelectorAll(".copy-btn")).forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-code") || "";
      var old = btn.textContent;
      function done() { btn.textContent = "已复制"; setTimeout(function () { btn.textContent = old; }, 1400); }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
      } else { fallbackCopy(text); done(); }
    });
  });

  // ---------- lightbox ----------
  var box = document.querySelector(".lightbox-overlay");
  if (!box) {
    box = document.createElement("div");
    box.className = "lightbox-overlay";
    box.innerHTML = '<button class="lightbox-close" aria-label="关闭">×</button><img alt="">';
    document.body.appendChild(box);
  }
  var boxImg = box.querySelector("img");
  var close = box.querySelector(".lightbox-close");
  function closeBox() { box.classList.remove("open"); boxImg.removeAttribute("src"); }
  Array.prototype.slice.call(document.querySelectorAll("a.lightbox")).forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      boxImg.src = a.getAttribute("href");
      boxImg.alt = a.querySelector("img") ? a.querySelector("img").alt : "";
      box.classList.add("open");
    });
  });
  box.addEventListener("click", function (e) { if (e.target === box) closeBox(); });
  if (close) close.addEventListener("click", closeBox);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && box.classList.contains("open")) closeBox();
  });

  // ---------- highlight active param on hash ----------
  function flashHash() {
    if (!location.hash) return;
    var el = document.getElementById(location.hash.slice(1));
    if (!el) return;
    el.style.background = "#fff8c5";
    setTimeout(function () { el.style.background = ""; }, 1800);
  }
  window.addEventListener("hashchange", flashHash);
  flashHash();
})();
