/* White Admin demo — super admin dashboard backed by localStorage.
   Mirrors the shop API data flow: Currency -> Category -> Model ->
   Attribute -> Attribute Value -> Product (values + variants). */
(function () {
"use strict";

/* ============================== storage ============================== */
var LS_KEY = "white_admin_demo_v1";
var memFallback = {};
var storageOK = true;
var store = {
  get: function (k) {
    try { return window.localStorage.getItem(k); }
    catch (e) { storageOK = false; return memFallback[k] !== undefined ? memFallback[k] : null; }
  },
  set: function (k, v) {
    try { window.localStorage.setItem(k, v); }
    catch (e) { storageOK = false; memFallback[k] = v; }
  },
  del: function (k) {
    try { window.localStorage.removeItem(k); }
    catch (e) { delete memFallback[k]; }
  }
};

/* ============================== utils ============================== */
function uid() {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
  return "id-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
}
function esc(s) {
  return String(s === null || s === undefined ? "" : s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}
function slugify(s) {
  return String(s || "").toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}
function deep(o) { return JSON.parse(JSON.stringify(o)); }
function blankImage() { return { url: "", title: "", caption: "", alt: "" }; }
function hasImage(img) { return !!(img && (img.url || "").trim()); }

var ICONS = {
  x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>',
  pencil: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>',
  image: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>',
  eye: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
  code: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 18l6-6-6-6M8 6l-6 6 6 6"/></svg>',
  copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
  back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>'
};

function toast(msg, kind) {
  var root = document.getElementById("toastRoot");
  var el = document.createElement("div");
  el.className = "toast" + (kind === "err" ? " err" : "");
  el.textContent = msg;
  root.appendChild(el);
  setTimeout(function () { el.classList.add("out"); setTimeout(function () { el.remove(); }, 300); }, 2600);
}

/* ============================== modal ============================== */
function openModal(html, wide) {
  var root = document.getElementById("modalRoot");
  root.innerHTML = '<div class="overlay" id="overlay"><div class="modal' + (wide ? " wide" : "") + '" role="dialog">' + html + "</div></div>";
  document.getElementById("overlay").addEventListener("mousedown", function (e) {
    if (e.target && e.target.id === "overlay") closeModal();
  });
}
function closeModal() { document.getElementById("modalRoot").innerHTML = ""; }
function modalShell(title, bodyHtml, footHtml) {
  return '<div class="modal-head"><h3>' + esc(title) + '</h3><button class="icon-btn" data-close aria-label="Close">' + ICONS.x + "</button></div>" +
    '<div class="modal-body">' + bodyHtml + "</div>" +
    (footHtml ? '<div class="modal-foot">' + footHtml + "</div>" : "");
}
var confirmCb = null;
function askConfirm(title, message, okLabel, cb) {
  confirmCb = cb;
  openModal(modalShell(title,
    '<p class="muted" style="margin:0">' + esc(message) + "</p>",
    '<button class="btn" data-close>Cancel</button><button class="btn btn-dark" id="confirmOk">' + esc(okLabel || "Delete") + "</button>"));
  document.getElementById("confirmOk").addEventListener("click", function () {
    closeModal(); if (confirmCb) { var f = confirmCb; confirmCb = null; f(); }
  });
}
function fieldError(msg) {
  var box = document.getElementById("formError");
  if (!box) { if (msg) toast(msg, "err"); return; }
  if (msg) { box.textContent = msg; box.classList.add("show"); }
  else { box.textContent = ""; box.classList.remove("show"); }
}

/* ============================== seed data ============================== */
function seed() {
  var npr = uid(), cat = uid(), mod = uid(), color = uid(), size = uid();
  var grey = uid(), blue = uid(), v40 = uid(), v41 = uid();
  return {
    currencies: [
      { id: npr, code: "NPR", name: "Nepalese Rupee", symbol: "Rs.", is_active: true }
    ],
    categories: [
      { id: cat, name: "Slippers", slug: "slippers", description: "Comfy everyday slippers.", is_active: true,
        image: { url: "https://picsum.photos/seed/slippers-cat/400/300", title: "Slippers", caption: "", alt: "Slippers" } }
    ],
    models: [
      { id: mod, name: "Celsi", slug: "celsi", description: "Wool felt slipper line.", is_active: true }
    ],
    attributes: [
      { id: color, name: "Color", requires_image: true, is_active: true },
      { id: size, name: "Size", requires_image: false, is_active: true }
    ],
    values: [
      { id: grey, attribute_id: color, name: "Grey", is_active: true },
      { id: blue, attribute_id: color, name: "Blue", is_active: true },
      { id: v40, attribute_id: size, name: "40", is_active: true },
      { id: v41, attribute_id: size, name: "41", is_active: true }
    ],
    products: [
      {
        id: uid(), name: "Celsi Wool Felt Slippers", slug: "celsi-wool-felt-slippers",
        model_id: mod, gender: "UNISEX", description: "Warm wool felt slippers.",
        general_information: "Handmade in Nepal.", materials_used: "Wool felt, rubber sole.",
        category_id: cat, is_featured: true, is_active: true,
        key_features: [
          { title: "Upper Material", value: "Wool Felt" },
          { title: "Sole", value: "Rubber" }
        ],
        attribute_values: [
          { id: uid(), key: "grey", attribute_id: color, attribute_value_id: grey, is_active: true,
            feature_image: { url: "https://picsum.photos/seed/grey-main/400/300", title: "Grey", caption: "Grey wool felt slippers", alt: "Grey slippers" },
            additional_images: [
              { url: "https://picsum.photos/seed/grey-side/400/300", title: "Side view", caption: "", alt: "Side" }
            ] },
          { id: uid(), key: "blue", attribute_id: color, attribute_value_id: blue, is_active: true,
            feature_image: { url: "https://picsum.photos/seed/blue-main/400/300", title: "Blue", caption: "", alt: "Blue slippers" },
            additional_images: [] },
          { id: uid(), key: "40", attribute_id: size, attribute_value_id: v40, is_active: true, feature_image: null, additional_images: [] },
          { id: uid(), key: "41", attribute_id: size, attribute_value_id: v41, is_active: true, feature_image: null, additional_images: [] }
        ],
        variants: [
          { id: uid(), sku: "CELSI-GREY-40", price: "5995.00", currency_id: npr, is_special_edition: false, is_active: true, options: [{ key: "grey" }, { key: "40" }] },
          { id: uid(), sku: "CELSI-GREY-41", price: "5995.00", currency_id: npr, is_special_edition: false, is_active: true, options: [{ key: "grey" }, { key: "41" }] },
          { id: uid(), sku: "CELSI-BLUE-40", price: "6495.00", currency_id: npr, is_special_edition: true, is_active: true, options: [{ key: "blue" }, { key: "40" }] }
        ]
      }
    ]
  };
}

/* ============================== db ============================== */
var DB = null;
function saveDB() {
  store.set(LS_KEY, JSON.stringify(DB));
  updateStorageBadge();
}
function loadDB() {
  try {
    var raw = store.get(LS_KEY);
    if (raw) { DB = JSON.parse(raw); updateStorageBadge(); return; }
  } catch (e) { /* corrupted -> reseed */ }
  DB = seed();
  saveDB();
}
function updateStorageBadge() {
  var pill = document.getElementById("storagePill");
  var txt = document.getElementById("storageText");
  if (!pill || !txt) return;
  if (storageOK) {
    pill.classList.remove("warn");
    txt.textContent = "localStorage saved " + new Date().toLocaleTimeString();
  } else {
    pill.classList.add("warn");
    txt.textContent = "memory only (storage blocked)";
  }
}
function byId(col, id) {
  if (!id) return null;
  for (var i = 0; i < DB[col].length; i++) if (DB[col][i].id === id) return DB[col][i];
  return null;
}
function valuesOf(attrId) { return DB.values.filter(function (v) { return v.attribute_id === attrId; }); }
function uniqueSlug(col, base, ignoreId) {
  var slug = slugify(base) || "item", n = 2, out = slug;
  var taken = function (s) { return DB[col].some(function (r) { return r.slug === s && r.id !== ignoreId; }); };
  while (taken(out)) { out = slug + "-" + (n++); }
  return out;
}
/* usage guards (mirror PROTECT relations) */
function productsUsingCategory(id) { return DB.products.filter(function (p) { return p.category_id === id; }); }
function productsUsingModel(id) { return DB.products.filter(function (p) { return p.model_id === id; }); }
function pavsUsingValue(id) {
  var n = 0;
  DB.products.forEach(function (p) { p.attribute_values.forEach(function (r) { if (r.attribute_value_id === id) n++; }); });
  return n;
}
function pavsUsingAttribute(id) {
  var n = 0;
  DB.products.forEach(function (p) { p.attribute_values.forEach(function (r) { if (r.attribute_id === id) n++; }); });
  return n;
}
function variantsUsingCurrency(id) {
  var n = 0;
  DB.products.forEach(function (p) { p.variants.forEach(function (v) { if (v.currency_id === id) n++; }); });
  return n;
}

/* ============================== shared bits ============================== */
var GENDERS = ["MEN", "WOMEN", "UNISEX", "KIDS", "BABY"];
function pill(on, onText, offText) {
  return '<span class="pill ' + (on ? "on" : "off") + '">' + esc(on ? onText || "Active" : offText || "Inactive") + "</span>";
}
function thumbHTML(url) {
  if (url) return '<img class="thumb" src="' + esc(url) + '" alt="" loading="lazy">';
  return '<span class="noimg">' + ICONS.image + "</span>";
}
function imgInputBlock(prefix, img, pvId) {
  img = img || blankImage();
  return '<div class="form-grid">' +
    '<div class="field full"><label>Image URL</label>' +
      '<div style="display:flex;gap:10px;align-items:center">' +
        '<img id="' + pvId + '" class="thumb" src="' + esc(img.url) + '" alt="" style="' + (img.url ? "" : "display:none") + '">' +
        '<input type="url" id="' + prefix + '_url" data-preview-for="' + pvId + '" value="' + esc(img.url) + '" placeholder="https://...">' +
      "</div>" +
      '<div class="hint">Paste an image URL — the same reference style the API accepts.</div></div>' +
    '<div class="field"><label>Title</label><input type="text" id="' + prefix + '_title" value="' + esc(img.title) + '"></div>' +
    '<div class="field"><label>Alt text</label><input type="text" id="' + prefix + '_alt" value="' + esc(img.alt) + '"></div>' +
    '<div class="field full"><label>Caption</label><input type="text" id="' + prefix + '_caption" value="' + esc(img.caption) + '"></div>' +
  "</div>";
}
function readImgInput(prefix) {
  var g = function (s) { var el = document.getElementById(prefix + s); return el ? el.value.trim() : ""; };
  var img = { url: g("_url"), title: g("_title"), caption: g("_caption"), alt: g("_alt") };
  return (img.url || img.title || img.caption || img.alt) ? img : null;
}
function sectionHead(step, title, desc, btnAction, btnLabel) {
  return '<div class="section-head"><div><div class="step-tag">Step ' + step + " of 6</div>" +
    "<h2>" + esc(title) + "</h2><p>" + esc(desc) + "</p></div>" +
    '<div><button class="btn btn-dark" data-action="' + btnAction + '">' + ICONS.plus + esc(btnLabel) + "</button></div></div>";
}
function emptyState(title, desc, btnAction, btnLabel) {
  return '<div class="table-wrap"><div class="empty"><div class="big">' + esc(title) + "</div>" +
    '<div style="margin-bottom:14px">' + esc(desc) + "</div>" +
    '<button class="btn btn-dark" data-action="' + btnAction + '">' + ICONS.plus + esc(btnLabel) + "</button></div></div>";
}

/* ============================== router ============================== */
var ROUTES = {
  dashboard: { title: "Dashboard", render: renderDashboard },
  currencies: { title: "Currencies", render: renderCurrencies },
  categories: { title: "Categories", render: renderCategories },
  models: { title: "Product Models", render: renderModels },
  attributes: { title: "Attributes", render: renderAttributes },
  values: { title: "Attribute Values", render: renderValues },
  products: { title: "Products", render: renderProducts }
};
var currentRoute = "dashboard";
function navigate(route) {
  if (route !== "products") productMode = "list";
  if (("#/" + route) === location.hash) syncFromHash();
  else location.hash = "#/" + route;
}
function syncFromHash() {
  var h = (location.hash || "").replace(/^#\//, "");
  currentRoute = ROUTES[h] ? h : "dashboard";
  var btns = document.querySelectorAll(".nav-item");
  for (var i = 0; i < btns.length; i++) btns[i].classList.toggle("active", btns[i].getAttribute("data-route") === currentRoute);
  document.getElementById("pageTitle").textContent = ROUTES[currentRoute].title;
  renderTopActions();
  document.getElementById("content").innerHTML = ROUTES[currentRoute].render();
  window.scrollTo(0, 0);
}
function renderTopActions() {
  var el = document.getElementById("topbarActions");
  if (currentRoute === "products" && productMode === "edit") {
    el.innerHTML = '<button class="btn" data-action="product-back">' + ICONS.back + "Back to list</button>";
  } else { el.innerHTML = ""; }
}

/* ============================== dashboard ============================== */
var FLOW = [
  { route: "currencies", name: "Currencies", col: "currencies", unit: "currencies", desc: "Money variants are priced in" },
  { route: "categories", name: "Categories", col: "categories", unit: "categories", desc: "Shelves products live on" },
  { route: "models", name: "Models", col: "models", unit: "models", desc: "Product lines (Celsi…)" },
  { route: "attributes", name: "Attributes", col: "attributes", unit: "attributes", desc: "Color, Size… (+ image rule)" },
  { route: "values", name: "Values", col: "values", unit: "values", desc: "Grey, Blue, 40, 41…" },
  { route: "products", name: "Products", col: "products", unit: "products", desc: "Ties everything together" }
];
function renderDashboard() {
  var steps = FLOW.map(function (s, i) {
    var arrow = i < FLOW.length - 1 ? '<div class="flow-arrow">→</div>' : "";
    return '<div class="flow-step" data-action="goto" data-id="' + s.route + '">' +
      '<div class="num">' + (i + 1) + '</div><div class="name">' + esc(s.name) + "</div>" +
      '<div class="count">' + DB[s.col].length + " " + s.unit + "</div>" +
      '<div class="go">' + esc(s.desc) + "</div></div>" + arrow;
  }).join("");
  var recent = DB.products.slice(0, 3).map(function (p) {
    var c = byId("categories", p.category_id);
    return "<tr><td><strong>" + esc(p.name) + "</strong><div class='small muted'>" + esc(p.slug) + "</div></td>" +
      "<td>" + esc(c ? c.name : "—") + "</td><td>" + p.attribute_values.length + "</td><td>" + p.variants.length + "</td>" +
      "<td>" + pill(p.is_active) + "</td></tr>";
  }).join("");
  return '<div class="card"><h2>Data flow</h2><p class="muted small" style="margin:0 0 14px">Add data in this order — each step feeds the next. Click any step to manage it.</p>' +
      '<div class="flow">' + steps + "</div></div>" +
    '<div class="stats">' +
      stat(DB.products.length, "Products") + stat(DB.categories.length, "Categories") +
      stat(DB.values.length, "Attribute values") + stat(DB.currencies.length, "Currencies") +
    "</div>" +
    '<div class="card"><h2>How to add data in the flow</h2><ol class="guide">' +
      "<li><span class='gnum'>1</span><span><strong>Currencies</strong> — add the money used on prices (e.g. NPR). Variants cannot be priced without one.</span></li>" +
      "<li><span class='gnum'>2</span><span><strong>Categories</strong> — add shelves like Slippers, each with an optional image.</span></li>" +
      "<li><span class='gnum'>3</span><span><strong>Product models</strong> — add lines like Celsi; the model name seeds auto SKUs.</span></li>" +
      "<li><span class='gnum'>4</span><span><strong>Attributes</strong> — add facets like Color or Size. Turn on <strong>Requires image</strong> when every value must carry a picture (e.g. Color).</span></li>" +
      "<li><span class='gnum'>5</span><span><strong>Attribute values</strong> — add Grey / Blue under Color, 40 / 41 under Size.</span></li>" +
      "<li><span class='gnum'>6</span><span><strong>Products</strong> — pick a category + model, attach values (with images where required), then add variants priced in a currency. Watch the live <strong>API payload</strong> preview to see exactly what the backend receives.</span></li>" +
    "</ol></div>" +
    '<div class="card"><h2>Recent products</h2>' +
      (DB.products.length
        ? '<div class="table-wrap" style="box-shadow:none"><table class="grid"><thead><tr><th>Product</th><th>Category</th><th>Values</th><th>Variants</th><th>Status</th></tr></thead><tbody>' + recent + "</tbody></table></div>"
        : '<p class="muted">No products yet — follow the flow above, then add your first product.</p>') +
    "</div>";
}
function stat(v, l) { return '<div class="stat"><div class="v">' + v + '</div><div class="l">' + esc(l) + "</div></div>"; }

/* ============================== currencies ============================== */
function renderCurrencies() {
  var h = sectionHead(1, "Currencies", "Money that variant prices are quoted in. Add at least one before creating variants.", "add-currency", "Add currency");
  if (!DB.currencies.length) return h + emptyState("No currencies", "Add your first currency to start the flow.", "add-currency", "Add currency");
  var rows = DB.currencies.map(function (c) {
    return "<tr><td><strong>" + esc(c.code) + "</strong></td><td>" + esc(c.name) + "</td><td>" + esc(c.symbol) + "</td>" +
      "<td>" + pill(c.is_active) + "</td>" + rowActions("currency", c.id) + "</tr>";
  }).join("");
  return h + '<div class="table-wrap"><table class="grid"><thead><tr><th>Code</th><th>Name</th><th>Symbol</th><th>Status</th><th></th></tr></thead><tbody>' + rows + "</tbody></table></div>";
}
function rowActions(kind, id) {
  return '<td class="row-actions"><button class="icon-btn" data-action="edit-' + kind + '" data-id="' + id + '" title="Edit">' + ICONS.pencil + "</button>" +
    '<button class="icon-btn danger" data-action="del-' + kind + '" data-id="' + id + '" title="Delete">' + ICONS.trash + "</button></td>";
}
function currencyForm(c) {
  c = c || { code: "", name: "", symbol: "", is_active: true };
  openModal(modalShell(c.id ? "Edit currency" : "Add currency",
    '<div class="form-error" id="formError"></div><div class="form-grid">' +
    '<div class="field"><label>Code</label><input type="text" id="f_code" value="' + esc(c.code) + '" placeholder="NPR"></div>' +
    '<div class="field"><label>Symbol</label><input type="text" id="f_symbol" value="' + esc(c.symbol) + '" placeholder="Rs."></div>' +
    '<div class="field full"><label>Name</label><input type="text" id="f_name" value="' + esc(c.name) + '" placeholder="Nepalese Rupee"></div>' +
    '<div class="field full"><label class="check-row"><input type="checkbox" id="f_active" ' + (c.is_active ? "checked" : "") + "> Active</label></div>" +
    "</div>",
    '<button class="btn" data-close>Cancel</button><button class="btn btn-dark" data-action="save-currency" data-id="' + (c.id || "") + '">Save currency</button>'));
}
function saveCurrency(id) {
  var code = val("f_code").toUpperCase(), name = val("f_name"), symbol = val("f_symbol");
  var active = document.getElementById("f_active").checked;
  if (!code) return fieldError("Code is required (e.g. NPR).");
  if (!name) return fieldError("Name is required.");
  if (DB.currencies.some(function (c) { return c.code === code && c.id !== id; })) return fieldError("Code '" + code + "' already exists.");
  if (id) { var c = byId("currencies", id); c.code = code; c.name = name; c.symbol = symbol; c.is_active = active; }
  else DB.currencies.unshift({ id: uid(), code: code, name: name, symbol: symbol, is_active: active });
  saveDB(); closeModal(); syncFromHash(); toast("Currency saved.");
}
function val(id) { var el = document.getElementById(id); return el ? el.value.trim() : ""; }

/* ============================== categories ============================== */
function renderCategories() {
  var h = sectionHead(2, "Categories", "Shelves that products live on. Each category can carry one image.", "add-category", "Add category");
  if (!DB.categories.length) return h + emptyState("No categories", "Add your first category to continue the flow.", "add-category", "Add category");
  var rows = DB.categories.map(function (c) {
    return "<tr><td>" + thumbHTML(c.image && c.image.url) + "</td>" +
      "<td><strong>" + esc(c.name) + "</strong><div class='small muted'>" + esc(c.slug) + "</div></td>" +
      "<td class='muted'>" + esc((c.description || "").slice(0, 80)) + "</td>" +
      "<td>" + pill(c.is_active) + "</td>" + rowActions("category", c.id) + "</tr>";
  }).join("");
  return h + '<div class="table-wrap"><table class="grid"><thead><tr><th></th><th>Name</th><th>Description</th><th>Status</th><th></th></tr></thead><tbody>' + rows + "</tbody></table></div>";
}
function categoryForm(c) {
  c = c || { name: "", slug: "", description: "", is_active: true, image: null };
  openModal(modalShell(c.id ? "Edit category" : "Add category",
    '<div class="form-error" id="formError"></div><div class="form-grid">' +
    '<div class="field"><label>Name</label><input type="text" id="f_name" value="' + esc(c.name) + '" placeholder="Slippers"></div>' +
    '<div class="field"><label>Slug (blank = auto)</label><input type="text" id="f_slug" value="' + esc(c.slug) + '" placeholder="slippers"></div>' +
    '<div class="field full"><label>Description</label><textarea id="f_desc" placeholder="Comfy everyday slippers.">' + esc(c.description || "") + "</textarea></div>" +
    '<div class="field full"><label class="check-row"><input type="checkbox" id="f_active" ' + (c.is_active ? "checked" : "") + "> Active</label></div>" +
    '<div class="field full"><label style="margin-bottom:8px">Image</label>' + imgInputBlock("f_img", c.image, "pv_cat") + "</div>" +
    "</div>",
    '<button class="btn" data-close>Cancel</button><button class="btn btn-dark" data-action="save-category" data-id="' + (c.id || "") + '">Save category</button>'));
}
function saveCategory(id) {
  var name = val("f_name"), slug = val("f_slug") || slugify(name);
  var desc = val("f_desc"), active = document.getElementById("f_active").checked;
  if (!name) return fieldError("Name is required.");
  if (DB.categories.some(function (c) { return c.name.toLowerCase() === name.toLowerCase() && c.id !== id; })) return fieldError("A category named '" + name + "' already exists.");
  slug = uniqueSlug("categories", slug, id);
  var image = readImgInput("f_img");
  if (id) { var c = byId("categories", id); c.name = name; c.slug = slug; c.description = desc; c.is_active = active; c.image = image; }
  else DB.categories.unshift({ id: uid(), name: name, slug: slug, description: desc, is_active: active, image: image });
  saveDB(); closeModal(); syncFromHash(); toast("Category saved.");
}

/* ============================== models ============================== */
function renderModels() {
  var h = sectionHead(3, "Product models", "Product lines such as Celsi. The model name seeds auto-generated SKUs.", "add-model", "Add model");
  if (!DB.models.length) return h + emptyState("No product models", "Add your first model to continue the flow.", "add-model", "Add model");
  var rows = DB.models.map(function (m) {
    return "<tr><td><strong>" + esc(m.name) + "</strong><div class='small muted'>" + esc(m.slug) + "</div></td>" +
      "<td class='muted'>" + esc((m.description || "").slice(0, 80)) + "</td>" +
      "<td>" + pill(m.is_active) + "</td>" + rowActions("model", m.id) + "</tr>";
  }).join("");
  return h + '<div class="table-wrap"><table class="grid"><thead><tr><th>Name</th><th>Description</th><th>Status</th><th></th></tr></thead><tbody>' + rows + "</tbody></table></div>";
}
function modelForm(m) {
  m = m || { name: "", slug: "", description: "", is_active: true };
  openModal(modalShell(m.id ? "Edit product model" : "Add product model",
    '<div class="form-error" id="formError"></div><div class="form-grid">' +
    '<div class="field"><label>Name</label><input type="text" id="f_name" value="' + esc(m.name) + '" placeholder="Celsi"></div>' +
    '<div class="field"><label>Slug (blank = auto)</label><input type="text" id="f_slug" value="' + esc(m.slug) + '" placeholder="celsi"></div>' +
    '<div class="field full"><label>Description</label><textarea id="f_desc" placeholder="Wool felt slipper line.">' + esc(m.description || "") + "</textarea></div>" +
    '<div class="field full"><label class="check-row"><input type="checkbox" id="f_active" ' + (m.is_active ? "checked" : "") + "> Active</label></div>" +
    "</div>",
    '<button class="btn" data-close>Cancel</button><button class="btn btn-dark" data-action="save-model" data-id="' + (m.id || "") + '">Save model</button>'));
}
function saveModel(id) {
  var name = val("f_name"), slug = val("f_slug") || slugify(name);
  var desc = val("f_desc"), active = document.getElementById("f_active").checked;
  if (!name) return fieldError("Name is required.");
  if (DB.models.some(function (m) { return m.name.toLowerCase() === name.toLowerCase() && m.id !== id; })) return fieldError("A model named '" + name + "' already exists.");
  slug = uniqueSlug("models", slug, id);
  if (id) { var m = byId("models", id); m.name = name; m.slug = slug; m.description = desc; m.is_active = active; }
  else DB.models.unshift({ id: uid(), name: name, slug: slug, description: desc, is_active: active });
  saveDB(); closeModal(); syncFromHash(); toast("Product model saved.");
}

/* ============================== attributes ============================== */
function renderAttributes() {
  var h = sectionHead(4, "Attributes", "Facets like Color or Size. 'Requires image' forces every active value of that attribute to carry a feature image.", "add-attribute", "Add attribute");
  if (!DB.attributes.length) return h + emptyState("No attributes", "Add your first attribute to continue the flow.", "add-attribute", "Add attribute");
  var rows = DB.attributes.map(function (a) {
    return "<tr><td><strong>" + esc(a.name) + "</strong></td>" +
      "<td>" + (a.requires_image ? '<span class="pill warn">Requires image</span>' : '<span class="pill">No image rule</span>') + "</td>" +
      "<td>" + valuesOf(a.id).length + " values</td>" +
      "<td>" + pill(a.is_active) + "</td>" + rowActions("attribute", a.id) + "</tr>";
  }).join("");
  return h + '<div class="table-wrap"><table class="grid"><thead><tr><th>Name</th><th>Image rule</th><th>Values</th><th>Status</th><th></th></tr></thead><tbody>' + rows + "</tbody></table></div>";
}
function attributeForm(a) {
  a = a || { name: "", requires_image: false, is_active: true };
  openModal(modalShell(a.id ? "Edit attribute" : "Add attribute",
    '<div class="form-error" id="formError"></div><div class="form-grid">' +
    '<div class="field full"><label>Name</label><input type="text" id="f_name" value="' + esc(a.name) + '" placeholder="Color"></div>' +
    '<div class="field full"><label class="check-row"><input type="checkbox" id="f_req" ' + (a.requires_image ? "checked" : "") + "> Requires image</label>" +
    '<div class="hint">When on, every active product value of this attribute must have a feature image.</div></div>' +
    '<div class="field full"><label class="check-row"><input type="checkbox" id="f_active" ' + (a.is_active ? "checked" : "") + "> Active</label></div>" +
    "</div>",
    '<button class="btn" data-close>Cancel</button><button class="btn btn-dark" data-action="save-attribute" data-id="' + (a.id || "") + '">Save attribute</button>'));
}
function saveAttribute(id) {
  var name = val("f_name");
  var req = document.getElementById("f_req").checked, active = document.getElementById("f_active").checked;
  if (!name) return fieldError("Name is required.");
  if (DB.attributes.some(function (a) { return a.name.toLowerCase() === name.toLowerCase() && a.id !== id; })) return fieldError("An attribute named '" + name + "' already exists.");
  if (id) { var a = byId("attributes", id); a.name = name; a.requires_image = req; a.is_active = active; }
  else DB.attributes.unshift({ id: uid(), name: name, requires_image: req, is_active: active });
  saveDB(); closeModal(); syncFromHash(); toast("Attribute saved.");
}

/* ============================== attribute values ============================== */
var valueFilter = "";
function renderValues() {
  var h = sectionHead(5, "Attribute values", "Concrete options under an attribute — Grey / Blue under Color, 40 / 41 under Size.", "add-value", "Add value");
  if (!DB.attributes.length) return h + emptyState("Add an attribute first", "Values belong to an attribute — create one before adding values.", "goto-attributes", "Go to attributes");
  var opts = '<option value="">All attributes</option>' + DB.attributes.map(function (a) {
    return '<option value="' + a.id + '"' + (valueFilter === a.id ? " selected" : "") + ">" + esc(a.name) + "</option>";
  }).join("");
  var list = DB.values.filter(function (v) { return !valueFilter || v.attribute_id === valueFilter; });
  var body = list.length ? '<div class="table-wrap"><table class="grid"><thead><tr><th>Value</th><th>Attribute</th><th>Status</th><th></th></tr></thead><tbody>' +
    list.map(function (v) {
      var a = byId("attributes", v.attribute_id);
      return "<tr><td><strong>" + esc(v.name) + "</strong></td><td>" + esc(a ? a.name : "—") +
        (a && a.requires_image ? ' <span class="pill warn">needs image</span>' : "") + "</td>" +
        "<td>" + pill(v.is_active) + "</td>" + rowActions("value", v.id) + "</tr>";
    }).join("") + "</tbody></table></div>"
    : emptyState("No values found", "Add values under any attribute.", "add-value", "Add value");
  return h + '<div class="card" style="padding:12px 16px"><div class="field" style="max-width:280px"><label>Filter by attribute</label><select id="valueFilter">' + opts + "</select></div></div>" + body;
}
function valueForm(v) {
  v = v || { attribute_id: valueFilter || (DB.attributes[0] && DB.attributes[0].id) || "", name: "", is_active: true };
  var opts = DB.attributes.map(function (a) {
    return '<option value="' + a.id + '"' + (v.attribute_id === a.id ? " selected" : "") + ">" + esc(a.name) + (a.requires_image ? " (needs image)" : "") + "</option>";
  }).join("");
  openModal(modalShell(v.id ? "Edit value" : "Add value",
    '<div class="form-error" id="formError"></div><div class="form-grid">' +
    '<div class="field"><label>Attribute</label><select id="f_attr">' + opts + "</select></div>" +
    '<div class="field"><label>Value name</label><input type="text" id="f_name" value="' + esc(v.name) + '" placeholder="Grey"></div>' +
    '<div class="field full"><label class="check-row"><input type="checkbox" id="f_active" ' + (v.is_active ? "checked" : "") + "> Active</label></div>" +
    "</div>",
    '<button class="btn" data-close>Cancel</button><button class="btn btn-dark" data-action="save-value" data-id="' + (v.id || "") + '">Save value</button>'));
}
function saveValue(id) {
  var attrId = val("f_attr"), name = val("f_name");
  var active = document.getElementById("f_active").checked;
  if (!attrId) return fieldError("Pick an attribute.");
  if (!name) return fieldError("Value name is required.");
  if (DB.values.some(function (v) { return v.attribute_id === attrId && v.name.toLowerCase() === name.toLowerCase() && v.id !== id; }))
    return fieldError("'" + name + "' already exists under this attribute.");
  if (id) { var v = byId("values", id); v.attribute_id = attrId; v.name = name; v.is_active = active; }
  else DB.values.unshift({ id: uid(), attribute_id: attrId, name: name, is_active: active });
  saveDB(); closeModal(); syncFromHash(); toast("Value saved.");
}

/* ============================== products ============================== */
var productMode = "list"; /* list | edit */
var editor = null;
var slugTouched = false;

function renderProducts() {
  if (productMode === "edit" && editor) return renderEditor();
  var h = sectionHead(6, "Products", "The final step: pick a category + model, attach attribute values (with images where required), then price variants in a currency.", "add-product", "Add product");
  if (!DB.products.length) return h + emptyState("No products yet", "Make sure currencies, a category, a model, attributes and values exist — then add your first product.", "add-product", "Add product");
  var rows = DB.products.map(function (p) {
    var c = byId("categories", p.category_id);
    var img = firstProductImage(p);
    return "<tr><td>" + thumbHTML(img) + "</td>" +
      "<td><strong>" + esc(p.name) + "</strong><div class='small muted'>" + esc(p.slug) + "</div></td>" +
      "<td>" + esc(c ? c.name : "—") + "</td><td>" + p.attribute_values.length + "</td><td>" + p.variants.length + "</td>" +
      "<td>" + (p.is_featured ? '<span class="pill warn">Featured</span> ' : "") + pill(p.is_active) + "</td>" +
      '<td class="row-actions">' +
        '<button class="icon-btn" data-action="view-product" data-id="' + p.id + '" title="View">' + ICONS.eye + "</button>" +
        '<button class="icon-btn" data-action="json-product" data-id="' + p.id + '" title="API payload">' + ICONS.code + "</button>" +
        '<button class="icon-btn" data-action="edit-product" data-id="' + p.id + '" title="Edit">' + ICONS.pencil + "</button>" +
        '<button class="icon-btn danger" data-action="del-product" data-id="' + p.id + '" title="Delete">' + ICONS.trash + "</button></td></tr>";
  }).join("");
  return h + '<div class="table-wrap"><table class="grid"><thead><tr><th></th><th>Product</th><th>Category</th><th>Values</th><th>Variants</th><th>Status</th><th></th></tr></thead><tbody>' + rows + "</tbody></table></div>";
}
function firstProductImage(p) {
  for (var i = 0; i < p.attribute_values.length; i++) {
    var f = p.attribute_values[i].feature_image;
    if (f && f.url) return f.url;
  }
  return "";
}
function blankProduct() {
  return { id: null, name: "", slug: "", model_id: "", gender: "UNISEX", description: "",
    general_information: "", materials_used: "", category_id: "", is_featured: false,
    is_active: true, key_features: [], attribute_values: [], variants: [] };
}
function openEditor(id) {
  var p = id ? byId("products", id) : null;
  editor = { id: id || null, draft: p ? deep(p) : blankProduct() };
  slugTouched = !!id;
  productMode = "edit";
  renderTopActions();
  document.getElementById("content").innerHTML = renderEditor();
  refreshJsonPreview();
  window.scrollTo(0, 0);
}
function closeEditor() {
  editor = null; productMode = "list"; renderTopActions();
  document.getElementById("content").innerHTML = renderProducts();
  window.scrollTo(0, 0);
}

/* ---------- editor render ---------- */
function optList(list, valId, labelFn) {
  return list.map(function (r) {
    return '<option value="' + r.id + '"' + (valId === r.id ? " selected" : "") + ">" + esc(labelFn(r)) + "</option>";
  }).join("");
}
function renderEditor() {
  var d = editor.draft;
  var prereq = [];
  if (!DB.currencies.length) prereq.push("currencies");
  if (!DB.categories.length) prereq.push("categories");
  if (!DB.models.length) prereq.push("models");
  if (!DB.attributes.length) prereq.push("attributes");
  if (!DB.values.length) prereq.push("values");
  var warn = prereq.length
    ? '<div class="card" style="border-color:#f0dfb8;background:#fffdf6"><strong>Missing data for the flow:</strong> <span class="muted">add ' + prereq.join(", ") + " first (see Dashboard), otherwise some dropdowns below will be empty.</span></div>"
    : "";
  return '<div class="section-head"><div><div class="step-tag">Step 6 of 6 — ' + (editor.id ? "edit" : "create") + '</div>' +
    "<h2>" + (editor.id ? "Edit product" : "Add product") + "</h2><p>Fill the form — the live panel shows the exact API payload this data produces.</p></div></div>" +
    warn + '<div class="form-error" id="editorError"></div>' +
    '<div class="editor-grid"><div>' +
      '<div class="sub-block"><div class="sub-head"><h3>Basics</h3></div><div class="sub-body"><div class="form-grid">' +
        '<div class="field"><label>Name</label><input type="text" data-draft="name" value="' + esc(d.name) + '" placeholder="Celsi Wool Felt Slippers"></div>' +
        '<div class="field"><label>Slug (auto)</label><input type="text" data-draft="slug" id="edSlug" value="' + esc(d.slug) + '" placeholder="auto from name"></div>' +
        '<div class="field"><label>Model</label><select data-draft="model_id"><option value="">— Select —</option>' + optList(DB.models, d.model_id, function (m) { return m.name; }) + "</select></div>" +
        '<div class="field"><label>Category</label><select data-draft="category_id"><option value="">— Select —</option>' + optList(DB.categories, d.category_id, function (c) { return c.name; }) + "</select></div>" +
        '<div class="field"><label>Gender</label><select data-draft="gender">' + GENDERS.map(function (g) { return '<option' + (d.gender === g ? " selected" : "") + ">" + g + "</option>"; }).join("") + "</select></div>" +
        '<div class="field"><label>Flags</label><div style="display:flex;gap:16px;padding-top:8px">' +
          '<label class="check-row"><input type="checkbox" data-draft="is_featured" ' + (d.is_featured ? "checked" : "") + "> Featured</label>" +
          '<label class="check-row"><input type="checkbox" data-draft="is_active" ' + (d.is_active ? "checked" : "") + "> Active</label></div></div>" +
        '<div class="field full"><label>Description</label><textarea data-draft="description" placeholder="Warm wool felt slippers.">' + esc(d.description) + "</textarea></div>" +
        '<div class="field"><label>General information</label><input type="text" data-draft="general_information" value="' + esc(d.general_information) + '" placeholder="Handmade in Nepal."></div>' +
        '<div class="field"><label>Materials used</label><input type="text" data-draft="materials_used" value="' + esc(d.materials_used) + '" placeholder="Wool felt, rubber sole."></div>' +
      "</div></div></div>" +
      '<div class="sub-block"><div class="sub-head"><h3>Key features</h3><button class="btn btn-sm" data-action="ed-add-kf">' + ICONS.plus + "Add</button></div>" +
        '<div class="sub-body" id="kfRows">' + kfRowsHTML() + "</div></div>" +
      '<div class="sub-block"><div class="sub-head"><h3>Attribute values</h3><button class="btn btn-sm" data-action="ed-add-value">' + ICONS.plus + "Add value</button></div>" +
        '<div class="sub-body" id="vRows">' + valueRowsHTML() + "</div></div>" +
      '<div class="sub-block"><div class="sub-head"><h3>Variants</h3><button class="btn btn-sm" data-action="ed-add-variant">' + ICONS.plus + "Add variant</button></div>" +
        '<div class="sub-body" id="varRows">' + variantRowsHTML() + "</div></div>" +
      '<div style="display:flex;gap:10px;margin:6px 0 20px"><button class="btn btn-dark" data-action="ed-save">Save product</button>' +
        '<button class="btn" data-action="product-back">Cancel</button></div>' +
    "</div>" +
    '<div class="json-pane"><div class="sub-block"><div class="sub-head"><h3>Live API payload</h3><button class="btn btn-sm" data-action="ed-copy">Copy</button></div>' +
      '<div class="sub-body"><div id="jsonIssues"></div><pre class="code" id="jsonPre">{}</pre>' +
      '<div class="hint">This is the body the dashboard would POST to <span style="font-family:var(--mono)">/api/v1/admin/products/</span>. Image slots accept a URL object, a stored name, or a file upload.</div></div></div></div>' +
    "</div>";
}
function kfRowsHTML() {
  var d = editor.draft;
  if (!d.key_features.length) return '<p class="muted small" style="margin:0">No key features yet — e.g. Sole / Rubber.</p>';
  return d.key_features.map(function (k, i) {
    return '<div class="kv-row"><input type="text" data-kf="' + i + '" data-kf-f="title" value="' + esc(k.title) + '" placeholder="Title">' +
      '<input type="text" data-kf="' + i + '" data-kf-f="value" value="' + esc(k.value) + '" placeholder="Value">' +
      '<button class="icon-btn danger" data-action="ed-del-kf" data-id="' + i + '">' + ICONS.trash + "</button></div>";
  }).join("");
}
function valueRowsHTML() {
  var d = editor.draft;
  if (!d.attribute_values.length) return '<p class="muted small" style="margin:0">No values yet — attach Grey / 40 style options with images.</p>';
  return d.attribute_values.map(function (r, i) {
    var a = byId("attributes", r.attribute_id);
    var vals = r.attribute_id ? valuesOf(r.attribute_id) : [];
    var needImg = a && a.requires_image && r.is_active !== false && !((r.feature_image || {}).url || "");
    var addImgs = (r.additional_images || []).map(function (im, j) {
      return '<div class="mini-row"><input type="url" data-va="' + i + ":" + j + '" data-va-f="url" value="' + esc(im.url) + '" placeholder="Additional image URL">' +
        '<button class="icon-btn danger" data-action="ed-del-addimg" data-id="' + i + ":" + j + '">' + ICONS.trash + "</button></div>";
    }).join("");
    var f = r.feature_image || blankImage();
    return '<div class="nested-card"><div class="nested-title"><span>Value ' + (i + 1) + (a ? " — " + esc(a.name) : "") + '</span>' +
      '<button class="icon-btn danger" data-action="ed-del-value" data-id="' + i + '">' + ICONS.trash + "</button></div>" +
      '<div class="form-grid">' +
        '<div class="field"><label>Temp key</label><input type="text" data-vf="' + i + '" data-vfield="key" value="' + esc(r.key || "") + '" placeholder="grey"></div>' +
        '<div class="field"><label>Active</label><div style="padding-top:8px"><label class="check-row"><input type="checkbox" data-vf="' + i + '" data-vfield="is_active" ' + (r.is_active !== false ? "checked" : "") + "> Active</label></div></div>" +
        '<div class="field"><label>Attribute</label><select data-vattr="' + i + '"><option value="">— Select —</option>' +
          optList(DB.attributes, r.attribute_id, function (x) { return x.name + (x.requires_image ? " (needs image)" : ""); }) + "</select></div>" +
        '<div class="field"><label>Value</label><select data-vf="' + i + '" data-vfield="attribute_value_id"><option value="">— Select —</option>' +
          optList(vals, r.attribute_value_id, function (x) { return x.name; }) + "</select></div>" +
        '<div class="field"><label>Feature image URL</label><input type="url" data-vimg="' + i + '" data-vfield="url" value="' + esc(f.url) + '" placeholder="https://..."></div>' +
        '<div class="field"><label>Image title</label><input type="text" data-vimg="' + i + '" data-vfield="title" value="' + esc(f.title) + '" placeholder="Grey"></div>' +
        '<div class="field"><label>Image alt</label><input type="text" data-vimg="' + i + '" data-vfield="alt" value="' + esc(f.alt) + '" placeholder="Grey slippers"></div>' +
        '<div class="field"><label>Image caption</label><input type="text" data-vimg="' + i + '" data-vfield="caption" value="' + esc(f.caption) + '" placeholder=""></div>' +
      "</div>" +
      (needImg ? '<div class="req-note">This attribute requires an image — add a feature image URL.</div>' : "") +
      '<div style="margin-top:10px"><label class="small muted" style="font-weight:700">Additional images</label>' + addImgs +
      '<button class="btn btn-sm" data-action="ed-add-addimg" data-id="' + i + '">' + ICONS.plus + "Add image</button></div>" +
    "</div>";
  }).join("");
}
function variantRowsHTML() {
  var d = editor.draft;
  if (!d.variants.length) return '<p class="muted small" style="margin:0">No variants yet — combine value keys (grey + 40) into priced SKUs.</p>';
  var keyed = d.attribute_values.filter(function (r) { return (r.key || "").trim(); });
  return d.variants.map(function (v, j) {
    var preview = autoSku(d, v);
    var opts = keyed.length ? keyed.map(function (r) {
      var on = (v.options || []).some(function (o) { return o.key === r.key; });
      var vn = valueName(r.attribute_value_id);
      return '<label class="opt' + (on ? " picked" : "") + '"><input type="checkbox" data-opt="' + j + '" data-optkey="' + esc(r.key) + '"' + (on ? " checked" : "") + "> " + esc(r.key) + " · " + esc(vn) + "</label>";
    }).join("") : '<span class="muted small">Give the values above temp keys first.</span>';
    return '<div class="nested-card"><div class="nested-title"><span>Variant ' + (j + 1) + '</span>' +
      '<button class="icon-btn danger" data-action="ed-del-variant" data-id="' + j + '">' + ICONS.trash + "</button></div>" +
      '<div class="form-grid">' +
        '<div class="field"><label>SKU (blank = auto)</label><input type="text" data-varf="' + j + '" data-varfield="sku" value="' + esc(v.sku || "") + '" placeholder="' + esc(preview || "auto") + '">' +
          (preview && !v.sku ? '<div class="hint">Auto: ' + esc(preview) + "</div>" : "") + "</div>" +
        '<div class="field"><label>Price</label><input type="text" data-varf="' + j + '" data-varfield="price" value="' + esc(v.price || "") + '" placeholder="5995.00"></div>' +
        '<div class="field"><label>Currency</label><select data-varf="' + j + '" data-varfield="currency_id"><option value="">— Select —</option>' +
          optList(DB.currencies, v.currency_id, function (c) { return c.code + " — " + c.name; }) + "</select></div>" +
        '<div class="field"><label>Flags</label><div style="display:flex;gap:14px;padding-top:8px">' +
          '<label class="check-row"><input type="checkbox" data-varf="' + j + '" data-varfield="is_special_edition" ' + (v.is_special_edition ? "checked" : "") + "> Special</label>" +
          '<label class="check-row"><input type="checkbox" data-varf="' + j + '" data-varfield="is_active" ' + (v.is_active !== false ? "checked" : "") + "> Active</label></div></div>" +
        '<div class="field full"><label>Options (pick value keys)</label><div class="opt-list">' + opts + "</div></div>" +
      "</div></div>";
  }).join("");
}
function valueName(id) { var v = byId("values", id); return v ? v.name : "—"; }

/* ---------- payload / validation / sku ---------- */
function cleanImage(img) {
  if (!img) return null;
  var o = { url: (img.url || "").trim(), title: (img.title || "").trim(), caption: (img.caption || "").trim(), alt: (img.alt || "").trim() };
  return (o.url || o.title || o.caption || o.alt) ? o : null;
}
function productPayload(d) {
  return {
    name: d.name, slug: d.slug, model: d.model_id || null, gender: d.gender,
    description: d.description, general_information: d.general_information,
    materials_used: d.materials_used, category: d.category_id || null,
    is_featured: !!d.is_featured, is_active: d.is_active !== false,
    key_features: d.key_features.filter(function (k) { return k.title.trim() || k.value.trim(); }),
    attribute_values: d.attribute_values.map(function (r) {
      var o = { key: r.key, attribute: r.attribute_id || null, attribute_value: r.attribute_value_id || null,
        feature_image: cleanImage(r.feature_image),
        additional_images: (r.additional_images || []).map(cleanImage).filter(Boolean),
        is_active: r.is_active !== false };
      if (r.id) o.id = r.id;
      return o;
    }),
    variants: d.variants.map(function (v) {
      var o = { sku: v.sku || autoSku(d, v), price: v.price, currency: v.currency_id || null,
        is_special_edition: !!v.is_special_edition, is_active: v.is_active !== false,
        options: (v.options || []).map(function (o2) { return { key: o2.key }; }) };
      if (v.id) o.id = v.id;
      return o;
    })
  };
}
function autoSku(d, v) {
  var m = byId("models", d.model_id);
  var words = m ? m.name.split(/\s+/).filter(Boolean) : [];
  var prefix = words.length ? words.map(function (w) { return w[0]; }).join("").toUpperCase() : (m ? "PRD" : "");
  /* Match backend flavor: first word of model, uppercased. */
  if (m && words.length) prefix = words[0].replace(/[^a-z0-9]/gi, "").toUpperCase();
  var names = (v.options || []).map(function (o) {
    var row = d.attribute_values.filter(function (r) { return r.key === o.key; })[0];
    var val = row ? byId("values", row.attribute_value_id) : null;
    return val ? val.name.replace(/[^a-z0-9]/gi, "").toUpperCase() : "";
  }).filter(Boolean);
  if (!prefix || !names.length) return "";
  return prefix + "-" + names.join("-");
}
function validateProduct(d) {
  var issues = [];
  if (!d.name.trim()) issues.push("Name is required.");
  if (!d.category_id || !byId("categories", d.category_id)) issues.push("Pick a category.");
  if (!d.model_id || !byId("models", d.model_id)) issues.push("Pick a product model.");
  var seenKeys = {}, seenPairs = {};
  d.attribute_values.forEach(function (r, i) {
    var n = "Value " + (i + 1);
    if (!r.attribute_id) { issues.push(n + ": pick an attribute."); return; }
    if (!r.attribute_value_id) { issues.push(n + ": pick a value."); return; }
    var v = byId("values", r.attribute_value_id);
    if (!v || v.attribute_id !== r.attribute_id) { issues.push(n + ": value does not belong to the attribute."); return; }
    if (!r.key || !r.key.trim()) issues.push(n + ": give it a temp key (variants point at keys).");
    else if (seenKeys[r.key]) issues.push("Temp key '" + r.key + "' is used twice — keys must be unique.");
    else seenKeys[r.key] = true;
    var pair = r.attribute_id + "|" + r.attribute_value_id;
    if (seenPairs[pair]) issues.push(n + ": duplicate attribute/value pair in this product.");
    else seenPairs[pair] = true;
    var a = byId("attributes", r.attribute_id);
    if (a && a.requires_image && r.is_active !== false && !((r.feature_image || {}).url || "").trim())
      issues.push(n + " (" + v.name + "): '" + a.name + "' requires a feature image.");
  });
  var combos = {};
  d.variants.forEach(function (v, j) {
    var n = "Variant " + (j + 1);
    if (!(parseFloat(v.price) > 0)) issues.push(n + ": price must be greater than 0.");
    if (!v.currency_id || !byId("currencies", v.currency_id)) issues.push(n + ": pick a currency.");
    var opts = v.options || [];
    if (!opts.length) { issues.push(n + ": pick at least one option."); return; }
    var attrs = {};
    for (var k = 0; k < opts.length; k++) {
      var row = d.attribute_values.filter(function (r) { return r.key === opts[k].key; })[0];
      if (!row) { issues.push(n + ": option '" + opts[k].key + "' matches no value key."); continue; }
      if (attrs[row.attribute_id]) issues.push(n + ": only one value per attribute allowed.");
      attrs[row.attribute_id] = true;
    }
    var combo = opts.map(function (o) { return o.key; }).sort().join("+");
    if (combos[combo]) issues.push(n + ": duplicate option combination (" + combo + ").");
    else combos[combo] = true;
  });
  return issues;
}
function refreshJsonPreview() {
  if (!editor) return;
  var d = editor.draft;
  var pre = document.getElementById("jsonPre");
  var box = document.getElementById("jsonIssues");
  if (pre) pre.textContent = JSON.stringify(productPayload(d), null, 2);
  if (box) {
    var issues = validateProduct(d);
    box.innerHTML = issues.length
      ? '<div class="req-note" style="margin:0 0 10px">Fix before saving:<br>• ' + issues.map(esc).join("<br>• ") + "</div>"
      : '<div class="hint" style="margin:0 0 10px;color:var(--green);font-weight:600">Payload is valid — ready to save.</div>';
  }
}
function saveProduct() {
  var d = editor.draft;
  var box = document.getElementById("editorError");
  var issues = validateProduct(d);
  if (issues.length) {
    box.textContent = issues[0] + (issues.length > 1 ? " (+" + (issues.length - 1) + " more — see the live panel)" : "");
    box.classList.add("show");
    toast("Fix the highlighted issues first.", "err");
    return;
  }
  box.classList.remove("show");
  d.slug = uniqueSlug("products", d.slug || slugify(d.name), d.id);
  d.attribute_values.forEach(function (r) {
    if (!r.id) r.id = uid();
    r.feature_image = cleanImage(r.feature_image);
    r.additional_images = (r.additional_images || []).map(cleanImage).filter(Boolean);
  });
  var usedSkus = {};
  DB.products.forEach(function (p) {
    if (editor.id && p.id === editor.id) return; /* own SKUs stay untouched on edit */
    p.variants.forEach(function (v) { if (v.sku) usedSkus[v.sku] = true; });
  });
  d.variants.forEach(function (v) {
    if (!v.id) v.id = uid();
    var sku = (v.sku || "").trim() || autoSku(d, v) || "SKU";
    var base = sku, n = 2;
    while (usedSkus[sku]) sku = base + "-" + (n++);
    usedSkus[sku] = true;
    v.sku = sku;
  });
  if (editor.id) {
    var i = DB.products.findIndex(function (p) { return p.id === editor.id; });
    DB.products[i] = deep(d);
  } else {
    d.id = uid();
    DB.products.unshift(deep(d));
  }
  saveDB(); closeEditor(); syncFromHash(); toast("Product saved to localStorage.");
}

/* ---------- product detail + payload modals ---------- */
function viewProduct(id) {
  var p = byId("products", id);
  if (!p) return;
  var c = byId("categories", p.category_id), m = byId("models", p.model_id);
  var gal = [];
  p.attribute_values.forEach(function (r) {
    if (r.feature_image && r.feature_image.url) gal.push(r.feature_image.url);
    (r.additional_images || []).forEach(function (im) { if (im.url) gal.push(im.url); });
  });
  var valRows = p.attribute_values.map(function (r) {
    var a = byId("attributes", r.attribute_id), v = byId("values", r.attribute_value_id);
    return "<tr><td>" + esc(a ? a.name : "—") + "</td><td>" + esc(v ? v.name : "—") + "</td>" +
      "<td>" + ((r.additional_images || []).length + (r.feature_image && r.feature_image.url ? 1 : 0)) + " img</td>" +
      "<td>" + pill(r.is_active !== false) + "</td></tr>";
  }).join("");
  var varRows = p.variants.map(function (v) {
    var cur = byId("currencies", v.currency_id);
    var opts = (v.options || []).map(function (o) { return o.key || o.id; }).join(" + ");
    return "<tr><td><strong>" + esc(v.sku) + "</strong></td><td>" + esc(v.price) + " " + esc(cur ? cur.code : "") + "</td>" +
      "<td>" + esc(opts) + "</td><td>" + (v.is_special_edition ? '<span class="pill warn">Special</span>' : '<span class="pill">Std</span>') + "</td></tr>";
  }).join("");
  openModal(modalShell(p.name,
    '<div class="detail-grid"><div>' +
      (gal.length ? '<img class="thumb-lg" src="' + esc(gal[0]) + '" alt="">' +
        (gal.length > 1 ? '<div class="gal">' + gal.slice(1, 5).map(function (u) { return '<img src="' + esc(u) + '" alt="" loading="lazy">'; }).join("") + "</div>" : "")
        : '<span class="noimg" style="width:100%;height:140px">' + ICONS.image + "</span>") +
    "</div><div>" +
      "<p class='muted small' style='margin-top:0'>" + esc(p.slug) + " · " + esc(p.gender) + " · " + (p.is_featured ? "Featured" : "Standard") + "</p>" +
      "<p>" + esc(p.description || "No description.") + "</p>" +
      "<p class='small'><strong>Category:</strong> " + esc(c ? c.name : "—") + " &nbsp; <strong>Model:</strong> " + esc(m ? m.name : "—") + "</p>" +
      (p.key_features.length ? "<p class='small'><strong>Key features:</strong> " + p.key_features.map(function (k) { return esc(k.title) + ": " + esc(k.value); }).join(" · ") + "</p>" : "") +
      "<h3 style='margin:14px 0 8px;font-size:13px'>Values</h3>" +
      '<div class="table-wrap" style="box-shadow:none"><table class="grid"><thead><tr><th>Attribute</th><th>Value</th><th>Images</th><th>Status</th></tr></thead><tbody>' + (valRows || '<tr><td colspan="4" class="muted">None</td></tr>') + "</tbody></table></div>" +
      "<h3 style='margin:14px 0 8px;font-size:13px'>Variants</h3>" +
      '<div class="table-wrap" style="box-shadow:none"><table class="grid"><thead><tr><th>SKU</th><th>Price</th><th>Options</th><th>Edition</th></tr></thead><tbody>' + (varRows || '<tr><td colspan="4" class="muted">None</td></tr>') + "</tbody></table></div>" +
    "</div></div>",
    '<button class="btn" data-action="json-product" data-id="' + p.id + '">API payload</button><button class="btn btn-dark" data-close>Close</button>'), true);
}
function jsonModal(id) {
  var p = byId("products", id);
  if (!p) return;
  openModal(modalShell("API payload — " + p.name,
    '<p class="muted small" style="margin-top:0">The exact body for <span style="font-family:var(--mono)">POST /api/v1/admin/products/</span>.</p>' +
    '<pre class="code light" id="payloadPre">' + esc(JSON.stringify(productPayload(p), null, 2)) + "</pre>",
    '<button class="btn" data-close>Close</button><button class="btn btn-dark" data-action="copy-json" data-id="' + p.id + '">Copy JSON</button>'));
}
function copyText(text, done) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
  } else {
    var ta = document.createElement("textarea");
    ta.value = text; document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); done(true); } catch (e) { done(false); }
    ta.remove();
  }
}

