import React, { useState } from "react";
import { register } from "./api";
import "./Login.css";

/**
 * Componente de registro de usuarios
 * Permite crear nuevas cuentas conectando con el endpoint /auth/register del backend
 */
export default function Register({ onRegister, onBackToLogin }) {
  // Estados del formulario de registro
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * Maneja el envío del formulario de registro
   * Valida los datos y envía la petición al backend
   */
  async function handleRegister(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    // Validaciones del lado del cliente
    if (!username.trim() || !email.trim() || !password || !confirmPassword) {
      setError("Todos los campos son requeridos");
      setLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres");
      setLoading(false);
      return;
    }

    // Validación básica de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Por favor ingresa un email válido");
      setLoading(false);
      return;
    }

    try {
      // Enviar petición de registro al backend
      await register(username, email, password);
      setSuccess("Usuario creado exitosamente. Ahora puedes iniciar sesión.");

      // Limpiar formulario después del registro exitoso
      setUsername("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");

      // Opcional: redirigir automáticamente al login después de 2 segundos
      setTimeout(() => {
        onBackToLogin();
      }, 2000);
    } catch (err) {
      // Manejar errores del servidor
      const errorMessage = err.response?.data?.error || "Error al crear la cuenta";
      setError(errorMessage);
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
          onSubmit={handleRegister}
          className="auth-form gpt-card"
          role="form"
          aria-labelledby="register-title"
        >
          <header className="form-header">
            {/* Logo simple */}
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

            <h2 id="register-title" className="title">
              Crear cuenta
            </h2>
            <p className="subtitle">Regístrate para comenzar</p>
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

          {/* Campo de email */}
          <div className="input-group">
            <span className="icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="18" height="18">
                <path
                  d="M20 6H4a2 2 0 0 0-2 2v.2l10 6.3 10-6.3V8a2 2 0 0 0-2-2Zm0 4.3-9.4 5.9a1 1 0 0 1-1.2 0L4 10.3V18a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2Z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <label htmlFor="email" className="sr-only">
              Correo electrónico
            </label>
            <input
              id="email"
              type="email"
              placeholder="Correo electrónico"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              autoComplete="email"
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
              placeholder="Contraseña (mínimo 6 caracteres)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              autoComplete="new-password"
              disabled={loading}
            />
          </div>

          {/* Campo de confirmación de contraseña */}
          <div className="input-group">
            <span className="icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="18" height="18">
                <path
                  d="M17 9h-1V7a4 4 0 1 0-8 0v2H7a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2Zm-6 0V7a3 3 0 1 1 6 0v2Z"
                  fill="currentColor"
                />
              </svg>
            </span>
            <label htmlFor="confirmPassword" className="sr-only">
              Confirmar contraseña
            </label>
            <input
              id="confirmPassword"
              type="password"
              placeholder="Confirmar contraseña"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="input-field"
              autoComplete="new-password"
              disabled={loading}
            />
          </div>

          {/* Botón de registro */}
          <button type="submit" disabled={loading} className="btn-primary gpt-btn">
            {loading ? (
              <>
                <span className="loading-spinner" aria-hidden="true"></span> Creando cuenta...
              </>
            ) : (
              "Crear Cuenta"
            )}
          </button>

          <div className="divider">
            <span>o</span>
          </div>

          {/* Botón para volver al login */}
          <button
            type="button"
            onClick={onBackToLogin}
            className="btn-secondary ghost-btn"
            disabled={loading}
          >
            ¿Ya tienes cuenta? Inicia sesión
          </button>

          {/* Mostrar mensajes de error / éxito */}
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}
        </form>
      </div>
    </div>
  );
}