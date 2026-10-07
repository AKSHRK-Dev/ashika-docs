# ASHIKA Network docs

Source of [docs.ashikanw.com](https://docs.ashikanw.com): how to use the ASHIKA Network API and SFTP.

- `pages/` — page bodies (HTML fragments). The first lines `<!-- title: ... -->` and `<!-- description: ... -->` set the page title and description. Fenced blocks (```` ```bash ````) become code blocks with a copy button.
- `build.py` — wraps the pages in the shared layout and builds the API reference from `ENDPOINTS`. Keep it in step with the panel's API (`src/app/api/v1` and `src/lib/api.ts` in ashika-dash).
- `static/` — stylesheet, script and images, copied as they are.
- `serve.mjs` — serves `dist/` with no dependencies.

```sh
python3 build.py          # → dist/
PORT=3400 node serve.mjs  # http://127.0.0.1:3400
```

Deploy (on the ASHIKA server, `~/apps/ashika-docs`, service `ashika-docs`): `git pull && python3 build.py`.

Developed by [ASHIKA Group](https://group.ashikanw.com/).
