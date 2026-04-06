#!/usr/bin/env python3
"""Admin CMS for Casandra Lee portfolio site."""
import json, os, shutil, uuid
from flask import Flask, request, jsonify, send_from_directory, send_file

ADMIN_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.dirname(ADMIN_DIR)
DATA_FILE = os.path.join(ADMIN_DIR, "site_data.json")
UPLOAD_DIR = os.path.join(SITE_DIR, "assets", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# --- Serve admin UI ---
@app.route("/")
def index():
    return send_file(os.path.join(ADMIN_DIR, "index.html"))

# --- Serve site assets (images) ---
@app.route("/assets/<path:path>")
def serve_asset(path):
    return send_from_directory(os.path.join(SITE_DIR, "assets"), path)

# --- API ---
@app.route("/api/data", methods=["GET"])
def get_data():
    return jsonify(load_data())

@app.route("/api/data", methods=["PUT"])
def put_data():
    data = request.get_json()
    save_data(data)
    return jsonify({"ok": True})

@app.route("/api/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file"}), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        return jsonify({"error": "Invalid file type"}), 400
    name = uuid.uuid4().hex[:12] + ext
    dest = os.path.join(UPLOAD_DIR, name)
    f.save(dest)
    return jsonify({"path": "assets/uploads/" + name})

@app.route("/api/publish", methods=["POST"])
def publish():
    """Regenerate static HTML files from site_data.json."""
    data = load_data()
    _generate_site(data)
    return jsonify({"ok": True})

# ---- Static site generator ----

SIDEBAR_HTML = '''  <aside class="sidebar">
    <a class="brand" href="index.html">Casandra Lee</a>
    <button class="hamburger" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
    <nav class="nav">
      <a {active_illustrations}href="index.html">Illustrations</a>
      <a {active_childrens}href="childrens-books.html">Children's Books</a>
      <a {active_paintings}href="paintings.html">Paintings</a>
      <a {active_brand}href="brand-illustrations.html">Brand Illustrations</a>
      <div class="dropdown">
        <button class="dropdown-toggle {active_shop}">Shop <span class="arrow">&#9662;</span></button>
        <div class="dropdown-menu">
          <a href="shop.html">All Works</a>
          <a href="shop.html#originals">Originals</a>
          <a href="shop.html#prints">Prints</a>
        </div>
      </div>
      <a {active_about}href="about.html">About</a>
      <div class="nav-icons">
        <a href="https://www.instagram.com/casandramlee/" target="_blank" rel="noopener" aria-label="Instagram">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>
        </a>
        <a href="mailto:casandramlee@gmail.com" aria-label="Email">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        </a>
      </div>
    </nav>
  </aside>'''

def _sidebar(active=""):
    keys = ["illustrations","childrens","paintings","brand","shop","about"]
    kw = {}
    for k in keys:
        kw["active_"+k] = 'class="active" ' if active == k else ""
    return SIDEBAR_HTML.format(**kw)

def _head(title):
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montaga&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/styles.css" />
</head>
<body>

  <div class="page-layout">
'''

FOOT = '''  <footer class="footer">
    <span>&copy; <span id="year"></span> Casandra Lee</span>
  </footer>
  </div><!-- .main-content -->
</div><!-- .page-layout -->

  <script src="js/app.js"></script>
</body>
</html>'''

def _generate_site(data):
    pages = data["pages"]

    # --- Illustrations (index.html) ---
    p = pages["illustrations"]
    imgs = ""
    for img in p["images"]:
        cap = ""
        if img.get("caption"):
            cap = f'\n        <div class="caption">{img["caption"]}</div>'
        imgs += f'''      <div class="grid-item">
        <img src="{img['src']}" data-full="{img['src']}" alt="{img.get('alt','')}" loading="lazy">{cap}
      </div>\n'''
    html = _head("Casandra Lee") + _sidebar("illustrations") + f'''  <div class="main-content">

  <main class="wrap">
    <div class="pagehead"><h1>{p["title"]}</h1></div>
    <div class="grid">
{imgs}    </div>
  </main>

  <div class="lightbox" id="lightbox">
    <button class="lightbox-close" aria-label="Close">&times;</button>
    <img src="" alt="">
  </div>

