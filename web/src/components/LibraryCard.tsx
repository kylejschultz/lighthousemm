export default function LibraryCard({lib}:{lib:any}) {
  return (
    <a href={`/libraries/${lib.id}`} style={{display:"block", padding:12, border:"1px solid #e5e7eb", borderRadius:8, textDecoration:"none", color:"inherit"}}>
      <div style={{fontWeight:700}}>{lib.name} <small>({lib.type})</small></div>
      <div style={{opacity:.8}}>Disk #{lib.root_disk_id} / {lib.root_subdir}</div>
    </a>
  );
}
