export default function TMDBResultCard({r}:{r:any}) {
  const title = r.title || r.name;
  const date = r.release_date || r.first_air_date || "";
  const mt = r.media_type || (r.first_air_date ? "tv" : "movie");
  return (
    <div style={{padding:12, border:"1px solid #e5e7eb", borderRadius:8}}>
      <div style={{fontWeight:700}}>{title} <small>({mt})</small></div>
      {date ? <div style={{opacity:.8}}>{date}</div> : null}
      {r.overview ? <div style={{marginTop:4, opacity:.9}}>{r.overview}</div> : null}
    </div>
  );
}
