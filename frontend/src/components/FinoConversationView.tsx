import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useFino } from '../context/FinoContext'
import { useAuth } from '../context/AuthContext'
import { FinoMark } from './FinoMark'
import { FinoMascot } from './illustrations/FinoMascot'
import { ProfileAvatar } from './ProfileAvatar'

const SUGGESTED_PROMPTS: { match: (path: string) => boolean; prompts: string[] }[] = [
  { match: (p) => p.startsWith('/dashboard'), prompts: ['How am I doing this month?', 'What should I focus on?'] },
  { match: (p) => p.startsWith('/import'), prompts: ['How do I upload a statement?', "What if my screenshot doesn't scan?"] },
  { match: (p) => p.startsWith('/forecast'), prompts: ['Why is this forecast low-confidence?'] },
  { match: (p) => p.startsWith('/advice'), prompts: ['Can you explain this recommendation?'] },
  { match: (p) => p.startsWith('/what-if'), prompts: ['How do I use the what-if simulator?'] },
  { match: (p) => p.startsWith('/transactions'), prompts: ['How do I fix a miscategorized transaction?'] },
  { match: (p) => p.startsWith('/budgets'), prompts: ['How do I set a budget?'] },
  { match: (p) => p.startsWith('/goals'), prompts: ['How do I create a goal?', 'Am I on track for my goals?'] },
  { match: (p) => p.startsWith('/reports'), prompts: ['How do I export my data?'] },
  { match: (p) => p.startsWith('/profile'), prompts: ['How do I delete my account?'] },
]
const DEFAULT_PROMPTS = ['What can you help me with?', 'How does FinPilot work?']

function suggestedPromptsFor(pathname: string): string[] {
  return SUGGESTED_PROMPTS.find((entry) => entry.match(pathname))?.prompts ?? DEFAULT_PROMPTS
}

export function FinoConversationView({ compact = false }: { compact?: boolean }) {
  const { messages, sending, loaded, sendMessage } = useFino()
  const { user } = useAuth()
  const location = useLocation()
  const [draft, setDraft] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!draft.trim() || sending) return
    sendMessage(draft)
    setDraft('')
  }

  const chips = suggestedPromptsFor(location.pathname)

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className={`flex-1 overflow-y-auto ${compact ? 'px-4 py-4' : 'px-6 py-6'} space-y-4`}>
        {!loaded && <div className="skeleton h-16 w-full" />}

        {loaded && messages.length === 0 && (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <FinoMascot size={compact ? 32 : 96} />
            <div className="font-heading text-sm font-semibold text-heading">Hi, I'm Fino.</div>
            <p className="max-w-[260px] text-xs text-muted">
              Ask me about your spending, your goals, or how to do something in FinPilot.
            </p>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={`flex items-start gap-2.5 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
            {m.role === 'assistant' ? (
              <FinoMark size={24} className="mt-0.5 flex-none" />
            ) : user ? (
              <div className="mt-0.5 flex-none">
                <ProfileAvatar user={user} size={24} />
              </div>
            ) : null}
            <div
              className={`max-w-[80%] rounded-lg px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                m.role === 'user' ? 'bg-primary text-white' : 'bg-hairline text-body'
              }`}
            >
              {m.content || (sending && m.role === 'assistant' ? '…' : '')}
            </div>
          </div>
        ))}
      </div>

      {messages.length === 0 && loaded && (
        <div className="flex flex-wrap gap-2 px-4 pb-2">
          {chips.map((chip) => (
            <button
              key={chip}
              onClick={() => sendMessage(chip)}
              className="rounded-full border border-border px-3 py-1.5 text-xs text-secondary hover:bg-hairline"
            >
              {chip}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-hairline p-3">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask Fino anything…"
          disabled={sending}
          className="flex-1 rounded-sm border border-border bg-card px-3 py-2 text-sm outline-none focus:border-primary disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={sending || !draft.trim()}
          className="rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  )
}
