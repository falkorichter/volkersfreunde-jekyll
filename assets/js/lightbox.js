/*
 * Minimal lightbox for post images: a click on an image link inside a post opens the
 * full-size image in a <dialog> instead of leaving the page.
 * Unlinked images that are shown smaller than their real size open the same way.
 * Esc / click / × closes it, ← → step through the other images of the same post.
 * Without JavaScript the links simply open the image.
 */
(function () {
  var IMAGE = /\.(jpe?g|png|gif|webp|bmp)$/i;
  if (typeof HTMLDialogElement !== "function") return; // very old browsers: plain links

  var dialog = document.createElement("dialog");
  dialog.className = "lightbox";
  dialog.setAttribute("aria-label", "Bild");
  dialog.innerHTML =
    '<button type="button" class="lightbox-close" aria-label="Schließen">×</button>' +
    '<button type="button" class="lightbox-prev" aria-label="Vorheriges Bild">‹</button>' +
    '<button type="button" class="lightbox-next" aria-label="Nächstes Bild">›</button>' +
    '<figure><img alt="" /><figcaption></figcaption></figure>';
  document.body.appendChild(dialog);

  var img = dialog.querySelector("img");
  var caption = dialog.querySelector("figcaption");
  var prev = dialog.querySelector(".lightbox-prev");
  var next = dialog.querySelector(".lightbox-next");
  var group = [];
  var index = 0;

  function isImageLink(a) {
    return IMAGE.test(a.pathname) && a.origin === location.origin;
  }

  // Unlinked images shown smaller than their real size (e.g. squeezed into the column).
  function isZoomable(image) {
    return !image.closest("a") && image.naturalWidth > image.clientWidth + 40;
  }

  function markZoomable(image) {
    image.classList.toggle("zoomable", isZoomable(image));
  }

  function items(root) {
    return Array.prototype.filter.call(root.querySelectorAll("a[href], img"), function (el) {
      return el.tagName === "A" ? isImageLink(el) : el.classList.contains("zoomable");
    });
  }

  function show(i) {
    index = (i + group.length) % group.length;
    var item = group[index];
    var thumb = item.tagName === "IMG" ? item : item.querySelector("img");
    var text = (thumb && (thumb.getAttribute("alt") || thumb.getAttribute("title"))) || item.getAttribute("title") || "";
    if (/^(image|thumbnail)$/i.test(text)) text = ""; // placeholder alt texts from old mobile apps
    dialog.classList.add("is-loading");
    img.onload = function () { dialog.classList.remove("is-loading"); };
    img.src = item.tagName === "IMG" ? item.currentSrc || item.src : item.href;
    img.alt = text;
    caption.textContent = text;
    caption.hidden = !text;
    prev.hidden = next.hidden = group.length < 2;
  }

  document.addEventListener("click", function (event) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (!event.target.closest) return;
    var item = event.target.closest(".entry-content a[href]");
    if (item && !isImageLink(item)) return;
    if (!item && event.target.matches(".entry-content img.zoomable")) item = event.target;
    if (!item) return;
    event.preventDefault();
    group = items(item.closest(".entry-content"));
    show(group.indexOf(item));
    if (!dialog.open) dialog.showModal();
  });

  dialog.addEventListener("click", function (event) {
    if (event.target === prev) show(index - 1);
    else if (event.target === next) show(index + 1);
    else dialog.close(); // click on the image, the backdrop or ×
  });

  dialog.addEventListener("keydown", function (event) {
    if (event.key === "ArrowLeft" && group.length > 1) show(index - 1);
    if (event.key === "ArrowRight" && group.length > 1) show(index + 1);
  });

  dialog.addEventListener("close", function () { img.removeAttribute("src"); });

  function scan() {
    Array.prototype.forEach.call(document.querySelectorAll(".entry-content img"), function (image) {
      if (image.closest("dialog")) return;
      if (image.complete) markZoomable(image);
      else image.addEventListener("load", function () { markZoomable(image); }, { once: true });
    });
  }
  scan();
  window.addEventListener("resize", scan);
})();
