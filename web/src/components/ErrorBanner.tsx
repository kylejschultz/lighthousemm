export default function ErrorBanner({error}:{error:any}) {
  const msg = (error && (error.message || String(error))) || "Unknown error";
  return <div style={{background:"#fee2e2", border:"1px solid #fecaca", color:"#7f1d1d", padding:8, borderRadius:8}}>Error: {msg}</div>;
}
