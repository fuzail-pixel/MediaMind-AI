import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/auth'
import { getMe } from '../services/api'
import { Loader } from 'lucide-react'

export default function AuthCallback() {
  const navigate = useNavigate()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token  = params.get('token')

    if (token) {
      authService.setToken(token)
      getMe()
        .then((res) => {
          authService.setUser(res.data)
          navigate('/')
        })
        .catch(() => {
          authService.removeToken()
          navigate('/login')
        })
    } else {
      navigate('/login')
    }
  }, [navigate])

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="text-center">
        <Loader size={32} className="spinner text-accent mx-auto mb-3" />
        <p className="text-text-secondary text-sm">Logging you in…</p>
      </div>
    </div>
  )
}