''' + FOOT
    with open(os.path.join(SITE_DIR, "index.html"), "w") as f:
        f.write(html)

    # --- Paintings ---
    p = pages["paintings"]
    imgs = ""
    for img in p["images"]:
        imgs += f'''      <div class="grid-item">
        <img src="{img['src']}" data-full="{img['src']}" alt="{img.get('alt','')}" loading="lazy">
      </div>\n'''
    html = _head("Paintings - Casandra Lee") + _sidebar("paintings") + f'''  <div class="main-content">

  <main class="wrap">
    <div class="pagehead"><h1>{p["title"]}</h1></div>
    <div class="grid">
{imgs}    </div>
  </main>

  <div class="lightbox" id="lightbox">
    <button class="lightbox-close" aria-label="Close">&times;</button>
    <img src="" alt="">
  </div>

''' + FOOT
    with open(os.path.join(SITE_DIR, "paintings.html"), "w") as f:
        f.write(html)

    # --- Section-based pages (children's books, brand illustrations) ---
    section_pages = {
        "childrens-books": ("childrens", "childrens-books.html"),
        "brand-illustrations": ("brand", "brand-illustrations.html"),
    }
    for key, (nav_active, filename) in section_pages.items():
        p = pages[key]
        sections = ""
        for sec in p["sections"]:
            imgs = ""
            for i, img in enumerate(sec["images"]):
                fw = ""
                cap_html = ""
                if img.get("fullWidth"):
                    if img.get("caption"):
                        cap_html = f'\n          <div class="caption">{img["caption"]}</div>'
                    imgs += f'''        <div class="grid-item" style="grid-column: 1 / -1; border: none;">
          <img src="{img['src']}" alt="{img.get('alt','')}" loading="lazy" style="border-radius: var(--radius); border: 1px solid var(--line);">{cap_html}
        </div>\n'''
                else:
                    imgs += f'        <img src="{img["src"]}" alt="{img.get("alt","")}" loading="lazy">\n'
            sections += f'''    <section class="project-section">
      <h2>{sec["title"]}</h2>
      <p>{sec["description"]}</p>
      <div class="project-images">
{imgs}      </div>
    </section>\n\n'''
        html = _head(f'{p["title"]} - Casandra Lee') + _sidebar(nav_active) + f'''  <div class="main-content">

  <main class="wrap">
    <div class="pagehead"><h1>{p["title"]}</h1></div>

{sections}  </main>

''' + FOOT
        with open(os.path.join(SITE_DIR, filename), "w") as f:
            f.write(html)

    # --- Shop ---
    shop = data["shop"]
    cards = ""
    for w in shop:
        pill = "Original" if w["type"] == "original" else "Print"
        detail_file = f'work-{w["id"]}.html'
        cards += f'''      <article class="work-card" data-type="{w['type']}">
        <a class="thumb" href="{detail_file}">
          <img src="{w['thumb']}" alt="{w['title']}" loading="lazy">
        </a>
        <div class="meta">
          <h2>{w['title']}</h2>
          <p class="specs">{w['medium']} &middot; {w['dimensions']} &middot; {w['year']}</p>
          <div class="pillrow"><span class="pill">{pill}</span></div>
          <div class="actions">
            <a class="btn btn-ghost" href="{detail_file}">View</a>
            <a class="btn" href="{w['checkoutUrl']}" target="_blank" rel="noopener">Buy now</a>
            <span class="price">{w['price']}</span>
          </div>
        </div>
      </article>\n\n'''

        # detail page
        shipping = f'<p class="tiny muted">{w["shipping"]}</p>' if w.get("shipping") else ""
        detail = _head(f'{w["title"]} - Casandra Lee') + _sidebar("shop") + f'''  <div class="main-content">

  <main class="wrap">
    <a class="muted" href="shop.html">&larr; Back to shop</a>
    <section class="workview">
      <div class="workimg"><img src="{w['image']}" alt="{w['title']}"></div>
      <div class="workmeta">
        <h1>{w['title']}</h1>
        <p class="muted">{w['medium']} &middot; {w['dimensions']} &middot; {w['year']}</p>
        <p>{w['description']}</p>
        <div class="pillrow"><span class="pill">{pill}</span></div>
        <div class="buyrow">
          <strong class="price">{w['price']}</strong>
          <a class="btn" href="{w['checkoutUrl']}" target="_blank" rel="noopener">Buy now</a>
        </div>
        {shipping}
      </div>
    </section>
  </main>

