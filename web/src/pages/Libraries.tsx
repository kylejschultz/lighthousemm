import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, Form, Input, Select, Button, List, Space, Typography } from "antd";

export default function Libraries() {
  const qc = useQueryClient();
  const { data: libs } = useQuery({ queryKey:["libraries"], queryFn: api.libraries.list });
  const mut = useMutation({
    mutationFn: (payload:any) => api.libraries.create(payload),
    onSuccess: () => qc.invalidateQueries({queryKey:["libraries"]}),
  });

  return (
    <Space direction="vertical" size={16} style={{width:"100%"}}>
      <Card title="Create Library">
        <Form layout="inline" onFinish={(values)=>mut.mutate({
          name: values.name,
          type: values.type,
          root_disk_id: Number(values.disk),
          root_subdir: values.subdir,
        })}>
          <Form.Item name="name" rules={[{required:true}]}>
            <Input placeholder="Name" />
          </Form.Item>
          <Form.Item name="type" initialValue="movie">
            <Select style={{width:120}} options={[{value:"movie"},{value:"tv"}]} />
          </Form.Item>
          <Form.Item name="subdir" rules={[{required:true}]}>
            <Input placeholder="Root subdir (e.g., Movies)" />
          </Form.Item>
          <Form.Item name="disk" rules={[{required:true}]}>
            <Input placeholder="Root disk id" />
          </Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" loading={mut.isPending}>Create</Button></Form.Item>
        </Form>
      </Card>

      <Card title="Libraries">
        <List
          dataSource={(libs?.items||[])}
          locale={{emptyText:"No libraries yet."}}
          renderItem={(l:any)=>(
            <List.Item
              actions={[<a key="open" href={`/libraries/${l.id}`}>Open</a>]}
            >
              <List.Item.Meta
                title={<Space><Typography.Text strong>{l.name}</Typography.Text><Typography.Text type="secondary">({l.type})</Typography.Text></Space>}
                description={<Typography.Text type="secondary">disk #{l.root_disk_id} / {l.root_subdir}</Typography.Text>}
              />
            </List.Item>
          )}
        />
      </Card>
    </Space>
  );
}
