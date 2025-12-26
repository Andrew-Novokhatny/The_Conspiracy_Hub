import React from 'react';
import { createRoot } from 'react-dom/client';
import MusicXMLViewer from './MusicXMLViewer';

const rootElement = document.getElementById('root');
const root = createRoot(rootElement);
root.render(<MusicXMLViewer />);
