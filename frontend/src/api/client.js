import axios from 'axios'
import { mockApi } from './mockApi'

const live = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000' })
export const mockMode = import.meta.env.VITE_MOCK_MODE !== 'false'
export const api = mockMode ? mockApi : {
  getReviews: () => live.get('/api/reviews').then(r => r.data),
  getAuditLogs: () => live.get('/api/audit-logs').then(r => r.data),
  getMetrics: () => live.get('/api/metrics').then(r => r.data),
  runAgent: payload => live.post('/api/agent/run', payload).then(r => r.data),
  decideReview: (id, payload) => live.post(`/api/reviews/${id}/decision`, payload).then(r => r.data),
}
