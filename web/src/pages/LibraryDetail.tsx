import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export default function LibraryDetail() {
  const { id } = useParams();
  const libId = Number(id);
  const { data: lib, isLoading, error } = useQuery({ queryKey:["library", libId], queryFn: () => api.libraries.get(libId), enabled: !!libId });
  if (!libId) return <div>Invalid library id.</div>;
  if (isLoading) return <div>Loading library…</div>;
  if (error) return <div>Failed to load library.</div>;
  const previewPath = `${lib.root_disk?.mount_path || ""}/${lib.root_subdir || ""}`.replace(/\\/g, "/");
  return (
    <div>
      <h2>{lib.name} <small>({lib.type})</small></h2>
      <div style={{opacity:.8, marginBottom:16}}>Root: {previewPath}</div>
      <section>
        <h3>Items</h3>
        <div style={{opacity:.6}}>Items endpoint not implemented yet; will appear here once scanner lands.</div>
      </section>
      <section style={{marginTop:16}}>
        <h3>Recent scans</h3>
        <div style={{opacity:.6}}>Scan history will appear here once implemented.</div>
      </section>
    </div>
  );
}
