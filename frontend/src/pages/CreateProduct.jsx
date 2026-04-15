import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PlusSquare, Upload, X, AlertTriangle } from 'lucide-react'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

export default function CreateProduct() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [categories, setCategories] = useState([])
  const [form, setForm] = useState({ title: '', price: '', description: '', category_id: '' })
  const [images, setImages] = useState([])
  const [previews, setPreviews] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [banned, setBanned] = useState(null) // null | { message, until }

  useEffect(() => {
    api.get('/categories').then(({ data }) => setCategories(data)).catch(() => {})
  }, [])

  // Detect ban from user object
  useEffect(() => {
    if (user?.banned_until) {
      const until = new Date(user.banned_until)
      if (until > new Date()) {
        setBanned({ until: until.toLocaleString() })
      }
    }
  }, [user])

  const handleImages = (e) => {
    const files = Array.from(e.target.files)
    const newImages = [...images, ...files].slice(0, 5)
    setImages(newImages)
    setPreviews(newImages.map((f) => URL.createObjectURL(f)))
  }

  const removeImage = (idx) => {
    const newImages = images.filter((_, i) => i !== idx)
    setImages(newImages)
    setPreviews(newImages.map((f) => URL.createObjectURL(f)))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const fd = new FormData()
    fd.append('title', form.title)
    fd.append('price', form.price)
    if (form.description) fd.append('description', form.description)
    if (form.category_id) fd.append('category_id', form.category_id)
    images.forEach((img) => fd.append('images', img))

    try {
      const { data } = await api.post('/products', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      navigate(`/products/${data.id}`)
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail ?? ''

      if (status === 403) {
        // Partial ban response from verify_user_not_banned
        const match = detail.match(/until (.+)\./)
        setBanned({ until: match?.[1] ?? 'an unknown date', message: detail })
      } else if (status === 429) {
        setError('You\'ve created too many listings recently. Please wait before trying again.')
      } else {
        setError(detail || 'Failed to create listing.')
      }
    } finally {
      setLoading(false)
    }
  }

  // Show ban wall
  if (banned) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-8">
          <AlertTriangle size={48} className="mx-auto text-amber-500 mb-4" />
          <h2 className="text-xl font-bold text-amber-900 mb-2">Posting restricted</h2>
          <p className="text-amber-800 text-sm leading-relaxed">
            {banned.message ?? `Your account is restricted from posting until ${banned.until}.`}
          </p>
          <p className="text-amber-600 text-xs mt-3">
            You can still browse the marketplace and use your account normally.
          </p>
          <button
            onClick={() => navigate('/')}
            className="mt-6 bg-amber-600 hover:bg-amber-700 text-white font-medium px-6 py-2.5 rounded-lg text-sm transition-colors"
          >
            Back to feed
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <PlusSquare size={24} className="text-blue-600" />
        New listing
      </h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 mb-4 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        {/* Images */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Photos (up to 5)</label>
          <div className="flex flex-wrap gap-2">
            {previews.map((src, i) => (
              <div key={i} className="relative w-20 h-20 rounded-xl overflow-hidden border border-gray-200">
                <img src={src} alt="" className="w-full h-full object-cover" />
                <button type="button" onClick={() => removeImage(i)}
                  className="absolute top-0.5 right-0.5 bg-black/60 hover:bg-black/80 text-white rounded-full p-0.5">
                  <X size={12} />
                </button>
              </div>
            ))}
            {images.length < 5 && (
              <label className="w-20 h-20 rounded-xl border-2 border-dashed border-gray-300 hover:border-blue-400 cursor-pointer flex flex-col items-center justify-center text-gray-400 hover:text-blue-500 transition-colors">
                <Upload size={20} />
                <span className="text-xs mt-1">Add</span>
                <input type="file" accept="image/*" multiple className="hidden" onChange={handleImages} />
              </label>
            )}
          </div>
        </div>

        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
          <input
            type="text" required
            value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="What are you selling?"
          />
        </div>

        {/* Price */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Price ($) *</label>
          <input
            type="number" required min="0" step="0.01"
            value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })}
            className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="0.00"
          />
        </div>

        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
          <select
            value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}
            className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a category</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            rows={4} value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Describe your item…"
          />
        </div>

        <button type="submit" disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold py-3 rounded-xl transition-colors">
          {loading ? 'Submitting for review…' : 'Submit listing'}
        </button>

        <p className="text-xs text-center text-gray-400">
          Listings go live after moderator approval.
        </p>
      </form>
    </div>
  )
}
