import { NavLink, Route, Routes } from 'react-router-dom'
import { Activity, Bot, ClipboardCheck, LayoutDashboard, ShieldCheck } from 'lucide-react'
import { mockMode } from './api/client'
import Overview from './pages/Overview'
import Playground from './pages/Playground'
import Reviews from './pages/Reviews'
import AuditLogs from './pages/AuditLogs'

const links = [[ '/', 'Overview', LayoutDashboard ], ['/playground', 'Agent Playground', Bot], ['/reviews', 'Human Reviews', ClipboardCheck], ['/audit-logs', 'Audit Logs', Activity]]
export default function App() { return <div className="app-shell"><aside><div className="brand"><ShieldCheck/> <span>ProofGate</span><small>AI</small></div><nav>{links.map(([to,label,Icon]) => <NavLink end={to==='/' } key={to} to={to}><Icon size={18}/>{label}</NavLink>)}</nav><div className="side-note"><span className="pulse"/> Protected actions require verification</div></aside><main><header><div><p className="eyebrow">AI ACTION SECURITY</p><h1>Verification control center</h1></div>{mockMode && <span className="mock-label">Development mock data</span>}</header><Routes><Route path="/" element={<Overview/>}/><Route path="/playground" element={<Playground/>}/><Route path="/reviews" element={<Reviews/>}/><Route path="/audit-logs" element={<AuditLogs/>}/></Routes></main></div> }
