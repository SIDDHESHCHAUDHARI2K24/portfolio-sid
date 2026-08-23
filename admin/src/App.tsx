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
import PostList from '@/routes/posts/PostList'
import PostForm from '@/routes/posts/PostForm'
import ProseList from '@/routes/prose/ProseList'
import ProseForm from '@/routes/prose/ProseForm'
import FormsList from '@/routes/forms/FormsList'
import ResumeList from '@/routes/resumes/ResumeList'
import ResumeForm from '@/routes/resumes/ResumeForm'
import OverviewList from '@/routes/overview/OverviewList'
import OverviewForm from '@/routes/overview/OverviewForm'
import ThesisList from '@/routes/thesis/ThesisList'
import ThesisForm from '@/routes/thesis/ThesisForm'
import TagMapMatrix from '@/routes/TagMapMatrix'
import CrawlerHits from '@/routes/crawlers/CrawlerHits'

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
        <Route path="/posts" element={<PostList />} />
        <Route path="/posts/new" element={<PostForm />} />
        <Route path="/posts/:id/edit" element={<PostForm />} />
        <Route path="/prose" element={<ProseList />} />
        <Route path="/prose/new" element={<ProseForm />} />
        <Route path="/prose/:id/edit" element={<ProseForm />} />
        <Route path="/forms" element={<FormsList />} />
        <Route path="/overview" element={<OverviewList />} />
        <Route path="/overview/new" element={<OverviewForm />} />
        <Route path="/overview/:id/edit" element={<OverviewForm />} />
        <Route path="/resumes" element={<ResumeList />} />
        <Route path="/resumes/new" element={<ResumeForm />} />
        <Route path="/resumes/:id/edit" element={<ResumeForm />} />
        <Route path="/thesis" element={<ThesisList />} />
        <Route path="/thesis/new" element={<ThesisForm />} />
        <Route path="/thesis/:id/edit" element={<ThesisForm />} />
        <Route path="/tag-map" element={<TagMapMatrix />} />
        <Route path="/crawlers" element={<CrawlerHits />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
