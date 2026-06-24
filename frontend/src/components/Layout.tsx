import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useWebSocketConnection } from "../hooks/useWebSocket";
import { useSettingsStore } from "../store/settings";
import { useUiStore } from "../store/ui";

// CHỈ UI điều hướng — KHÔNG đổi route/label/chức năng. Route giữ nguyên 100%.
interface NavEntry {
  to: string;
  label: string;
  end?: boolean;
}

// Mục đơn lẻ (1 chức năng) -> hiển thị trực tiếp.
const SINGLES: NavEntry[] = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/projects", label: "Projects" },
  { to: "/video-sources", label: "Video Sources" },
];
const SINGLES_AFTER: NavEntry[] = [
  { to: "/files", label: "File Manager" },
];
const SETTINGS: NavEntry = { to: "/settings", label: "Settings" };

// Nhóm CÓ ≥2 chức năng -> menu con thu gọn/mở rộng.
const GROUPS: { label: string; items: NavEntry[] }[] = [
  { label: "Workflow", items: [
    { to: "/workflow", label: "Workflow" },
    { to: "/queue", label: "Queue" },
  ] },
  { label: "Agent", items: [
    { to: "/agent", label: "Desktop Agent" },
    { to: "/plugins", label: "Plugin Manager" },
  ] },
  { label: "Monitoring", items: [
    { to: "/logs", label: "Logs" },
    { to: "/stats", label: "Statistics" },
  ] },
];

// Ngoại lệ: External Applications -> chỉ nằm trong menu Hamburger (☰), không trên Sidebar.
const HAMBURGER: NavEntry[] = [
  { to: "/external", label: "External Applications" },
];

const LINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  `block rounded px-3 py-2 text-sm transition-colors ${
    isActive ? "bg-primary text-white" : "text-muted hover:bg-border hover:text-text"
  }`;

const SUBLINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  `block rounded px-3 py-1.5 text-sm transition-colors ${
    isActive ? "bg-primary text-white" : "text-muted hover:bg-border hover:text-text"
  }`;

function Item({ entry, onNavigate }: { entry: NavEntry; onNavigate?: () => void }) {
  return (
    <NavLink to={entry.to} end={entry.end} className={LINK_CLASS} onClick={onNavigate}>
      {entry.label}
    </NavLink>
  );
}

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
            <NavLink key={it.to} to={it.to} className={SUBLINK_CLASS} onClick={onNavigate}>
              {it.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
}

/** Cây điều hướng (mục đơn lẻ + nhóm). `includeExternal` để dùng trong Drawer (mobile/☰). */
function NavTree({
  openGroups,
  toggleGroup,
  includeExternal,
  onNavigate,
}: {
  openGroups: Record<string, boolean>;
  toggleGroup: (label: string) => void;
  includeExternal?: boolean;
  onNavigate?: () => void;
}) {
  return (
    <nav className="flex flex-col gap-1">
      {SINGLES.map((e) => (
        <Item key={e.to} entry={e} onNavigate={onNavigate} />
      ))}
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
      {SINGLES_AFTER.map((e) => (
        <Item key={e.to} entry={e} onNavigate={onNavigate} />
      ))}
      <Item entry={SETTINGS} onNavigate={onNavigate} />
      {includeExternal &&
        HAMBURGER.map((e) => <Item key={e.to} entry={e} onNavigate={onNavigate} />)}
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
      className="rounded p-1.5 text-text hover:bg-border"
    >
      ☰
    </button>
  );

  return (
    <div className="flex min-h-screen">
      {/* Sidebar cố định (desktop) */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-surface p-4 md:flex">
        <div className="mb-6 flex items-center justify-between px-2">
          <div>
            <div className="text-lg font-bold text-text">AI Video</div>
            <div className="text-xs text-muted">Platform V2</div>
          </div>
          {hamburgerBtn}
        </div>
        <NavTree openGroups={openGroups} toggleGroup={toggleGroup} />
        <div className="mt-6">{wsStatus}</div>
      </aside>

      {/* Thanh trên cùng (mobile) với ☰ */}
      <div className="fixed inset-x-0 top-0 z-30 flex items-center justify-between border-b border-border bg-surface px-4 py-2 md:hidden">
        <div className="text-sm font-bold text-text">AI Video Platform V2</div>
        {hamburgerBtn}
      </div>

      {/* Drawer (☰): mobile = toàn bộ nav + External; desktop = External Applications */}
      {drawerOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50"
          onClick={() => setDrawerOpen(false)}
        >
          <div
            className="flex h-full w-72 max-w-[80%] flex-col border-r border-border bg-surface p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between px-2">
              <div className="text-lg font-bold text-text">AI Video</div>
              <button
                onClick={() => setDrawerOpen(false)}
                aria-label="Đóng menu"
                className="rounded p-1 text-muted hover:bg-border hover:text-text"
              >
                ✕
              </button>
            </div>
            {/* Mobile: hiện toàn bộ nav (sidebar ẩn). Desktop: ẩn (đã có sidebar). */}
            <div className="md:hidden">
              <NavTree
                openGroups={openGroups}
                toggleGroup={toggleGroup}
                onNavigate={() => setDrawerOpen(false)}
              />
              <div className="my-2 border-t border-border" />
            </div>
            {/* External Applications luôn nằm trong ☰ */}
            <div className="text-xs uppercase tracking-wide text-muted">Khác</div>
            <nav className="mt-1 flex flex-col gap-1">
              {HAMBURGER.map((e) => (
                <Item key={e.to} entry={e} onNavigate={() => setDrawerOpen(false)} />
              ))}
            </nav>
            <div className="mt-auto md:hidden">{wsStatus}</div>
          </div>
        </div>
      )}

      <main className="flex-1 overflow-auto p-6 pt-16 md:pt-6">
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
