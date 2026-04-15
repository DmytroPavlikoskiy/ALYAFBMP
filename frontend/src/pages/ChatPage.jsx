import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'
import ChatWindow from '../components/ChatWindow'

export default function ChatPage() {
  const { chatId } = useParams()
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) navigate('/login')
  }, [user, authLoading, navigate])

  useEffect(() => {
    if (!user || !chatId) return
    api.get(`/chats/${chatId}/messages`)
      .then(({ data }) => setMessages(data.items ?? data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [user, chatId])

  if (authLoading || !user) return null

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 flex flex-col" style={{ height: 'calc(100vh - 56px)' }}>
      <Link to="/chats" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-blue-600 mb-4 transition-colors">
        <ChevronLeft size={16} /> All messages
      </Link>

      <div className="flex-1 min-h-0">
        {loading ? (
          <div className="bg-gray-100 rounded-2xl h-full animate-pulse" />
        ) : (
          <ChatWindow
            chatId={chatId}
            currentUserId={user.id}
            initialMessages={messages}
          />
        )}
      </div>
    </div>
  )
}
