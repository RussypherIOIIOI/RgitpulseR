import Link from "next/link";
import { Frame } from "./_components/site";

export default function NotFound() {
  return <Frame><section className="band state-band"><div className="band-inner not-found">
    <p className="readout not-found-code" aria-hidden="true">404 · No record</p>
    <h1>This page isn’t in the snapshot</h1>
    <p>The address doesn’t match a GitPulse page. The dashboard, activity table and method notes all live on the home page.</p>
    <div className="hero-actions"><Link className="btn btn-primary" href="/">Open the dashboard</Link>
      <Link className="btn" href="/#methodology">How the metrics work</Link></div>
  </div></section></Frame>;
}
