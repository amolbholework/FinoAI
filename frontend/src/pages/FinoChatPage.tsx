import { FinoMark } from '../components/FinoMark'
import { FinoConversationView } from '../components/FinoConversationView'

export function FinoChatPage() {
  return (
    <div className="flex h-[calc(100vh-var(--disclaimer-bar-h)-4rem)] flex-col rounded-lg border border-hairline bg-card">
      <div className="flex items-center gap-2.5 border-b border-hairline px-6 py-4">
        <FinoMark size={26} />
        <div>
          <div className="font-heading text-base font-semibold text-heading">Fino</div>
          <div className="text-xs text-muted">Your FinPilot assistant</div>
        </div>
      </div>
      <div className="min-h-0 flex-1">
        <FinoConversationView />
      </div>
    </div>
  )
}
