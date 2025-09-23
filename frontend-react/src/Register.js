import React, { useState } from "react";
import { register } from "./api";

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
    <div className="app-container">
      <form onSubmit={handleRegister} className="auth-form">
        <h2>Crear Cuenta</h2>
        
        {/* Campo de nombre de usuario */}
        <input
          type="text"
          placeholder="Nombre de usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="input-field"
          disabled={loading}
        />
        
        {/* Campo de email */}
        <input
          type="email"
          placeholder="Correo electrónico"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="input-field"
          disabled={loading}
        />
        
        {/* Campo de contraseña */}
        <input
          type="password"
          placeholder="Contraseña (mínimo 6 caracteres)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="input-field"
          disabled={loading}
        />
        
        {/* Campo de confirmación de contraseña */}
        <input
          type="password"
          placeholder="Confirmar contraseña"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="input-field"
          disabled={loading}
        />
        
        {/* Botón de registro */}
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? (
            <>
              <span className="loading-spinner"></span> Creando cuenta...
            </>
          ) : (
            "Crear Cuenta"
          )}
        </button>
        
        {/* Botón para volver al login */}
        <button 
          type="button" 
          onClick={onBackToLogin} 
          className="btn-secondary"
          disabled={loading}
        >
          ¿Ya tienes cuenta? Inicia sesión
        </button>
        
        {/* Mostrar mensajes de error */}
        {error && <div className="error-message">{error}</div>}
        
        {/* Mostrar mensajes de éxito */}
        {success && <div className="success-message">{success}</div>}
      </form>
    </div>
  );
}