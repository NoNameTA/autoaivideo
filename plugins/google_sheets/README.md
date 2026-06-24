# Plugin: Google Sheets (cloud-api)

Adapter **đầu tiên** dùng Cloud Adapter Framework (SPEC 06 §9–§11). Dùng API Google Sheets chính
thức qua `gspread` với **access token ngắn hạn** do Backend cấp JIT (Service Account key KHÔNG ở
Agent — SPEC 11 §3.3).

## Capabilities
`cloud.google_sheets.read` · `.write` · `.append` · `.update_cell` · `.update_row`

## Cài đặt (Agent)
```
pip install -r plugins/google_sheets/requirements.txt
```

## Cấu hình (config — KHÔNG hard-code, xem config.schema.json)
- `spreadsheet_id`, `worksheet`, `range`, `values`, `cell`, `value`, `row_index`, `value_input_option`.
- Bí mật qua `credential_ref`/`connection_id` (Credential Store / Connection Manager). KHÔNG đặt key ở đây.

## Credential (SPEC 11 §3, SETUP_GOOGLE_SHEETS.md)
- V2.0: `service_account`. Owner đặt Service Account JSON tại `.secrets/gsa.json` (gitignored) hoặc
  Credential Store (khi có `MASTER_KEY`). Quản lý Connection + Test kết nối ở trang **External Apps**.
