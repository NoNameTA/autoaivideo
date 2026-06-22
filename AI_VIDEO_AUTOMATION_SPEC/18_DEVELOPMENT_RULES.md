# 18 — DEVELOPMENT RULES

> Quy tắc code, commit, PR, review cho cả nhóm/agent AI. Bắt buộc tuân thủ.

---

## 1. Nguyên tắc vàng

1. **Spec là nguồn chân lý** — code theo bộ `AI_VIDEO_AUTOMATION_SPEC`; nếu code lệch spec, sửa spec trước (PR riêng) rồi code.
2. **Lõi không phụ thuộc External App cụ thể** — chỉ qua Plugin SDK (`08`).
3. **Free-only** — mọi phụ thuộc/dịch vụ tuân `14`.
4. **Không secret trong repo** (`11`).
5. **Không bỏ test** để merge nhanh.

## 2. Phong cách code

### Python (backend, agent)
- Python 3.11+, type hint bắt buộc, `ruff` (lint+format), `mypy` cho core.
- Async-first (FastAPI/SQLAlchemy async). Không block event loop.
- Hàm nhỏ, service tách biệt; không logic nghiệp vụ trong router.
- Lỗi: dùng exception phân loại (`TransientError`/`PermanentError`).

### TypeScript (frontend)
- Strict mode. ESLint + Prettier.
- Component hàm + hooks; state qua Zustand/TanStack Query.
- Không `any` trừ khi có lý do + comment.

## 3. Git & commit

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `ci:`.
- Commit nhỏ, một mục đích. Message rõ ràng (tiếng Việt hoặc Anh, nhất quán trong PR).
- Nhánh: `feat/<scope>-<mô-tả>`, `fix/...`.
- Không commit `data/`, `.env`, profile trình duyệt, build artefact.

## 4. Pull Request

- PR map tới 1 mục roadmap (`16`) khi có thể.
- Mô tả: mục tiêu, thay đổi chính, cách test, ảnh hưởng spec.
- Bắt buộc: CI xanh (lint + test + audit) + cập nhật `17_CHANGELOG.md`.
- ≥ 1 review (hoặc self-review checklist nếu solo) trước merge vào `main`.

## 5. Checklist review

- [ ] Theo đúng spec liên quan?
- [ ] Có test cho logic mới?
- [ ] Xử lý lỗi & phân loại Transient/Permanent đúng?
- [ ] Không rò rỉ secret / log nhạy cảm?
- [ ] Đường dẫn file validate (chống traversal)?
- [ ] Free-software gate ok (nếu thêm dependency/plugin)?
- [ ] Cập nhật CHANGELOG?

## 6. Quy tắc thêm dependency

- Lý do rõ ràng + giấy phép hợp lệ (`14`). Pin phiên bản.
- Ưu tiên thư viện đã dùng; tránh trùng lặp chức năng.

## 7. Tài liệu

- Thay đổi hành vi → cập nhật file spec tương ứng cùng PR.
- Public API/endpoint mới → cập nhật `09`/`04`.
- Plugin mới → README plugin + manifest đầy đủ (`08`,`14`).

## 8. Quy tắc cho agent AI (Claude/automation)

- Trước thao tác phá huỷ (xoá/ghi đè) phải xác nhận & kiểm tra mục tiêu.
- Không tự ý đổi kiến trúc/invariant (`01 §9`) — đề xuất trước.
- Mỗi thay đổi đi kèm cách kiểm chứng (test/chạy thử).
- Báo cáo trung thực: test fail thì nói rõ, không che giấu.
