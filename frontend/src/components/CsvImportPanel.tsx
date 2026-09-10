import { useRef, useState } from 'react'
import { api } from '../lib/api'
import { CategoryPillSelect } from './CategoryPillSelect'
import { ConfidenceBar } from './ConfidenceBar'
import type { Category, UploadCommitResponse, UploadPreviewResponse } from '../lib/types'

interface CsvImportPanelProps {
  categories: Category[]
  onImported: () => void
}

type Phase = 'empty' | 'uploading' | 'preview' | 'committing' | 'error'

export function CsvImportPanel({ categories, onImported }: CsvImportPanelProps) {
  const [phase, setPhase] = useState<Phase>('empty')
  const [fileName, setFileName] = useState('')
  const [preview, setPreview] = useState<UploadPreviewResponse | null>(null)
  const [categoryEdits, setCategoryEdits] = useState<Record<number, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<UploadCommitResponse | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  async function handleFile(file: File) {
    setFileName(file.name)
    setPhase('uploading')
    setError(null)

    const form = new FormData()
    form.append('file', file)

    try {
      const res = await api.post<UploadPreviewResponse>('/transactions/upload/preview', form)
      setPreview(res.data)
      setCategoryEdits({})
      setPhase('preview')
    } catch (err) {
      setError(extractError(err))
      setPhase('error')
    }
  }

  function reset() {
    setPhase('empty')
    setPreview(null)
    setResult(null)
    setError(null)
    setCategoryEdits({})
    if (inputRef.current) inputRef.current.value = ''
  }

  async function confirmImport() {
    if (!preview) return
    setPhase('committing')
    try {
      const res = await api.post<UploadCommitResponse>('/transactions/upload/commit', {
        upload_token: preview.upload_token,
        mapping: preview.suggested_mapping,
        category_overrides: categoryEdits,
      })
      setResult(res.data)
      onImported()
    } catch (err) {
      setError(extractError(err))
      setPhase('error')
    }
  }

  if (phase === 'empty' || phase === 'uploading') {
    return (
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          const file = e.dataTransfer.files[0]
          if (file) handleFile(file)
        }}
        className={`rounded-xl border-[1.5px] border-dashed bg-card p-16 text-center transition-colors ${
          dragOver ? 'border-cyan bg-cyan-soft/30' : 'border-cyan'
        }`}
      >
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-md bg-cyan-soft">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 4 V16 M7 9 L12 4 L17 9 M5 20 H19"
              stroke="var(--color-cyan-ink)"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        {phase === 'uploading' ? (
          <>
            <div className="font-heading text-h4 font-semibold text-heading">Reading {fileName}…</div>
            <div className="mt-2 text-sm text-muted">Parsing columns and detecting categories</div>
          </>
        ) : (
          <>
            <div className="font-heading text-h4 font-semibold text-heading">Drop your statement here</div>
            <div className="mt-2 mb-6 text-sm text-muted">CSV from any bank — we'll handle the rest</div>
            <button
              onClick={() => inputRef.current?.click()}
              className="rounded-sm bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:brightness-110"
            >
              Browse files
            </button>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
          }}
        />
      </div>
    )
  }

  if (phase === 'error') {
    return (
      <div className="rounded-xl border border-overspend/30 bg-overspend-soft p-8 text-center">
        <div className="font-heading text-h4 font-semibold text-overspend-ink">Import failed</div>
        <p className="mt-2 text-sm text-secondary">{error}</p>
        <button onClick={reset} className="mt-5 rounded-sm bg-primary px-5 py-2.5 text-sm font-semibold text-white">
          Try again
        </button>
      </div>
    )
  }

  if (result) {
    return (
      <div className="card-lifted p-8 text-center">
        <div className="font-heading text-h4 font-semibold text-heading">Import complete</div>
        <p className="mt-2 text-sm text-secondary">
          {result.inserted} transaction{result.inserted === 1 ? '' : 's'} added
          {result.duplicates_skipped > 0 && `, ${result.duplicates_skipped} duplicate${result.duplicates_skipped === 1 ? '' : 's'} skipped`}
          {result.unparseable_skipped > 0 && `, ${result.unparseable_skipped} row${result.unparseable_skipped === 1 ? '' : 's'} unreadable`}.
        </p>
        <button onClick={reset} className="mt-5 rounded-sm bg-primary px-5 py-2.5 text-sm font-semibold text-white">
          Import another file
        </button>
      </div>
    )
  }

  if (!preview) return null

  const descCol = preview.suggested_mapping.description
  const amountCol = preview.suggested_mapping.amount

  return (
    <div className="card-lifted p-8">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <div className="font-heading text-h4 font-semibold text-heading">{fileName}</div>
          <div className="mt-0.5 text-xs text-muted">{preview.total_rows} transactions detected · review categories below</div>
        </div>
        <button onClick={reset} className="rounded-sm bg-hairline px-4 py-2 text-xs font-semibold text-secondary">
          Start over
        </button>
      </div>

      <div className="max-h-[420px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left text-xs text-muted">
              <th className="pb-3 font-normal">Description</th>
              <th className="pb-3 font-normal">Category</th>
              <th className="pb-3 text-right font-normal">Amount</th>
            </tr>
          </thead>
          <tbody>
            {preview.sample_rows.map((row, i) => {
              const guess = preview.category_guesses[i]
              const currentCategory = categoryEdits[i] ?? guess?.category ?? ''
              const rawAmount = amountCol ? row[amountCol] : ''
              return (
                <tr key={i} className="border-b border-[color:var(--color-hairline)]/60">
                  <td className="max-w-[220px] truncate py-3 pr-3 font-medium text-body">
                    {descCol ? row[descCol] : '—'}
                  </td>
                  <td className="py-3 pr-3">
                    <div className="flex items-center gap-2">
                      <CategoryPillSelect
                        categories={categories}
                        value={currentCategory || null}
                        onChange={(name) => setCategoryEdits((prev) => ({ ...prev, [i]: name }))}
                      />
                      {guess?.confidence != null && <ConfidenceBar value={guess.confidence} />}
                    </div>
                  </td>
                  <td className="py-3 text-right tabular-nums font-semibold text-body">{rawAmount}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-6 flex justify-end gap-3">
        <button onClick={reset} className="rounded-sm px-4 py-2.5 text-sm font-semibold text-secondary">
          Cancel
        </button>
        <button
          onClick={confirmImport}
          disabled={phase === 'committing'}
          className="rounded-sm bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:brightness-110 disabled:opacity-60"
        >
          {phase === 'committing' ? 'Importing…' : 'Confirm import'}
        </button>
      </div>
    </div>
  )
}

function extractError(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const res = (err as { response?: { data?: { detail?: string } } }).response
    if (res?.data?.detail) return res.data.detail
  }
  return 'Something went wrong. Please try again.'
}
