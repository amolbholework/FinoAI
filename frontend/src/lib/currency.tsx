import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from './api'

const CurrencyContext = createContext<string>('INR')

export function CurrencyProvider({ children }: { children: ReactNode }) {
  const [currency, setCurrency] = useState('INR')

  useEffect(() => {
    api
      .get('/settings')
      .then((res) => setCurrency(res.data.currency))
      .catch(() => {})
  }, [])

  return <CurrencyContext.Provider value={currency}>{children}</CurrencyContext.Provider>
}

export function useCurrency() {
  return useContext(CurrencyContext)
}
