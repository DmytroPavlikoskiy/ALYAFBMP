import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, Package, ShoppingCart, Bell, CheckCircle, Clock, AlertTriangle } from 'lucide-react'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'
import ProductCard from '../components/ProductCard'

const ORDER_STATUS = {
  CREATED:   { label: 'Pending',   cls: 'text-yellow-600 bg-yellow-50' },
  CONFIRMED: { label: 'Confirmed', cls: 'text-green-600 bg-green-50' },
  CANCELLED: { label: 'Cancelled', cls: 'text-gray-500 bg-gray-50' },
}

export default function Profile() {
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()

  const [myProducts, setMyProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [notifications, setNotifications] = useState([])
  const [tab, setTab] = useState('listings')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) navigate('/login')
  }, [user, authLoading, navigate])

  useEffect(() => {
    if (!user) return
    setLoading(true)
    Promise.all([
      api.get('/users/me/products').then(({ data }) => setMyProducts(data)).catch(() => {}),
      api.get('/orders/').then(({ data }) => setOrders(data)).catch(() => {}),
      api.get('/users/me').then(({ data }) => {
        setNotifications(data.notifications ?? [])
      }).catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [user])

  const markRead = async (notifId) => {
    try {
      await api.patch(`/users/me/notifications/${notifId}/read`)
      setNotifications((prev) => prev.map((n) => n.id === notifId ? { ...n, is_read: true } : n))
    } catch {}
  }

  const confirmOrder = async (orderId) => {
    try {
      await api.patch(`/orders/${orderId}/confirm`)
      setOrders((prev) => prev.map((o) => o.id === orderId ? { ...o, status: 'CONFIRMED' } : o))
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to confirm order.')
    }
  }

  const cancelOrder = async (orderId) => {
    if (!confirm('Cancel this order?')) return
    try {
      await api.patch(`/orders/${orderId}/cancel`)
      setOrders((prev) => prev.map((o) => o.id === orderId ? { ...o, status: 'CANCELLED' } : o))
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to cancel order.')
    }
  }

  const unread = notifications.filter((n) => !n.is_read).length

  if (authLoading || !user) return null

  const isBanned = user.banned_until && new Date(user.banned_until) > new Date()

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Profile header */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6 flex items-center gap-4">
        <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 flex-shrink-0">
          {user.avatar_url
            ? <img src={user.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
            : <User size={28} />}
        </div>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-gray-900">
            {user.first_name} {user.last_name ?? ''}
          </h1>
          <p className="text-sm text-gray-500">{user.email}</p>
          {isBanned && (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 px-3 py-1.5 rounded-full w-fit">
              <AlertTriangle size={13} />
              Posting restricted until {new Date(user.banned_until).toLocaleDateString()}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-6 w-fit">
        {[
          { key: 'listings', label: 'My listings', icon: Package, count: myProducts.length },
          { key: 'orders', label: 'Orders', icon: ShoppingCart, count: orders.length },
          { key: 'notifications', label: 'Notifications', icon: Bell, count: unread || undefined },
        ].map(({ key, label, icon: Icon, count }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === key ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Icon size={15} />
            {label}
            {count !== undefined && (
              <span className={`text-xs font-bold px-1.5 py-0.5 rounded-full ${
                tab === key ? 'bg-blue-100 text-blue-700' : 'bg-gray-200 text-gray-600'
              }`}>
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-2xl animate-pulse aspect-square" />
          ))}
        </div>
      ) : (
        <>
          {/* Listings tab */}
          {tab === 'listings' && (
            myProducts.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <Package size={40} className="mx-auto mb-3 opacity-30" />
                <p>You have no listings yet.</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                {myProducts.map((p) => <ProductCard key={p.id} product={p} showStatus />)}
              </div>
            )
          )}

          {/* Orders tab */}
          {tab === 'orders' && (
            orders.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <ShoppingCart size={40} className="mx-auto mb-3 opacity-30" />
                <p>No orders yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {orders.map((order) => {
                  const st = ORDER_STATUS[order.status] ?? ORDER_STATUS.CREATED
                  return (
                    <div key={order.id} className="bg-white border border-gray-100 rounded-2xl p-4 flex items-center gap-4 shadow-sm">
                      {/* Product thumb */}
                      <div className="w-14 h-14 bg-gray-100 rounded-xl overflow-hidden flex-shrink-0">
                        {order.product?.images?.[0]?.image_url
                          ? <img src={order.product.images[0].image_url} alt="" className="w-full h-full object-cover" />
                          : <Package size={24} className="m-auto mt-3 text-gray-300" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-800 truncate">
                          {order.product?.title ?? `Order #${order.id}`}
                        </p>
                        <p className="text-sm text-blue-600 font-semibold">
                          ${Number(order.product?.price ?? 0).toLocaleString()}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full flex items-center gap-1 ${st.cls}`}>
                            <Clock size={10} /> {st.label}
                          </span>
                          <span className="text-xs text-gray-400">
                            {new Date(order.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      {order.status === 'CREATED' && (
                        <div className="flex gap-2">
                          <button onClick={() => confirmOrder(order.id)}
                            className="text-xs bg-green-100 text-green-700 hover:bg-green-200 px-3 py-1.5 rounded-lg font-medium transition-colors">
                            Confirm
                          </button>
                          <button onClick={() => cancelOrder(order.id)}
                            className="text-xs bg-gray-100 text-gray-600 hover:bg-gray-200 px-3 py-1.5 rounded-lg font-medium transition-colors">
                            Cancel
                          </button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )
          )}

          {/* Notifications tab */}
          {tab === 'notifications' && (
            notifications.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <Bell size={40} className="mx-auto mb-3 opacity-30" />
                <p>No notifications.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {notifications.map((n) => (
                  <div key={n.id} className={`flex items-start gap-3 bg-white rounded-xl border p-4 shadow-sm transition-opacity ${n.is_read ? 'opacity-60 border-gray-100' : 'border-blue-100'}`}>
                    <CheckCircle size={18} className={n.is_read ? 'text-gray-300 mt-0.5' : 'text-blue-500 mt-0.5'} />
                    <div className="flex-1">
                      <p className="text-sm text-gray-800">{n.text}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {new Date(n.created_at).toLocaleString()}
                      </p>
                    </div>
                    {!n.is_read && (
                      <button onClick={() => markRead(n.id)}
                        className="text-xs text-blue-600 hover:underline flex-shrink-0">
                        Mark read
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )
          )}
        </>
      )}
    </div>
  )
}
