import { FileText, Link as LinkIcon, Play } from 'lucide-react';

const TYPE_CONFIG = {
  pdf: { icon: FileText, color: 'text-rose-400', bg: 'bg-rose-400/10' },
  url: { icon: LinkIcon, color: 'text-blue-400', bg: 'bg-blue-400/10' },
  youtube: { icon: Play, color: 'text-red-400', bg: 'bg-red-400/10' },
};

export default function SourceCard({ source }) {
  const config = TYPE_CONFIG[source.type] || TYPE_CONFIG.url;
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2.5 transition-colors hover:bg-white/[0.05] hover:border-white/20">
      <div className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md ${config.bg}`}>
        <Icon size={16} className={config.color} />
      </div>
      <div className="flex-1 overflow-hidden">
        <p className="truncate text-sm font-medium text-ink" title={source.title}>
          {source.title}
        </p>
        <p className="text-xs text-white/40">{source.chunk_count} chunks</p>
      </div>
    </div>
  );
}
