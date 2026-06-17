import { useRef, useState } from 'react';
import { Brain, FileText, Link as LinkIcon, Play, Loader2 } from 'lucide-react';
import SourceCard from './SourceCard.jsx';

const TABS = [
  { id: 'pdf', label: 'PDF', icon: FileText },
  { id: 'url', label: 'URL', icon: LinkIcon },
  { id: 'youtube', label: 'YouTube', icon: Play },
];

export default function SourcePanel({ sources, onSourceAdded }) {
  const [activeTab, setActiveTab] = useState('pdf');
  const [urlInput, setUrlInput] = useState('');
  const [youtubeInput, setYoutubeInput] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const resetError = () => setError('');

  const handlePdfChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    resetError();
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/ingest/pdf', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      onSourceAdded();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleUrlSubmit = async () => {
    const url = urlInput.trim();
    if (!url || isUploading) return;

    resetError();
    setIsUploading(true);
    try {
      const response = await fetch('/api/ingest/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      setUrlInput('');
      onSourceAdded();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleYoutubeSubmit = async () => {
    const url = youtubeInput.trim();
    if (!url || isUploading) return;

    resetError();
    setIsUploading(true);
    try {
      const response = await fetch('/api/ingest/youtube', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }

      setYoutubeInput('');
      onSourceAdded();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex h-full w-[280px] flex-shrink-0 flex-col border-r border-white/10 bg-sidebar">
      <div className="flex items-center gap-2 border-b border-white/10 px-4 py-4">
        <Brain size={20} className="text-accent" />
        <h1 className="text-base font-semibold text-ink">DocuMind AI</h1>
      </div>

      <div className="flex border-b border-white/10 px-2 pt-2">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                resetError();
              }}
              className={`flex flex-1 items-center justify-center gap-1.5 rounded-t-md px-2 py-2 text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-white/5 text-ink border-b-2 border-accent'
                  : 'text-white/40 hover:text-white/70'
              }`}
            >
              <Icon size={14} />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="px-4 py-4">
        {activeTab === 'pdf' && (
          <div className="space-y-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handlePdfChange}
              disabled={isUploading}
              className="block w-full text-xs text-white/60 file:mr-3 file:rounded-md file:border-0 file:bg-accent file:px-3 file:py-2 file:text-xs file:font-medium file:text-white hover:file:bg-accent/80 file:cursor-pointer disabled:opacity-50"
            />
            {isUploading && (
              <div className="flex items-center gap-2 text-xs text-white/50">
                <Loader2 size={12} className="animate-spin" />
                Uploading and processing…
              </div>
            )}
          </div>
        )}

        {activeTab === 'url' && (
          <div className="space-y-2">
            <input
              type="text"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleUrlSubmit()}
              placeholder="https://example.com/article"
              disabled={isUploading}
              className="w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink placeholder:text-white/30 focus:border-accent focus:outline-none disabled:opacity-50"
            />
            <button
              onClick={handleUrlSubmit}
              disabled={isUploading || !urlInput.trim()}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-accent px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-accent/80 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isUploading && <Loader2 size={14} className="animate-spin" />}
              Add Source
            </button>
          </div>
        )}

        {activeTab === 'youtube' && (
          <div className="space-y-2">
            <input
              type="text"
              value={youtubeInput}
              onChange={(e) => setYoutubeInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleYoutubeSubmit()}
              placeholder="https://youtube.com/watch?v=..."
              disabled={isUploading}
              className="w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-ink placeholder:text-white/30 focus:border-accent focus:outline-none disabled:opacity-50"
            />
            <button
              onClick={handleYoutubeSubmit}
              disabled={isUploading || !youtubeInput.trim()}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-accent px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-accent/80 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isUploading && <Loader2 size={14} className="animate-spin" />}
              Add Source
            </button>
          </div>
        )}

        {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4">
        {sources.length === 0 ? (
          <p className="mt-4 text-center text-xs text-white/30">
            Add a PDF, URL, or YouTube video to get started
          </p>
        ) : (
          <div className="space-y-2">
            {sources.map((source) => (
              <SourceCard key={source.id} source={source} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
