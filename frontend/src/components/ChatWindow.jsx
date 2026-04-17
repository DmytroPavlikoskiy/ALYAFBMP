import { useState, useEffect, useRef, useCallback } from 'react'
import { Send, Wifi, WifiOff } from 'lucide-react'
import { getChatWebSocketUrl } from '../utils/websocketUrl'

export default function ChatWindow({ chatId, currentUserId, initialMessages = [] }) {
  const [messages, setMessages] = useState(initialMessages)
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const bottomRef = useRef(null)
  /** Якщо true — з’єднання закрили навмисно (unmount / заміна сокета), не плануємо reconnect. */
  const intentionalCloseRef = useRef(false)
  const reconnectTimerRef = useRef(null)

  const connect = useCallback(() => {
    clearTimeout(reconnectTimerRef.current)
    reconnectTimerRef.current = null

    const prev = wsRef.current
    if (prev) {
      intentionalCloseRef.current = true
      wsRef.current = null
      prev.close()
    }

    const token = localStorage.getItem('access_token')
    if (!token || !chatId) return

    const ws = new WebSocket(getChatWebSocketUrl(chatId, token))
    wsRef.current = ws

    ws.onopen = () => setConnected(true)

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        setMessages((prev) => {
          if (msg.id != null && prev.some((m) => m.id === msg.id)) return prev
          return [...prev, msg]
        })
      } catch {
        setMessages((prev) => [...prev, { text: event.data, sender_id: null, sent_at: new Date().toISOString() }])
      }
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
      if (intentionalCloseRef.current) {
        intentionalCloseRef.current = false
        return
      }
      reconnectTimerRef.current = setTimeout(() => connect(), 3000)
    }

    ws.onerror = () => ws.close()
  }, [chatId])

  useEffect(() => {
    connect()
    return () => {
      intentionalCloseRef.current = true
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
      const w = wsRef.current
      wsRef.current = null
      w?.close()
    }
  }, [connect])

  // Після refresh access_token (axios single-flight) — новий JWT у query, інакше WS лишається з простроченим токеном.
  useEffect(() => {
    const onAccessTokenChanged = () => connect()
    window.addEventListener('auth:access-token-changed', onAccessTokenChanged)
    return () => window.removeEventListener('auth:access-token-changed', onAccessTokenChanged)
  }, [connect])

  // Після повернення у вкладку перепідключитись, якщо сокет упав (сон вкладки, мережа).
  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState !== 'visible' || !chatId) return
      const w = wsRef.current
      if (!w || w.readyState === WebSocket.CLOSED || w.readyState === WebSocket.CLOSING) {
        connect()
      }
    }
    document.addEventListener('visibilitychange', onVis)
    return () => document.removeEventListener('visibilitychange', onVis)
  }, [connect, chatId])

  useEffect(() => {
    setMessages(initialMessages)
  }, [chatId, initialMessages])

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = () => {
    const text = input.trim()
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    wsRef.current.send(JSON.stringify({ text }))
    setInput('')
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Status bar */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-50 border-b border-gray-100 text-xs">
        {connected ? (
          <><Wifi size={13} className="text-green-500" /><span className="text-green-600 font-medium">Connected</span></>
        ) : (
          <><WifiOff size={13} className="text-gray-400" /><span className="text-gray-400">Reconnecting…</span></>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 text-sm mt-8">No messages yet. Say hello!</p>
        )}
        {messages.map((msg, i) => {
          const isMe = msg.sender_id === currentUserId
          return (
            <div key={i} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm shadow-sm ${
                isMe
                  ? 'bg-blue-600 text-white rounded-br-sm'
                  : 'bg-gray-100 text-gray-800 rounded-bl-sm'
              }`}>
                <p className="whitespace-pre-wrap break-words">{msg.text}</p>
                {msg.sent_at && (
                  <p className={`text-xs mt-1 ${isMe ? 'text-blue-200' : 'text-gray-400'}`}>
                    {new Date(msg.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                )}
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 p-3 flex gap-2">
        <textarea
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Type a message… (Enter to send)"
          className="flex-1 resize-none border border-gray-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || !connected}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white p-2.5 rounded-xl transition-colors"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  )
}
