import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Layout/Navbar'
import Sidebar from './components/Layout/Sidebar'
import Home from './pages/Home'
import Library from './pages/Library'
import DocumentView from './pages/DocumentView'
import Login from './pages/Login'
import AuthCallback from './pages/AuthCallback'
import ProtectedRoute from './components/ProtectedRoute'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes — no layout */}
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />

        {/* Protected routes — with navbar + sidebar */}
        <Route path="/*" element={
          <ProtectedRoute>
            <div className="flex flex-col h-screen overflow-hidden">
              <Navbar />
              <div className="flex flex-1 overflow-hidden">
                <Sidebar />
                <main className="flex-1 overflow-auto bg-surface">
                  <Routes>
                    <Route path="/"               element={<Home />} />
                    <Route path="/library"        element={<Library />} />
                    <Route path="/documents/:id"  element={<DocumentView />} />
                    <Route path="*"               element={<Navigate to="/" replace />} />
                  </Routes>
                </main>
              </div>
            </div>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}