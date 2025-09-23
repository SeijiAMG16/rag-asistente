from django.apps import AppConfig
import os

class BootstrapConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bootstrap'

    def ready(self):
        # Ejecuta bootstrap si está habilitado por env y la base es MySQL
        if os.environ.get('AUTO_INIT_DB', '0') != '1':
            return
        if os.environ.get('USE_SQLITE', '1') == '1':
            return

        from django.conf import settings
        engine = settings.DATABASES['default']['ENGINE']
        if 'mysql' not in engine:
            return

        # Evitar en procesos de migración/collectstatic
        import sys
        if any(cmd in sys.argv for cmd in ['migrate', 'makemigrations', 'collectstatic', 'loaddata', 'dumpdata', 'shell']):
            return

        try:
            from django.core.management import call_command
            # Intenta migrar; si falla por base inexistente, crea y reintenta
            try:
                call_command('migrate')
                return
            except Exception:
                pass

            # Crear base y usuario con root (requiere DB_ADMIN_USER/PASSWORD)
            admin_user = os.environ.get('DB_ADMIN_USER', 'root')
            admin_password = os.environ.get('DB_ADMIN_PASSWORD', '')
            db_name = settings.DATABASES['default']['NAME']
            app_user = settings.DATABASES['default']['USER']
            app_password = settings.DATABASES['default']['PASSWORD']

            call_command('initdb',
                         **{
                             'admin_user': admin_user,
                             'admin_password': admin_password,
                             'host': settings.DATABASES['default'].get('HOST', '127.0.0.1'),
                             'port': int(settings.DATABASES['default'].get('PORT', '3306')),
                             'db_name': db_name,
                             'app_user': app_user,
                             'app_password': app_password,
                         })
            call_command('migrate')
        except Exception:
            # No interrumpir arranque en dev; logs del server mostrarán el error
            pass
