import { Link, useNavigate, useLocation } from 'react-router-dom'
import { ShoppingBag, PlusSquare, User, LogOut, MessageSquare, Home } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const active = (path) =>
    location.pathname === path
      ? 'text-blue-600 font-semibold'
      : 'text-gray-600 hover:text-blue-600'

  return (
    <header className="bg-white shadow-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 text-blue-600 font-bold text-lg">
          <ShoppingBag size={22} />
          <span className="hidden sm:inline">Marketplace</span>
        </Link>

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          <Link to="/" className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition-colors ${active('/')}`}>
            <Home size={17} />
            <span className="hidden sm:inline">Feed</span>
          </Link>

          {user && (
            <>
              <Link to="/create" className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition-colors ${active('/create')}`}>
                <PlusSquare size={17} />
                <span className="hidden sm:inline">Sell</span>
              </Link>
              <Link to="/chats" className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition-colors ${active('/chats')}`}>
                <MessageSquare size={17} />
                <span className="hidden sm:inline">Chats</span>
              </Link>
              <Link to="/profile" className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition-colors ${active('/profile')}`}>
                <User size={17} />
                <span className="hidden sm:inline">{user.first_name}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-gray-600 hover:text-red-600 transition-colors"
              >
                <LogOut size={17} />
                <span className="hidden sm:inline">Sign out</span>
              </button>
            </>
          )}

          {!user && (
            <Link to="/login" className="ml-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
              Sign in
            </Link>
          )}
        </nav>
      </div>
    </header>
  )
}
