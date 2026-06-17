import { useEffect, useState } from 'react';
import SourcePanel from './components/SourcePanel.jsx';
import ChatPanel from './components/ChatPanel.jsx';

export default function App() {
  const [sources, setSources] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const fetchSources = async () => {
    try {
      const response = await fetch('/api/ingest/sources');
      if (!response.ok) return;
      const data = await response.json();
      setSources(data);
    } catch {
      // Network errors here are non-fatal; the source list just stays
      // empty until the next successful refresh.
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-graphite">
      <SourcePanel sources={sources} onSourceAdded={fetchSources} />
      <ChatPanel
        messages={messages}
        setMessages={setMessages}
        isStreaming={isStreaming}
        setIsStreaming={setIsStreaming}
      />
    </div>
  );
}
