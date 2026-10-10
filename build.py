#!/usr/bin/env python3
"""docs.ashikanw.com を組み立てる。依存なし: python3 build.py → dist/

- pages/ の HTML の断片を、共通の枠（ヘッダー・左のメニュー・目次・フッター）に入れて書き出す。
  断片の先頭の <!-- title: ... --> と <!-- description: ... --> がページの題名と説明になる。
- API リファレンス（/api/reference/）は、下の ENDPOINTS から作る。
  パネルの API（ashika-dash の src/app/api/v1 と src/lib/api.ts）を変えたら、ここもそろえる。
"""
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SITE = "https://docs.ashikanw.com"
API_BASE = "https://api.ashikanw.com/v1"

NAV = [
    ("はじめに", [("/", "ドキュメントのトップ")]),
    ("API", [("/api/", "API の使い方"), ("/api/reference/", "API リファレンス"), ("/api/examples/", "使い方の例")]),
    ("ファイル", [("/sftp/", "SFTP でつなぐ")]),
    ("つなぎ方", [("/ports/", "ポート"), ("/subdomains/", "4l.vc のサブドメイン"), ("/domains/", "独自ドメイン")]),
]

LINKS = [
    ("お客様パネル", "https://dash.ashikanw.com"),
    ("稼働状況", "https://status.ashikanw.com"),
    ("Discord で質問", "https://link.ashikanw.com/discord"),
]

e = html.escape


# ---------------------------------------------------------------------------------------------
# API リファレンスの中身
# ---------------------------------------------------------------------------------------------
SERVER_EXAMPLE = {
    "id": "1a2bc34d",
    "uuid": "6f1c2b3a-6a3e-4c5b-9a1d-2f7e8c9b0a1d",
    "name": "my-bot",
    "status": "RUNNING",
    "suspended": False,
    "plan": {"slug": "mini", "name": "ミニ"},
    "software": {"slug": "python", "name": "Python"},
    "location": "大阪",
    "limits": {"memoryMb": 256, "cpuPercent": 20, "diskMb": 512},
    "address": {"ip": "node1.ashikanw.com", "port": 4012},
    "allocations": [
        {"ip": "node1.ashikanw.com", "port": 4012, "primary": True, "purchased": False, "note": ""},
        {"ip": "node1.ashikanw.com", "port": 4057, "primary": False, "purchased": True, "note": "追加ポート"},
    ],
    "sftpEnabled": False,
    "supported": False,
    "expiresAt": "2026-11-06T12:00:00.000Z",
    "createdAt": "2026-10-07T12:00:00.000Z",
}
RESOURCES_EXAMPLE = {
    "cpuPercent": 1.42,
    "memoryBytes": 73400320,
    "memoryLimitBytes": 268435456,
    "networkRxBytes": 1048576,
    "networkTxBytes": 524288,
    "uptimeSeconds": 3600,
}

ID_PARAM = ("id", "パス", "サーバーの ID。パネルの URL やサーバー一覧に出る 8 文字（例: 1a2bc34d）か、UUID。")

PORT_EXAMPLE = {"ip": "node1.ashikanw.com", "port": 4057, "primary": False, "purchased": True, "note": "追加ポート"}
SUB_EXAMPLE = {
    "id": "clx9sub001",
    "name": "myserver",
    "hostname": "myserver.4l.vc",
    "port": 4012,
    "https": False,
    "status": "active",
    "minecraftSrv": True,
    "records": [{"id": "clx9rec001", "type": "TXT", "name": "myserver.4l.vc", "content": "hello", "createdAt": "2026-10-10T12:00:00.000Z"}],
    "createdAt": "2026-10-10T12:00:00.000Z",
}
SUB_PARAM = ("name", "パス", "サブドメインの名前（myserver）。myserver.4l.vc のような完全な名前や、サブドメインの id でも指定できます。")
AUTH = '-H "Authorization: Bearer $ASHIKA_API_KEY"'
JSON_H = '-H "Content-Type: application/json"'

