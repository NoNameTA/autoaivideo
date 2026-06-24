import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useWebSocketConnection } from "../hooks/useWebSocket";
import { useSettingsStore } from "../store/settings";
import { useUiStore } from "../store/ui";

// CHỈ UI điều hướng — KHÔNG đổi route/label/chức năng. Route giữ nguyên 100%.
// Toàn bộ Navigation nằm TRONG menu Hamburger (☰); Sidebar/Top bar chỉ còn Logo + ☰.
interface NavEntry {
  to: string;
  label: string;
  end?: boolean;
}

// Toàn bộ chức năng gom thành nhóm thu gọn (collapsible). KHÔNG bỏ sót mục nào.
// Mọi route hiện có đều có mặt: Dashboard, Projects, Video Sources, Workflow, Queue,
// Logs, Statistics, Desktop Agent, Plugin Manager, File Manager, External Applications, Settings.
const GROUPS: { label: string; items: NavEntry[] }[] = [
  { label: "Dashboard", items: [
    { to: "/", label: "Dashboard", end: true },
  ] },
  { label: "Projects", items: [
    { to: "/projects", label: "Projects" },
  ] },
  { label: "Workflow", items: [
    { to: "/workflow", label: "Workflow" },
    { to: "/queue", label: "Queue" },
  ] },
  { label: "Video", items: [
    { to: "/video-sources", label: "Video Sources" },
  ] },
  { label: "Monitoring", items: [
    { to: "/logs", label: "Logs" },
    { to: "/stats", label: "Statistics" },
  ] },
  { label: "Agent", items: [
    { to: "/agent", label: "Desktop Agent" },
    { to: "/plugins", label: "Plugin Manager" },
  ] },
  { label: "Files", items: [
    { to: "/files", label: "File Manager" },
  ] },
  { label: "Integration", items: [
    { to: "/external", label: "External Applications" },
  ] },
  { label: "Settings", items: [
    { to: "/settings", label: "Settings" },
  ] },
];

const SUBLINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  `block rounded px-3 py-1.5 text-sm transition-colors ${
    isActive ? "bg-primary text-white" : "text-muted hover:bg-border hover:text-text"
  }`;

function Group({
  label,
  items,
  open,
  onToggle,
  onNavigate,
}: {
  label: string;
  items: NavEntry[];
  open: boolean;
  onToggle: () => void;
  onNavigate?: () => void;
}) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-1 rounded px-3 py-2 text-sm font-medium text-text hover:bg-border"
        aria-expanded={open}
      >
        <span className="w-3 text-muted transition-transform">{open ? "▾" : "▸"}</span>
        {label}
      </button>
      {open && (
        <div className="ml-3 flex flex-col gap-0.5 border-l border-border pl-2">
          {items.map((it) => (
            <NavLink
              key={it.to}
              to={it.to}
              end={it.end}
              className={SUBLINK_CLASS}
              onClick={onNavigate}
            >
              {it.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
}

/** Cây điều hướng đầy đủ — chỉ render bên trong Drawer (☰). */
function NavTree({
  openGroups,
  toggleGroup,
  onNavigate,
}: {
  openGroups: Record<string, boolean>;
  toggleGroup: (label: string) => void;
  onNavigate?: () => void;
}) {
  return (
    <nav className="flex flex-col gap-1">
      {GROUPS.map((g) => (
        <Group
          key={g.label}
          label={g.label}
          items={g.items}
          open={openGroups[g.label] ?? true}
          onToggle={() => toggleGroup(g.label)}
          onNavigate={onNavigate}
        />
      ))}
    </nav>
  );
}

const GROUPS_KEY = "nav-open-groups";

export function Layout() {
  const wsConnected = useUiStore((s) => s.wsConnected);
  const token = useSettingsStore((s) => s.token);
  const theme = useSettingsStore((s) => s.theme);

  useWebSocketConnection();

  useEffect(() => {
    document.documentElement.className = theme;
  }, [theme]);

  // Ghi nhớ trạng thái mở/đóng nhóm trong phiên (sessionStorage).
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>(() => {
    try {
      const raw = sessionStorage.getItem(GROUPS_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  });
  const toggleGroup = (label: string) =>
    setOpenGroups((prev) => {
      const next = { ...prev, [label]: !(prev[label] ?? true) };
      try {
        sessionStorage.setItem(GROUPS_KEY, JSON.stringify(next));
      } catch {
        /* phiên không hỗ trợ -> bỏ qua */
      }
      return next;
    });

  const [drawerOpen, setDrawerOpen] = useState(false);

  // Đóng Drawer bằng phím Esc.
  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setDrawerOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  const wsStatus = (
    <div className="px-3 text-xs">
      <span className={wsConnected ? "text-success" : "text-muted"}>
        ● {wsConnected ? "Realtime đã kết nối" : "Realtime ngắt"}
      </span>
    </div>
  );

  const hamburgerBtn = (
    <button
      onClick={() => setDrawerOpen(true)}
      aria-label="Mở menu"
      aria-expanded={drawerOpen}
      className="rounded p-1.5 text-lg leading-none text-text hover:bg-border"
    >
      ☰
    </button>
  );

  return (
    <div className="flex min-h-screen flex-col">
      {/* Thanh trên cùng (mọi kích thước màn hình): CHỈ ☰ + Logo. Không mục chức năng nào. */}
      <header className="fixed inset-x-0 top-0 z-30 flex items-center justify-between border-b border-border bg-surface px-4 py-2">
        <div className="flex items-center gap-3">
          {hamburgerBtn}
          <div className="flex items-baseline gap-2">
            <span className="text-base font-bold text-text">AI Video</span>
            <span className="hidden text-xs text-muted sm:inline">Platform V2</span>
          </div>
        </div>
        <div className="hidden sm:block">{wsStatus}</div>
      </header>

      {/* Drawer (☰): chứa TOÀN BỘ Navigation. Đóng ☰ -> nav biến mất hoàn toàn. */}
      {drawerOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50"
          onClick={() => setDrawerOpen(false)}
        >
          <div
            className="flex h-full w-72 max-w-[80%] flex-col border-r border-border bg-surface p-4"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-label="Menu điều hướng"
          >
            <div className="mb-4 flex items-center justify-between px-2">
              <div>
                <div className="text-lg font-bold text-text">AI Video</div>
                <div className="text-xs text-muted">Platform V2</div>
              </div>
              <button
                onClick={() => setDrawerOpen(false)}
                aria-label="Đóng menu"
                className="rounded p-1 text-muted hover:bg-border hover:text-text"
              >
                ✕
              </button>
            </div>
            <div className="-mr-2 flex-1 overflow-y-auto pr-2">
              <NavTree
                openGroups={openGroups}
                toggleGroup={toggleGroup}
                onNavigate={() => setDrawerOpen(false)}
              />
            </div>
            <div className="mt-4 border-t border-border pt-3">{wsStatus}</div>
          </div>
        </div>
      )}

      {/* Nội dung trang — toàn chiều rộng, chừa chỗ cho thanh trên cùng. */}
      <main className="flex-1 overflow-auto p-6 pt-16">
        {!token && (
          <div className="mb-4 rounded border-l-4 border-warning bg-surface px-4 py-2 text-sm text-text">
            Chưa cấu hình token. Vào <span className="font-semibold">Settings</span> để nhập token
            chủ sở hữu trước khi gọi API.
          </div>
        )}
        {token && !wsConnected && (
          <div className="mb-4 rounded border-l-4 border-info bg-surface px-4 py-2 text-sm text-text">
            Đang kết nối lại realtime…
          </div>
        )}
        <Outlet />
      </main>
    </div>
  );
}
