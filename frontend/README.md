# Frontend — AI Video Platform V2

Vite + React + TypeScript + Tailwind. Xem hướng dẫn ở [`../INSTALL.md`](../INSTALL.md).

## Lệnh

```bash
npm install      # hoặc npm ci (clean)
npm run dev      # http://localhost:5173 (proxy /api,/ws -> :8000)
npm run build    # -> dist/ (kèm 404.html SPA fallback cho GitHub Pages)
npm run lint
```

## GitHub Pages

Deploy qua workflow `.github/workflows/frontend-pages.yml` (base = `/<tên-repo>/`).
Cấu hình backend self-host trong **Settings → API Base URL** trên giao diện.

Site (sau khi bật Pages): https://nonameta.github.io/autoaivideo/

> Deploy tự động qua GitHub Actions khi push vào `main` (frontend).
