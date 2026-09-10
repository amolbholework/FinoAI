import type { Category } from '../lib/types'
import { categoryPillColors } from '../lib/categoryColors'

interface CategoryPillSelectProps {
  categories: Category[]
  value: string | null // category name
  onChange: (name: string) => void
  disabled?: boolean
}

/**
 * The category picker used everywhere a transaction row needs one — the CSV
 * preview table and the screenshot review card both use this exact
 * component rather than parallel implementations.
 */
export function CategoryPillSelect({ categories, value, onChange, disabled }: CategoryPillSelectProps) {
  const { bg, ink } = categoryPillColors(value)

  return (
    <select
      value={value ?? ''}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
      className="cursor-pointer rounded-full border-0 py-1.5 pr-7 pl-3 text-xs font-semibold outline-none disabled:cursor-not-allowed"
      style={{ background: bg, color: ink }}
    >
      <option value="" disabled>
        Select category
      </option>
      {categories.map((c) => (
        <option key={c.id} value={c.name}>
          {c.name}
        </option>
      ))}
    </select>
  )
}