/* ============================== actions ============================== */
var ACTIONS = {
  "goto": function (t) { navigate(t.dataset.id); },
  "goto-attributes": function () { navigate("attributes"); },
  "add-currency": function () { currencyForm(null); },
  "edit-currency": function (t, id) { currencyForm(byId("currencies", id)); },
  "save-currency": function (t, id) { saveCurrency(id || null); },
  "del-currency": function (t, id) {
    var c = byId("currencies", id), n = variantsUsingCurrency(id);
    if (n) return toast("Cannot delete: used by " + n + " variant(s).", "err");
    askConfirm("Delete currency", "Delete '" + c.code + "'? This cannot be undone.", "Delete", function () {
      DB.currencies = DB.currencies.filter(function (x) { return x.id !== id; });
      saveDB(); syncFromHash(); toast("Currency deleted.");
    });
  },
  "add-category": function () { categoryForm(null); },
  "edit-category": function (t, id) { categoryForm(byId("categories", id)); },
  "save-category": function (t, id) { saveCategory(id || null); },
  "del-category": function (t, id) {
    var c = byId("categories", id), ps = productsUsingCategory(id);
    if (ps.length) return toast("Cannot delete: used by " + ps.length + " product(s).", "err");
    askConfirm("Delete category", "Delete '" + c.name + "'? This cannot be undone.", "Delete", function () {
      DB.categories = DB.categories.filter(function (x) { return x.id !== id; });
      saveDB(); syncFromHash(); toast("Category deleted.");
    });
  },
  "add-model": function () { modelForm(null); },
  "edit-model": function (t, id) { modelForm(byId("models", id)); },
  "save-model": function (t, id) { saveModel(id || null); },
  "del-model": function (t, id) {
    var m = byId("models", id), ps = productsUsingModel(id);
    if (ps.length) return toast("Cannot delete: used by " + ps.length + " product(s).", "err");
    askConfirm("Delete model", "Delete '" + m.name + "'? This cannot be undone.", "Delete", function () {
      DB.models = DB.models.filter(function (x) { return x.id !== id; });
      saveDB(); syncFromHash(); toast("Model deleted.");
    });
  },
  "add-attribute": function () { attributeForm(null); },
  "edit-attribute": function (t, id) { attributeForm(byId("attributes", id)); },
  "save-attribute": function (t, id) { saveAttribute(id || null); },
  "del-attribute": function (t, id) {
    var a = byId("attributes", id);
    if (valuesOf(id).length) return toast("Cannot delete: it still has values.", "err");
    if (pavsUsingAttribute(id)) return toast("Cannot delete: used inside products.", "err");
    askConfirm("Delete attribute", "Delete '" + a.name + "'? This cannot be undone.", "Delete", function () {
      DB.attributes = DB.attributes.filter(function (x) { return x.id !== id; });
      saveDB(); syncFromHash(); toast("Attribute deleted.");
    });
  },
  "add-value": function () { valueForm(null); },
  "edit-value": function (t, id) { valueForm(byId("values", id)); },
  "save-value": function (t, id) { saveValue(id || null); },
  "del-value": function (t, id) {
    var v = byId("values", id), n = pavsUsingValue(id);
    if (n) return toast("Cannot delete: used inside " + n + " product value(s).", "err");
    askConfirm("Delete value", "Delete '" + v.name + "'? This cannot be undone.", "Delete", function () {
      DB.values = DB.values.filter(function (x) { return x.id !== id; });
      saveDB(); syncFromHash(); toast("Value deleted.");
    });
  },
  "add-product": function () { openEditor(null); },
  "edit-product": function (t, id) { openEditor(id); },
  "view-product": function (t, id) { viewProduct(id); },
  "json-product": function (t, id) { jsonModal(id); },
  "copy-json": function (t, id) {
    var p = byId("products", id);
    copyText(JSON.stringify(productPayload(p), null, 2), function (ok) {
      toast(ok ? "Payload copied to clipboard." : "Copy failed in this browser.", ok ? undefined : "err");
    });
  },
  "del-product": function (t, id) {
    var p = byId("products", id);
    askConfirm("Delete product", "Delete '" + p.name + "' and all its values + variants?", "Delete", function () {
      DB.products = DB.products.filter(function (x) { return x.id !== id; });
      saveDB(); syncFromHash(); toast("Product deleted.");
    });
  },
  "product-back": function () { closeEditor(); syncFromHash(); },
  /* editor structural actions */
  "ed-add-kf": function () { editor.draft.key_features.push({ title: "", value: "" }); document.getElementById("kfRows").innerHTML = kfRowsHTML(); refreshJsonPreview(); },
  "ed-del-kf": function (t, id) { editor.draft.key_features.splice(Number(id), 1); document.getElementById("kfRows").innerHTML = kfRowsHTML(); refreshJsonPreview(); },
  "ed-add-value": function () {
    editor.draft.attribute_values.push({ id: null, key: "", attribute_id: "", attribute_value_id: "", is_active: true, feature_image: null, additional_images: [] });
    document.getElementById("vRows").innerHTML = valueRowsHTML(); refreshJsonPreview();
  },
  "ed-del-value": function (t, id) {
    var gone = editor.draft.attribute_values.splice(Number(id), 1)[0];
    editor.draft.variants.forEach(function (v) { v.options = (v.options || []).filter(function (o) { return o.key !== (gone && gone.key); }); });
    document.getElementById("vRows").innerHTML = valueRowsHTML();
    document.getElementById("varRows").innerHTML = variantRowsHTML();
    refreshJsonPreview();
  },
  "ed-add-addimg": function (t, id) {
    editor.draft.attribute_values[Number(id)].additional_images.push(blankImage());
    document.getElementById("vRows").innerHTML = valueRowsHTML(); refreshJsonPreview();
  },
  "ed-del-addimg": function (t, id) {
    var parts = id.split(":");
    editor.draft.attribute_values[Number(parts[0])].additional_images.splice(Number(parts[1]), 1);
    document.getElementById("vRows").innerHTML = valueRowsHTML(); refreshJsonPreview();
  },
  "ed-add-variant": function () {
    editor.draft.variants.push({ id: null, sku: "", price: "", currency_id: DB.currencies.length === 1 ? DB.currencies[0].id : "", is_special_edition: false, is_active: true, options: [] });
    document.getElementById("varRows").innerHTML = variantRowsHTML(); refreshJsonPreview();
  },
  "ed-del-variant": function (t, id) {
    editor.draft.variants.splice(Number(id), 1);
    document.getElementById("varRows").innerHTML = variantRowsHTML(); refreshJsonPreview();
  },
  "ed-save": function () { saveProduct(); },
  "ed-copy": function () {
    copyText(JSON.stringify(productPayload(editor.draft), null, 2), function (ok) {
      toast(ok ? "Payload copied to clipboard." : "Copy failed in this browser.", ok ? undefined : "err");
    });
  }
};

