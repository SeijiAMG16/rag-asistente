import React, { useState, useRef, useEffect } from 'react';
import { query as queryApi, syncDrive, uploadPdf, getConversations, getMessages, syncDriveFull } from './api';
import './Chat.css';

const Chat = ({ onLogout }) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [actionMsg, setActionMsg] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  // Cargar conversaciones al montar
  useEffect(() => {
    (async () => {
      try {
        const res = await getConversations();
        const list = res.conversations || [];
        setConversations(list);
        if (list.length > 0) setActiveConversation(list[0].id);
      } catch (e) {
        console.error('No se pudieron cargar conversaciones', e);
      }
    })();
  }, []);

  // Cargar mensajes al cambiar de conversación
  useEffect(() => {
    if (!activeConversation) { setMessages([]); return; }
    (async () => {
      try {
        const res = await getMessages(activeConversation);
        const msgs = (res.messages || []).map(m => ({
          id: m.id,
          text: m.text,
          sender: m.sender,
          timestamp: new Date(m.created_at).toLocaleTimeString()
        }));
        setMessages(msgs);
      } catch (e) {
        console.error('No se pudieron cargar mensajes', e);
        setMessages([]);
      }
    })();
  }, [activeConversation]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: message,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);

    try {
      const response = await queryApi(message, 5, activeConversation || undefined);
      const botMessage = {
        id: Date.now() + 1,
        text: response.answer,
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        sources: response.sources || []
      };
      setMessages(prev => [...prev, botMessage]);
      // Actualizar conversación activa si el backend la creó
      if (!activeConversation && response.conversation_id) {
        setActiveConversation(response.conversation_id);
        try {
          const r = await getConversations();
          setConversations(r.conversations || []);
        } catch {}
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Error al procesar la consulta. Intenta nuevamente.',
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setActiveConversation(null);
  };

  return (
    <div className="chat">
      <div className={`chat-container ${!sidebarOpen ? 'sidebar-closed' : ''}`}>
        {/* Sidebar */}
        <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
          <div className="sidebar-header">
            <button
              className="toggle-sidebar"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle sidebar"
            >
              {sidebarOpen ? '◀' : '▶'}
            </button>

            {sidebarOpen && (
              <button className="new-chat-btn" onClick={startNewConversation}>
                Nueva Conversación
              </button>
            )}
          </div>

          {sidebarOpen && (
            <>
              <div className="conversations-section">
                <h4 className="sidebar-title">Chats</h4>
                <div className="conversations-list">
                  {conversations.map(conv => (
                    <div
                      key={conv.id}
                      className={`conversation-item ${activeConversation === conv.id ? 'active' : ''}`}
                      onClick={() => setActiveConversation(conv.id)}
                      title={conv.title}
                    >
                      {conv.title}
                    </div>
                  ))}
                </div>

                <div className="sidebar-actions">
                  <button
                    className="action-btn"
                    onClick={async () => {
                      setActionMsg('Sincronizando Drive...');
                      try {
                        const r = await syncDrive();
                        setActionMsg(`Descargados: ${(r.downloaded||[]).length}, Omitidos: ${(r.skipped||[]).length}`);
                      } catch (e) {
                        setActionMsg('Error al sincronizar Drive');
                      }
                    }}
                  >
                    Sync Drive
                  </button>

                  <button
                    className="action-btn"
                    onClick={async () => {
                      setActionMsg('Sync + extraer + ingestar desde Drive...');
                      try {
                        const r = await syncDriveFull({ force: false });
                        const d = (r.downloaded||[]).length, s = (r.skipped||[]).length, i = (r.ingested||[]).length;
                        setActionMsg(`Descargados:${d} Omitidos:${s} Ingeridos:${i}`);
                      } catch (e) {
                        setActionMsg('Error en Sync+Ingest');
                      }
                    }}
                  >
                    Sync+Ingest Drive
                  </button>

                  <label className="upload-label">
                    Subir PDF
                    <input
                      type="file"
                      accept="application/pdf"
                      onChange={async (ev) => {
                        const f = ev.target.files?.[0]; if (!f) return;
                        setActionMsg('Subiendo/ingestando PDF...');
                        try {
                          const r = await uploadPdf(f);
                          setActionMsg(`Chunks agregados: ${r.chunks_added}`);
                        } catch (e) {
                          setActionMsg('Error al subir/ingerir');
                        }
                        ev.target.value = '';
                      }}
                    />
                  </label>

                  {actionMsg && <div className="action-msg">{actionMsg}</div>}
                </div>
              </div>

              <div className="sidebar-footer">
                <button className="logout-btn" onClick={onLogout}>
                  Cerrar Sesión
                </button>
              </div>
            </>
          )}
        </aside>

        {/* Main Chat Area */}
        <main className="chat-main">
          <header className="chat-header">
            <h1>Asistente RAG Inteligente</h1>
          </header>

          <section className="messages-container">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <div className="welcome-icon">🤖</div>
                <h2>¡Hola! Soy tu asistente para consultar documentación</h2>
                <p>Pregúntame lo que necesites sobre los documentos disponibles</p>
              </div>
            ) : (
              <>
                {messages.map(msg => (
                  <article key={msg.id} className={`message ${msg.sender}-message ${msg.isError ? 'error' : ''}`}>
                    <div className="message-avatar">
                      {msg.sender === 'user' ? '👤' : '🤖'}
                    </div>
                    <div className="message-bubble">
                      <div className="message-text">{msg.text}</div>

                      {msg.sources && msg.sources.length > 0 && (
                        <div className="message-sources">
                          <div className="sources-header">📄 Fuentes consultadas ({msg.sources.length}) ▼</div>
                          <div className="sources-list">
                            {msg.sources.map((source, idx) => (
                              <div key={idx} className="source-item">
                                🔗 {source.metadata?.source || `Fuente ${idx + 1}`}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="message-meta">
                        <span className="message-time">⏰ {msg.timestamp}</span>
                        {msg.sender === 'bot' && !msg.isError && (
                          <span className="message-feedback">
                            ¿Te ayudó esta respuesta?
                            <button className="feedback-btn" type="button" aria-label="Me ayudó">👍</button>
                            <button className="feedback-btn" type="button" aria-label="No me ayudó">👎</button>
                          </span>
                        )}
                      </div>
                    </div>
                  </article>
                ))}

                {isLoading && (
                  <article className="message bot-message">
                    <div className="message-avatar">🤖</div>
                    <div className="message-bubble">
                      <div className="typing-indicator" aria-label="Escribiendo">
                        <span></span><span></span><span></span>
                      </div>
                    </div>
                  </article>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </section>

          <footer className="input-container">
            <form onSubmit={handleSubmit} className="input-form">
              <div className="input-wrapper">
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Ingresa tu consulta"
                  className="message-input"
                  rows="1"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                />
                <button
                  type="submit"
                  className="send-button"
                  disabled={isLoading || !message.trim()}
                  aria-label="Enviar"
                  title="Enviar"
                >
                  ✈️
                </button>
              </div>
            </form>
          </footer>
        </main>
      </div>
    </div>
  );
};

export default Chat;