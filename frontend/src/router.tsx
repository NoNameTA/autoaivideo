import { createBrowserRouter } from "react-router-dom";
import { Layout } from "./components/Layout";
import { BatchView } from "./pages/BatchView";
import { CreateBatch } from "./pages/CreateBatch";
import { Dashboard } from "./pages/Dashboard";
import { DesktopAgent } from "./pages/DesktopAgent";
import { ExternalApps } from "./pages/ExternalApps";
import { FileManager } from "./pages/FileManager";
import { JobDetail } from "./pages/JobDetail";
import { Logs } from "./pages/Logs";
import { Plugins } from "./pages/Plugins";
import { ProjectDetail } from "./pages/ProjectDetail";
import { Projects } from "./pages/Projects";
import { Queue } from "./pages/Queue";
import { Settings } from "./pages/Settings";
import { Statistics } from "./pages/Statistics";
import { Workflow } from "./pages/Workflow";

export const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <Layout />,
      children: [
        { index: true, element: <Dashboard /> },
        { path: "projects", element: <Projects /> },
        { path: "projects/:id", element: <ProjectDetail /> },
        { path: "projects/:id/batches/new", element: <CreateBatch /> },
        { path: "batches/:id", element: <BatchView /> },
        { path: "jobs/:id", element: <JobDetail /> },
        { path: "workflow", element: <Workflow /> },
        { path: "queue", element: <Queue /> },
        { path: "files", element: <FileManager /> },
        { path: "agent", element: <DesktopAgent /> },
        { path: "external", element: <ExternalApps /> },
        { path: "plugins", element: <Plugins /> },
        { path: "logs", element: <Logs /> },
        { path: "stats", element: <Statistics /> },
        { path: "settings", element: <Settings /> },
      ],
    },
  ],
  { basename: import.meta.env.BASE_URL },
);
