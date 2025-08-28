import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider, theme as antdTheme } from "antd";
import App from "./App";
import "antd/dist/reset.css";
import "./index.css";

const qc = new QueryClient();

function AppWithTheme() {
  const initialDark =
    (localStorage.getItem("lhmm.theme") || "").toLowerCase() === "dark" ||
    document.documentElement.getAttribute("data-theme") === "dark";
  const [dark, setDark] = useState<boolean>(initialDark);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "");
    localStorage.setItem("lhmm.theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    const onTheme = (e: any) => setDark(!!(e.detail?.dark));
    window.addEventListener("lhmm-theme", onTheme as EventListener);
    return () => window.removeEventListener("lhmm-theme", onTheme as EventListener);
  }, []);

  return (
    <ConfigProvider
      theme={{
        algorithm: dark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: {
          // primary palette: AntD Geek Blue
          colorPrimary: "#1677ff",
          // dark navy surface tones (works under both algorithms)
          colorBgLayout: dark ? "#0e1624" : undefined,     // page background
          colorBgContainer: dark ? "#141b2b" : undefined,  // cards/panels
          colorBorderSecondary: dark ? "#202836" : undefined,
          borderRadius: 12,
        },
      }}
    >
      <QueryClientProvider client={qc}>
        <App />
      </QueryClientProvider>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppWithTheme />
  </React.StrictMode>
);
