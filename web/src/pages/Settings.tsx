import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, Descriptions } from "antd";

export default function Settings() {
  const { data: cfg } = useQuery({ queryKey:["config"], queryFn: api.config });
  return (
    <Card title="Settings (read-only)">
      <pre style={{margin:0}}>{JSON.stringify(cfg, null, 2)}</pre>
    </Card>
  );
}
