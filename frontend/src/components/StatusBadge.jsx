export function StatusBadge({ value }) { const type = value?.toLowerCase().replaceAll('_','-'); return <span className={`badge ${type}`}>{value?.replaceAll('_', ' ')}</span> }
export function Money({ value = 0 }) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(value / 100) }
