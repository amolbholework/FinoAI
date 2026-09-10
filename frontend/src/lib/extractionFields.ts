import type { TransactionExtraction } from './types'

export const LOW_CONFIDENCE_THRESHOLD = 0.7

export interface EditableFields {
  amount: string
  merchant: string
  date: string // yyyy-mm-dd for <input type="date">
  direction: 'debit' | 'credit'
  category: string
}

export function toEditableFields(extraction: TransactionExtraction): EditableFields {
  return {
    amount: extraction.amount != null ? String(extraction.amount) : '',
    merchant: extraction.merchant ?? '',
    date: extraction.datetime ? extraction.datetime.slice(0, 10) : '',
    direction: extraction.direction ?? 'debit',
    category: extraction.category ?? '',
  }
}

export function isFieldFlagged(
  field: 'amount' | 'merchant' | 'category',
  extraction: TransactionExtraction,
): boolean {
  if (extraction.unreadable_fields.includes(field)) return true
  return extraction.confidence[field] < LOW_CONFIDENCE_THRESHOLD
}