/* ============================== events ============================== */
document.addEventListener("click", function (e) {
  var r = e.target.closest("[data-route]");
  if (r) { navigate(r.getAttribute("data-route")); return; }
  var t = e.target.closest("[data-action]");
  if (t && ACTIONS[t.dataset.action]) { ACTIONS[t.dataset.action](t, t.dataset.id, e); return; }
  if (e.target.closest("[data-close]")) closeModal();
});
document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeModal(); });
/* broken remote images -> placeholder */
document.addEventListener("error", function (e) {
  var t = e.target;
  if (t && t.tagName === "IMG" && !t.dataset.fbk) {
    t.dataset.fbk = "1";
    var d = document.createElement("span");
    d.className = "noimg";
    if (t.className.indexOf("thumb-lg") >= 0) d.setAttribute("style", "width:100%;height:160px");
    d.innerHTML = ICONS.image;
    t.replaceWith(d);
  }
}, true);
/* live thumbnail previews in modal forms */
document.addEventListener("input", function (e) {
  var t = e.target;
  if (t.matches && t.matches("[data-preview-for]")) {
    var img = document.getElementById(t.getAttribute("data-preview-for"));
    if (img) { img.src = t.value.trim(); img.style.display = t.value.trim() ? "" : "none"; }
  }
  if (!editor || productMode !== "edit") return;
  var d = editor.draft;
  /* scalar fields */
  if (t.matches && t.matches("[data-draft]") && t.type !== "checkbox" && t.tagName !== "SELECT") {
    var f = t.getAttribute("data-draft");
    d[f] = t.value;
    if (f === "name" && !slugTouched) {
      d.slug = slugify(t.value);
      var s = document.getElementById("edSlug");
      if (s) s.value = d.slug;
    }
    if (f === "slug") slugTouched = true;
    refreshJsonPreview();
  }
  if (t.matches && t.matches("[data-kf]")) {
    var kf = d.key_features[Number(t.getAttribute("data-kf"))];
    if (kf) kf[t.getAttribute("data-kf-f")] = t.value;
    refreshJsonPreview();
  }
  if (t.matches && t.matches("[data-vf]") && t.type !== "checkbox" && t.tagName !== "SELECT") {
    var vr = d.attribute_values[Number(t.getAttribute("data-vf"))];
    if (vr) vr[t.getAttribute("data-vfield")] = t.value;
    refreshJsonPreview();
    if (t.getAttribute("data-vfield") === "key") {
      /* keys feed variant options -> refresh variant option labels */
      document.getElementById("varRows").innerHTML = variantRowsHTML();
    }
  }
  if (t.matches && t.matches("[data-vimg]")) {
    var vr2 = d.attribute_values[Number(t.getAttribute("data-vimg"))];
    if (vr2) {
      if (!vr2.feature_image) vr2.feature_image = blankImage();
      vr2.feature_image[t.getAttribute("data-vfield")] = t.value;
    }
    refreshJsonPreview();
  }
  if (t.matches && t.matches("[data-va]")) {
    var parts = (t.getAttribute("data-va") || "").split(":");
    var row = d.attribute_values[Number(parts[0])];
    var im = row && row.additional_images[Number(parts[1])];
    if (im) im[t.getAttribute("data-va-f")] = t.value;
    refreshJsonPreview();
  }
  if (t.matches && t.matches("[data-varf]") && t.type !== "checkbox" && t.tagName !== "SELECT") {
    var vv = d.variants[Number(t.getAttribute("data-varf"))];
    if (vv) vv[t.getAttribute("data-varfield")] = t.value;
    refreshJsonPreview();
  }
});
document.addEventListener("change", function (e) {
  var t = e.target;
  if (t.id === "valueFilter") { valueFilter = t.value; syncFromHash(); return; }
  if (!editor || productMode !== "edit") return;
  var d = editor.draft;
  if (t.matches && t.matches("[data-draft]") && (t.type === "checkbox" || t.tagName === "SELECT")) {
    var f = t.getAttribute("data-draft");
    d[f] = t.type === "checkbox" ? t.checked : t.value;
    refreshJsonPreview();
    if (f === "model_id") document.getElementById("varRows").innerHTML = variantRowsHTML();
    return;
  }
  if (t.matches && t.matches("[data-vf]") && (t.type === "checkbox" || t.tagName === "SELECT")) {
    var vr = d.attribute_values[Number(t.getAttribute("data-vf"))];
    if (vr) vr[t.getAttribute("data-vfield")] = t.type === "checkbox" ? t.checked : t.value;
    refreshJsonPreview();
    return;
  }
  if (t.matches && t.matches("[data-vattr]")) {
    var i = Number(t.getAttribute("data-vattr"));
    var row = d.attribute_values[i];
    if (row) {
      row.attribute_id = t.value;
      row.attribute_value_id = "";
      if (!row.key) {
        var a = byId("attributes", t.value);
        if (a && !row.key) { /* keep key manual */ }
      }
    }
    document.getElementById("vRows").innerHTML = valueRowsHTML();
    refreshJsonPreview();
    return;
  }
  if (t.matches && t.matches("[data-varf]") && (t.type === "checkbox" || t.tagName === "SELECT")) {
    var v = d.variants[Number(t.getAttribute("data-varf"))];
    if (v) v[t.getAttribute("data-varfield")] = t.type === "checkbox" ? t.checked : t.value;
    refreshJsonPreview();
    return;
  }
  if (t.matches && t.matches("[data-opt]")) {
    var v2 = d.variants[Number(t.getAttribute("data-opt"))];
    var key = t.getAttribute("data-optkey");
    if (v2) {
      v2.options = v2.options || [];
      if (t.checked) { if (!v2.options.some(function (o) { return o.key === key; })) v2.options.push({ key: key }); }
      else v2.options = v2.options.filter(function (o) { return o.key !== key; });
      var lab = t.closest("label.opt");
      if (lab) lab.classList.toggle("picked", t.checked);
      /* sku preview may change -> re-render variant rows (no focus issue: click already done) */
      document.getElementById("varRows").innerHTML = variantRowsHTML();
    }
    refreshJsonPreview();
  }
});

/* ============================== init ============================== */
document.getElementById("resetBtn").addEventListener("click", function () {
  askConfirm("Reset demo data", "Throw away all changes and restore the original demo dataset?", "Reset", function () {
    store.del(LS_KEY);
    DB = seed(); saveDB();
    valueFilter = ""; editor = null; productMode = "list";
    syncFromHash(); toast("Demo data reset.");
  });
});
window.addEventListener("hashchange", syncFromHash);
loadDB();
syncFromHash();
})();
