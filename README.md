# TWS SCHEDULE 5.0 — Auto Sync

This is a public website. Japanese official schedule entries are fetched by GitHub Actions every six hours, committed to `schedule.json`, and displayed by the HTML calendar. No Cloudflare KV, Access or secrets are required.

## Deploy
1. Upload `index.html`, `schedule.json`, `sync.py`, `README.md` and the `.github/workflows/sync.yml` file to a GitHub repository, preserving the workflow folder structure.
2. GitHub repo Settings → Actions → General → Workflow permissions → Read and write permissions → Save (if your organization permits it).
3. Actions → Sync TWS public schedule → Run workflow. Inspect the log; if the source HTML changes, parsing may fail safely without overwriting the existing data.
4. Cloudflare Workers & Pages → Create application → Pages → Connect to Git → select the repository. Framework preset None, build command empty, output directory `/` or `.` as accepted by UI. Do NOT create a Worker for this static site.
5. New commits from the scheduled workflow trigger Cloudflare Pages redeployment. The site fetches the published `schedule.json` when opened/refreshed.

Important: GitHub Actions scheduled runs may be delayed or paused due to inactivity; the source may change its HTML and break parsing. This is a best-effort feed, **not** guaranteed complete coverage. Only Japan official schedule list is parsed. Weverse is a manual link. Locally edited entries are stored in browser localStorage, not shared across devices.
