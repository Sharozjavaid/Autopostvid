import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import StaticSlideshow from './pages/StaticSlideshow';
import NarrativeSlideshow from './pages/NarrativeSlideshow';
import VideoGenerator from './pages/VideoGenerator';
import ScriptGenerator from './pages/ScriptGenerator';
import Automations from './pages/Automations';
import Settings from './pages/Settings';

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
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="projects" element={<Projects />} />
            <Route path="projects/:projectId" element={<StaticSlideshow />} />
            <Route path="static-slideshow" element={<StaticSlideshow />} />
            <Route path="static-slideshow/:projectId" element={<StaticSlideshow />} />
            <Route path="narrative-slideshow" element={<NarrativeSlideshow />} />
            <Route path="narrative-slideshow/:projectId" element={<NarrativeSlideshow />} />
            <Route path="video-generator" element={<VideoGenerator />} />
            <Route path="script-generator" element={<ScriptGenerator />} />
            <Route path="automations" element={<Automations />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
