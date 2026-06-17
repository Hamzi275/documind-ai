import { useEffect, useRef, useState } from 'react';
import { Send, FileText, Link as LinkIcon, Play } from 'lucide-react';

const TYPE_ICON = {
  pdf: FileText,
  url: LinkIcon,
  youtube: Play,
};

function CitationChip({ citation }) {
  const Icon = TYPE_ICON[citation.source_type] || LinkIcon;
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-white/60"
      title={citation.chunk_text}
    >
      <Icon size={11} />
      {citation.source_title}
    </span>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-1.5 py-1">
      <span className="typing-dot h-1.5 w-1.5 rounded-full bg-white/40" style={{ animationDelay: '0ms' }} />
      <span className="typing-dot h-1.5 w-1.5 rounded-full bg-white/40" style={{ animationDelay: '160ms' }} />
      <span className="typing-dot h-1.5 w-1.5 rounded-full bg-white/40" style={{ animationDelay: '320ms' }} />
    </div>
  );
}

export default function ChatPanel({ messages, setMessages, isStreaming, setIsStreaming }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    const maxHeight = 4 * 24; // ~4 rows
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, [input]);

  const sendMessage = async () => {
    const message = input.trim();
    if (!message || isStreaming) return;

    const history = messages.map((m) => ({ role: m.role, content: m.content }));

    setInput('');
    setIsStreaming(true);
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: message },
      { role: 'assistant', content: '', citations: [] },
    ]);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, chat_history: history }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop();

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data:')) continue;
          const payload = line.slice(5).trimStart();
          if (!payload || payload === '[DONE]') continue;

          if (payload.startsWith('__CITATIONS__')) {
            const citations = JSON.parse(payload.replace('__CITATIONS__', ''));
            // IMMUTABLE update: build a new message object instead of
            // mutating the existing one in place. React 18 StrictMode
            // double-invokes setState updater functions in development
            // to catch exactly this kind of impurity — an in-place
            // mutation here would silently double-apply on every call.
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = { ...last, citations };
              return updated;
            });
            continue;
          }

          // Tokens arrive JSON-encoded (backend uses json.dumps per token).
          // This is necessary, not optional: a token can itself be a
          // literal "\n\n" (common for paragraph breaks), which would
          // otherwise be indistinguishable from the SSE frame delimiter
          // and corrupt the split('\n\n') parsing above. JSON.parse safely
          // recovers the exact original token text either way.
          let token;
          try {
            token = JSON.parse(payload);
          } catch {
            token = payload;
          }

          // Same immutability fix as above: create a new message object
          // with the appended content rather than mutating `.content`
          // in place, so double-invocation under StrictMode is harmless.
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            updated[updated.length - 1] = { ...last, content: last.content + token };
            return updated;
          });
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        updated[updated.length - 1] = { ...last, content: `Error: ${err.message}` };
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-full flex-1 flex-col bg-chat">
      <div className="border-b border-white/10 px-6 py-4">
        <h2 className="text-base font-semibold text-ink">Chat</h2>
        <p className="text-xs text-white/40">Ask across all your sources</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-white/30">Ask a question about your uploaded sources</p>
          </div>
        ) : (
          <div className="space-y-5">
            {messages.map((msg, idx) => {
              const isLast = idx === messages.length - 1;
              const isStreamingThis = isLast && isStreaming && msg.role === 'assistant';

              if (msg.role === 'user') {
                return (
                  <div key={idx} className="flex justify-end">
                    <div className="max-w-[75%] rounded-lg bg-[#2d2d2d] px-4 py-2.5 text-sm text-white">
                      {msg.content}
                    </div>
                  </div>
                );
              }

              return (
                <div key={idx} className="flex flex-col gap-2">
                  <div className="max-w-[85%] whitespace-pre-wrap text-sm leading-relaxed text-ink">
                    {msg.content.length === 0 && isStreamingThis ? (
                      <TypingIndicator />
                    ) : (
                      <>
                        {msg.content}
                        {isStreamingThis && (
                          <span className="streaming-cursor text-accent">▌</span>
                        )}
                      </>
                    )}
                  </div>
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {msg.citations.map((c, cIdx) => (
                        <CitationChip key={cIdx} citation={c} />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-white/10 px-6 py-4">
        <div className="flex items-end gap-3 rounded-lg border border-white/10 bg-white/5 px-3 py-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question…"
            rows={1}
            className="flex-1 resize-none bg-transparent text-sm text-ink placeholder:text-white/30 focus:outline-none"
          />
          <button
            onClick={sendMessage}
            disabled={isStreaming || !input.trim()}
            className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-accent text-white transition-colors hover:bg-accent/80 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Send size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}