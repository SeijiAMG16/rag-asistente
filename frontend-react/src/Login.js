import React, { useState } from "react";
import { login } from "./api";
import "./Login.css";

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
        localStorage.setItem("token", data.access);
        localStorage.setItem("refresh", data.refresh || "");
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
    <div className="login">
      <div className="app-container">
        {/* Fondo decorativo estilo GPT */}
        <div className="bg-grid" aria-hidden="true" />
        <div className="bg-glow" aria-hidden="true" />

        <form
          onSubmit={handleLogin}
          className="auth-form gpt-card"
          role="form"
          aria-labelledby="login-title"
        >
          <header className="form-header">
            {/* Logo simple inspirado en GPT */}
            <div className="gpt-logo" aria-hidden="true">
              <svg viewBox="0 0 64 64" width="40" height="40">
                <path
                  d="M32 6c7 0 10 3 14 7s7 7 7 14-3 10-7 14-7 7-14 7-10-3-14-7-7-7-7-14 3-10 7-14 7-7 14-7z"
                  className="gpt-logo-ring"
                />
                <path
                  d="M19 25c6-10 20-10 26 0M45 39c-6 10-20 10-26 0"
                  className="gpt-logo-lines"
                />
              </svg>
            </div>

            <h2 id="login-title" className="title">
              Iniciar sesión
            </h2>
            <p className="subtitle">Bienvenido de vuelta</p>
          </header>

          {/* Campo de nombre de usuario */}
          <div className="input-group">
            <span className="icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="18" height="18">
                <path
                  d="M12 12a5 5 0 1 0-5-5 5 5 0 0 0 5 5Zm0 2c-5 0-9 2.5-9 5.5V22h18v-2.5C21 16.5 17 14 12 14Z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <label htmlFor="username" className="sr-only">
              Nombre de usuario
            </label>
            <input
              id="username"
              type="text"
              placeholder="Nombre de usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field"
              autoComplete="username"
              disabled={loading}
            />
          </div>

          {/* Campo de contraseña */}
          <div className="input-group">
            <span className="icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="18" height="18">
                <path
                  d="M17 9h-1V7a4 4 0 1 0-8 0v2H7a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2Zm-6 0V7a3 3 0 1 1 6 0v2Z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <label htmlFor="password" className="sr-only">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              placeholder="Contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          {/* Botón de inicio de sesión */}
          <button type="submit" disabled={loading} className="btn-primary gpt-btn">
            {loading ? (
              <>
                <span className="loading-spinner" aria-hidden="true"></span> Entrando...
              </>
            ) : (
              "Iniciar Sesión"
            )}
          </button>

          <div className="divider">
            <span>o</span>
          </div>

          {/* Botón para ir al registro */}
          <button
            type="button"
            onClick={onShowRegister}
            className="btn-secondary ghost-btn"
            disabled={loading}
          >
            ¿No tienes cuenta? Regístrate
          </button>

          {/* Mostrar mensajes de error */}
          {error && <div className="error-message">{error}</div>}
        </form>
      </div>
    </div>
  );
}