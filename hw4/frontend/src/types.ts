// Mirrors backend/models.py — the API contract between FastAPI and the site.

export interface SizeStock {
  size: string
  quantity: number
  in_stock: boolean
}

export interface ProductCard {
  product_id: string
  name: string
  garment_type: string
  price: number
  short_description: string
  colors: string[]
  image_url: string
  total_stock: number
  category?: string
}

export interface ProductDetail extends ProductCard {
  description: string
  search_tags: string[]
  sizes: SizeStock[]
}

export interface CatalogueResponse {
  products: ProductCard[]
  categories: Record<string, number>
  low_stock_threshold: number
}

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
  created_at: string
}

export interface AuthResponse {
  token: string
  user: User
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
  products: ProductCard[]
  created_at?: string | null
}

export interface PageContext {
  path: string
  product_id?: string | null
  product_name?: string | null
}

export interface ChatResponse {
  reply: string
  products: ProductCard[]
  saved: boolean
}
