import os, io, json, zipfile, requests, joblib, xgboost as xgb

def _gh_headers(tok=None):
    h={"Accept":"application/vnd.github+json"}
    if tok: h["Authorization"]=f"token {tok}"
    return h

def find_zip_url(repo, token=None, tag=None):
    if tag:
        r = requests.get(f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
                         headers=_gh_headers(token), timeout=60)
        if r.ok:
            for a in r.json().get("assets", []):
                if a["name"].endswith(".zip"):
                    return a["browser_download_url"]
        raise RuntimeError(f"Tidak ada .zip pada tag {tag}")
    r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest",
                     headers=_gh_headers(token), timeout=60)
    if r.ok:
        for a in r.json().get("assets", []):
            if a["name"].endswith(".zip"):
                return a["browser_download_url"]
    r2 = requests.get(f"https://api.github.com/repos/{repo}/releases?per_page=20",
                      headers=_gh_headers(token), timeout=60)
    r2.raise_for_status()
    for rel in r2.json():
        for a in rel.get("assets", []):
            if a["name"].endswith(".zip"):
                return a["browser_download_url"]
    raise RuntimeError("Tidak ditemukan asset .zip pada releases.")

def download_bundle(repo, token=None, tag=None, direct_url=None):
    url = direct_url or find_zip_url(repo, token=token, tag=tag)
    z = requests.get(url, headers=_gh_headers(token), timeout=120)
    z.raise_for_status()
    return z.content

def load_bundle_flex(bundle_bytes:bytes, extract_dir="/tmp/ara_bundle"):
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(bundle_bytes)) as z:
        z.extractall(extract_dir)
        names = z.namelist()

    card = {}
    card_path = os.path.join(extract_dir, "model_card.json")
    if os.path.exists(card_path):
        card = json.load(open(card_path, "r", encoding="utf-8"))

    calib = None
    for cand in ("artifacts/isotonic_calibrator.pkl","isotonic_calibrator.pkl"):
        p = os.path.join(extract_dir, cand)
        if os.path.exists(p):
            calib = joblib.load(p)
            break

    model_files = [n for n in names if n.endswith(".json") and n.startswith("xgb_cls_seed")]
    if not model_files:
        alt = [n for n in names if n.endswith(".json")]
        if not alt:
            raise FileNotFoundError("Tidak ada XGBoost model JSON di bundle.")
        model_files = [alt[0]]

    models = []
    for mf in model_files:
        b = xgb.Booster()
        b.load_model(os.path.join(extract_dir, mf))
        models.append(b)

    feat_from_bundle = None
    for cand in ("feature_cols_final.json","artifacts/blend_config.json"):
        p=os.path.join(extract_dir,cand)
        if os.path.exists(p):
            try:
                d=json.load(open(p,"r",encoding="utf-8"))
                if isinstance(d,list):
                    feat_from_bundle=d
                elif isinstance(d,dict) and "feature_cols" in d:
                    feat_from_bundle=d["feature_cols"]
            except:
                pass

    return extract_dir, card, calib, models, feat_from_bundle
