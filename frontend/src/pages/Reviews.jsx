import { useCallback, useState } from 'react'
import { api } from '../api/client'
import { Money, StatusBadge } from '../components/StatusBadge'
import { EmptyState, ErrorState, LoadingState } from '../components/State'
import { useLoad } from '../hooks'

export default function Reviews(){const load=useCallback(()=>api.getReviews(),[]);const {loading,data,error}=useLoad(load);const [resolved,setResolved]=useState({}); if(loading)return <LoadingState/>;if(error)return <ErrorState message={error}/>; const items=data.items.map(r=>resolved[r.review_id]||r); async function decide(id,outcome){const review=await api.decideReview(id,{outcome});setResolved(s=>({...s,[id]:review}))} return <section className="panel"><p className="eyebrow">HUMAN-IN-THE-LOOP</p><h2>Human Reviews</h2>{!items.length?<EmptyState message="No reviews awaiting a decision."/>:<div className="review-list">{items.map(r=><article className="review-card" key={r.review_id}><div><strong>{r.review_id}</strong><p>{r.action_id} · {r.customer_id} · <Money value={r.amount_minor}/></p><code>{r.reason_codes.join(', ')}</code></div><div className="review-actions"><StatusBadge value={r.status}/>{r.status==='PENDING'&&<><button onClick={()=>decide(r.review_id,'APPROVED')}>Approve review</button><button className="secondary" onClick={()=>decide(r.review_id,'REJECTED')}>Reject</button></>}</div></article>)}</div>}</section>}
