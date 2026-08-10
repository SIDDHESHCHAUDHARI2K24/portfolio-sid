import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthGuard } from '@/components/AuthGuard'
import { AdminLayout } from '@/components/AdminLayout'
import LoginPage from '@/routes/login'
import VerifyPage from '@/routes/login-verify'
import Dashboard from '@/routes/Dashboard'
import TimelineList from '@/routes/timeline/TimelineList'
import TimelineForm from '@/routes/timeline/TimelineForm'
import ProjectList from '@/routes/projects/ProjectList'
import ProjectForm from '@/routes/projects/ProjectForm'
import SkillsList from '@/routes/skills/SkillsList'
import SkillsForm from '@/routes/skills/SkillsForm'
import CertsList from '@/routes/certs/CertsList'
import CertsForm from '@/routes/certs/CertsForm'
import CollectionsList from '@/routes/collections/CollectionsList'
import CollectionsForm from '@/routes/collections/CollectionsForm'
import ProseList from '@/routes/prose/ProseList'
import ProseForm from '@/routes/prose/ProseForm'
import FormsList from '@/routes/forms/FormsList'
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
        <Route path="/projects" element={<ProjectList />} />
        <Route path="/projects/new" element={<ProjectForm />} />
        <Route path="/projects/:id/edit" element={<ProjectForm />} />
        <Route path="/skills" element={<SkillsList />} />
        <Route path="/skills/new" element={<SkillsForm />} />
        <Route path="/skills/:id/edit" element={<SkillsForm />} />
        <Route path="/certs" element={<CertsList />} />
        <Route path="/certs/new" element={<CertsForm />} />
        <Route path="/certs/:id/edit" element={<CertsForm />} />
        <Route path="/collections" element={<CollectionsList />} />
        <Route path="/collections/new" element={<CollectionsForm />} />
        <Route path="/collections/:id/edit" element={<CollectionsForm />} />
        <Route path="/prose" element={<ProseList />} />
        <Route path="/prose/new" element={<ProseForm />} />
        <Route path="/prose/:id/edit" element={<ProseForm />} />
        <Route path="/forms" element={<FormsList />} />
        <Route path="/tag-map" element={<TagMapMatrix />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
