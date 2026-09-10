import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { CategoryPillSelect } from './CategoryPillSelect'
import { ConfidenceBar } from './ConfidenceBar'
import { isFieldFlagged, toEditableFields, type EditableFields } from '../lib/extractionFields'
import type { Category, TransactionExtraction } from '../lib/types'

interface ScreenshotScannerProps {
  categories: Category[]
  onSaved: () => void
}

type ItemStatus = 'uploading' | 'extracted' | 'not_transaction' | 'error' | 'saving' | 'saved'

interface QueueItem {
  id: string
  file: File
  previewUrl: string
  status: ItemStatus
  extraction?: TransactionExtraction
  fields?: EditableFields
  error?: string
}

const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'image/heic', 'image/heif']
const MAX_BYTES = 8 * 1024 * 1024

function newId() {
  return Math.random().toString(36).slice(2)
}

export function ScreenshotScanner({ categories, onSaved }: ScreenshotScannerProps) {
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const addFiles = useCallback((files: File[]) => {
    const valid = files.filter((f) => ACCEPTED_TYPES.includes(f.type) || /\.(png|jpe?g|webp|heic|heif)$/i.test(f.name))
    if (valid.length === 0) return

    const items: QueueItem[] = valid.map((file) => ({
      id: newId(),
      file,
      previewUrl: URL.createObjectURL(file),
      status: 'uploading',
    }))

    setQueue((prev) => [...prev, ...items])
    items.forEach((item) => processItem(item))
  }, [])

  async function processItem(item: QueueItem) {
    if (item.file.size > MAX_BYTES) {
      updateItem(item.id, { status: 'error', error: 'Image exceeds the 8MB limit.' })
      return
    }

    const form = new FormData()
    form.append('file', item.file)

    try {
      const res = await api.post<TransactionExtraction>('/transactions/extract', form)
      const extraction = res.data
      if (!extraction.is_transaction) {
        updateItem(item.id, { status: 'not_transaction', extraction })
      } else {
        updateItem(item.id, { status: 'extracted', extraction, fields: toEditableFields(extraction) })
      }
    } catch (err) {
      updateItem(item.id, { status: 'error', error: extractError(err) })
    }
  }

  function updateItem(id: string, patch: Partial<QueueItem>) {
    setQueue((prev) => prev.map((it) => (it.id === id ? { ...it, ...patch } : it)))
  }

  function updateFields(id: string, patch: Partial<EditableFields>) {
    setQueue((prev) => prev.map((it) => (it.id === id ? { ...it, fields: { ...it.fields!, ...patch } } : it)))
  }

  function advance() {
    setCurrentIndex((i) => Math.min(i + 1, queue.length))
  }

  async function confirmCurrent(item: QueueItem) {
    if (!item.fields) return
    updateItem(item.id, { status: 'saving' })

    const category = categories.find((c) => c.name === item.fields!.category)
    const signedAmount = Math.round(parseFloat(item.fields.amount) * 100) * (item.fields.direction === 'debit' ? -1 : 1)

    try {
      await api.post('/transactions', {
        date: item.fields.date,
        description: item.fields.merchant,
        amount_minor: signedAmount,
        category_id: category?.id ?? null,
      })
      updateItem(item.id, { status: 'saved' })
      URL.revokeObjectURL(item.previewUrl)
      onSaved()
      advance()
    } catch (err) {
      updateItem(item.id, { status: 'extracted', error: extractError(err) })
    }
  }

  function discardCurrent(item: QueueItem) {
    URL.revokeObjectURL(item.previewUrl)
    advance()
  }

  function retryCurrent(item: QueueItem) {
    updateItem(item.id, { status: 'uploading', error: undefined })
    processItem(item)
  }

  // Ctrl/Cmd+V of a screenshot — the primary way most people will actually use this.
  useEffect(() => {
    function onPaste(e: ClipboardEvent) {
      const files = Array.from(e.clipboardData?.items ?? [])
        .filter((it) => it.kind === 'file' && it.type.startsWith('image/'))
        .map((it) => it.getAsFile())
        .filter((f): f is File => f !== null)
      if (files.length > 0) addFiles(files)
    }
    document.addEventListener('paste', onPaste)
    return () => document.removeEventListener('paste', onPaste)
  }, [addFiles])

  useEffect(() => {
    return () => {
      queue.forEach((it) => URL.revokeObjectURL(it.previewUrl))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const current = queue[currentIndex]
  const remaining = queue.length - currentIndex

  return (
    <div ref={containerRef}>
      {queue.length > 0 && (
        <div className="mb-3 flex items-center justify-between">
          <span className="text-xs font-semibold tracking-wide text-muted uppercase">
            {remaining > 0 ? `Reviewing ${currentIndex + 1} of ${queue.length}` : `${queue.length} screenshot${queue.length === 1 ? '' : 's'} processed`}
          </span>
          {remaining > 0 && (
            <button onClick={() => inputRef.current?.click()} className="text-xs font-semibold text-primary">
              + Add more
            </button>
          )}
        </div>
      )}

      {current ? (
        <QueueItemCard
          item={current}
          categories={categories}
          onFieldsChange={(patch) => updateFields(current.id, patch)}
          onConfirm={() => confirmCurrent(current)}
          onDiscard={() => discardCurrent(current)}
          onRetry={() => retryCurrent(current)}
          onSkip={() => advance()}
        />
      ) : (
        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragOver(false)
            addFiles(Array.from(e.dataTransfer.files))
          }}
          className={`rounded-xl border-[1.5px] border-dashed p-8 text-center transition-colors ${
            dragOver ? 'border-cyan bg-cyan-soft/30' : 'border-border bg-canvas'
          }`}
        >
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-cyan-soft">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="5" width="18" height="14" rx="2" stroke="var(--color-cyan-ink)" strokeWidth="1.6" />
              <circle cx="9" cy="11" r="2" stroke="var(--color-cyan-ink)" strokeWidth="1.6" />
              <path d="M4 17 L9 13 L12 15.5 L16 12 L20 16" stroke="var(--color-cyan-ink)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div className="font-heading text-sm font-semibold text-heading">Scan a screenshot</div>
          <div className="mt-1.5 text-xs text-muted">
            UPI confirmation, bank SMS, or receipt — drop it, paste it (Ctrl+V), or pick a file
          </div>
          <button
            onClick={() => inputRef.current?.click()}
            className="mt-4 rounded-sm border border-primary-border bg-card px-4 py-2 text-xs font-semibold text-primary"
          >
            Choose image
          </button>
          <div className="mt-2 text-[11px] text-muted">PNG, JPG, WEBP, HEIC · up to 8MB · not stored</div>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/heic,image/heif"
        capture="environment"
        multiple
        className="hidden"
        onChange={(e) => {
          if (e.target.files) addFiles(Array.from(e.target.files))
          e.target.value = ''
        }}
      />
    </div>
  )
}

function QueueItemCard({
  item,
  categories,
  onFieldsChange,
  onConfirm,
  onDiscard,
  onRetry,
  onSkip,
}: {
  item: QueueItem
  categories: Category[]
  onFieldsChange: (patch: Partial<EditableFields>) => void
  onConfirm: () => void
  onDiscard: () => void
  onRetry: () => void
  onSkip: () => void
}) {
  if (item.status === 'uploading') {
    return (
      <div className="card-lifted flex items-center gap-4 p-5">
        <img src={item.previewUrl} alt="" className="h-16 w-16 rounded-md object-cover" />
        <div className="flex-1">
          <div className="text-sm font-semibold text-heading">Reading screenshot…</div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-hairline">
            <div className="h-full w-1/2 animate-pulse rounded-full bg-primary" />
          </div>
        </div>
      </div>
    )
  }

  if (item.status === 'not_transaction') {
    return (
      <div className="card-lifted p-6 text-center">
        <img src={item.previewUrl} alt="" className="mx-auto mb-4 h-20 w-20 rounded-md object-cover opacity-60" />
        <div className="font-heading text-sm font-semibold text-heading">Nothing financial found</div>
        <p className="mx-auto mt-1.5 max-w-xs text-xs text-muted">
          {item.extraction?.notes ?? "This doesn't look like a payment confirmation, receipt, or bank message."}
        </p>
        <div className="mt-4 flex justify-center gap-2">
          <button onClick={onSkip} className="rounded-sm bg-hairline px-4 py-2 text-xs font-semibold text-secondary">
            Skip
          </button>
          <button onClick={onRetry} className="rounded-sm bg-primary px-4 py-2 text-xs font-semibold text-white">
            Try again
          </button>
        </div>
      </div>
    )
  }

  if (item.status === 'error') {
    return (
      <div className="rounded-xl border border-overspend/30 bg-overspend-soft p-6 text-center">
        <div className="font-heading text-sm font-semibold text-overspend-ink">Couldn't read this image</div>
        <p className="mx-auto mt-1.5 max-w-xs text-xs text-secondary">{item.error}</p>
        <div className="mt-4 flex justify-center gap-2">
          <button onClick={onSkip} className="rounded-sm bg-hairline px-4 py-2 text-xs font-semibold text-secondary">
            Skip
          </button>
          <button onClick={onRetry} className="rounded-sm bg-primary px-4 py-2 text-xs font-semibold text-white">
            Retry
          </button>
        </div>
      </div>
    )
  }

  // extracted or saving
  const extraction = item.extraction!
  const fields = item.fields!
  const canConfirm = fields.amount.trim() !== '' && fields.merchant.trim() !== '' && fields.date.trim() !== ''

  return (
    <div className="card-lifted grid grid-cols-1 gap-6 p-6 sm:grid-cols-[160px_1fr]">
      <img src={item.previewUrl} alt="Screenshot" className="h-40 w-full rounded-md border border-hairline object-cover sm:h-full" />

      <div>
        <Field
          label="Amount"
          flagged={isFieldFlagged('amount', extraction)}
          note={extraction.unreadable_fields.includes('amount') ? "Couldn't read the amount clearly" : undefined}
        >
          <div className="flex items-center gap-2">
            <select
              value={fields.direction}
              onChange={(e) => onFieldsChange({ direction: e.target.value as 'debit' | 'credit' })}
              className="rounded-md border border-border bg-canvas px-2 py-2 text-sm"
            >
              <option value="debit">Paid</option>
              <option value="credit">Received</option>
            </select>
            <input
              type="number"
              step="0.01"
              value={fields.amount}
              onChange={(e) => onFieldsChange({ amount: e.target.value })}
              placeholder="0.00"
              className={`w-full rounded-md border bg-canvas px-3 py-2 text-sm tabular-nums ${
                isFieldFlagged('amount', extraction) ? 'border-overspend' : 'border-border'
              }`}
            />
          </div>
        </Field>

        <Field
          label="Merchant"
          flagged={isFieldFlagged('merchant', extraction)}
          note={extraction.unreadable_fields.includes('merchant') ? "Couldn't read the merchant name" : undefined}
        >
          <input
            value={fields.merchant}
            onChange={(e) => onFieldsChange({ merchant: e.target.value })}
            placeholder="e.g. Swiggy"
            className={`w-full rounded-md border bg-canvas px-3 py-2 text-sm ${
              isFieldFlagged('merchant', extraction) ? 'border-overspend' : 'border-border'
            }`}
          />
        </Field>

        <Field label="Date">
          <input
            type="date"
            value={fields.date}
            onChange={(e) => onFieldsChange({ date: e.target.value })}
            className="w-full rounded-md border border-border bg-canvas px-3 py-2 text-sm"
          />
        </Field>

        <Field label="Category" flagged={isFieldFlagged('category', extraction)}>
          <div className="flex items-center gap-2">
            <CategoryPillSelect categories={categories} value={fields.category || null} onChange={(name) => onFieldsChange({ category: name })} />
            <ConfidenceBar value={extraction.confidence.category} />
          </div>
        </Field>

        {extraction.reference && <p className="mb-3 text-xs text-muted">Ref: {extraction.reference}</p>}

        <p className="mb-4 text-xs text-muted">This screenshot is used only to read the transaction and is not stored.</p>

        {item.error && <p className="mb-3 text-xs text-overspend">{item.error}</p>}

        <div className="flex gap-2">
          <button onClick={onDiscard} className="rounded-sm px-4 py-2.5 text-sm font-semibold text-secondary">
            Discard
          </button>
          <button
            onClick={onConfirm}
            disabled={!canConfirm || item.status === 'saving'}
            className="rounded-sm bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {item.status === 'saving' ? 'Saving…' : 'Confirm & add'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Field({
  label,
  flagged,
  note,
  children,
}: {
  label: string
  flagged?: boolean
  note?: string
  children: React.ReactNode
}) {
  return (
    <div className="mb-4">
      <label className="mb-1.5 flex items-center gap-1.5 text-xs text-muted">
        {label}
        {flagged && <span className="font-semibold text-overspend">· needs a look</span>}
      </label>
      {children}
      {flagged && note && <p className="mt-1 text-[11px] text-overspend">{note}</p>}
    </div>
  )
}

function extractError(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const res = (err as { response?: { data?: { detail?: string }; status?: number } }).response
    if (res?.status === 429) return 'Too many scans right now — please wait a moment and try again.'
    if (res?.data?.detail) return res.data.detail
  }
  return 'Network error — please try again.'
}
