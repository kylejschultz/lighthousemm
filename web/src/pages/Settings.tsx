import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import {
  App as AntdApp,
  Card, Form, Input, Select, InputNumber, Button, Space, Typography, Row, Col,
} from "antd";

const LVL = ["DEBUG","INFO","WARNING","ERROR","CRITICAL"];

export default function Settings() {
  const { message } = AntdApp.useApp();
  const qc = useQueryClient();
  const { data: cfg, refetch } = useQuery({ queryKey:["config"], queryFn: api.config });
  const [appForm] = Form.useForm();
  const [sabForm] = Form.useForm();
  const [testing, setTesting] = useState(false);
  const [savingSab, setSavingSab] = useState(false);

  const mutApp = useMutation({
    mutationFn: (payload:any) => api.system.updateConfig(payload),
    onSuccess: async () => { message.success("Settings saved"); await refetch(); },
    onError: (e:any) => message.error(e?.message || "Save failed"),
  });

  useEffect(() => {
    if (!cfg) return;
    // App settings
    appForm.setFieldsValue({
      tmdb_api_key: cfg.tmdb_api_key || "",
      log_level: cfg.log_level || "INFO",
      log_max_mb: cfg.log_max_bytes ? Math.round(Number(cfg.log_max_bytes)/1_000_000) : 10,
      log_backups: cfg.log_backups ?? 5,
      cors_allowed_origins: (cfg.cors_allowed_origins || []).join(", "),
    });
    // SAB settings
    sabForm.setFieldsValue({
      sab_url: cfg.sab_url || "",
      sab_api_key: cfg.sab_api_key || "",
      sab_category_movies: cfg.sab_category_movies || "movies",
      sab_category_tv: cfg.sab_category_tv || "tv",
    });
  }, [cfg, appForm, sabForm]);

  const onSaveApp = async (vals:any) => {
    const payload:any = { ...vals };
    if (typeof payload.cors_allowed_origins === "string") {
      payload.cors_allowed_origins = payload.cors_allowed_origins
        .split(",").map((s:string)=>s.trim()).filter(Boolean);
    }
    if (payload.log_max_mb) payload.log_max_mb = Number(payload.log_max_mb);
    await mutApp.mutateAsync(payload);
  };

  const saveSab = async () => {
    setSavingSab(true);
    try {
      const vals = await sabForm.validateFields();
      const patch:any = {};
      ["sab_url","sab_api_key","sab_category_movies","sab_category_tv"].forEach(k => patch[k] = vals[k]);
      await api.system.updateConfig(patch);
      message.success("SAB settings saved");
      await refetch();
    } catch (e:any) {
      if (e?.errorFields) {
        message.error("Please correct SAB form errors");
      } else {
        message.error(e?.message || "Save failed");
      }
    } finally {
      setSavingSab(false);
    }
  };

  const testSab = async () => {
    setTesting(true);
    try {
      // Ensure config has the latest SAB values before hitting backend
      const vals = sabForm.getFieldsValue();
      const patch:any = {};
      let changed = false;
      ["sab_url","sab_api_key","sab_category_movies","sab_category_tv"].forEach(k => {
        const cur = (cfg?.[k] ?? "");
        if ((vals?.[k] ?? "") !== cur) { changed = true; patch[k] = vals[k]; }
      });
      if (changed) {
        await api.system.updateConfig(patch);
        await refetch();
      }
      const res = await api.sab.test();
      if (res?.ok) {
        message.success("SAB connection OK");
      } else {
        message.warning("SAB responded unexpectedly");
      }
    } catch (e:any) {
      const detail = e?.response?.data?.detail || e?.message || "SAB test failed";
      message.error(detail);
    } finally {
      setTesting(false);
    }
  };

  return (
    <Space direction="vertical" size={16} style={{width:"100%"}}>
      <Card title="Application Settings">
        <Form form={appForm} layout="vertical" initialValues={{
          tmdb_api_key: "",
          log_level: "INFO",
          log_max_mb: 10,
          log_backups: 5,
          cors_allowed_origins: "",
        }} onFinish={onSaveApp}>
          <Form.Item label="TMDB API Key" name="tmdb_api_key">
            <Input.Password placeholder="••••••••" autoComplete="off" />
          </Form.Item>

          <Form.Item label="Log Level" name="log_level">
            <Select options={LVL.map(x=>({value:x,label:x}))} style={{maxWidth:220}} />
          </Form.Item>

          <Form.Item label="Log File Size (MB)" name="log_max_mb" rules={[{type:"number", min:1}] }>
            <InputNumber min={1} step={1} style={{maxWidth:260}} />
          </Form.Item>

          <Form.Item label="Log File Backups" name="log_backups" rules={[{type:"number", min:0, max:20}] }>
            <InputNumber min={0} max={20} style={{maxWidth:260}} />
          </Form.Item>

          <Form.Item label="Allowed Origins (comma-separated)" name="cors_allowed_origins">
            <Input placeholder="https://lhmm.dev, http://localhost:5173, http://127.0.0.1:5173" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={mutApp.isPending}>Save</Button>
              <Button onClick={()=>appForm.resetFields()}>Reset</Button>
            </Space>
          </Form.Item>

          <Typography.Text type="secondary">
            Note: CORS origin changes require a backend restart to fully apply.
          </Typography.Text>
        </Form>
      </Card>

      <Card title="Downloads — SABnzbd">
        <Form form={sabForm} layout="vertical" initialValues={{
          sab_url: "",
          sab_api_key: "",
          sab_category_movies: "movies",
          sab_category_tv: "tv",
        }}>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label="SABnzbd URL" name="sab_url" rules={[{required:true, message:"URL required"}] }>
                <Input placeholder="http://127.0.0.1:8080" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="SABnzbd API Key" name="sab_api_key" rules={[{required:true, message:"API key required"}] }>
                <Input.Password placeholder="••••••••" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label="Movies Category" name="sab_category_movies">
                <Input placeholder="movies" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="TV Category" name="sab_category_tv">
                <Input placeholder="tv" />
              </Form.Item>
            </Col>
          </Row>
          <Space>
            <Button type="primary" onClick={saveSab} loading={savingSab}>Save</Button>
            <Button onClick={testSab} loading={testing}>Test Connection</Button>
          </Space>
        </Form>
      </Card>

      <Card title="Current Config (read-only)">
        <pre style={{margin:0}}>{JSON.stringify(cfg, null, 2)}</pre>
      </Card>
    </Space>
  );
}
