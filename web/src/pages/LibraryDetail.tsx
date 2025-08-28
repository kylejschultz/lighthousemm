import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, Button, List, Space, Typography, Tag } from "antd";

export default function LibraryDetail() {
  const { id } = useParams();
  const libId = Number(id);
  const qc = useQueryClient();

  const { data: lib } = useQuery({ queryKey:["library", libId], queryFn: () => api.libraries.get(libId), enabled: !!libId });
  const { data: items } = useQuery({ queryKey:["library-items", libId], queryFn: () => fetch(`${api.API_BASE || ""}/api/v1/libraries/${libId}/items`).then(r=>r.json()), enabled: !!libId, refetchInterval: 5000 });
  const { data: scans } = useQuery({ queryKey:["library-scans", libId], queryFn: () => fetch(`${api.API_BASE || ""}/api/v1/libraries/${libId}/scans`).then(r=>r.json()), enabled: !!libId, refetchInterval: 5000 });

  const scanMut = useMutation({
    mutationFn: async () => {
      await fetch(`${api.API_BASE || ""}/api/v1/libraries/${libId}/scan`, { method: "POST" });
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey:["library-scans", libId]});
      qc.invalidateQueries({queryKey:["library-items", libId]});
    }
  });

  if (!libId) return <div>Invalid library id.</div>;

  return (
    <Space direction="vertical" size={16} style={{width:"100%"}}>
      <Card title={`${lib?.name || "Library"} (${lib?.type || ""})`} extra={<Button type="primary" loading={scanMut.isPending} onClick={()=>scanMut.mutate()}>Start Scan</Button>}>
        <div><Typography.Text type="secondary">Root:</Typography.Text> {`${lib?.root_disk?.mount_path || ""}/${lib?.root_subdir || ""}`}</div>
      </Card>

      <Card title="Recent scans" bodyStyle={{paddingTop:8}}>
        <List
          dataSource={scans?.items || []}
          locale={{emptyText:"No scans yet."}}
          renderItem={(s:any)=>(
            <List.Item>
              <Space>
                <Tag color={s.status==="succeeded"?"green":s.status==="failed"?"red":"blue"}>{s.status}</Tag>
                <Typography.Text type="secondary">files={s.stats?.files||0} matched={s.stats?.matched||0}</Typography.Text>
                <Typography.Text type="secondary">{s.started_at} → {s.finished_at || "-"}</Typography.Text>
              </Space>
            </List.Item>
          )}
        />
      </Card>

      <Card title={`Items (${items?.total ?? 0})`} bodyStyle={{paddingTop:8}}>
        <List
          dataSource={items?.items || []}
          locale={{emptyText:"No items indexed yet."}}
          renderItem={(it:any)=>(
            <List.Item>
              <List.Item.Meta
                title={<Space>
                  <Typography.Text strong>{it.series ? `${it.series} S${String(it.season).padStart(2,"0")}E${String(it.episode).padStart(2,"0")}` : it.title}</Typography.Text>
                  {it.series ? <Tag>episode</Tag> : <Tag>movie</Tag>}
                </Space>}
                description={<Typography.Text type="secondary">{it.path}</Typography.Text>}
              />
              <div>{it.year || ""}</div>
            </List.Item>
          )}
        />
      </Card>
    </Space>
  );
}
