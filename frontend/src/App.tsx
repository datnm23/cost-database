import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import MainLayout from './components/Layout/MainLayout'
import Login from './pages/Auth/Login'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import FileUpload from './pages/FileUpload'
import LineItems from './pages/LineItems'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import MasterItems from './pages/MasterItems'
import WorkCodeGenerator from './pages/WorkCodeGenerator'
import MasterStatistics from './pages/MasterStatistics'
import PendingItemsReview from './pages/PendingItemsReview'
import QuarantineLog from './pages/QuarantineLog'
import BOQProcessing from './pages/BOQProcessing'
import NamingTools from './pages/NamingTools'
import CodeManagement from './pages/CodeManagement'
import SynonymManagement from './pages/SynonymManagement'
import SystemHealth from './pages/SystemHealth'
import TemplateManagement from './pages/TemplateManagement'
import { useAuthStore } from './store/authStore'

const { Content } = Layout

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <MainLayout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/projects" element={<Projects />} />
                  <Route path="/upload" element={<FileUpload />} />
                  <Route path="/line-items" element={<LineItems />} />
                  <Route path="/master-items" element={<MasterItems />} />
                  <Route path="/work-code-generator" element={<WorkCodeGenerator />} />
                  <Route path="/master-statistics" element={<MasterStatistics />} />
                  <Route path="/pending-items" element={<PendingItemsReview />} />
                  <Route path="/quarantine-log" element={<QuarantineLog />} />
                  <Route path="/boq-processing" element={<BOQProcessing />} />
                  <Route path="/naming-tools" element={<NamingTools />} />
                  <Route path="/code-management" element={<CodeManagement />} />
                  <Route path="/synonyms" element={<SynonymManagement />} />
                  <Route path="/system-health" element={<SystemHealth />} />
                  <Route path="/templates" element={<TemplateManagement />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </MainLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
