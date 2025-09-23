from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import health_view, query_view, ingest_view, register_view, sync_drive_view, ingest_upload_view, conversations_view, messages_view, sync_drive_full_view

# URLs de la API - Endpoints disponibles
urlpatterns = [
    # Endpoints de autenticación JWT
    path("auth/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),  # Login
    path("auth/refresh", TokenRefreshView.as_view(), name="token_refresh"),       # Renovar token
    path("auth/register", register_view, name="register"),                        # Registro de usuarios
    
    # Endpoints de la aplicación
    path("health", health_view, name="health"),      # Verificar estado del servidor
    path("query", query_view, name="query"),         # Realizar consultas RAG
    path("ingest", ingest_view, name="ingest"),      # Ingerir documentos
    path("sync-drive", sync_drive_view, name="sync_drive"),  # Sincronizar PDFs desde Drive
    path("sync-drive/full", sync_drive_full_view, name="sync_drive_full"),  # Sync + extraer + ingestar
    path("ingest/upload", ingest_upload_view, name="ingest_upload"),  # Subir PDF y reingestar
    path("conversations", conversations_view, name="conversations"),
    path("conversations/<int:conv_id>/messages", messages_view, name="messages"),
]
