import os
import django
from io import StringIO
from django.core import management


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    os.environ['USE_SQLITE'] = '1'
    django.setup()

    buf = StringIO()
    management.call_command('dumpdata', 'auth.user', 'api.Conversation', 'api.Message', indent=2, stdout=buf)

    data = buf.getvalue()
    out_path = os.path.join(os.path.dirname(__file__), '..', 'export.json')
    out_path = os.path.abspath(out_path)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(data)
    print(f"Exported to {out_path} ({len(data)} bytes)")


if __name__ == '__main__':
    main()