ENDPOINTS = [
    {
        "group": "アカウント",
        "items": [
            {
                "id": "get-account",
                "method": "GET",
                "path": "/account",
                "title": "アカウントを見る",
                "desc": "キーの持ち主のアカウントと、残高を返します。",
                "params": [],
                "curl": f'curl {API_BASE}/account \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY"',
                "response": {"data": {"id": "clx0abc123", "email": "you@example.com", "name": "あなたの名前", "balanceYen": 300}},
            },
        ],
    },
    {
        "group": "サーバー",
        "items": [
            {
                "id": "list-servers",
                "method": "GET",
                "path": "/servers",
                "title": "サーバーの一覧",
                "desc": "自分のサーバーを、作った順に返します。状態（status）はパネルが最後に確かめたときのものです。今の状態は「サーバーを見る」で取れます。",
                "params": [],
                "curl": f'curl {API_BASE}/servers \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY"',
                "response": {"data": [SERVER_EXAMPLE]},
            },
            {
                "id": "get-server",
                "method": "GET",
                "path": "/servers/{id}",
                "title": "サーバーを見る",
                "desc": "サーバー1台の情報に、今の状態と使用量（resources）を足して返します。止まっているときの resources は null です。",
                "params": [ID_PARAM],
                "curl": f'curl {API_BASE}/servers/1a2bc34d \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY"',
                "response": {"data": {**SERVER_EXAMPLE, "resources": RESOURCES_EXAMPLE}},
            },
            {
                "id": "power",
                "method": "POST",
                "path": "/servers/{id}/power",
                "title": "起動・停止・再起動",
                "desc": "サーバーを起動・停止・再起動・強制終了します。終わってからの状態を返します。期限切れで止まっているサーバーは動かせません（409）。",
                "params": [
                    ID_PARAM,
                    ("signal", "本文", "start（起動）・stop（停止）・restart（再起動）・kill（強制終了）のどれか。"),
                ],
                "curl": f'curl -X POST {API_BASE}/servers/1a2bc34d/power \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY" \\\n  -H "Content-Type: application/json" \\\n  -d \'{{"signal": "restart"}}\'',
                "response": {"data": {"signal": "restart", "status": "RUNNING"}},
            },
            {
                "id": "command",
                "method": "POST",
                "path": "/servers/{id}/command",
                "title": "コマンドを送る",
                "desc": "コンソールに1行送ります（プログラムの標準入力に書き込まれます）。動いていないサーバーには送れません（409）。",
                "params": [ID_PARAM, ("command", "本文", "送る文字。改行なしで 2000 文字まで。")],
                "curl": f'curl -X POST {API_BASE}/servers/1a2bc34d/command \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY" \\\n  -H "Content-Type: application/json" \\\n  -d \'{{"command": "say hello"}}\'',
                "response": {"data": {"sent": True}},
            },
            {
                "id": "logs",
                "method": "GET",
                "path": "/servers/{id}/logs",
                "title": "コンソールの出力",
                "desc": "コンソールの直近の出力を、1行ずつの配列で返します。",
                "params": [ID_PARAM, ("lines", "クエリ", "何行さかのぼるか。1〜1000。省略すると 100。")],
                "curl": f'curl "{API_BASE}/servers/1a2bc34d/logs?lines=20" \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY"',
                "response": {"data": {"lines": ["Logged in as my-bot#1234", "Ready."]}},
            },
        ],
    },
    {
        "group": "ファイル",
        "note": "パスはサーバーのフォルダ（コンテナの /home/container）からの位置で、/ から書きます。サーバーのフォルダの外には出られません。",
        "items": [
            {
                "id": "list-files",
                "method": "GET",
                "path": "/servers/{id}/files/list",
                "title": "フォルダの中身",
                "desc": "フォルダの中のファイルとフォルダを返します。フォルダが先、名前の順です。type は file・directory・symlink のどれかです。",
                "params": [ID_PARAM, ("path", "クエリ", "見るフォルダ。省略すると /。")],
                "curl": f'curl "{API_BASE}/servers/1a2bc34d/files/list?path=/" \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY"',
                "response": {"data": [
                    {"name": "cogs", "path": "/cogs", "type": "directory", "size": 4096, "modifiedAt": "2026-10-07T12:00:00.000Z", "mode": "755"},
                    {"name": "main.py", "path": "/main.py", "type": "file", "size": 1234, "modifiedAt": "2026-10-07T12:00:00.000Z", "mode": "644"},
                ]},
            },
            {
                "id": "read-file",
                "method": "GET",
                "path": "/servers/{id}/files/contents",
                "title": "テキストを読む",
                "desc": "テキストファイルの中身を、そのまま本文で返します（JSON ではありません）。2MB まで。大きいファイルや画像は「ダウンロード」を使ってください。",
                "params": [ID_PARAM, ("path", "クエリ", "読むファイル。")],
                "curl": f'curl "{API_BASE}/servers/1a2bc34d/files/contents?path=/config.json" \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY"',
                "response_text": '{\n  "prefix": "!"\n}',
            },
            {
                "id": "write-file",
                "method": "PUT",
                "path": "/servers/{id}/files/contents",
                "title": "ファイルを書く・送る",
                "desc": "本文をそのままファイルに書きます。テキストでも画像などでも構いません。ファイルが無ければ作り、途中のフォルダも作ります。あれば上書きします。50MB まで（それより大きいものは SFTP で）。ディスクの上限を超える場合は書きません。",
                "params": [ID_PARAM, ("path", "クエリ", "書くファイル。"), ("本文", "本文", "ファイルの中身。")],
                "curl": f'curl -X PUT "{API_BASE}/servers/1a2bc34d/files/contents?path=/main.py" \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY" \\\n  --data-binary @main.py',
                "response": {"data": {"path": "/main.py", "size": 1234}},
            },
            {
                "id": "download-file",
                "method": "GET",
                "path": "/servers/{id}/files/download",
                "title": "ダウンロード",
                "desc": "ファイルをそのまま返します。大きさの上限はありません。",
                "params": [ID_PARAM, ("path", "クエリ", "取り出すファイル。")],
                "curl": f'curl -o world.zip "{API_BASE}/servers/1a2bc34d/files/download?path=/world.zip" \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY"',
                "response_text": "（ファイルの中身）",
            },
            {
                "id": "create-folder",
                "method": "POST",
                "path": "/servers/{id}/files/folder",
                "title": "フォルダを作る",
                "desc": "フォルダを作ります。途中のフォルダも作ります。すでにあれば何もしません。",
                "params": [ID_PARAM, ("path", "本文", "作るフォルダ。")],
                "curl": f'curl -X POST {API_BASE}/servers/1a2bc34d/files/folder \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY" \\\n  -H "Content-Type: application/json" \\\n  -d \'{{"path": "/data/logs"}}\'',
                "response": {"data": {"path": "/data/logs"}},
            },
            {
                "id": "rename-file",
                "method": "POST",
                "path": "/servers/{id}/files/rename",
                "title": "名前を変える・動かす",
                "desc": "ファイルやフォルダの名前を変えます。別のフォルダを指せば、そこへ動かします。",
                "params": [ID_PARAM, ("from", "本文", "今の場所。"), ("to", "本文", "新しい場所。")],
                "curl": f'curl -X POST {API_BASE}/servers/1a2bc34d/files/rename \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY" \\\n  -H "Content-Type: application/json" \\\n  -d \'{{"from": "/main.py", "to": "/old/main.py"}}\'',
                "response": {"data": {"from": "/main.py", "to": "/old/main.py"}},
            },
            {
                "id": "delete-files",
                "method": "POST",
                "path": "/servers/{id}/files/delete",
                "title": "消す",
                "desc": "ファイルやフォルダを消します。フォルダは中身ごと消えます。元には戻せません。",
                "params": [ID_PARAM, ("paths", "本文", "消すものの配列。1〜100 個。")],
                "curl": f'curl -X POST {API_BASE}/servers/1a2bc34d/files/delete \\\n  -H "Authorization: Bearer $ASHIKA_API_KEY" \\\n  -H "Content-Type: application/json" \\\n  -d \'{{"paths": ["/old", "/debug.log"]}}\'',
                "response": {"data": {"deleted": ["/old", "/debug.log"]}},
            },
        ],
    },
    {
        "group": "ポート",
        "note": "ポートの追加は残高から払います。1個の月額は下の「ポートの一覧」の pricePerMonthYen で分かります。買ったときは今の期限までの日割り（purchaseNowYen）を払い、そのあとは期限を延長するたびにプラン料金と一緒に払います。ポートを足したり外したりすると、反映のためサーバーを作り直します（動いていれば自動で起動し直します。ファイルは消えません）。",
        "items": [
            {
                "id": "list-ports",
                "method": "GET",
                "path": "/servers/{id}/ports",
                "title": "ポートの一覧と料金",
                "desc": "サーバーのポートのすべてと、追加するときの料金を返します。purchased が true のものが、追加で買ったポートです。",
                "params": [ID_PARAM],
                "curl": f'curl {API_BASE}/servers/1a2bc34d/ports \\\n  {AUTH}',
                "response": {"data": {"pricePerMonthYen": 10, "purchaseNowYen": 9, "expiresAt": "2026-11-06T12:00:00.000Z", "ports": SERVER_EXAMPLE["allocations"]}},
            },
            {
                "id": "buy-port",
                "method": "POST",
                "path": "/servers/{id}/ports",
                "title": "ポートを追加する",
                "desc": "ポートを1個買います。番号は空いているものから選ばれます。本文は要りません。残高が足りなければ 402（insufficient_balance）を返します。",
                "params": [ID_PARAM],
                "curl": f'curl -X POST {API_BASE}/servers/1a2bc34d/ports \\\n  {AUTH}',
                "response": {"data": {"port": PORT_EXAMPLE, "chargedYen": 9, "balanceYen": 291, "message": "ポート 4057 を追加しました（¥9）。サーバーを作り直して、起動し直しました。"}},
            },
            {
                "id": "release-port",
                "method": "DELETE",
                "path": "/servers/{id}/ports/{port}",
                "title": "ポートを外す",
                "desc": "追加で買ったポートを外します。プランに付いているポートは外せません（409）。返金はなく、次の延長から料金に入らなくなります。このポートにつないでいたサブドメイン・独自ドメインも消えます。",
                "params": [ID_PARAM, ("port", "パス", "外すポートの番号。")],
                "curl": f'curl -X DELETE {API_BASE}/servers/1a2bc34d/ports/4057 \\\n  {AUTH}',
                "response": {"data": {"port": 4057, "released": True, "message": "ポート 4057 を外しました。次の延長から料金に入りません。"}},
            },
        ],
    },
    {
        "group": "サブドメイン",
        "note": "「名前.4l.vc」で、サーバーのポートにつなげます。無料で、1台につき作れる本数に上限があります（一覧の maxPerServer）。名前は英小文字・数字・ハイフンで 3〜32 文字。予約されている名前は使えません（reserved_name）。",
        "items": [
            {
                "id": "list-subdomains",
                "method": "GET",
                "path": "/servers/{id}/subdomains",
                "title": "サブドメインの一覧",
                "desc": "サーバーのサブドメインを、作った順に返します。",
                "params": [ID_PARAM],
                "curl": f'curl {API_BASE}/servers/1a2bc34d/subdomains \\\n  {AUTH}',
                "response": {"data": {"zone": "4l.vc", "enabled": True, "maxPerServer": 3, "subdomains": [SUB_EXAMPLE]}},
            },
            {
                "id": "create-subdomain",
                "method": "POST",
                "path": "/servers/{id}/subdomains",
                "title": "サブドメインを作る",
                "desc": "サブドメインを作り、すぐに使える状態にします（201）。DNS が行き渡るまで数分かかることがあります。",
                "params": [
                    ID_PARAM,
                    ("name", "本文", "使う名前（myserver）。"),
                    ("port", "本文", "つなぐポートの番号。省略するとメインのポート。"),
                    ("https", "本文", "自動 HTTPS を使うか。省略すると false。Web を公開するときだけ true に。"),
                ],
                "curl": f'curl -X POST {API_BASE}/servers/1a2bc34d/subdomains \\\n  {AUTH} \\\n  {JSON_H} \\\n  -d \'{{"name": "myserver", "https": false}}\'',
                "response": {"data": {**SUB_EXAMPLE, "records": []}},
            },
            {
                "id": "get-subdomain",
                "method": "GET",
                "path": "/servers/{id}/subdomains/{name}",
                "title": "サブドメインを見る",
                "desc": "サブドメイン1つと、足した DNS レコードを返します。",
                "params": [ID_PARAM, SUB_PARAM],
                "curl": f'curl {API_BASE}/servers/1a2bc34d/subdomains/myserver \\\n  {AUTH}',
                "response": {"data": SUB_EXAMPLE},
            },
            {
                "id": "update-subdomain",
                "method": "PATCH",
                "path": "/servers/{id}/subdomains/{name}",
                "title": "自動 HTTPS の入り切り",
                "desc": "自動 HTTPS を入れたり切ったりします。入れると 1 分ほどで https://名前.4l.vc が使えるようになります（証明書は最初のアクセスのときに取ります）。",
                "params": [ID_PARAM, SUB_PARAM, ("https", "本文", "true で入れる、false で切る。")],
                "curl": f'curl -X PATCH {API_BASE}/servers/1a2bc34d/subdomains/myserver \\\n  {AUTH} \\\n  {JSON_H} \\\n  -d \'{{"https": true}}\'',
                "response": {"data": {**SUB_EXAMPLE, "https": True}},
            },
            {
                "id": "delete-subdomain",
                "method": "DELETE",
                "path": "/servers/{id}/subdomains/{name}",
                "title": "サブドメインを消す",
                "desc": "サブドメインを消します。足した DNS レコードも消えます。同じ名前は、ほかの方が取れるようになります。",
                "params": [ID_PARAM, SUB_PARAM],
                "curl": f'curl -X DELETE {API_BASE}/servers/1a2bc34d/subdomains/myserver \\\n  {AUTH}',
                "response": {"data": {"hostname": "myserver.4l.vc", "deleted": True}},
            },
            {
                "id": "list-records",
                "method": "GET",
                "path": "/servers/{id}/subdomains/{name}/records",
                "title": "DNS レコードの一覧",
                "desc": "サブドメインに足した DNS レコードを返します。こちらが自動で作る A・SRV は含みません。",
                "params": [ID_PARAM, SUB_PARAM],
                "curl": f'curl {API_BASE}/servers/1a2bc34d/subdomains/myserver/records \\\n  {AUTH}',
                "response": {"data": {"hostname": "myserver.4l.vc", "records": SUB_EXAMPLE["records"]}},
            },
            {
                "id": "add-record",
                "method": "POST",
                "path": "/servers/{id}/subdomains/{name}/records",
                "title": "DNS レコードを足す",
                "desc": "TXT・CNAME・A・AAAA を足します（201）。サブドメインそのもの（name を省略）には TXT だけ付けられます。CNAME・A・AAAA は、その下の名前（www など）に付けます。1つのサブドメインにつき 20 件まで。",
                "params": [
                    ID_PARAM,
                    SUB_PARAM,
                    ("type", "本文", "TXT・CNAME・A・AAAA のどれか。"),
                    ("name", "本文", "サブドメインから見た名前（_acme-challenge、www など）。省略するとサブドメインそのもの。"),
                    ("content", "本文", "値。"),
                ],
                "curl": f'curl -X POST {API_BASE}/servers/1a2bc34d/subdomains/myserver/records \\\n  {AUTH} \\\n  {JSON_H} \\\n  -d \'{{"type": "TXT", "name": "_acme-challenge", "content": "abc123"}}\'',
                "response": {"data": {"id": "clx9rec002", "type": "TXT", "name": "_acme-challenge.myserver.4l.vc", "content": "abc123", "createdAt": "2026-10-10T12:00:00.000Z"}},
            },
            {
                "id": "delete-record",
                "method": "DELETE",
                "path": "/servers/{id}/subdomains/{name}/records/{recordId}",
                "title": "DNS レコードを消す",
                "desc": "足した DNS レコードを1つ消します。",
                "params": [ID_PARAM, SUB_PARAM, ("recordId", "パス", "レコードの id。")],
                "curl": f'curl -X DELETE {API_BASE}/servers/1a2bc34d/subdomains/myserver/records/clx9rec002 \\\n  {AUTH}',
                "response": {"data": {"id": "clx9rec002", "deleted": True}},
            },
        ],
    },
]


