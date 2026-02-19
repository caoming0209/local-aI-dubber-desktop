import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import SingleCreation from './pages/SingleCreation';
import BatchCreation from './pages/BatchCreation';
import AvatarManager from './pages/AvatarManager';
import VoiceManager from './pages/VoiceManager';
import WorksLibrary from './pages/WorksLibrary';
import Settings from './pages/Settings';
import Help from './pages/Help';
import { RoutePath } from './types';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path={RoutePath.HOME} element={<Home />} />
          <Route path={RoutePath.SINGLE_CREATE} element={<SingleCreation />} />
          <Route path={RoutePath.BATCH_CREATE} element={<BatchCreation />} />
          <Route path={RoutePath.AVATARS} element={<AvatarManager />} />
          <Route path={RoutePath.VOICES} element={<VoiceManager />} />
          <Route path={RoutePath.WORKS} element={<WorksLibrary />} />
          <Route path={RoutePath.SETTINGS} element={<Settings />} />
          <Route path={RoutePath.HELP} element={<Help />} />
          <Route path="*" element={<Navigate to={RoutePath.HOME} replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;