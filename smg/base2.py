import os
import re
import typer
import asyncpg
from asyncpg import DuplicateTableError
from .utils import check_dir, is_projectdir
import json
from pathlib import Path
import sqlparse
from .exceptions import ExistingMigrationError, EmptyContentError, UnidentifiedSQLError, NoMigrationsError

ROOT = Path(os.getcwd())
PUBLIC_DIR = ROOT / 'public'
TENANT_DIR = ROOT / 'tenant'
PUBLIC_SQL = PUBLIC_DIR / 'sql'
TENANT_SQL = TENANT_DIR / 'sql'
PUBLIC_MIGRATIONS = PUBLIC_DIR / 'migrations'
TENANT_MIGRATIONS = TENANT_DIR / 'migrations'


class Migrator:

    config = {}
    latest_file = {}
    public = False

    @classmethod
    def read_file(cls, file='config.json'):
        check_dir()
        with open(file) as _file:
            if file is 'config.json':
                cls.config = json.loads(_file.read())
                return cls.config
            else:
                cls.latest_file = json.loads(_file.read())
                return cls.latest_file

    @classmethod
    def write_file(cls, data=None, file='config.json'):
        content = cls.config
        if data:
            content = data
        if not content:
            raise EmptyContentError
        with open(file, 'w') as _file:
            _file.write(json.dumps(content))

    @classmethod
    async def new_project(cls, db, schema_table, schema_row, name):
        if is_projectdir():
            procceed = typer.confirm(
                'This foder seems to contain an already existing project. Are you sure you want to create your new project here?')
            if not procceed:
                raise typer.Abort()
        try:
            os.mkdir(name)
        except:
            typer.secho(
                f'Directory "{name}" already exists. Will proceed through')

        try:
            os.mkdir(ROOT / name / 'public')
            os.mkdir(ROOT / name / 'public' / 'migrations')
            os.mkdir(ROOT / name / 'public' / 'sql')
        except:
            typer.secho(
                'Directory "public" already exists. Will proceed through')

        try:
            os.mkdir(ROOT / name / 'tenant')
            os.mkdir(ROOT / name / 'tenant' / 'migrations')
            os.mkdir(ROOT / name / 'tenant' / 'sql')
        except:
            typer.secho(
                'Directory "tenants" already exists. Will proceed through')

        con: asyncpg.Connection = await asyncpg.connect(db)
        try:
            await con.execute(f'''
            CREATE TABLE {schema_table} (
            {schema_row} VARCHAR(32) NOT NULL UNIQUE,
            created DATE NOT NULL DEFAULT NOW(),
            version UUID
        )
        ''')
        except DuplicateTableError as e:
            typer.secho(
                f'WARNING: Table {schema_table} already exists.Checking if column {schema_row} exists', fg='yellow')
            column_records = await con.fetch('''
            SELECT column_name
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = $1
            AND TABLE_SCHEMA = 'public'
            ''', schema_table)
            columns = [val for record in column_records for val in record]
            if schema_row in columns:
                typer.secho(
                    f'WARNING: column {schema_row} already exists. Checking its datatype', fg='yellow')
                current_row_type = await con.fetchval('''
                SELECT DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = $1
                AND TABLE_SCHEMA = 'public'
                AND COLUMN_NAME = $2
                ''', schema_table, schema_row)
                if current_row_type != 'character varying':
                    overwrite = typer.confirm(
                        f'Column "{schema_row}" is of type {current_row_type}. Are you sure you want to change it to VARCHAR')
                    if not overwrite:
                        typer.secho(
                            'WARNING: schema column is not of type VARCHAR. This culd result in errors in the future.', fg='yellow')
                    else:
                        await con.execute(f'''ALTER TABLE {schema_table}
                                            ALTER COLUMN {schema_row} TYPE VARCHAR(32)''')
                else:
                    typer.secho(
                        f'column {schema_row} is of correct datatype. Skipping overwrite', fg='green')
            else:
                typer.secho(
                    f'WARNING: column {schema_row} was not found in existing table {schema_table}. Attempting to create it', fg='yellow')
                await con.execute(f'''
                ALTER TABLE {schema_table}
                ADD COLUMN {schema_row} VARCHAR(32) UNIQUE
                ''')
        mig_config = {'dsn': db, 'schemaTable': schema_table,
                      'schemaRow': schema_row, 'migrations': {'public': [], 'tenant': []}, 'current_public': None, 'current_tenant': None}
        cls.write_file(data=mig_config, file=Path(ROOT) / name / 'config.json')

    @classmethod
    def new_migration(cls, mig_data, sql_file):
        migrations_dir = TENANT_MIGRATIONS
        schema = 'tenant'
        if cls.public:
            migrations_dir = public_versions
            schema = 'public'

        new_mig_id = uuid.uuid4()
        new_mig_name = f'{new_mig_id}.json'
        mig_config = cls.read_config()
        mig_names = [mig['name'] for mig in mig_config['migrations'][schema]]
        if new_mig_name in mig_names:
            raise ExistingMigrationError()
        with open(migrations_dir / new_mig_name, 'w') as new_mig:
            new_mig.write(json.dumps(mig_data))
            cls.write_config(file='config.json.backup')
            cls.config['migrations'][schema].append(
                {'name': new_mig_name, 'sql': sql_file})
            cls.write_config()
        return new_mig_id

    @classmethod
    def check_for_migrations(cls):
        schema = 'tenant'
        sql_dir = TENANT_SQL
        sql_files = [
            TENANT_SQL / file for file in os.listdir(TENANT_SQL) if file.endswith('.sql')]
        existing_migration_sql = []
        if cls.public:
            schema = 'public'
            sql_dir = PUBLIC_SQL
            sql_files = [
                PUBLIC_SQL / file for file in os.listdir(PUBLIC_SQL) if file.endswith('.sql')]
        mig_config = cls.read_file()
        existing_migration_sql = [sql_dir / migration['sql']
                                  for migration in mig_config['migrations'][schema]]
        files_to_migrate_unprioritized = [
            file for file in sql_files if file not in existing_migration_sql]
        files_to_migrate_prioritized = []
        if not files_to_migrate_unprioritized:
            raise NoMigrationsError()

        for file in files_to_migrate_unprioritized:
            with open(file) as sql_file:
                contents = sql_file.read()
                priority_comment_match = re.match(
                    r'\s*(\-\-\s*(priority):\s*\d+)', contents)
                if priority_comment_match:
                    priority_comment = priority_comment_match.string
                    priority_val = int(re.findall('\d+', priority_comment)[0])
                    files_to_migrate_prioritized.append((file, priority_val))
                else:
                    files_to_migrate_prioritized.append((file, 1))
        files_to_migrate_sorted = files_to_migrate_prioritized.sort(
            key=lambda x: x[1])
        print(files_to_migrate_sorted)
        files_to_migrate_parsed = [value[0]
                                   for value in files_to_migrate_sorted]
        return files_to_migrate_parsed

    @classmethod
    def make_migrations(cls):
        schema = 'tenant'
        if cls.public:
            schema = 'public'
        migration_files = []
        migration_files = cls.check_for_migrations()
        for sql_file in migration_files:
            upgrade = None
            downgrade = None
            last_comment = None
            with open(sql_file) as file:
                contents = file.read()
                stmts = sqlparse.parse(contents)
                for stmt in stmts:
                    upgrade_comment_match = re.match(
                        r'\s*(\-\-\s*(upgrade)\s*)', str(stmt))

                    downgrade_comment_match = re.match(
                        r'\s*(\-\-\s*(downgrade)\s*)', str(stmt))
                    if upgrade_comment_match:
                        upgrade = str(stmt)
                        last_comment = upgrade
                    elif downgrade_comment_match:
                        downgrade = str(stmt)
                        last_comment = downgrade
                    else:
                        if not last_comment:
                            raise UnidentifiedSQLError(sqlparse.format(
                                str(stmt), reindent=True), sql_file)
                        elif last_comment == upgrade:
                            upgrade = ''.join([upgrade, stmt])
                            last_comment = upgrade
                        elif last_comment == downgrade:
                            downgrade = ''.join([downgrade, stmt])
                            last_comment = downgrade
                        else:
                            raise ValueError(
                                'variable "last_comment" does not match upgrade or downgrade. Please fix this bug')
            migration_data = {'upgrade': str(sqlparse.format(upgrade, reindent=True, strip_comments=True)), 'downgrade': str(
                sqlparse.format(downgrade, reindent=True, strip_comments=True))}
            new_migration(migration_data, os.path.basename(sql_file))
