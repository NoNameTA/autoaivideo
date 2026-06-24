import { useEffect } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useWebSocketConnection } from "../hooks/useWebSocket";
import { useSettingsStore } from "../store/settings";
import { useUiStore } from "../store/ui";

// Khu vực website bắt buộc (SPEC 12 §5 + yêu cầu Website).
const NAV = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/projects", label: "Projects" },
  { to: "/video-sources", label: "Video Sources" },
  { to: "/workflow", label: "Workflow" },
  { to: "/queue", label: "Queue" },
  { to: "/files", label: "File Manager" },
  { to: "/agent", label: "Desktop Agent" },
  { to: "/external", label: "External Applications" },
  { to: "/plugins", label: "Plugin Manager" },
  { to: "/logs", label: "Logs" },
  { to: "/stats", label: "Statistics" },
  { to: "/settings", label: "Settings" },
];

export function Layout() {
  const wsConnected = useUiStore((s) => s.wsConnected);
  const token = useSettingsStore((s) => s.token);
  const theme = useSettingsStore((s) => s.theme);

  useWebSocketConnection();

  useEffect(() => {
    document.documentElement.className = theme;
  }, [theme]);

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 shrink-0 border-r border-border bg-surface p-4">
        <div className="mb-6 px-2">
          <div className="text-lg font-bold text-text">AI Video</div>
          <div className="text-xs text-muted">Platform V2</div>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-primary text-white"
                    : "text-muted hover:bg-border hover:text-text"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-6 px-3 text-xs">
          <span className={wsConnected ? "text-success" : "text-muted"}>
            ● {wsConnected ? "Realtime đã kết nối" : "Realtime ngắt"}
          </span>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6">
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
