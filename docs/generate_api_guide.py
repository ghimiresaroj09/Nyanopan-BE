"""Generate the Data Entry Guide PDF for the Ecommerce Shop API.

Run:  python docs/generate_api_guide.py
Out:  docs/API_Data_Entry_Guide.pdf
"""

import datetime
import json
from fpdf import FPDF
from fpdf.enums import XPos, YPos

OUT = "docs/API_Data_Entry_Guide.pdf"
TODAY = datetime.date.today().isoformat()

# ---------------------------------------------------------------- palette
BLACK = (26, 26, 26)
GRAY = (85, 85, 85)
LIGHT = (244, 244, 244)
BORDER = (210, 210, 210)
ACCENT = (31, 58, 95)
METHOD_COLORS = {
    "GET": (26, 127, 55),
    "POST": (31, 111, 235),
    "PUT": (154, 103, 0),
    "PATCH": (110, 64, 201),
    "DELETE": (207, 34, 46),
}


def js(obj):
    return json.dumps(obj, indent=2, ensure_ascii=True)


class Guide(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 6, "Ecommerce Shop API  -  Data Entry Guide", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*BORDER)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_font("helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 6, f"Page {self.page_no()}/{{nb}}", align="C")

    # ---------------------------------------------------------- primitives
    def need(self, h):
        if self.h - self.b_margin - self.get_y() < h:
            self.add_page()

    def h1(self, text):
        self.need(30)
        self.set_text_color(*BLACK)
        self.set_font("helvetica", "B", 17)
        self.multi_cell(0, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.7)
        self.line(self.l_margin, self.get_y() + 1, self.l_margin + 60, self.get_y() + 1)
        self.set_line_width(0.2)
        self.ln(5)

    def h2(self, text):
        self.need(24)
        self.set_text_color(*ACCENT)
        self.set_font("helvetica", "B", 13)
        self.multi_cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def h3(self, text):
        self.need(18)
        self.set_text_color(*BLACK)
        self.set_font("helvetica", "B", 11)
        self.multi_cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def para(self, text):
        self.set_text_color(*GRAY)
        self.set_font("helvetica", "", 10)
        self.multi_cell(0, 5.5, text, markdown=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1.5)

    def bullets(self, items):
        self.set_text_color(*GRAY)
        self.set_font("helvetica", "", 10)
        for it in items:
            x = self.get_x()
            self.cell(6, 5.5, "-")
            self.multi_cell(0, 5.5, it, markdown=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1.5)

    def code(self, text, size=8.2):
        self.set_font("courier", "", size)
        self.set_text_color(30, 30, 30)
        self.set_fill_color(*LIGHT)
        self.multi_cell(0, 4.4, text, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def label_code(self, label, text, size=8.2):
        self.set_text_color(*BLACK)
        self.set_font("helvetica", "B", 10)
        self.cell(0, 6, label, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.code(text, size)

    def note(self, text):
        self.need(20)
        self.set_fill_color(235, 242, 255)
        self.set_draw_color(31, 111, 235)
        x, y = self.l_margin, self.get_y()
        self.set_text_color(*BLACK)
        self.set_font("helvetica", "", 9.5)
        self.multi_cell(self.w - self.l_margin - self.r_margin, 5.2, "Note: " + text,
                        fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT, markdown=True)
        y2 = self.get_y()
        self.rect(x, y, self.w - self.l_margin - self.r_margin, y2 - y, style="D")
        self.ln(2)

    def field_rows(self, rows):
        """rows: (name, type, req, desc)."""
        for name, typ, req, desc in rows:
            self.need(14)
            self.set_font("courier", "B", 9.5)
            self.set_text_color(*BLACK)
            self.write(5.5, name + "  ")
            self.set_font("helvetica", "", 9.5)
            self.set_text_color(*GRAY)
            self.write(5.5, f"({typ}, {req})  {desc}")
            self.ln(6)
        self.ln(1)

    def endpoint(self, method, path, auth, purpose):
        self.need(26)
        color = METHOD_COLORS.get(method, ACCENT)
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 9.5)
        w = self.get_string_width(method) + 8
        y0 = self.get_y()
        self.cell(w, 7, method, fill=True)
        self.set_text_color(*BLACK)
        self.set_font("courier", "B", 10)
        self.cell(0, 7, "  " + path, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*GRAY)
        self.set_font("helvetica", "", 9.5)
        self.multi_cell(0, 5.2, f"Auth: {auth}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.multi_cell(0, 5.2, purpose, markdown=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)


def render_toc(pdf, section_list):
    pdf.set_xy(pdf.l_margin, 30)  # below the running header
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(*BLACK)
    pdf.cell(0, 10, "Contents", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font("helvetica", "", 10)
    for sec in section_list:
        indent = 6 + sec.level * 8
        pdf.set_x(pdf.l_margin + indent)
        pdf.set_text_color(*GRAY)
        w = pdf.w - pdf.l_margin - pdf.r_margin - indent - 14
        pdf.cell(w, 6, sec.name)
        pdf.set_text_color(*BLACK)
        pdf.cell(14, 6, str(sec.page_number), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


pdf = Guide(format="A4")
pdf.set_auto_page_break(True, 20)
pdf.set_margins(18, 16, 18)
pdf.alias_nb_pages("{nb}")

# ================================================================= COVER
pdf.add_page()
pdf.ln(38)
pdf.set_text_color(*ACCENT)
pdf.set_font("helvetica", "B", 30)
pdf.multi_cell(0, 13, "Ecommerce Shop API", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_text_color(*BLACK)
pdf.set_font("helvetica", "", 21)
pdf.multi_cell(0, 11, "Data Entry Guide", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.ln(6)
pdf.set_draw_color(*ACCENT)
pdf.set_line_width(0.9)
pdf.line(70, pdf.get_y(), 140, pdf.get_y())
pdf.set_line_width(0.2)
pdf.ln(10)
pdf.set_text_color(*GRAY)
pdf.set_font("helvetica", "", 12)
pdf.multi_cell(0, 7, "Every endpoint explained, the exact order to enter data,\nwith many complete examples.", align="C",
               new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.ln(14)
pdf.set_font("helvetica", "", 10)
pdf.multi_cell(0, 6, f"API version 1.0.0   |   {TODAY}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.multi_cell(0, 6, "Base URL (local):  http://127.0.0.1:8000", align="C",
               new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf.add_page()  # fresh page that the TOC will occupy (placeholder includes current page)
pdf.insert_toc_placeholder(render_toc, pages=1)

# ============================================================ 1. BASICS
pdf.start_section("1. Basics: URL, login, envelopes", level=0)
pdf.h1("1. Basics: URL, login, envelopes")

pdf.h2("1.1 Base URL and versions")
pdf.para("Every endpoint in this guide lives under **/api/v1/**. On your own machine the full address looks like this:")
pdf.code("http://127.0.0.1:8000/api/v1/admin/products/\nhttp://127.0.0.1:8000/api/v1/products/")
pdf.para("There are two families: **Public** (`/api/v1/...`) - read-only, no login, used by the shop website; and **Admin** (`/api/v1/admin/...`) - read and write, login required, used for data entry. This guide focuses on Admin, because that is where you type data in.")

pdf.h2("1.2 Login and the Bearer token (do this first)")
pdf.para("**Step 0, before any data entry:** log in as a staff user. Send your email and password:")
pdf.label_code("POST /api/v1/admin/auth/login/  (request)", js({"email": "admin@example.com", "password": "change-me"}))
pdf.label_code("Response 200", js({
    "success": True, "message": "Login successful.",
    "data": {"access": "eyJhbGciOi... (long token, valid 60 minutes)",
             "refresh": "eyJhbGciOi... (valid 7 days)",
             "user": {"id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "email": "admin@example.com",
                      "first_name": "", "last_name": "", "is_staff": True,
                      "is_active": True, "date_joined": "2026-09-17T10:00:00Z"}}}))
pdf.para("Copy the **access** token (not the refresh token). Every admin request must carry it in the header:")
pdf.code("Authorization: Bearer <paste the access token here>")
pdf.para("When the access token expires after 60 minutes, get a new one without retyping your password:")
pdf.label_code("POST /api/v1/admin/auth/refresh/", js({"refresh": "eyJhbGciOi..."}))
pdf.para("Only staff users can log in here. A normal (non-staff) account gets `Admin access required.`")

pdf.h2("1.3 The response envelope (always the same shape)")
pdf.para("Every success looks like this - your payload is always inside **data**:")
pdf.code(js({"success": True, "message": "Created successfully.", "data": {"id": "..."}}))
pdf.para("Every error looks like this - field problems are listed inside **errors**:")
pdf.code(js({"success": False, "message": "Validation failed.",
             "errors": {"gender": ["Select a valid choice. UNISEX is not one of the available choices."]}}))
pdf.bullets([
    "List endpoints put pagination inside `data`: `{count, next, previous, results}`.",
    "Successful **DELETE** returns **200** (not 204) with `{\"success\": true, \"message\": \"Deleted successfully.\", \"data\": {}}`.",
    "List endpoints support `?page=` and `?page_size=`, plus `?search=` and `?ordering=` where documented.",
])

pdf.h2("1.4 Three simplifications that make typing easy")
pdf.bullets([
    "**Human keys instead of UUIDs.** Anywhere a reference is required you may pass a slug, name or SKU instead of a UUID: category/model/product slugs (`\"slippers\"`), attribute names (`\"Color\"`), value names resolved within the attribute (`\"Grey\"`), variant SKUs (`\"CELSI-GREY-40\"`). Matching is exact-first with a single-match case-insensitive fallback, so `\"slippers\"` also works. UUIDs keep working everywhere.",
    "**Images in one JSON step.** Image slots accept `{\"file\": \"data:image/png;base64,...\"}` (png/jpg/webp/gif, max 5 MB by default), so a product with pictures needs a single request - no pre-upload, no multipart. The classic two-step flow (upload, then reference the URL) still works.",
    "**Attribute + values in one call.** `POST /admin/attributes/` accepts `\"value\": [\"Grey\", \"Blue\"]` and creates the names together with the attribute. Updates add missing names without complaining about existing ones.",
])

# ============================================================ 2. FLOW
pdf.start_section("2. The data-entry flow (what to enter first)", level=0)
pdf.h1("2. The data-entry flow (what to enter first)")

pdf.para("Enter data in this order. Each step feeds the next one - that is why the order matters:")
pdf.need(30)
steps = [("1", "Category"), ("2", "Model"), ("3", "Attribute"), ("4", "Values"), ("5", "Product")]
box_w, gap = 25, 4
x0 = pdf.l_margin
y0 = pdf.get_y()
pdf.set_font("helvetica", "B", 8)
for i, (num, name) in enumerate(steps):
    x = x0 + i * (box_w + gap)
    pdf.set_xy(x, y0)
    pdf.set_fill_color(31, 58, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(box_w, 6, num, align="C", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_xy(x, pdf.get_y() + 6)
    pdf.set_fill_color(244, 244, 244)
    pdf.set_draw_color(*BORDER)
    pdf.set_text_color(*BLACK)
    pdf.cell(box_w, 8, name, align="C", fill=True, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
    if i < len(steps) - 1:
        pdf.set_xy(x + box_w, y0)
        pdf.set_text_color(*ACCENT)
        pdf.cell(gap, 14, ">", align="C")
pdf.set_y(y0 + 18)

pdf.h2("2.1 Why this order (the dependency map)")
pdf.bullets([
    "**1. Category** - products must sit on one (`Slippers`). Needs nothing except optionally an image.",
    "**2. Product model** - the product line (`Celsi`). Its first word seeds auto-SKUs (`CELSI-...`). Needs nothing.",
    "**3. Attribute** - facets like `Color` or `Size`. Set **requires_image** now if every active value must carry a picture (typical for Color). Needs nothing.",
    "**4. Attribute values** - concrete options under an attribute (`Grey`, `Blue` under Color; `40`, `41` under Size). Needs its attribute (or create both in one call, section 4.5).",
    "**5. Product (last)** - ties everything together: pick category + model, attach values (with images where required) and priced variants. Needs steps 1-4.",
])
pdf.note("If a dropdown or reference looks empty while entering a product, you skipped an earlier step. Go back, add the missing piece, then continue - the product form does not create categories, models or values for you.")

pdf.h2("2.2 Rules a data-entry person must know")
pdf.bullets([
    "**Names are unique**: category, model, and attribute. Value names are unique **per attribute** (Size can have `40` and another attribute can also have `40`).",
    "**Slugs and SKUs auto-generate** when left blank, and stay stable afterwards. You only type them to override.",
    "**requires_image** (e.g. on Color) forces every **active** value of that attribute to carry a feature image. Inactive values are exempt; variants can only use active values.",
    "**Variant rules**: at least 1 option; only one value per attribute (Grey+Blue together is rejected); no two variants of a product may repeat the same combination; every option must belong to the same product.",
    "**Nothing is ever implicitly deleted.** PATCH/PUT lists upsert by `id`; omitted values/variants are left untouched. Delete explicitly with DELETE.",
    "**Some deletes are blocked while in use** (category/model, values inside products). The API answers 400 with `This record is in use...` - deactivate instead, or delete the referencing records first.",
    "**Prices** are plain decimals (`\"5995.00\"`), 0 or greater. There is no currency object; the frontend shows a static symbol.",
    "**additional_images always replaces the whole gallery** on update: send the complete list you want to keep.",
])

# ============================================================ 3. AUTH
pdf.start_section("3. Endpoint reference", level=0)
pdf.h1("3. Endpoint reference")
pdf.para("Every endpoint below shows its method, path, who may call it, what it is for, and its fields. Admin endpoints need `Authorization: Bearer <access>`. Public endpoints need nothing.")

pdf.start_section("3.1 Admin auth", level=1)
pdf.h2("3.1 Admin auth (staff users only)")
pdf.endpoint("POST", "/api/v1/admin/auth/login/", "none (public door to the admin API).",
             "Log in with email + password. Returns the **access** token (60 min), **refresh** token (7 days) and your profile. Non-staff users are rejected.")
pdf.field_rows([
    ("email", "string", "required", "Staff account email."),
    ("password", "string", "required", "Account password."),
])
pdf.endpoint("POST", "/api/v1/admin/auth/refresh/", "none (needs a valid refresh token).",
             "Trade a refresh token for a fresh access token when the old one expires.")
pdf.endpoint("POST", "/api/v1/admin/auth/logout/", "logged-in user.",
             "Blacklist a refresh token (true logout). Request: `{\"refresh\": \"...\"}`. Response data is `{}`.")
pdf.endpoint("GET", "/api/v1/admin/auth/me/", "staff user.",
             "Return the current admin profile (id, email, names, is_staff, is_active, date_joined).")
pdf.endpoint("POST", "/api/v1/admin/auth/change-password/", "staff user.",
             "Change your own password. Rejects a wrong old password, a new password equal to the old one, or a weak password.")
pdf.field_rows([
    ("old_password", "string", "required", "Current password."),
    ("new_password", "string", "required", "New password (validated for strength)."),
    ("new_password_confirm", "string", "optional", "If sent, must exactly match new_password."),
])

# ============================================================ 4. ADMIN CRUD
pdf.start_section("3.2 Categories - step 1 of the flow", level=1)
pdf.h2("3.2 Categories - step 1 of the flow")
pdf.para("Shelves that products live on (`Slippers`, `Boots`). Each category carries at most one image plus title/caption/alt metadata.")
pdf.endpoint("GET", "/api/v1/admin/categories/", "staff user.",
             "List categories (each row includes `product_count`). Search name/description/slug, filter `?is_active=`.")
pdf.endpoint("POST", "/api/v1/admin/categories/", "staff user.", "Create a category, with or without an image.")
pdf.field_rows([
    ("name", "string", "required", "Unique. E.g. `Slippers`."),
    ("slug", "string", "optional", "Blank = auto from name (`slippers`)."),
    ("description", "string", "optional", "Free text."),
    ("is_active", "boolean", "optional", "Default true. Inactive categories disappear from the public shop."),
    ("image", "image slot", "optional", "null/omitted = blank. See image shapes in section 3.7."),
])
pdf.label_code("Request - plain category", js({"name": "Boots", "description": "Sturdy boots."}))
pdf.label_code("Request - with an inline picture (single step)", js({
    "name": "Sandals", "image": {"file": "data:image/png;base64,iVBORw0KGgo...",
                                 "title": "Sandals", "alt": "Sandals"}}))
pdf.endpoint("GET", "/api/v1/admin/categories/{id}/", "staff user.", "Retrieve one category.")
pdf.endpoint("PUT", "/api/v1/admin/categories/{id}/", "staff user.", "Replace a category (all fields).")
pdf.endpoint("PATCH", "/api/v1/admin/categories/{id}/", "staff user.",
             "Partially update. Omit `image` to keep it, send `null` to clear it.")
pdf.endpoint("DELETE", "/api/v1/admin/categories/{id}/", "staff user.",
             "Delete a category. **Blocked (400)** while any product sits on it.")

pdf.start_section("3.3 Product models - step 2 of the flow", level=1)
pdf.h2("3.3 Product models - step 2 of the flow")
pdf.para("Product lines such as `Celsi`. The first word of the model name seeds auto-generated SKUs (`CELSI-GREY-40`).")
pdf.endpoint("GET", "/api/v1/admin/product-models/", "staff user.",
             "List models (each row includes `product_count`). Search name/description/slug, filter `?is_active=`.")
pdf.endpoint("POST", "/api/v1/admin/product-models/", "staff user.", "Create a model.")
pdf.field_rows([
    ("name", "string", "required", "Unique. E.g. `Celsi`."),
    ("slug", "string", "optional", "Blank = auto from name."),
    ("description", "string", "optional", "Free text."),
    ("is_active", "boolean", "optional", "Default true."),
])
pdf.label_code("Request", js({"name": "Celsi", "description": "Wool felt slipper line."}))
pdf.endpoint("GET", "/api/v1/admin/product-models/{id}/", "staff user.", "Retrieve one model.")
pdf.endpoint("PUT", "/api/v1/admin/product-models/{id}/", "staff user.", "Replace a model.")
pdf.endpoint("PATCH", "/api/v1/admin/product-models/{id}/", "staff user.", "Partially update a model.")
pdf.endpoint("DELETE", "/api/v1/admin/product-models/{id}/", "staff user.",
             "Delete a model. **Blocked (400)** while any product uses it.")

pdf.start_section("3.4 Attributes - step 3 of the flow", level=1)
pdf.h2("3.4 Attributes - step 3 of the flow")
pdf.para("Facets like `Color` or `Size`. Flip **requires_image** on when every active value must carry a feature image (typical for Color - no code change needed for new image-requiring attributes). You can create the attribute **and its values in one call** with `\"value\": [...]`.")
pdf.endpoint("GET", "/api/v1/admin/attributes/", "staff user.",
             "List attributes (rows include `values_count` and the `values` name list). Search name, filter `?is_active=` and `?requires_image=`.")
pdf.endpoint("POST", "/api/v1/admin/attributes/", "staff user.", "Create an attribute, optionally with nested value names (all-or-nothing).")
pdf.field_rows([
    ("name", "string", "required", "Unique. E.g. `Color`."),
    ("requires_image", "boolean", "optional", "Default false. When true, active values need a feature image."),
    ("is_active", "boolean", "optional", "Default true."),
    ("value", "string[]", "optional, write-only", "Up to 200 names created with the attribute, e.g. `[\"Grey\",\"Blue\"]`. Duplicates or blanks fail the whole request."),
])
pdf.label_code("Request - attribute + values in one call", js({"name": "Color", "requires_image": True, "value": ["Grey", "Blue"]}))
pdf.label_code("Response 201 (data)", js({"id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "name": "Color",
    "requires_image": True, "is_active": True, "values_count": 2, "values": ["Blue", "Grey"],
    "created_at": "2026-09-17T10:00:00Z", "updated_at": "2026-09-17T10:00:00Z"}))
pdf.endpoint("GET", "/api/v1/admin/attributes/{id}/", "staff user.", "Retrieve one attribute with its values list.")
pdf.endpoint("PUT", "/api/v1/admin/attributes/{id}/", "staff user.", "Replace an attribute; nested `value` names are ensured to exist.")
pdf.endpoint("PATCH", "/api/v1/admin/attributes/{id}/", "staff user.",
             "Partially update. Nested `value` names are **added if missing** and existing ones are left untouched (never an error, never deleted).")
pdf.endpoint("DELETE", "/api/v1/admin/attributes/{id}/", "staff user.",
             "Delete an attribute. Its global values go with it (CASCADE), but the delete is **blocked (400)** while any product value references it.")

pdf.start_section("3.5 Attribute values - step 4 of the flow", level=1)
pdf.h2("3.5 Attribute values - step 4 of the flow")
pdf.para("Concrete options under an attribute: `Grey`/`Blue` under Color, `40`/`41` under Size. Unique per attribute. Create them one by one or in bulk.")
pdf.endpoint("GET", "/api/v1/admin/attribute-values/", "staff user.",
             "List values. Filter `?attribute=<uuid>` and `?is_active=`, search value or attribute name.")
pdf.endpoint("POST", "/api/v1/admin/attribute-values/", "staff user.",
             "Create ONE value (`{attribute, name}`) or MANY at once (`{attribute, value: [...]}` - same as the bulk endpoint). Send `name` or `value`, never both.")
pdf.field_rows([
    ("attribute", "uuid or name", "required", "E.g. `\"Color\"` or the attribute UUID."),
    ("name", "string", "single shape", "The value name, e.g. `Grey`."),
    ("value", "string[]", "bulk shape", "1-200 names, all-or-nothing. Duplicates or existing names fail everything."),
    ("is_active", "boolean", "optional", "Single shape only. Default true."),
])
pdf.label_code("Request - single", js({"attribute": "Color", "name": "Red"}))
pdf.label_code("Request - bulk (same URL)", js({"attribute": "Color", "value": ["Red", "Black", "Blue"]}))
pdf.endpoint("POST", "/api/v1/admin/attribute-values/bulk/", "staff user.",
             "Bulk-only alias: `{attribute, value: [...]}` creates many values atomically and returns the created rows.")
pdf.endpoint("GET", "/api/v1/admin/attribute-values/{id}/", "staff user.", "Retrieve one value.")
pdf.endpoint("PUT", "/api/v1/admin/attribute-values/{id}/", "staff user.", "Replace one value.")
pdf.endpoint("PATCH", "/api/v1/admin/attribute-values/{id}/", "staff user.", "Partially update one value (rename, move attribute, toggle active).")
pdf.endpoint("DELETE", "/api/v1/admin/attribute-values/{id}/", "staff user.",
             "Delete a value. **Blocked (400)** while any product uses it.")

pdf.start_section("3.6 Products - step 5 of the flow", level=1)
pdf.h2("3.6 Products - step 5 of the flow")
pdf.para("The final step that ties everything together. One POST can carry the product, its attribute values (with images) and its priced variants - the whole write is atomic: any nested failure rolls everything back.")
pdf.endpoint("GET", "/api/v1/admin/products/", "staff user.",
             "List products (compact rows with nested category/model and `variants_count`). Search name/slug/description; filter category slug (`?category=slippers`), gender, featured, price range, active; order by name/created_at/featured.")
pdf.endpoint("POST", "/api/v1/admin/products/", "staff user.",
             "Create a product with nested values + variants. Temp `key`s let variants point at values created in the same request. Returns the full read shape (201).")
pdf.field_rows([
    ("name", "string", "required", "E.g. `Celsi Wool Felt Slippers`."),
    ("model", "uuid or slug", "required", "E.g. `\"celsi\"`."),
    ("gender", "choice", "required", "One of MEN, WOMEN, UNISEX, KIDS, BABY."),
    ("category", "uuid or slug", "required", "E.g. `\"slippers\"`."),
    ("slug", "string", "optional", "Blank = auto from name."),
    ("description / general_information / materials_used", "string", "optional", "Free text blocks."),
    ("is_featured", "boolean", "optional", "Default false."),
    ("is_active", "boolean", "optional", "Default true."),
    ("key_features", "object[]", "optional", "`[{\"title\": \"Sole\", \"value\": \"Rubber\"}]`."),
    ("attribute_values", "object[]", "optional", "Nested values - see fields below."),
    ("variants", "object[]", "optional", "Nested variants - see fields below."),
])
pdf.para("**Nested value fields** (inside `attribute_values`): `id` (omit = create, send = update that row), `key` (temp label variants point at, unique per request), `attribute` + `attribute_value` (required on create; UUIDs or names like `\"Color\"`/`\"Grey\"`), `feature_image` (image slot; **mandatory** when the attribute requires images and the row is active), `additional_images` (gallery list), `is_active` (default true).")
pdf.para("**Nested variant fields** (inside `variants`): `id` (omit = create), `sku` (blank = auto like `CELSI-GREY-40`), `price` (required on create, e.g. `\"5995.00\"`), `name` (optional display name), `is_special_edition` / `is_active`, `options` (required on create, at least one: a value UUID, a temp key `\"grey\"`, or `{\"id\"...}`/`{\"key\"...}` objects).")
pdf.label_code("Request - full product in one call", js({
    "name": "Celsi Wool Felt Slippers", "model": "celsi", "gender": "UNISEX",
    "description": "Warm wool felt slippers.", "category": "slippers", "is_featured": True,
    "key_features": [{"title": "Sole", "value": "Rubber"}],
    "attribute_values": [
        {"key": "grey", "attribute": "Color", "attribute_value": "Grey",
         "feature_image": {"file": "data:image/png;base64,iVBORw0KGgo...",
                           "title": "Grey", "alt": "Grey slippers"}},
        {"key": "40", "attribute": "Size", "attribute_value": "40"}],
    "variants": [{"price": "5995.00", "options": [{"key": "grey"}, {"key": "40"}]}]}))
pdf.endpoint("GET", "/api/v1/admin/products/{id}/", "staff user.",
             "Retrieve one product fully expanded (values with images, variants with priced options, category/model details, creator).")
pdf.endpoint("PUT", "/api/v1/admin/products/{id}/", "staff user.",
             "Update a product. Nested lists **upsert by id**; items without `id` are created; omitted relations are never deleted.")
pdf.endpoint("PATCH", "/api/v1/admin/products/{id}/", "staff user.",
             "Partially update - e.g. add one variant, change a price, or attach a new value - everything else untouched.")
pdf.endpoint("DELETE", "/api/v1/admin/products/{id}/", "staff user.",
             "Delete a product with all its values, variants and images (stored assets are cleaned up too).")

pdf.start_section("3.7 Image slots (how pictures work)", level=1)
pdf.h2("3.7 Image slots (how pictures work)")
pdf.para("`image` (category), `feature_image` and `additional_images` (product values) all follow one contract. **Reads** return delivery URLs plus metadata; **writes** are flexible:")
pdf.bullets([
    "`null`, `\"\"` or `{}` clears a single image (omit the field to keep it).",
    "A plain URL string sets just the URL: `\"image\": \"https://...\"`.",
    "An object references an existing asset: `{\"url\"...}`, `{\"name\"...}` or `{\"public_id\"...}`, plus optional `title`/`caption`/`alt`. Paste back what a previous read returned.",
    "Multipart uploads: send the binary file itself as the field (`image`, `feature_image`, repeat `additional_images` for several).",
    "Inside JSON, upload inline: `{\"file\": \"data:image/png;base64,...\"}` - no pre-upload needed.",
    "Inside nested multipart payloads, point at a file part: `{\"file\": \"grey-img\"}` plus a `grey-img` file part.",
])
pdf.label_code("Read shape (what GET returns)", js({"url": "https://res.cloudinary.com/demo/image/upload/v1/shop/grey-main.jpg",
    "public_id": "shop/grey-main", "title": "Grey", "caption": "Grey wool felt slippers", "alt": "Grey slippers"}))
pdf.note("additional_images replaces the whole gallery on update: always send the complete list you want to keep, in order.")

pdf.start_section("3.8 Standalone values, variants, options, images", level=1)
pdf.h2("3.8 Standalone values, variants, options, images")
pdf.para("Everything in section 3.6 can also be managed piece by piece. Useful for small fixes without touching the whole product.")
pdf.endpoint("GET / POST", "/api/v1/admin/product-attribute-values/", "staff user.",
             "List values (filter `?product=`, `?attribute=`, `?is_active=`, search product/attribute/value names) or attach ONE value to a product. Fields: `product` (uuid/slug, immutable), `attribute` (uuid/name), `attribute_value` (uuid/name), `feature_image`, `additional_images`, `is_active`. The attribute/value must match, and image-requiring attributes need a feature image.")
pdf.endpoint("GET / PUT / PATCH / DELETE", "/api/v1/admin/product-attribute-values/{id}/", "staff user.",
             "Read, replace, partially update or detach one product value. Values are never moved between products. Delete is **blocked (400)** while any variant option points at it.")
pdf.endpoint("GET / POST", "/api/v1/admin/variants/", "staff user.",
             "List variants (filter `?product=`, `?is_special_edition=`, `?is_active=`, search sku/product) or create ONE variant. Fields: `product`, `sku` (blank = auto), `name`, `price`, flags, and `options` = list of product-value UUIDs (**required on create**, at least one, one per attribute, unique combination).")
pdf.endpoint("GET / PUT / PATCH / DELETE", "/api/v1/admin/variant-options/{id}/", "staff user.",
             "Read, replace, partially update or delete one variant. Variants are never moved between products; omit `options` on update to keep them.")
pdf.endpoint("GET / POST", "/api/v1/admin/variant-options/", "staff user.",
             "List single options (filter `?variant=`, `?product=`) or add ONE option to a variant: `{\"variant\": \"<uuid-or-SKU>\", \"product_attribute_value\": \"<uuid>\"}`. Same combination rules apply.")
pdf.endpoint("GET / PUT / PATCH / DELETE", "/api/v1/admin/variant-options/{id}/", "staff user.",
             "Read, repoint (`{\"product_attribute_value\": \"<new uuid>\"}`), or remove one option. Removing must not empty the variant nor duplicate a sibling combination.")
pdf.endpoint("POST", "/api/v1/admin/images/upload/", "staff user.",
             "Upload one image file (`multipart/form-data`, field `image`, optional `folder`). Returns `{public_id, url, width, height, format}` - paste the reference into any image slot. Validated: png/jpg/webp/gif, max 5 MB default.")
pdf.endpoint("POST", "/api/v1/admin/images/delete/", "staff user.",
             "Delete one uploaded asset: `{\"public_id\": \"...\"}` returns `{\"deleted\": true/false}`. Normally you never need this - replacing or deleting records cleans their images automatically.")

pdf.start_section("3.9 Public endpoints (the shop website)", level=1)
pdf.h2("3.9 Public endpoints (the shop website)")
pdf.para("Read-only, no login, active records only. Included so data-entry staff can verify what shoppers will see after each change.")
pdf.endpoint("GET", "/api/v1/categories/  and  /api/v1/categories/{slug}/", "none.",
             "List categories (slug, image, product_count) or one category by slug. Search name/description.")
pdf.endpoint("GET", "/api/v1/product-models/  and  /api/v1/product-models/{slug}/", "none.",
             "List product models or one model by slug.")
pdf.endpoint("GET", "/api/v1/attributes/  and  /api/v1/attributes/{id}/", "none.",
             "List attributes with their values, or one attribute.")
pdf.endpoint("GET", "/api/v1/products/", "none.",
             "Product cards: price_range, primary_image. Filters `?category=slippers&gender=UNISEX&is_featured=true&min_price=&max_price=`, `?search=`, `?ordering=price|-price|-created_at|name`, pagination.")
pdf.endpoint("GET", "/api/v1/products/{slug}/", "none.",
             "Full product page: grouped attribute values with images, every variant with price/edition and option ids (the frontend matches the shopper's selection to find the SKU for WhatsApp checkout).")

# ============================================================ 4. EXAMPLES
pdf.start_section("4. Complete examples (copy and adapt)", level=0)
pdf.h1("4. Complete examples (copy and adapt)")
pdf.para("Five end-to-end stories plus an error gallery. All requests are JSON with `Authorization: Bearer <access>` unless stated otherwise.")

pdf.start_section("Example A - a slipper shop, start to finish", level=1)
pdf.h2("Example A - a slipper shop, start to finish")
pdf.para("**A1. Category with a picture in one step** (inline base64 upload).")
pdf.label_code("POST /api/v1/admin/categories/", js({"name": "Slippers", "description": "Comfy everyday slippers.",
    "image": {"file": "data:image/png;base64,iVBORw0KGgo...", "title": "Slippers", "alt": "Slippers"}}))
pdf.para("**A2. Product model.**")
pdf.label_code("POST /api/v1/admin/product-models/", js({"name": "Celsi", "description": "Wool felt slipper line."}))
pdf.para("**A3. Attributes with their values - two calls total.**")
pdf.label_code("POST /api/v1/admin/attributes/  (x2)", js({"name": "Color", "requires_image": True, "value": ["Grey", "Blue"]}) + "\n" +
    js({"name": "Size", "value": ["40", "41"]}))
pdf.para("**A4. The product** - category + model by slug, values by name, one inline picture, three priced variants. Notice the temp `key`s (`grey`, `blue`, `40`, `41`) that variants point at.")
pdf.label_code("POST /api/v1/admin/products/", js({
    "name": "Celsi Wool Felt Slippers", "model": "celsi", "gender": "UNISEX",
    "description": "Warm wool felt slippers.", "general_information": "Handmade in Nepal.",
    "materials_used": "Wool felt, rubber sole.", "category": "slippers", "is_featured": True,
    "key_features": [{"title": "Upper Material", "value": "Wool Felt"}, {"title": "Sole", "value": "Rubber"}],
    "attribute_values": [
        {"key": "grey", "attribute": "Color", "attribute_value": "Grey",
         "feature_image": {"file": "data:image/png;base64,iVBORw0KGgo...", "title": "Grey", "alt": "Grey slippers"},
         "additional_images": [{"file": "data:image/png;base64,iVBORw0KGgo...", "title": "Side view"}]},
        {"key": "blue", "attribute": "Color", "attribute_value": "Blue",
         "feature_image": {"file": "data:image/png;base64,iVBORw0KGgo...", "title": "Blue"}},
        {"key": "40", "attribute": "Size", "attribute_value": "40"},
        {"key": "41", "attribute": "Size", "attribute_value": "41"}],
    "variants": [
        {"price": "5995.00", "options": [{"key": "grey"}, {"key": "40"}]},
        {"price": "5995.00", "options": [{"key": "grey"}, {"key": "41"}]},
        {"price": "6495.00", "is_special_edition": True, "options": [{"key": "blue"}, {"key": "40"}]}]}))
pdf.para("Response is **201** with the full product: auto slug `celsi-wool-felt-slippers`, auto SKUs `CELSI-GREY-40`, `CELSI-GREY-41`, `CELSI-BLUE-40`, and delivery URLs for every picture. Verify on the public side with `GET /api/v1/products/celsi-wool-felt-slippers/`.")

pdf.start_section("Example B - boots via bulk values + upload-then-reference", level=1)
pdf.h2("Example B - boots via bulk values + upload-then-reference")
pdf.para("**B1.** Upload the photo first (multipart form): `POST /api/v1/admin/images/upload/` with file field `image` and `folder=products`. Response data:")
pdf.code(js({"public_id": "products/a1b2c3.png", "url": "https://res.cloudinary.com/demo/image/upload/v1/products/a1b2c3.png",
             "width": 800, "height": 600, "format": "png"}))
pdf.para("**B2.** Attribute without values, then 3 values in one bulk call:")
pdf.label_code("POST /api/v1/admin/attributes/  then  POST /api/v1/admin/attribute-values/bulk/",
    js({"name": "Material"}) + "\n" + js({"attribute": "Material", "value": ["Leather", "Suede", "Canvas"]}))
pdf.para("**B3.** Category referencing the uploaded picture (paste the URL back):")
pdf.label_code("POST /api/v1/admin/categories/", js({"name": "Boots",
    "image": {"url": "https://res.cloudinary.com/demo/image/upload/v1/products/a1b2c3.png", "title": "Boots", "alt": "Boots"}}))
pdf.para("**B4.** Product using UUIDs for a change (both styles are valid), reusing the same picture object on the value:")
pdf.label_code("POST /api/v1/admin/products/ (excerpt)", js({
    "name": "Trail Boots", "model": "3fa85f64-5717-4562-b3fc-2c963f66afa1", "gender": "MEN", "category": "boots",
    "attribute_values": [{"key": "leather", "attribute": "3fa85f64-5717-4562-b3fc-2c963f66afa3",
                           "attribute_value": "3fa85f64-5717-4562-b3fc-2c963f66afa4",
                           "feature_image": {"public_id": "products/a1b2c3", "title": "Boots"}}],
    "variants": [{"sku": "TRAIL-LEATHER", "price": "8995.00", "options": ["leather"]}]}))
pdf.para("Here the SKU is typed explicitly (`TRAIL-LEATHER`) and the option uses the bare key string `\"leather\"` - all three option styles (UUID, bare key, `{key}` object) are equivalent.")

pdf.start_section("Example C - the smallest possible product", level=1)
pdf.h2("Example C - the smallest possible product")
pdf.para("Only truly-required fields. Slugs, SKUs, flags and timestamps fill themselves in:")
pdf.label_code("POST /api/v1/admin/products/", js({
    "name": "Kids Sandals", "model": "sandalino", "gender": "KIDS", "category": "sandals",
    "attribute_values": [{"attribute": "Size", "attribute_value": "30"}],
    "variants": [{"price": "1995.00", "options": [{"key": "30"}]}]}))
pdf.para("Wait - the variant points at key `\"30\"` but the value above has no `key`! Correct version: either give the value `\"key\": \"30\"`, or (after creating) point at its UUID. Keys are only needed when variants must reference values from the same request:")
pdf.label_code("Corrected (add the key)", js({
    "name": "Kids Sandals", "model": "sandalino", "gender": "KIDS", "category": "sandals",
    "attribute_values": [{"key": "30", "attribute": "Size", "attribute_value": "30"}],
    "variants": [{"price": "1995.00", "options": ["30"]}]}))

pdf.start_section("Example D - growing a product later (PATCH)", level=1)
pdf.h2("Example D - growing a product later (PATCH)")
pdf.para("Size `42` just arrived for the Celsi slippers. First ensure the global value exists (idempotent - safe to repeat):")
pdf.label_code("PATCH /api/v1/admin/attributes/{size-id}/", js({"value": ["42"]}))
pdf.para("Then attach it to the product and add the new variant - one PATCH, everything else untouched (ids below are illustrative):")
pdf.label_code("PATCH /api/v1/admin/products/{product-id}/", js({
    "attribute_values": [{"key": "42", "attribute": "Size", "attribute_value": "42"}],
    "variants": [{"price": "5995.00", "options": [{"key": "grey"}, {"key": "42"}]}]}))
pdf.para("To change an existing variant's price instead, send its `id`: `{\"variants\": [{\"id\": \"<variant-uuid>\", \"price\": \"6295.00\"}]}`. To rename a value's picture, PATCH the standalone value (section 3.8) with the new `feature_image` object.")

pdf.start_section("Example E - all three image flows side by side", level=1)
pdf.h2("Example E - all three image flows side by side")
pdf.para("Same result - a feature image on a product value - three ways:")
pdf.label_code("1) Inline base64 (1 JSON request - simplest)", js(
    {"feature_image": {"file": "data:image/png;base64,iVBORw0KGgo...", "title": "Grey"}}))
pdf.label_code("2) Upload then reference (2 requests)", js(
    {"feature_image": {"url": "https://res.cloudinary.com/demo/image/upload/v1/shop/grey-main.jpg", "title": "Grey"}}))
pdf.code("3) Multipart in one request (for scripts):\n"
         "curl -X POST http://127.0.0.1:8000/api/v1/admin/products/ \\\n"
         "  -H \"Authorization: Bearer $ACCESS\" \\\n"
         "  -F name=\"Wool Slippers\" -F model=\"celsi\" -F gender=\"UNISEX\" -F category=\"slippers\" \\\n"
         "  -F attribute_values='[{\"key\": \"grey\", \"attribute\": \"Color\", \"attribute_value\": \"Grey\", \"feature_image\": {\"file\": \"grey-img\"}}]' \\\n"
         "  -F variants='[{\"price\": \"5995.00\", \"options\": [{\"key\": \"grey\"}]}]' \\\n"
         "  -F grey-img=@grey.png")
pdf.para("Rule of thumb: humans and dashboards use (1); file pipelines that already speak multipart use (3); (2) is handy when the same picture is reused in many places.")

pdf.start_section("Example F - error gallery (what went wrong?)", level=1)
pdf.h2("Example F - error gallery (what went wrong?)")
pdf.para("Real error shapes you may meet, and the fix:")
pdf.label_code("Missing feature image (Color requires one)", js({"success": False, "message": "Validation failed.",
    "errors": {"attribute_values": {"0": {"feature_image": ["A feature image is required for 'Color' values."]}}}}))
pdf.para("Fix: add `feature_image` to that value, or deactivate the value.")
pdf.label_code("Value name from the wrong attribute", js({"success": False, "message": "Validation failed.",
    "errors": {"attribute_value": ["No value '40' for attribute 'Color'. Available for 'Color': Blue, Grey."]}}))
pdf.para("Fix: pick a name from the suggested list, or pass the right `attribute` alongside the name.")
pdf.label_code("Duplicate variant combination", js({"success": False, "message": "Validation failed.",
    "errors": {"variants": {"1": {"options": ["This exact combination already exists for another variant of this product."]}}}}))
pdf.para("Fix: each variant needs a different option set - check the existing variants first.")
pdf.label_code("Delete blocked (record in use)", js({"success": False,
    "message": "Cannot delete this record because it is referenced by other records.",
    "errors": {"non_field_errors": ["This record is in use and cannot be deleted. Deactivate it instead, or remove the referencing records first."]}}))
pdf.para("Fix: follow the message - deactivate, or delete the referencing products/variants first.")
pdf.label_code("Bad login", js({"success": False, "message": "Authentication required.",
    "errors": {"detail": "No active account found with the given credentials"}}))
pdf.para("Fix: check email/password and that the account is staff + active.")

# ============================================================ 5. CHEAT SHEET
pdf.start_section("5. One-page cheat sheet", level=0)
pdf.h1("5. One-page cheat sheet")
pdf.h2("Order of entry")
pdf.bullets([
    "0. Login -> `Authorization: Bearer <access>`.",
    "1. Category (`Slippers` + image?) -> 2. Model (`Celsi`).",
    "3. Attribute (`Color`, requires_image?) + 4. values (`Grey`, `Blue`) - one call with `\"value\": [...]`.",
    "5. Product: category + model, values with keys + images, variants with price + options.",
    "Verify on public `GET /api/v1/products/{slug}/`.",
])
pdf.h2("References (UUID or human key)")
pdf.bullets([
    "Category / model / product: slug - `\"slippers\"`, `\"celsi\"`.",
    "Attribute: name - `\"Color\"`. Value: name within the attribute - `\"Grey\"`.",
    "Variant: SKU - `\"CELSI-GREY-40\"`.",
])
pdf.h2("Images")
pdf.bullets([
    "Simplest: `{\"file\": \"data:image/png;base64,...\"}` with title/alt.",
    "Reuse: paste `{\"url\": ...}` or `{\"public_id\": ...}` from any earlier read.",
    "`null` clears a single image; omitting keeps it; `additional_images` always replaces fully.",
])
pdf.h2("Variants")
pdf.bullets([
    "Options: UUID, `\"key\"`, or `{\"key\"}` / `{\"id\"}` - at least one per variant.",
    "Blank SKU auto-generates (`CELSI-GREY-40`) and never changes afterwards.",
    "Rules: one value per attribute, unique combination per product, active values only.",
])
pdf.h2("Safety")
pdf.bullets([
    "Product writes are atomic - a failure rolls back the entire request.",
    "Updates never delete omitted relations; DELETE is explicit and returns 200.",
    "In-use records refuse deletion with a 400 - deactivate or unlink first.",
])

pdf.output(OUT)
print("wrote", OUT)
