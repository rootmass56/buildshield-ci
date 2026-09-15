import type { ReactNode } from 'react';
import { AlertTriangle, CheckCircle2, CircleDashed, FileDown } from 'lucide-react';
import type { ReportLink } from '../types/api';
import { normalizeEnumLabel } from '../utils/security';
export function ErrorPanel({message}:{message:string}){return <div className="message-panel danger" role="alert"><AlertTriangle size={18}/><span>{message}</span></div>;}
export function LoadingPanel({message='Loading…'}:{message?:string}){return <div className="message-panel" aria-live="polite"><CircleDashed className="spin" size={18}/><span>{message}</span></div>;}
export function EmptyPanel({title,detail}:{title:string;detail:string}){return <div className="empty-panel"><CheckCircle2 size={26}/><strong>{title}</strong><span>{detail}</span></div>;}
export function MetricCard({label,value,detail,icon}:{label:string;value:ReactNode;detail:string;icon?:ReactNode}){return <article className="metric-card">{icon?<div className="metric-icon">{icon}</div>:null}<span>{label}</span><strong>{value}</strong><p>{detail}</p></article>;}
export function SeverityBadge({value}:{value:string}){const normalized=normalizeEnumLabel(value);const first=normalized.split(' ')[0].toLowerCase();return <span className={`severity-badge severity-${first}`}>{normalized}</span>;}
export function StatusBadge({value,positive=false}:{value:string;positive?:boolean}){return <span className={positive?'status-badge positive':'status-badge'}>{normalizeEnumLabel(value)}</span>;}
export function ReportLinks({reports}:{reports:ReportLink[]}){if(!reports.length)return null;return <div className="report-links">{reports.map(r=><a key={`${r.run_id}-${r.filename}`} href={r.download_url} className="report-link"><FileDown size={16}/><span>{r.filename}</span></a>)}</div>;}
