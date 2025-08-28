import { Layout, Menu, Button } from "antd";
import {
  HomeOutlined,
  SearchOutlined,
  AppstoreOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MenuOutlined,
} from "@ant-design/icons";
import { useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

const { Header, Sider, Content } = Layout;

export default function AppLayout() {
  const nav = useNavigate();
  const loc = useLocation();
  const [collapsed, setCollapsed] = useState<boolean>(() => localStorage.getItem("lhmm.sidebar")==="1");
  useEffect(()=>localStorage.setItem("lhmm.sidebar", collapsed?"1":"0"), [collapsed]);

  const items = [
    { key: "/", icon: <HomeOutlined />, label: "Home" },
    { key: "/search", icon: <SearchOutlined />, label: "Search" },
    { key: "/libraries", icon: <AppstoreOutlined />, label: "Libraries" },
    { key: "/settings", icon: <SettingOutlined />, label: "Settings" },
  ];
  const selectedKeys = items.map(i=>i.key).includes(loc.pathname) ? [loc.pathname] : [];

  return (
    <Layout style={{minHeight: "100vh"}}>
      <Sider collapsible collapsed={collapsed} trigger={null} width={240}>
        <div
          style={{
            height: collapsed ? 56 : 150,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: collapsed ? "0 12px" : "12px",
            color: "#fff",
          }}
        >
          {collapsed ? (
            <MenuOutlined style={{ color: "#fff", fontSize: 18 }} />
          ) : (
            <img
              src="https://raw.githubusercontent.com/kylejschultz/lighthousemm/main/images/logo.png"
              alt="Lighthouse"
              style={{ height: 125, maxWidth: "100%", objectFit: "contain", display: "block" }}
            />
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          items={items}
          onClick={(e)=>nav(e.key)}
        />
      </Sider>
      <Layout>
        <Header style={{display:"flex", gap:8, alignItems:"center", paddingInline:12, background:"transparent"}}>
          <Button
            type="default"
            size="small"
            onClick={()=>setCollapsed(c=>!c)}
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            style={{borderRadius: 10}}
          />
          <div style={{marginLeft:"auto"}} />
        </Header>
        <Content style={{padding:16}}>
          <div style={{maxWidth: 1200, margin: "0 auto"}}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
