const actions = [
  { action_id: 'act_001', customer_id: 'cus_001', order_id: 'ord_001', verification_decision: 'APPROVE', risk_level: 'MEDIUM', execution_status: 'EXECUTED', reason_codes: ['ELIGIBLE'], amount_minor: 129900, created_at: '2026-10-18T09:10:00Z' },
  { action_id: 'act_002', customer_id: 'cus_002', order_id: 'ord_002', verification_decision: 'REVIEW', risk_level: 'HIGH', execution_status: 'PENDING_REVIEW', reason_codes: ['AUTO_CEILING_EXCEEDED'], amount_minor: 250000, created_at: '2026-10-18T09:15:00Z' },
  { action_id: 'act_003', customer_id: 'cus_003', order_id: 'ord_003', verification_decision: 'BLOCK', risk_level: 'LOW', execution_status: 'NOT_EXECUTED', reason_codes: ['REFUND_WINDOW_EXPIRED'], amount_minor: 99900, created_at: '2026-10-18T09:20:00Z' },
]
const reviews = [{ review_id: 'rev_001', action_id: 'act_002', status: 'PENDING', outcome: null, customer_id: 'cus_002', reason_codes: ['AUTO_CEILING_EXCEEDED'], amount_minor: 250000 }]
const audit = actions.flatMap((a, i) => [{ audit_id: `aud_${String(i * 2 + 1).padStart(3, '0')}`, action_id: a.action_id, event_type: 'ACTION_RECEIVED', occurred_at: a.created_at, payload: { order_id: a.order_id } }, { audit_id: `aud_${String(i * 2 + 2).padStart(3, '0')}`, action_id: a.action_id, event_type: 'VERIFICATION_COMPLETED', occurred_at: a.created_at, payload: { decision: a.verification_decision, reason_codes: a.reason_codes } }])
const later = value => new Promise(resolve => setTimeout(() => resolve(structuredClone(value)), 180))
export const mockApi = {
  getReviews: () => later({ items: reviews }), getAuditLogs: () => later({ items: audit }),
  getMetrics: () => later({ window: 'demo fixtures', counts: { total: 3, approved: 1, blocked: 1, review: 1 }, verification_latency_ms: { p50: 82, p95: 126 } }),
  runAgent: ({ request, customer_id }) => later({ action_id: 'act_demo_001', customer_id, order_id: 'ord_001', verification_decision: 'REVIEW', risk_level: 'HIGH', execution_status: 'PENDING_REVIEW', reason_codes: ['AUTO_CEILING_EXCEEDED'], request }),
  decideReview: (id, { outcome }) => later({ ...reviews.find(r => r.review_id === id), status: 'RESOLVED', outcome }),
}
