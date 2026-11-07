"""Генерация картинок через Cloudflare Workers AI.

Читает CLOUDFLARE_ACCOUNT_ID и CLOUDFLARE_API_TOKEN из ~/.hermes/.env.

Примеры:
  python tools/gen_image.py "prompt" -o out.png
  python tools/gen_image.py "prompt" --model @cf/black-forest-labs/flux-2-dev --size 1024x1536
  python tools/gen_image.py --list
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

ENV = os.path.join(os.path.expanduser("~"), ".hermes", ".env")
API = "https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{model}"

FAST = "@cf/black-forest-labs/flux-1-schnell"
BEST = "@cf/black-forest-labs/flux-2-dev"


def load_env():
    conf = {}
    if os.path.exists(ENV):
        for line in open(ENV, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            conf[k.strip()] = v.strip().strip('"').strip("'")
    acc = os.environ.get("CLOUDFLARE_ACCOUNT_ID") or conf.get("CLOUDFLARE_ACCOUNT_ID")
    tok = os.environ.get("CLOUDFLARE_API_TOKEN") or conf.get("CLOUDFLARE_API_TOKEN")
    if not acc or not tok:
        sys.exit("нет CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN в ~/.hermes/.env")
    return acc, tok


def _multipart(fields):
    boundary = "----hermes" + uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                 % (boundary, k, v)).encode()
    body += ("--%s--\r\n" % boundary).encode()
    return body, "multipart/form-data; boundary=" + boundary


def generate(prompt, model=FAST, size=(1024, 1024), steps=4, seed=None):
    acc, tok = load_env()
    url = API.format(acc=acc, model=urllib.parse.quote(model, safe="@/"))
    payload = {"prompt": prompt}
    # flux-1-schnell не принимает width/height — только prompt, steps, seed
    if "flux-1-schnell" not in model:
        payload["width"], payload["height"] = size[0], size[1]
    if "flux" in model:
        payload["steps"] = steps
    if seed is not None:
        payload["seed"] = seed

    # flux-2-* принимает только multipart
    if "flux-2" in model:
        fields = {k: str(v) for k, v in payload.items()}
        body, ctype = _multipart(fields)
    else:
        body, ctype = json.dumps(payload).encode(), "application/json"

    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Authorization": "Bearer " + tok,
                                          "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %s: %s" % (e.code, e.read().decode()[:400]))

    if not data.get("success"):
        raise RuntimeError(json.dumps(data.get("errors"), ensure_ascii=False))

    res = data["result"]
    if isinstance(res, dict) and res.get("image"):
        return base64.b64decode(res["image"])
    if isinstance(res, (bytes, bytearray)):
        return bytes(res)
    raise RuntimeError("неизвестный формат ответа: " + str(list(res) if isinstance(res, dict) else type(res)))


def list_models():
    acc, tok = load_env()
    url = ("https://api.cloudflare.com/client/v4/accounts/%s/ai/models/search"
           "?task=Text-to-Image&per_page=50" % acc)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
    res = d.get("result")
    items = res if isinstance(res, list) else (res or {}).get("items", [])
    for m in items:
        print(m.get("name"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("-o", "--out", default="image.png")
    ap.add_argument("--model", default=FAST)
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        list_models()
        return
    if not a.prompt:
        sys.exit("нужен prompt")

    w, h = (int(x) for x in a.size.lower().split("x"))
    img = generate(a.prompt, a.model, (w, h), a.steps, a.seed)
    with open(a.out, "wb") as f:
        f.write(img)
    print("%s  %d Б  %s" % (a.out, len(img), a.model))


if __name__ == "__main__":
    main()
