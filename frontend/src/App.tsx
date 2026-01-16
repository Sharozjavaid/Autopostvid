import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { GalleryProvider } from './context/GalleryContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import StaticSlideshow from './pages/StaticSlideshow';
import NarrativeSlideshow from './pages/NarrativeSlideshow';
import VideoGenerator from './pages/VideoGenerator';
import ScriptGenerator from './pages/ScriptGenerator';
import Automations from './pages/Automations';
import Settings from './pages/Settings';
import Agent from './pages/Agent';
import CompletedProjectView from './pages/CompletedProjectView';
import Inspiration from './pages/Inspiration';
import MediaLibrary from './pages/MediaLibrary';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <GalleryProvider>
          <BrowserRouter>
            <Routes>
              {/* Public route - Login */}
              <Route path="/login" element={<Login />} />
              
              {/* Protected routes - require authentication */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }>
                <Route index element={<Dashboard />} />
                <Route path="projects" element={<Projects />} />
                <Route path="projects/:projectId" element={<CompletedProjectView />} />
                <Route path="static-slideshow" element={<StaticSlideshow />} />
                <Route path="static-slideshow/:projectId" element={<StaticSlideshow />} />
                <Route path="narrative-slideshow" element={<NarrativeSlideshow />} />
                <Route path="narrative-slideshow/:projectId" element={<NarrativeSlideshow />} />
                <Route path="video-generator" element={<VideoGenerator />} />
                <Route path="script-generator" element={<ScriptGenerator />} />
                <Route path="automations" element={<Automations />} />
                <Route path="settings" element={<Settings />} />
                <Route path="agent" element={<Agent />} />
                <Route path="inspiration" element={<Inspiration />} />
                <Route path="media" element={<MediaLibrary />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </GalleryProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