def code_block(text, lang=""):
    label = f'<span class="code-lang">{e(lang)}</span>' if lang else ""
    return (
        f'<div class="code">{label}<button class="copy" type="button" aria-label="コピー">コピー</button>'
        f"<pre><code>{e(text)}</code></pre></div>"
    )


def method_badge(method):
    return f'<span class="method m-{method.lower()}">{method}</span>'


def reference_page():
    parts = ["""<!-- title: API リファレンス -->
<!-- description: ASHIKA Network の API の、すべてのエンドポイントの説明です。 -->
<h1>API リファレンス</h1>
<p class="lead">どのエンドポイントも、URL の頭は <code>https://api.ashikanw.com/v1</code> です。
APIキーを <code>Authorization: Bearer</code> ヘッダに入れて送ります。キーの作り方やエラーの形は <a href="/api/">API の使い方</a> をご覧ください。</p>
<p class="lead">例の <code>$ASHIKA_API_KEY</code> は、発行した APIキー（<code>ashk_</code> で始まるもの）に置き換えてください。</p>"""]
    # 一覧
    rows = []
    for group in ENDPOINTS:
        for item in group["items"]:
            rows.append(
                f'<tr><td>{method_badge(item["method"])}</td><td><a href="#{item["id"]}"><code>{e(item["path"])}</code></a></td><td>{e(item["title"])}</td></tr>'
            )
    parts.append(f'<h2 id="endpoints">エンドポイントの一覧</h2><div class="table"><table class="list"><thead><tr><th>メソッド</th><th>パス</th><th>内容</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')

    for group in ENDPOINTS:
        gid = {"アカウント": "account", "サーバー": "servers", "ファイル": "files", "ポート": "ports", "サブドメイン": "subdomains"}[group["group"]]
        parts.append(f'<h2 id="{gid}">{e(group["group"])}</h2>')
        if group.get("note"):
            parts.append(f'<p>{e(group["note"])}</p>')
        for item in group["items"]:
            params = ""
            if item["params"]:
                prow = "".join(f"<tr><td><code>{e(n)}</code></td><td>{e(w)}</td><td>{e(d)}</td></tr>" for n, w, d in item["params"])
                params = f'<div class="table"><table class="params"><thead><tr><th>名前</th><th>場所</th><th>説明</th></tr></thead><tbody>{prow}</tbody></table></div>'
            if "response" in item:
                response = code_block(json.dumps(item["response"], ensure_ascii=False, indent=2), "応答（JSON）")
            else:
                response = code_block(item["response_text"], "応答")
            parts.append(f"""<section class="endpoint" id="{item['id']}">
  <h3>{e(item['title'])}</h3>
  <p class="route">{method_badge(item['method'])}<code>{e(item['path'])}</code></p>
  <p>{e(item['desc'])}</p>
  {params}
  {code_block(item['curl'], 'curl')}
  {response}
</section>""")

    parts.append("""<h2 id="objects">返ってくるもの</h2>
<h3 id="server-object">サーバー</h3>
<div class="table"><table class="params"><thead><tr><th>名前</th><th>説明</th></tr></thead><tbody>
<tr><td><code>id</code></td><td>8 文字の ID。ほかのエンドポイントの <code>{id}</code> に使えます。</td></tr>
<tr><td><code>uuid</code></td><td>UUID。<code>{id}</code> の代わりにも使えます。</td></tr>
<tr><td><code>name</code></td><td>サーバー名。</td></tr>
<tr><td><code>status</code></td><td>状態。下の表のどれか。</td></tr>
<tr><td><code>suspended</code></td><td>期限切れなどで止められているか。</td></tr>
<tr><td><code>plan</code></td><td>プラン（<code>slug</code> と <code>name</code>）。管理者が作ったサーバーなどでは null。</td></tr>
<tr><td><code>software</code></td><td>種類（Python・Node.js など）。</td></tr>
<tr><td><code>location</code></td><td>置いてある場所。</td></tr>
<tr><td><code>limits</code></td><td>メモリ（MB）・CPU（%。100 で 1 コア分）・ディスク（MB）の上限。</td></tr>
<tr><td><code>address</code></td><td>外からつなぐときの接続先（<code>ip</code> と <code>port</code>）。</td></tr>
<tr><td><code>allocations</code></td><td>割り当てられたポートのすべて（下の「ポート」の形）。</td></tr>
<tr><td><code>sftpEnabled</code></td><td>SFTP がオンか。</td></tr>
<tr><td><code>supported</code></td><td>支援プログラムのサーバーか。</td></tr>
<tr><td><code>expiresAt</code></td><td>期限（ISO 8601）。</td></tr>
<tr><td><code>createdAt</code></td><td>作った日時（ISO 8601）。</td></tr>
<tr><td><code>resources</code></td><td>「サーバーを見る」だけ。動いているときの使用量。止まっていれば null。</td></tr>
</tbody></table></div>
<h3 id="port-object">ポート</h3>
<div class="table"><table class="params"><thead><tr><th>名前</th><th>説明</th></tr></thead><tbody>
<tr><td><code>ip</code> / <code>port</code></td><td>外からつなぐときの接続先。</td></tr>
<tr><td><code>primary</code></td><td>メインのポートか（環境変数 <code>SERVER_PORT</code> に入る番号）。</td></tr>
<tr><td><code>purchased</code></td><td>追加で買ったポートか。true のものは外せて、延長のたびに月額がかかります。</td></tr>
<tr><td><code>note</code></td><td>メモ。</td></tr>
</tbody></table></div>
<h3 id="subdomain-object">サブドメイン</h3>
<div class="table"><table class="params"><thead><tr><th>名前</th><th>説明</th></tr></thead><tbody>
<tr><td><code>id</code></td><td>サブドメインの id。</td></tr>
<tr><td><code>name</code> / <code>hostname</code></td><td>名前（myserver）と完全な名前（myserver.4l.vc）。</td></tr>
<tr><td><code>port</code></td><td>つないでいるポート。<code>hostname:port</code> でつながります。</td></tr>
<tr><td><code>https</code></td><td>自動 HTTPS がオンか。</td></tr>
<tr><td><code>status</code></td><td><code>active</code>（使える）か <code>disabled</code>（運営が止めている）。</td></tr>
<tr><td><code>minecraftSrv</code></td><td>Minecraft (Java版) 用の SRV レコードがあるか。true ならポートなしの <code>hostname</code> だけでつながります。</td></tr>
<tr><td><code>records</code></td><td>足した DNS レコード（<code>id</code>・<code>type</code>・<code>name</code>・<code>content</code>・<code>createdAt</code>）。</td></tr>
<tr><td><code>createdAt</code></td><td>作った日時（ISO 8601）。</td></tr>
</tbody></table></div>
<h3 id="status">状態（status）</h3>
<div class="table"><table class="params"><thead><tr><th>値</th><th>意味</th></tr></thead><tbody>
<tr><td><code>INSTALLING</code></td><td>準備中</td></tr>
<tr><td><code>OFFLINE</code></td><td>停止</td></tr>
<tr><td><code>STARTING</code></td><td>起動中</td></tr>
<tr><td><code>RUNNING</code></td><td>動作中</td></tr>
<tr><td><code>STOPPING</code></td><td>停止中</td></tr>
<tr><td><code>SUSPENDED</code></td><td>期限切れなどで止められている</td></tr>
<tr><td><code>ERROR</code></td><td>エラー（パネルから再インストールを試してください）</td></tr>
</tbody></table></div>
<h3 id="resources">使用量（resources）</h3>
<div class="table"><table class="params"><thead><tr><th>名前</th><th>説明</th></tr></thead><tbody>
<tr><td><code>cpuPercent</code></td><td>CPU の使用率（%。100 で 1 コア分）。</td></tr>
<tr><td><code>memoryBytes</code> / <code>memoryLimitBytes</code></td><td>使っているメモリと上限（バイト）。</td></tr>
<tr><td><code>networkRxBytes</code> / <code>networkTxBytes</code></td><td>起動してから受け取った・送った量（バイト）。</td></tr>
<tr><td><code>uptimeSeconds</code></td><td>起動してからの秒数。</td></tr>
</tbody></table></div>""")
    return "\n".join(parts)


