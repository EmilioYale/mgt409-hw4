import { useEffect, useState } from 'react'
import { api } from './api'
import type { CatalogueResponse } from './types'

let cache: Promise<CatalogueResponse> | null = null

/** Fetch the catalogue once per page load and share it between pages. */
export function useCatalogue() {
  const [data, setData] = useState<CatalogueResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    cache ??= api.catalogue()
    cache.then(setData).catch((e) => {
      cache = null
      setError(e instanceof Error ? e.message : 'Could not load products')
    })
  }, [])
  return { data, error }
}
