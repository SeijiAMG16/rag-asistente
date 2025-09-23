# Configuración MySQL para RAG Asistente

## 🚀 Configuración Automática

Este proyecto está configurado para usar **MySQL** como base de datos principal. Sigue estos pasos para configurar todo automáticamente:

### Prerrequisitos

1. **MySQL instalado y ejecutándose**
   ```bash
   # Verificar que MySQL esté corriendo
   mysql --version
   ```

2. **Python 3.8+ instalado**

### Configuración Rápida

1. **Edita el archivo `.env`** con tus credenciales MySQL:
   ```env
   DB_NAME=rag_asistente
   DB_USER=root
   DB_PASSWORD=tu_password_mysql
   DB_HOST=localhost
   DB_PORT=3306
   ```

2. **Ejecuta el script de configuración automática**:
   ```powershell
   cd backend
   .\setup_complete.ps1
   ```

   Este script automáticamente:
   - ✅ Instala todas las dependencias
   - ✅ Crea la base de datos MySQL
   - ✅ Ejecuta las migraciones
   - ✅ Crea un usuario administrador
   - ✅ Configura todo para producción

### Configuración Manual (Alternativa)

Si prefieres configurar manualmente:

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar base de datos**:
   ```bash
   python setup_mysql.py
   ```

3. **Ejecutar migraciones**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Crear superusuario**:
   ```bash
   python manage.py init_mysql --create-admin
   ```

5. **Iniciar servidor**:
   ```bash
   python manage.py runserver
   ```

## 🗃️ Información de la Base de Datos

- **Motor**: MySQL 8.0+
- **Base de datos**: `rag_asistente`
- **Codificación**: UTF8MB4
- **Tablas principales**:
  - `auth_user`: Usuarios del sistema
  - `api_conversation`: Conversaciones de chat
  - `api_message`: Mensajes individuales

## 👤 Acceso Administrativo

- **URL**: http://localhost:8000/admin/
- **Usuario**: `admin`
- **Contraseña**: `admin123`

## 🔧 Comandos Útiles

```bash
# Ver estadísticas de la BD
python manage.py init_mysql

# Crear respaldo de la BD
mysqldump -u root -p rag_asistente > backup.sql

# Restaurar respaldo
mysql -u root -p rag_asistente < backup.sql

# Reiniciar migraciones (si es necesario)
python manage.py migrate --fake-initial
```

## 🐛 Solución de Problemas

### Error de conexión MySQL
```
django.db.utils.OperationalError: (2002, "Can't connect to MySQL server")
```
**Solución**: Verifica que MySQL esté ejecutándose y las credenciales sean correctas.

### Error de permisos
```
django.db.utils.OperationalError: (1045, "Access denied for user")
```
**Solución**: Verifica usuario y contraseña en el archivo `.env`.

### Error de base de datos inexistente
```
django.db.utils.OperationalError: (1049, "Unknown database 'rag_asistente'")
```
**Solución**: Ejecuta `python setup_mysql.py` para crear la base de datos automáticamente.

## 📋 Estructura de Datos

### Modelo de Conversación
```python
class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Modelo de Mensaje
```python
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=[('user', 'User'), ('bot', 'Bot')])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

## 🔄 Migración desde SQLite (si es necesario)

Si tienes datos en SQLite y quieres migrarlos:

1. **Exportar datos de SQLite**:
   ```bash
   python manage.py dumpdata > data.json
   ```

2. **Cambiar a MySQL y migrar**:
   ```bash
   python setup_mysql.py
   python manage.py loaddata data.json
   ```