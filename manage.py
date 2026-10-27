import os,sys
if len(sys.argv)>1 and sys.argv[1] in {'migrate','makemigrations','dumpdata','loaddata','import_sqlite','import_legacy','dbshell','sqlmigrate','sqlsequencereset'}:
    os.environ.setdefault('FRAME_DATABASE_DIRECT','1')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
from django.core.management import execute_from_command_line
if __name__=='__main__':execute_from_command_line(sys.argv)
