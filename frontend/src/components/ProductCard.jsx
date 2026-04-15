import { Link } from 'react-router-dom'
import { Tag, Clock } from 'lucide-react'

// Static files are served by the FastAPI backend, not the Vite dev server.
const BACKEND = import.meta.env.VITE_API_BASE_URL
  ? import.meta.env.VITE_API_BASE_URL.replace('/api/v1', '')
  : 'http://localhost:8000'

/**
 * Resolve an image entry to an absolute URL.
 * The feed returns images as plain path strings ("static/products/...").
 * The detail endpoint may return objects with an image_url property.
 */
function resolveImageUrl(entry) {
  if (!entry) return null
  const raw = typeof entry === 'string' ? entry : entry.image_url
  if (!raw) return null
  // Already absolute (http/https/blob)
  if (/^https?:\/\//.test(raw)) return raw
  // Relative path — prepend backend origin
  return `${BACKEND}/${raw.replace(/^\//, '')}`
}

const STATUS_STYLES = {
  APPROVE:  { label: 'Active',    cls: 'bg-green-100 text-green-700' },
  PENDING:  { label: 'Pending',   cls: 'bg-yellow-100 text-yellow-700' },
  REJECTED: { label: 'Rejected',  cls: 'bg-red-100 text-red-700' },
  RESERVED: { label: 'Reserved',  cls: 'bg-blue-100 text-blue-700' },
  SOLD:     { label: 'Sold',      cls: 'bg-gray-100 text-gray-500' },
}

export default function ProductCard({ product, showStatus = false }) {
  const image = resolveImageUrl(product.images?.[0]) ?? resolveImageUrl(product.image_url)
  const status = STATUS_STYLES[product.status] ?? STATUS_STYLES.PENDING
  const categoryName = product.category?.name ?? product.category_name ?? null

  return (
    <Link to={`/products/${product.id}`} className="group block bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow overflow-hidden border border-gray-100">
      {/* Image */}
      <div className="aspect-square bg-gray-100 overflow-hidden">
        {image ? (
          <img
            src={image}
            alt={product.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300">
            <Tag size={40} />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <p className="font-bold text-gray-900 text-base">
          ${Number(product.price).toLocaleString()}
        </p>
        <p className="text-sm text-gray-700 mt-0.5 line-clamp-2">{product.title}</p>

        <div className="flex items-center justify-between mt-2">
          {categoryName && (
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <Tag size={11} />
              {categoryName}
            </span>
          )}
          {showStatus && (
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${status.cls}`}>
              {status.label}
            </span>
          )}
        </div>

        {product.created_at && (
          <p className="text-xs text-gray-400 mt-1.5 flex items-center gap-1">
            <Clock size={11} />
            {new Date(product.created_at).toLocaleDateString()}
          </p>
        )}
      </div>
    </Link>
  )
}
