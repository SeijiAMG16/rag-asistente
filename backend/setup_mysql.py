#!/usr/bin/env python
"""
Script para configurar automáticamente la base de datos MySQL
y ejecutar las migraciones de Django.
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import django
from django.core.management import execute_from_command_line
from django.core.management.base import CommandError
from dotenv import load_dotenv

def create_database():
    """Crear la base de datos MySQL si no existe"""
    load_dotenv()
    
    db_name = os.getenv('DB_NAME', 'rag_asistente')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    
    try:
        # Conectar a MySQL sin especificar la base de datos
        connection = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Crear la base de datos si no existe
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Base de datos '{db_name}' creada o ya existe")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"❌ Error al conectar con MySQL: {e}")
        print("\n🔧 Asegúrate de que:")
        print("   - MySQL está instalado y ejecutándose")
        print("   - Las credenciales en .env son correctas")
        print("   - El usuario tiene permisos para crear bases de datos")
        return False

def run_migrations():
    """Ejecutar las migraciones de Django"""
    try:
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        django.setup()
        
        print("\n🔄 Ejecutando migraciones...")
        
        # Crear migraciones si no existen
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        # Aplicar migraciones
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Migraciones aplicadas correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al ejecutar migraciones: {e}")
        return False

def create_superuser():
    """Crear un superusuario si no existe"""
    try:
        from django.contrib.auth.models import User
        
        if not User.objects.filter(is_superuser=True).exists():
            print("\n👤 Creando superusuario...")
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            print("✅ Superusuario creado: admin / admin123")
        else:
            print("ℹ️ Ya existe un superusuario")
            
    except Exception as e:
        print(f"❌ Error al crear superusuario: {e}")

def main():
    """Función principal"""
    print("🚀 Configurando base de datos MySQL para RAG Asistente")
    print("=" * 50)
    
    # Paso 1: Crear la base de datos
    if not create_database():
        sys.exit(1)
    
    # Paso 2: Ejecutar migraciones
    if not run_migrations():
        sys.exit(1)
    
    # Paso 3: Crear superusuario
    create_superuser()
    
    print("\n🎉 Configuración completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("   1. Instalar dependencias: pip install -r requirements.txt")
    print("   2. Ejecutar servidor: python manage.py runserver")
    print("   3. Acceder al admin: http://localhost:8000/admin/")

if __name__ == '__main__':
    main()