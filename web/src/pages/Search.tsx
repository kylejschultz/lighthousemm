import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, Input, List, Typography, Space } from "antd";

export default function Search() {
  const [sp] = useSearchParams();
  const initial = sp.get("q") || "";
  const [q, setQ] = useState(initial);
  const { data, refetch, isFetching } = useQuery({
    queryKey:["tmdb","search",q,"multi"],
    queryFn: () => api.tmdb.search(q.trim(), "multi"),
    enabled: false,
  });
  useEffect(()=>{ if (initial) refetch(); }, []);
  const results = data?.results || [];

  return (
    <Space direction="vertical" size={16} style={{width:"100%"}}>
      <Card title="TMDB Search">
        <Input.Search
          value={q}
          onChange={e=>setQ(e.target.value)}
          placeholder="Search movies/TV…"
          loading={isFetching}
          enterButton="Search"
          onSearch={()=>{ if(q.trim()) refetch(); }}
        />
      </Card>

      <Card title="Results">
        <List
          loading={isFetching}
          dataSource={results}
          locale={{emptyText: "No results."}}
          renderItem={(r:any)=>(
            <List.Item>
              <List.Item.Meta
                title={<Space><Typography.Text strong>{r.title || r.name}</Typography.Text><Typography.Text type="secondary">({r.media_type})</Typography.Text></Space>}
                description={<Typography.Text type="secondary">{r.release_date || r.first_air_date || ""}</Typography.Text>}
              />
              {r.overview ? <div style={{maxWidth:640}}>{r.overview}</div> : null}
            </List.Item>
          )}
        />
      </Card>
    </Space>
  );
}