# ---------------------------------------------------------------------------------------------
# 枠
# ---------------------------------------------------------------------------------------------
def slug(text):
    return re.sub(r"[^\w-]+", "-", text).strip("-").lower() or "s"


def add_heading_ids(body):
    """h2 に id が無ければ付けて、目次に使う (id, 見出し) を返す。"""
    toc = []

    def fix(match):
        attrs, inner = match.group(1), match.group(2)
        found = re.search(r'id="([^"]+)"', attrs)
        hid = found.group(1) if found else slug(re.sub("<[^>]+>", "", inner))
        toc.append((hid, re.sub("<[^>]+>", "", inner)))
        if not found:
            attrs = f'{attrs} id="{hid}"'
        return f'<h2{attrs}><a class="anchor" href="#{hid}" aria-hidden="true">#</a>{inner}</h2>'

    body = re.sub(r"<h2([^>]*)>(.*?)</h2>", fix, body)
    return body, toc


def meta(body, name):
    found = re.search(rf"<!--\s*{name}:\s*(.*?)\s*-->", body)
    return found.group(1) if found else ""


def layout(url, title, description, body, toc):
    nav = []
    for section, items in NAV:
        links = "".join(
            f'<li><a href="{href}"{" aria-current=page" if href == url else ""}>{e(label)}</a></li>' for href, label in items
        )
        nav.append(f'<div class="nav-group"><p>{e(section)}</p><ul>{links}</ul></div>')
    toc_html = ""
    if len(toc) > 1:
        toc_html = '<nav class="toc" aria-label="このページの目次"><p>このページ</p><ul>' + "".join(
            f'<li><a href="#{hid}">{e(label)}</a></li>' for hid, label in toc
        ) + "</ul></nav>"
    links = "".join(f'<a href="{href}">{e(label)}</a>' for label, href in LINKS)
    full_title = f"{title} | ASHIKA Network ドキュメント" if url != "/" else "ASHIKA Network ドキュメント"
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{SITE}{url}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{SITE}{url}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#14497e">
<link rel="icon" href="/favicon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<a class="skip" href="#main">本文へ</a>
<header class="top">
  <button class="menu" type="button" aria-label="メニューを開く" aria-expanded="false" aria-controls="side">
    <span></span><span></span><span></span>
  </button>
  <a class="brand" href="/"><img src="/logo.png" alt="ASHIKA Network" width="143" height="26"><span>ドキュメント</span></a>
  <nav class="top-links" aria-label="関連するサイト">{links}</nav>
