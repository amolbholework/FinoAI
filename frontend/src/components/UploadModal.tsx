import { useState } from 'react'
import { api } from '../lib/api'

interface PreviewResponse {
  columns: string[]
  suggested_mapping: Record<string, string | null>
  sample_rows: Record<string, string>[]
  total_rows: number
  upload_token: string
}

const MAPPING_FIELDS = ['date', 'description', 'amount', 'debit', 'credit'] as const

export function UploadModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [preview, setPreview] = useState<PreviewResponse | null>(null)
  const [mapping, setMapping] = useState<Record<string, string | null>>({})
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<{ inserted: number; duplicates_skipped: number; unparseable_skipped: number } | null>(null)

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setError(null)
    setBusy(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await api.post<PreviewResponse>('/transactions/upload/preview', form)
      setPreview(res.data)
      setMapping(res.data.suggested_mapping)
    } catch (err) {
      setError('Could not read that file — is it a CSV?')
    } finally {
      setBusy(false)
    }
  }

  const useDebitCredit = !mapping.amount

  async function handleCommit() {
    if (!preview) return
    setBusy(true)
    setError(null)
    try {
      const res = await api.post('/transactions/upload/commit', { upload_token: preview.upload_token, mapping })
      setResult(res.data)
    } catch (err) {
      setError('Could not import this file — check the column mapping and try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="card-lifted w-full max-w-lg p-6">
        <h2 className="font-heading text-lg font-semibold text-heading">Import bank statement CSV</h2>

        {!preview && !result && (
          <div className="mt-4">
            <input type="file" accept=".csv" onChange={handleFileChange} disabled={busy} className="text-sm" />
            {error && <p className="mt-2 text-sm text-[var(--color-overspend)]">{error}</p>}
          </div>
        )}

        {preview && !result && (
          <div className="mt-4 space-y-4">
            <p className="text-sm text-secondary">
              {preview.total_rows} rows found. Confirm the column mapping — pick either a single signed <em>amount</em>{' '}
              column, or separate <em>debit</em>/<em>credit</em> columns.
            </p>

            <div className="grid grid-cols-2 gap-3">
              {MAPPING_FIELDS.map((field) => (
                <label key={field} className="text-xs">
                  <span className="mb-1 block font-medium capitalize text-secondary">{field}</span>
                  <select
                    className="w-full rounded-lg border border-border bg-white px-2 py-1.5 text-sm"
                    value={mapping[field] ?? ''}
                    onChange={(e) => setMapping((m) => ({ ...m, [field]: e.target.value || null }))}
                  >
                    <option value="">—</option>
                    {preview.columns.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>

            <div className="max-h-48 overflow-auto rounded-lg border border-border">
              <table className="w-full text-xs">
                <thead className="bg-canvas text-muted">
                  <tr>
                    {preview.columns.map((c) => (
                      <th key={c} className="px-2 py-1 text-left font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.sample_rows.slice(0, 6).map((row, i) => (
                    <tr key={i} className="border-t border-border">
                      {preview.columns.map((c) => (
                        <td key={c} className="px-2 py-1 text-secondary">
                          {row[c]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {error && <p className="text-sm text-[var(--color-overspend)]">{error}</p>}

            <div className="flex justify-end gap-2">
              <button onClick={onClose} className="rounded-lg px-3 py-1.5 text-sm text-secondary">
                Cancel
              </button>
              <button
                onClick={handleCommit}
                disabled={busy || (!mapping.date || !mapping.description || (!mapping.amount && !mapping.debit && !mapping.credit))}
                className="rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy ? 'Importing…' : `Import ${preview.total_rows} rows`}
              </button>
            </div>
            {useDebitCredit && <p className="text-[10px] text-muted">Using debit/credit columns since no single amount column is mapped.</p>}
          </div>
        )}

        {result && (
          <div className="mt-4 space-y-3">
            <p className="text-sm text-heading">
              Imported <strong>{result.inserted}</strong> transactions. Skipped {result.duplicates_skipped} duplicates
              {result.unparseable_skipped > 0 && ` and ${result.unparseable_skipped} unparseable rows`}.
            </p>
            <div className="flex justify-end">
              <button onClick={onDone} className="rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-white">
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
