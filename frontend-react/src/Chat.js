import React, { useState, useRef, useEffect } from 'react';
import { query as queryApi, syncDrive, uploadPdf, getConversations, getMessages, syncDriveFull } from './api';

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
        // refrescar lista de conversaciones
        try { const r = await getConversations(); setConversations(r.conversations || []); } catch {}
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
    <div className="chat-container">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <button className="toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? '←' : '→'}
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
              <h4>Chats</h4>
              <div className="conversations-list">
                {conversations.map(conv => (
                  <div
                    key={conv.id}
                    className={`conversation-item ${activeConversation === conv.id ? 'active' : ''}`}
                    onClick={() => setActiveConversation(conv.id)}
                  >
                    {conv.title}
                  </div>
                ))}
              </div>
              <div style={{padding:'10px'}}>
                <button className="new-chat-btn" onClick={async ()=>{
                  setActionMsg('Sincronizando Drive...');
                  try { const r = await syncDrive(); setActionMsg(`Descargados: ${(r.downloaded||[]).length}, Omitidos: ${(r.skipped||[]).length}`); } catch(e){ setActionMsg('Error al sincronizar Drive'); }
                }}>Sync Drive</button>
                <button className="new-chat-btn" style={{marginTop:8}} onClick={async ()=>{
                  setActionMsg('Sync + extraer + ingestar desde Drive...');
                  try {
                    const r = await syncDriveFull({ force: false });
                    const d = (r.downloaded||[]).length, s = (r.skipped||[]).length, i = (r.ingested||[]).length;
                    setActionMsg(`Descargados:${d} Omitidos:${s} Ingeridos:${i}`);
                  } catch(e){ setActionMsg('Error en Sync+Ingest'); }
                }}>Sync+Ingest Drive</button>
                <label style={{display:'block', marginTop:8}}>
                  Subir PDF
                  <input type="file" accept="application/pdf" onChange={async (ev)=>{
                    const f = ev.target.files?.[0]; if(!f) return;
                    setActionMsg('Subiendo/ingestando PDF...');
                    try { const r = await uploadPdf(f); setActionMsg(`Chunks agregados: ${r.chunks_added}`); } catch(e){ setActionMsg('Error al subir/ingerir'); }
                    ev.target.value = '';
                  }}/>
                </label>
                {actionMsg && <div style={{marginTop:6, fontSize:12}}>{actionMsg}</div>}
              </div>
            </div>
            
            <div className="sidebar-footer">
              <button className="logout-btn" onClick={onLogout}>
                Cerrar Sesión
              </button>
            </div>
          </>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="chat-main">
        <div className="chat-header">
          <h1>Asistente RAG Inteligente</h1>
        </div>

        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <div className="welcome-icon">🤖</div>
              <h2>¡Hola! Soy tu asistente para consultar documentación</h2>
              <p>Pregúntame lo que necesites sobre los documentos disponibles</p>
            </div>
          ) : (
            <>
              {messages.map(msg => (
                <div key={msg.id} className={`message ${msg.sender}-message`}>
                  <div className="message-avatar">
                    {msg.sender === 'user' ? '👤' : '🤖'}
                  </div>
                  <div className="message-content">
                    <div className="message-text">
                      {msg.text}
                    </div>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="message-sources">
                        <div className="sources-header">
                          📄 Fuentes consultadas ({msg.sources.length}) ▼
                        </div>
                        <div className="sources-list">
                          {msg.sources.map((source, idx) => (
                            <div key={idx} className="source-item">
                              🔗 {source.metadata?.source || `Fuente ${idx + 1}`}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="message-time">
                      ⏰ {msg.timestamp}
                    </div>
                    {msg.sender === 'bot' && !msg.isError && (
                      <div className="message-feedback">
                        <span>¿Te ayudó esta respuesta?</span>
                        <button className="feedback-btn">👍</button>
                        <button className="feedback-btn">👎</button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="message bot-message">
                  <div className="message-avatar">🤖</div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <div className="input-container">
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
              >
                ✈️
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chat;