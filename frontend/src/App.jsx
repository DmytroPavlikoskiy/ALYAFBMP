import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'

import Feed          from './pages/Feed'
import Login         from './pages/Login'
import Register      from './pages/Register'
import ProductDetail from './pages/ProductDetail'
import CreateProduct from './pages/CreateProduct'
import Profile       from './pages/Profile'
import ChatList      from './pages/ChatList'
import ChatPage      from './pages/ChatPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <main>
            <Routes>
              {/* Public */}
              <Route path="/"            element={<Feed />} />
              <Route path="/login"       element={<Login />} />
              <Route path="/register"    element={<Register />} />
              <Route path="/products/:id" element={<ProductDetail />} />

              {/* Protected */}
              <Route path="/create" element={
                <ProtectedRoute><CreateProduct /></ProtectedRoute>
              } />
              <Route path="/profile" element={
                <ProtectedRoute><Profile /></ProtectedRoute>
              } />
              <Route path="/chats" element={
                <ProtectedRoute><ChatList /></ProtectedRoute>
              } />
              <Route path="/chats/:chatId" element={
                <ProtectedRoute><ChatPage /></ProtectedRoute>
              } />

              {/* Fallback */}
              <Route path="*" element={
                <div className="text-center py-24 text-gray-400">
                  <p className="text-6xl mb-4">404</p>
                  <p>Page not found</p>
                </div>
              } />
            </Routes>
          </main>
        </div>
      </AuthProvider>
    </BrowserRouter>
  )
}
