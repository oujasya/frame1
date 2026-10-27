"""One-time, verified import from a stopped Django SQLite database."""
import copy
import io
import json
from pathlib import Path
from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command
from django.db import connections, transaction


class Command(BaseCommand):
    help = 'Import a Django SQLite snapshot into an empty PostgreSQL database.'

    def add_arguments(self, parser):
        parser.add_argument('--source', required=True)

    def handle(self, *args, **options):
        if connections['default'].vendor != 'postgresql':
            raise CommandError('The destination must be PostgreSQL.')
        source = Path(options['source']).resolve()
        if not source.is_file():
            raise CommandError('The source snapshot does not exist.')
        if any(model.objects.exists() for model in apps.get_app_config('core').get_models()):
            raise CommandError('Destination already contains FRAME data; import refused.')
        if apps.get_model('sessions', 'Session').objects.exists() or apps.get_model('admin', 'LogEntry').objects.exists():
            raise CommandError('Destination already contains session or admin data; import refused.')
        config = copy.deepcopy(settings.DATABASES['default'])
        config.update(ENGINE='django.db.backends.sqlite3', NAME=f'file:{source.as_posix()}?mode=ro', OPTIONS={'uri': True}, CONN_MAX_AGE=0)
        connections.databases['sqlite_import'] = config
        def exported(alias):
            stream = io.StringIO()
            call_command('dumpdata', database=alias, use_natural_foreign_keys=True,
                         exclude=['contenttypes', 'auth.permission'], stdout=stream, verbosity=0)
            records = json.loads(stream.getvalue())
            return records
        try:
            expected = exported('sqlite_import')
            # The fixture contains password hashes and sessions: keep it in ignored data/.
            fixture = settings.BASE_DIR / 'data' / 'postgres-import.json'
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text(json.dumps(expected), encoding='utf-8')
            with transaction.atomic():
                call_command('loaddata', str(fixture), verbosity=0)
                ordered = lambda rows: sorted(rows, key=lambda row: (row['model'], str(row['pk'])))
                if ordered(exported('default')) != ordered(expected):
                    raise CommandError('Imported records differ from SQLite. Import rolled back.')
            fixture.unlink()
            self.stdout.write(self.style.SUCCESS(f'Verified {len(expected)} records imported into PostgreSQL.'))
        finally:
            connections['sqlite_import'].close()