</header>
<div class="shell">
  <aside class="side" id="side"><nav aria-label="ドキュメントのメニュー">{''.join(nav)}</nav></aside>
  <main id="main" class="content">
{body}
  </main>
  {toc_html}
</div>
<footer class="foot">
  <p>© 2026 ASHIKA Network ・ Developed by <a href="https://group.ashikanw.com/">ASHIKA Group</a></p>
  <p><a href="https://www.ashikanw.com/">ASHIKA Network</a> ・ <a href="https://www.ashikanw.com/terms">利用規約</a> ・ <a href="https://www.ashikanw.com/privacy">プライバシーポリシー</a></p>
</footer>
<script src="/docs.js" defer></script>
</body>
</html>
"""


def write(url, html_text):
    target = DIST / url.strip("/") / "index.html" if url != "/" else DIST / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_text, encoding="utf-8")


def render(url, fragment):
    title = meta(fragment, "title")
    description = meta(fragment, "description")
    fragment = re.sub(r"<!--\s*(title|description):.*?-->\n?", "", fragment)
    # 断片の中の ```lang ... ``` をコードの枠にする（手で書く例を楽にするため）
    fragment = re.sub(
        r"```(\w*)\n(.*?)\n```",
        lambda m: code_block(html.unescape(m.group(2)), m.group(1)),
        fragment,
        flags=re.S,
    )
    body, toc = add_heading_ids(fragment)
    write(url, layout(url, title, description, body, toc))
    return url


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for item in (ROOT / "static").iterdir():
        shutil.copy(item, DIST / item.name)

    urls = []
    for page in sorted((ROOT / "pages").rglob("*.html")):
        rel = page.relative_to(ROOT / "pages")
        url = "/" if rel.as_posix() == "index.html" else "/" + rel.with_suffix("").as_posix().removesuffix("/index") + "/"
        urls.append(render(url, page.read_text(encoding="utf-8")))
    urls.append(render("/api/reference/", reference_page()))

    not_found = """<!-- title: ページが見つかりません -->
<!-- description: お探しのページは見つかりませんでした。 -->
<h1>ページが見つかりません</h1>
<p class="lead">URL が間違っているか、ページが移動した可能性があります。</p>
<p><a class="button" href="/">ドキュメントのトップへ</a></p>"""
    render("/404/", not_found)
    shutil.move(DIST / "404" / "index.html", DIST / "404.html")
    (DIST / "404").rmdir()

    sitemap = "".join(f"<url><loc>{SITE}{u}</loc></url>" for u in sorted(urls))
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sitemap}</urlset>\n',
        encoding="utf-8",
    )
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    print(f"built {len(urls)} pages into {DIST}")


if __name__ == "__main__":
    main()
