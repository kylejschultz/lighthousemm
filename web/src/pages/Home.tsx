import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, Statistic, Row, Col } from "antd";

export default function Home() {
  const { data: health } = useQuery({ queryKey:["health"], queryFn: api.health });
  const { data: disks } = useQuery({ queryKey:["disks"], queryFn: api.disks.list });
  return (
    <Row gutter={[16,16]}>
      <Col span={24}>
        <Card><pre style={{margin:0}}>Health: {JSON.stringify(health, null, 2)}</pre></Card>
      </Col>
      <Col span={8}><Card><Statistic title="Disks" value={disks?.total ?? 0} /></Card></Col>
    </Row>
  );
}
