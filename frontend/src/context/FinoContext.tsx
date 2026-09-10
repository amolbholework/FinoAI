import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { useAuth } from './AuthContext'
import type { FinoMessage } from '../lib/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface FinoContextValue {
  messages: FinoMessage[]
  sending: boolean
  loaded: boolean
  sendMessage: (text: string) => Promise<void>
  panelOpen: boolean
  openPanel: () => void
  closePanel: () => void
}

const FinoContext = createContext<FinoContextValue | undefined>(undefined)

/** One shared conversation, one shared loading/sending state — so the
 * floating launcher panel and the full-page /fino view never show two
 * different histories or let the user send twice at once. */
export function FinoProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [messages, setMessages] = useState<FinoMessage[]>([])
  const [sending, setSending] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [panelOpen, setPanelOpen] = useState(false)
  const nextLocalId = useRef(0)

  useEffect(() => {
    if (!user) {
      setMessages([])
      setLoaded(false)
      return
    }
    fetch(`${API_BASE_URL}/api/fino/messages`, { credentials: 'include' })
      .then((res) => (res.ok ? res.json() : []))
      .then((data: FinoMessage[]) => setMessages(data))
      .finally(() => setLoaded(true))
  }, [user])

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return

    const userMessage: FinoMessage = {
      id: `local-${nextLocalId.current++}`,
      role: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
    }
    const assistantId = `local-${nextLocalId.current++}`
    const assistantMessage: FinoMessage = { id: assistantId, role: 'assistant', content: '', created_at: userMessage.created_at }

    setMessages((prev) => [...prev, userMessage, assistantMessage])
    setSending(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/fino/messages`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, current_route: window.location.pathname }),
      })

      if (!response.ok || !response.body) {
        throw new Error('Fino request failed')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulated = ''

      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        accumulated += decoder.decode(value, { stream: true })
        setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: accumulated } : m)))
      }
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: "I'm having trouble connecting right now — please try again in a moment." }
            : m,
        ),
      )
    } finally {
      setSending(false)
    }
  }, [])

  const openPanel = useCallback(() => setPanelOpen(true), [])
  const closePanel = useCallback(() => setPanelOpen(false), [])

  return (
    <FinoContext.Provider value={{ messages, sending, loaded, sendMessage, panelOpen, openPanel, closePanel }}>
      {children}
    </FinoContext.Provider>
  )
}

export function useFino() {
  const ctx = useContext(FinoContext)
  if (!ctx) throw new Error('useFino must be used within FinoProvider')
  return ctx
}
