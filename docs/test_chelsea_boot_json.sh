#!/bin/bash
# Chelsea Boot test. 1) log in and paste the ACCESS token below. 2) run: bash docs/test_chelsea_boot_XXX.sh
BASE="http://127.0.0.1:8000"
TOKEN="PASTE_ACCESS_TOKEN_HERE"
# ---- API 1: prerequisites (safe to re-run; 400 "already exists" is fine) ----
echo "== category =="
curl -s -o /dev/null -w "POST categories HTTP %{http_code}\n" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Boots","description":"Sturdy boots."}' $BASE/api/v1/admin/categories/
echo "== model =="
curl -s -o /dev/null -w "POST product-models HTTP %{http_code}\n" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Chelsea","description":"Elastic-sided boot line."}' $BASE/api/v1/admin/product-models/
echo "== attributes + values (Color with 5, Size with 10) =="
curl -s -o /dev/null -w "POST Color HTTP %{http_code}\n" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Color","requires_image":true,"value":["Black","Brown","Tan","Burgundy","Grey"]}' $BASE/api/v1/admin/attributes/
curl -s -o /dev/null -w "POST Size HTTP %{http_code}\n" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Size","value":["39","40","41","42","43","44","45","46","47","48"]}' $BASE/api/v1/admin/attributes/

# ---- API 2: product create (JSON, pictures inline as base64) ----
echo "== product (JSON) =="
curl -s -w "\nHTTP %{http_code}\n" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data @docs/chelsea_product.json $BASE/api/v1/admin/products/ | python3 -c "
import json,sys
raw = sys.stdin.read()
body, _, status = raw.rpartition(chr(10)+'HTTP ')
print('HTTP', status.strip())
d = json.loads(body)
if d.get('status') != 'success':
    print(json.dumps(d, indent=2)[:2000]); sys.exit(1)
p = d['data']
print('message:', d['message'], '| statusCode:', d['statusCode'])
print('id:', p['id'], '| name:', p['name'])
print('model:', p['model']['name'], '| category:', p['category']['name'])
"
