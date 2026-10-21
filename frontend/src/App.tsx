/** Main App Component */
import { Routes, Route, Navigate } from 'react-router-dom';
import { MemoryListPage } from './pages/MemoryListPage';
import { MemoryDetailPage } from './pages/MemoryDetailPage';
import { ConsolidationPage } from './pages/ConsolidationPage';
import { Layout } from './components/Layout';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/memories" replace />} />
        <Route path="memories" element={<MemoryListPage />} />
        <Route path="memories/:id" element={<MemoryDetailPage />} />
        <Route path="consolidate" element={<ConsolidationPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/memories" replace />} />
    </Routes>
  );
}

export default App;