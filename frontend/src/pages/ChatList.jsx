import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageSquare, User } from 'lucide-react'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

export default function ChatList() {
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [chats, setChats] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) navigate('/login')
  }, [user, authLoading, navigate])

  useEffect(() => {
    if (!user) return
    api.get('/chats')
      .then(({ data }) => setChats(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [user])

  if (authLoading || !user) return null

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <MessageSquare size={24} className="text-blue-600" />
        Messages
      </h1>

      {loading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-2xl h-16 animate-pulse" />
          ))}
        </div>
      ) : chats.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <MessageSquare size={40} className="mx-auto mb-3 opacity-30" />
          <p>No conversations yet.</p>
          <p className="text-sm mt-1">Contact a seller from a product page to start chatting.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {chats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => navigate(`/chats/${chat.id}`)}
              className="w-full text-left bg-white border border-gray-100 hover:border-blue-200 rounded-2xl p-4 shadow-sm hover:shadow-md transition-all flex items-center gap-3"
            >
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 flex-shrink-0">
                <User size={18} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-800 text-sm">
                  {chat.opponent_name ?? `Chat #${chat.id.slice(0, 8)}`}
                </p>
                {chat.last_message && (
                  <p className="text-xs text-gray-500 truncate mt-0.5">{chat.last_message}</p>
                )}
              </div>
              {chat.created_at && (
                <span className="text-xs text-gray-400 flex-shrink-0">
                  {new Date(chat.created_at).toLocaleDateString()}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