''' + FOOT
        with open(os.path.join(SITE_DIR, detail_file), "w") as f:
            f.write(detail)

    shop_filter_script = '''  <script>
    document.querySelectorAll(".filter-tab").forEach(function(btn) {
      btn.addEventListener("click", function() {
        document.querySelectorAll(".filter-tab").forEach(function(b) { b.classList.remove("active"); });
        btn.classList.add("active");
        var filter = btn.dataset.filter;
        document.querySelectorAll(".work-card").forEach(function(card) {
          card.style.display = (filter === "all" || card.dataset.type === filter) ? "" : "none";
        });
      });
    });
    (function() {
      var h = location.hash.replace("#","");
      if (h === "originals" || h === "prints") {
        var f = h === "originals" ? "original" : "print";
        document.querySelectorAll(".filter-tab").forEach(function(b) {
          b.classList.toggle("active", b.dataset.filter === f);
        });
        document.querySelectorAll(".work-card").forEach(function(card) {
          card.style.display = card.dataset.type === f ? "" : "none";
        });
      }
    })();
  </script>'''

    shop_html = _head("Shop - Casandra Lee") + _sidebar("shop") + f'''  <div class="main-content">

  <main class="wrap">
    <div class="pagehead">
      <h1>Shop</h1>
      <p class="muted">Original paintings and archival prints available for purchase.</p>
    </div>
    <div class="filter-tabs">
      <button class="filter-tab active" data-filter="all">All</button>
      <button class="filter-tab" data-filter="original">Originals</button>
      <button class="filter-tab" data-filter="print">Prints</button>
    </div>
    <section class="works">
{cards}    </section>
  </main>

  <footer class="footer">
    <span>&copy; <span id="year"></span> Casandra Lee</span>
  </footer>
  </div>
</div>

  <script src="js/app.js"></script>
{shop_filter_script}
</body>
</html>'''
    with open(os.path.join(SITE_DIR, "shop.html"), "w") as f:
        f.write(shop_html)

    # --- About ---
    ab = data["about"]
    paras = "\n\n".join(f"        <p>{p}</p>" for p in ab["bio"])
    about_html = _head("About - Casandra Lee") + _sidebar("about") + f'''  <div class="main-content">

  <main class="wrap prose">
    <h1>About</h1>
    <section class="about-layout">
      <div class="about-photo">
        <img src="{ab['photo']}" alt="Portrait of Casandra Lee">
      </div>
      <div class="about-text">
{paras}
      </div>
    </section>
    <h2>Contact</h2>
    <p>Email: <a href="mailto:{ab['email']}">{ab['email']}</a></p>
    <p>Instagram: <a href="{ab['instagram']}" target="_blank" rel="noopener noreferrer">@casandramlee</a></p>
  </main>

''' + FOOT
    with open(os.path.join(SITE_DIR, "about.html"), "w") as f:
        f.write(about_html)


if __name__ == "__main__":
    print("Admin CMS running at http://localhost:5000")
    app.run(port=5000, debug=False)
