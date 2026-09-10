import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { CsvImportPanel } from '../components/CsvImportPanel'
import { ScreenshotScanner } from '../components/ScreenshotScanner'
import type { Category } from '../lib/types'

export function ImportPage() {
  const [categories, setCategories] = useState<Category[]>([])

  useEffect(() => {
    api.get<Category[]>('/categories').then((res) => setCategories(res.data))
  }, [])

  function refreshCategories() {
    api.get<Category[]>('/categories').then((res) => setCategories(res.data))
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-heading text-h2 font-bold text-heading">Import transactions</h1>
        <p className="mt-1.5 text-sm text-muted">Upload a bank statement, or scan a payment screenshot</p>
      </div>

      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[1fr_360px]">
        <CsvImportPanel categories={categories} onImported={refreshCategories} />

        <div>
          <ScreenshotScanner categories={categories} onSaved={refreshCategories} />
        </div>
      </div>
    </div>
  )
}
