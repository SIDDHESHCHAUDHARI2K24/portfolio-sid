import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthGuard } from '@/components/AuthGuard'
import { AdminLayout } from '@/components/AdminLayout'
import LoginPage from '@/routes/login'
import VerifyPage from '@/routes/login-verify'
import Dashboard from '@/routes/Dashboard'
import TimelineList from '@/routes/timeline/TimelineList'
import TimelineForm from '@/routes/timeline/TimelineForm'
import TagMapMatrix from '@/routes/TagMapMatrix'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/login/verify" element={<VerifyPage />} />

      <Route
        element={
          <AuthGuard>
            <AdminLayout />
          </AuthGuard>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="/timeline" element={<TimelineList />} />
        <Route path="/timeline/new" element={<TimelineForm />} />
        <Route path="/timeline/:id/edit" element={<TimelineForm />} />
        <Route path="/tag-map" element={<TagMapMatrix />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
