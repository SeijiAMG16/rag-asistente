import React, { useState } from "react";
import { login } from "./api";

/**
 * Componente de inicio de sesión
 * Permite a los usuarios autenticarse con username y password
 */
export default function Login({ onLogin, onShowRegister }) {
  // Estados del formulario de login
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * Maneja el envío del formulario de login
   * Valida credenciales y autentica al usuario
   */
  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError("");

    // Validación básica del lado del cliente
    if (!username.trim() || !password) {
      setError("Por favor ingresa usuario y contraseña");
      setLoading(false);
      return;
    }

    try {
      // Enviar petición de login al backend
      const data = await login(username, password);
      try {
        localStorage.setItem('token', data.access);
        localStorage.setItem('refresh', data.refresh || '');
      } catch {}
      // Si el login es exitoso, notificar al componente padre
      onLogin();
    } catch (err) {
      // Manejar errores de autenticación
      if (err.response?.status === 401) {
        setError("Usuario o contraseña incorrectos");
      } else {
        setError("Error de conexión. Intenta nuevamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-container">
      <form onSubmit={handleLogin} className="auth-form">
        <h2>Iniciar Sesión</h2>
        
        {/* Campo de nombre de usuario */}
        <input
          type="text"
          placeholder="Nombre de usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="input-field"
          disabled={loading}
        />
        
        {/* Campo de contraseña */}
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="input-field"
          disabled={loading}
        />
        
        {/* Botón de inicio de sesión */}
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? (
            <>
              <span className="loading-spinner"></span> Entrando...
            </>
          ) : (
            "Iniciar Sesión"
          )}
        </button>
        
        {/* Botón para ir al registro */}
        <button 
          type="button" 
          onClick={onShowRegister} 
          className="btn-secondary"
          disabled={loading}
        >
          ¿No tienes cuenta? Regístrate
        </button>
        
        {/* Mostrar mensajes de error */}
        {error && <div className="error-message">{error}</div>}
      </form>
    </div>
  );
}
