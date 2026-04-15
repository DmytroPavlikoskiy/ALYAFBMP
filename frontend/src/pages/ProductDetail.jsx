import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Tag, User, ShoppingCart, MessageSquare, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

const STATUS_STYLES = {
  APPROVE:  { label: 'Available',  cls: 'bg-green-100 text-green-700' },
  PENDING:  { label: 'Pending review', cls: 'bg-yellow-100 text-yellow-700' },
  REJECTED: { label: 'Rejected',   cls: 'bg-red-100 text-red-700' },
  RESERVED: { label: 'Reserved',   cls: 'bg-blue-100 text-blue-700' },
  SOLD:     { label: 'Sold',       cls: 'bg-gray-100 text-gray-500' },
}

export default function ProductDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()

  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [imgIndex, setImgIndex] = useState(0)
  const [ordering, setOrdering] = useState(false)
  const [orderMsg, setOrderMsg] = useState(null)
  const [chatLoading, setChatLoading] = useState(false)

  useEffect(() => {
    api.get(`/products/${id}`)
      .then(({ data }) => setProduct(data))
      .catch(() => navigate('/'))
      .finally(() => setLoading(false))
  }, [id, navigate])

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-10">
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-gray-100 rounded-2xl aspect-square animate-pulse" />
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => <div key={i} className="h-4 bg-gray-100 rounded animate-pulse" />)}
          </div>
        </div>
      </div>
    )
  }

  if (!product) return null

  const images = product.images ?? []
  const status = STATUS_STYLES[product.status] ?? STATUS_STYLES.PENDING
  const isOwn = user?.id === product.seller?.id || user?.id === product.seller_id
  const canBuy = user && !isOwn && product.status === 'APPROVE'

  const placeOrder = async () => {
    setOrdering(true)
    setOrderMsg(null)
    try {
      await api.post('/orders/', { product_id: product.id })
      setOrderMsg({ type: 'success', text: 'Order placed! The seller will be notified.' })
      setProduct({ ...product, status: 'RESERVED' })
    } catch (err) {
      const detail = err.response?.data?.detail
      setOrderMsg({ type: 'error', text: detail || 'Could not place order.' })
    } finally {
      setOrdering(false)
    }
  }

  const openChat = async () => {
    setChatLoading(true)
    try {
      const { data } = await api.post('/chats', { product_id: product.id })
      navigate(`/chats/${data.id}`)
    } catch (err) {
      const detail = err.response?.data?.detail
      alert(detail || 'Could not open chat.')
    } finally {
      setChatLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-blue-600 mb-6 transition-colors">
        <ChevronLeft size={16} /> Back to listings
      </Link>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Image gallery */}
        <div>
          <div className="relative bg-gray-100 rounded-2xl overflow-hidden aspect-square">
            {images.length > 0 ? (
              <>
                <img src={images[imgIndex]?.image_url} alt={product.title} className="w-full h-full object-cover" />
                {images.length > 1 && (
                  <>
                    <button onClick={() => setImgIndex((imgIndex - 1 + images.length) % images.length)}
                      className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full p-1.5 shadow">
                      <ChevronLeft size={18} />
                    </button>
                    <button onClick={() => setImgIndex((imgIndex + 1) % images.length)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full p-1.5 shadow">
                      <ChevronRight size={18} />
                    </button>
                  </>
                )}
              </>
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-300">
                <Tag size={56} />
              </div>
            )}
          </div>
          {/* Thumbnails */}
          {images.length > 1 && (
            <div className="flex gap-2 mt-2 overflow-x-auto pb-1">
              {images.map((img, i) => (
                <button key={i} onClick={() => setImgIndex(i)}
                  className={`w-14 h-14 rounded-lg overflow-hidden flex-shrink-0 border-2 transition-colors ${i === imgIndex ? 'border-blue-500' : 'border-transparent'}`}>
                  <img src={img.image_url} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Details */}
        <div>
          <div className="flex items-start justify-between gap-2 mb-2">
            <h1 className="text-2xl font-bold text-gray-900">{product.title}</h1>
            <span className={`text-xs font-medium px-2.5 py-1 rounded-full flex-shrink-0 ${status.cls}`}>
              {status.label}
            </span>
          </div>

          <p className="text-3xl font-bold text-blue-600 mb-4">
            ${Number(product.price).toLocaleString()}
          </p>

          {product.description && (
            <p className="text-gray-600 text-sm leading-relaxed mb-4 whitespace-pre-wrap">
              {product.description}
            </p>
          )}

          {(product.category_name || product.category?.name) && (
            <div className="flex items-center gap-1.5 text-sm text-gray-500 mb-4">
              <Tag size={14} />
              <span>{product.category_name ?? product.category?.name}</span>
            </div>
          )}

          {/* Seller */}
          {product.seller && (
            <div className="flex items-center gap-2 bg-gray-50 rounded-xl p-3 mb-5">
              <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                {product.seller.avatar_url
                  ? <img src={product.seller.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
                  : <User size={18} />}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-800">{product.seller.first_name}</p>
                <p className="text-xs text-gray-400">Seller</p>
              </div>
            </div>
          )}

          {/* Order feedback */}
          {orderMsg && (
            <div className={`flex items-start gap-2 rounded-xl px-4 py-3 mb-4 text-sm ${
              orderMsg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
            }`}>
              <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
              {orderMsg.text}
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col gap-3">
            {canBuy && (
              <button onClick={placeOrder} disabled={ordering}
                className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold py-3 rounded-xl transition-colors">
                <ShoppingCart size={18} />
                {ordering ? 'Placing order…' : 'Buy now'}
              </button>
            )}
            {user && !isOwn && (
              <button onClick={openChat} disabled={chatLoading}
                className="flex items-center justify-center gap-2 border border-blue-600 text-blue-600 hover:bg-blue-50 font-semibold py-3 rounded-xl transition-colors">
                <MessageSquare size={18} />
                {chatLoading ? 'Opening chat…' : 'Message seller'}
              </button>
            )}
            {!user && (
              <Link to="/login" className="text-center bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition-colors">
                Sign in to buy
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
