import { useCallback } from 'react'
import { api } from '../api/client'
import { EmptyState, ErrorState, LoadingState } from '../components/State'
import { useLoad } from '../hooks'

export default function AuditLogs(){const load=useCallback(()=>api.getAuditLogs(),[]);const {loading,data,error}=useLoad(load);if(loading)return <LoadingState/>;if(error)return <ErrorState message={error}/>;return <section className="panel"><p className="eyebrow">APPEND-ONLY RECORD</p><h2>Audit Logs</h2>{!data.items.length?<EmptyState message="No audit records."/>:<table><thead><tr><th>Time</th><th>Audit ID</th><th>Action</th><th>Event</th><th>Payload</th></tr></thead><tbody>{data.items.map(e=><tr key={e.audit_id}><td>{new Date(e.occurred_at).toLocaleTimeString()}</td><td>{e.audit_id}</td><td>{e.action_id}</td><td>{e.event_type}</td><td><code>{JSON.stringify(e.payload)}</code></td></tr>)}</tbody></table>}</section>}
