import { useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, Form, Input, Select, InputNumber, Button, Space, Typography, message } from "antd";

const LVL = ["DEBUG","INFO","WARNING","ERROR","CRITICAL"];

export default function Settings() {
  const { data: cfg, refetch } = useQuery({ queryKey:["config"], queryFn: api.config });
  const [form] = Form.useForm();

  const mut = useMutation({
    mutationFn: (payload:any) => api.system.updateConfig(payload),
    onSuccess: () => { message.success("Saved"); refetch(); },
    onError: (e:any) => message.error(e.message || "Save failed"),
  });

  // Keep the form in sync with the fetched config
  useEffect(() => {
    if (!cfg) return;
    form.setFieldsValue({
      tmdb_api_key: cfg.tmdb_api_key || "",
      log_level: cfg.log_level || "INFO",
      log_max_mb: cfg.log_max_bytes ? Math.round(Number(cfg.log_max_bytes)/1_000_000) : 10,
      log_backups: cfg.log_backups ?? 5,
      cors_allowed_origins: (cfg.cors_allowed_origins || []).join(", "),
    });
  }, [cfg, form]);

  const onFinish = (vals:any) => {
    const payload:any = { ...vals };
    if (typeof payload.cors_allowed_origins === "string") {
      payload.cors_allowed_origins = payload.cors_allowed_origins
        .split(",")
        .map((s:string)=>s.trim())
        .filter(Boolean);
    }
    // accept MB; backend converts to bytes
    if (payload.log_max_mb) {
      payload.log_max_mb = Number(payload.log_max_mb);
    }
    mut.mutate(payload);
  };

  return (
    <Space direction="vertical" size={16} style={{width:"100%"}}>
      <Card title="Application Settings">
        <Form form={form} layout="vertical" initialValues={{
          tmdb_api_key: "",
          log_level: "INFO",
          log_max_mb: 10,
          log_backups: 5,
          cors_allowed_origins: "",
        }} onFinish={onFinish}>
          <Form.Item label="TMDB API Key" name="tmdb_api_key">
            <Input.Password placeholder="••••••••" autoComplete="off" />
          </Form.Item>

          <Form.Item label="Log Level" name="log_level">
            <Select options={LVL.map(x=>({value:x,label:x}))} style={{maxWidth:220}} />
          </Form.Item>

          <Form.Item label="Log File Size (MB)" name="log_max_mb">
            <InputNumber min={1} step={1} style={{maxWidth:260}} />
          </Form.Item>

          <Form.Item label="Log File Backups" name="log_backups">
            <InputNumber min={0} max={20} style={{maxWidth:260}} />
          </Form.Item>

          <Form.Item label="Allowed Origins (comma-separated)" name="cors_allowed_origins">
            <Input placeholder="https://lhmm.dev, http://localhost:5173, http://127.0.0.1:5173" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={mut.isPending}>Save</Button>
              <Button onClick={()=>form.resetFields()}>Reset</Button>
            </Space>
          </Form.Item>

          <Typography.Text type="secondary">
            Note: CORS origin changes require a backend restart to fully apply.
          </Typography.Text>
        </Form>
      </Card>

      <Card title="Current Config (read-only)">
        <pre style={{margin:0}}>{JSON.stringify(cfg, null, 2)}</pre>
      </Card>
    </Space>
  );
}
