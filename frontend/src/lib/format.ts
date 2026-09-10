const CURRENCY_SYMBOLS: Record<string, string> = { INR: '₹', USD: '$', EUR: '€', GBP: '£' }

export function formatMoney(minor: number, currency = 'INR'): string {
  const symbol = CURRENCY_SYMBOLS[currency] ?? currency + ' '
  const major = minor / 100
  const sign = major < 0 ? '-' : ''
  return `${sign}${symbol}${Math.abs(major).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

export function formatMonth(monthStr: string): string {
  const [year, month] = monthStr.split('-').map(Number)
  return new Date(year, month - 1, 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
}
