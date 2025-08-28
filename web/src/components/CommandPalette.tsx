import { useEffect, useState } from "react";
import { Modal, Input, List, Typography, Space, Button, Switch } from "antd";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

export default function CommandPalette() {
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [libs, setLibs] = useState<any[]>([]);
  const [tmdb, setTmdb] = useState<any[]>([]);
  const isMac = typeof navigator !== "undefined" && navigator.platform.includes("Mac");

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((isMac && e.metaKey && e.key.toLowerCase()==="k") || (!isMac && e.ctrlKey && e.key.toLowerCase()==="k")) {
        e.preventDefault(); setOpen(true);
      } else if (e.key === "Escape") { setOpen(false); }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  useEffect(()=>{ api.libraries.list().then(d=>setLibs(d.items||[])).catch(()=>{}); }, []);
  useEffect(()=>{
    const t = setTimeout(()=>{
      if (q.trim().length >= 2) {
        api.tmdb.search(q.trim(), "multi").then(d=>setTmdb(d.results||[])).catch(()=>setTmdb([]));
      } else { setTmdb([]); }
    }, 200);
    return ()=>clearTimeout(t);
  }, [q]);

  const goto = (path: string) => { setOpen(false); nav(path); };

  return (
    <>
      <Space>
        <Button onClick={()=>setOpen(true)}>[⌘/Ctrl+K] Command</Button>
        <ThemeToggle />
      </Space>
      <Modal open={open} onCancel={()=>setOpen(false)} footer={null} title="Command" width={720} destroyOnClose>
        <Input.Search
          value={q}
          onChange={e=>setQ(e.target.value)}
          placeholder="Search TMDB or navigate…"
          enterButton="Search"
          onSearch={()=>{ if(q.trim()){ goto(`/search?q=${encodeURIComponent(q.trim())}`); } }}
        />
        <div style={{marginTop:16}} />
        <Typography.Title level={5}>Libraries</Typography.Title>
        <List
          size="small"
          dataSource={libs}
          renderItem={(l:any)=>(
            <List.Item onClick={()=>goto(`/libraries/${l.id}`)} style={{cursor:"pointer"}}>
              <Space><Typography.Text strong>{l.name}</Typography.Text><Typography.Text type="secondary">({l.type})</Typography.Text></Space>
            </List.Item>
          )}
        />
        {tmdb.length>0 && <>
          <div style={{marginTop:16}} />
          <Typography.Title level={5}>TMDB</Typography.Title>
          <List
            size="small"
            dataSource={tmdb.slice(0,10)}
            renderItem={(r:any)=>(
              <List.Item style={{cursor:"default"}}>
                <Space><Typography.Text strong>{r.title || r.name}</Typography.Text><Typography.Text type="secondary">{r.release_date || r.first_air_date || ""}</Typography.Text></Space>
              </List.Item>
            )}
          />
        </>}
      </Modal>
    </>
  );
}

function ThemeToggle() {
  const [dark, setDark] = useState(()=>document.documentElement.getAttribute("data-theme")==="dark");
  useEffect(()=>{
    document.documentElement.setAttribute("data-theme", dark? "dark":"");
    localStorage.setItem("lhmm.theme", dark? "dark":"light");
    window.dispatchEvent(new CustomEvent("lhmm-theme", { detail: { dark } }));
  }, [dark]);
  return (
    <Space>
      <Typography.Text type="secondary">Dark</Typography.Text>
      <Switch checked={dark} onChange={setDark} />
    </Space>
  );
}
