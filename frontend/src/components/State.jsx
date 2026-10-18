export function LoadingState() { return <div className="state">Loading protected records…</div> }
export function ErrorState({ message }) { return <div className="state error">{message}</div> }
export function EmptyState({ message }) { return <div className="state">{message}</div> }
