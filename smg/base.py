import os
import uuid
import json
import re
import sqlparse
import asyncpg
import typer
from asyncpg.exceptions import DuplicateTableError


migrations_dir = os.path.join(os.getcwd(), 'migrations')
public_versions = os.path.join(migrations_dir, 'versions', 'public')
tenant_versions = os.path.join(migrations_dir, 'versions', 'tenants')
sql_public_dir = os.path.join(migrations_dir, 'sql', 'public')
sql_tenant_dir = os.path.join(migrations_dir, 'sql', 'tenant')


def new_migration(mig_data, sql_file, schema='tenant'):
    versions_dir = ''
    if schema is 'public':
        versions_dir = public_versions
    elif schema is 'tenant':
        versions_dir = tenant_versions
    else:
        raise ValueError(
            f'schema must be set to either "public" or "tenant". Schema value: "{schema}" was provided instead')

    new_mig_id = uuid.uuid4()
    new_mig_name = f'{new_mig_id}.json'
    with open(os.path.join(migrations_dir, 'config.json'), 'rb') as mig_config_file:
        mig_config = json.loads(mig_config_file.read())
        mig_names = [mig['name'] for mig in mig_config['migrations'][schema]]
        if new_mig_name in mig_names:
            raise ValueError(
                F' New migration "{new_mig_name}" already exists. Select another name')
    with open(os.path.join(versions_dir, new_mig_name), 'wb') as new_mig:
        new_mig.write(mig_data)
        with open(os.path.join(migrations_dir, 'config.json'), 'rb+') as mig_config_file:
            mig_config = json.loads(mig_config_file.read())
            mig_config['migrations'][schema].append(
                {'name': new_mig_name, 'sql': sql_file})
            with open(os.path.join(migrations_dir, 'config.json.backup')) as backup_file:
                backup_file.write(json.dumps(mig_config))
            mig_config_file.write(json.dumps(mig_config))
    return new_mig_id


async def new_project(db, schema_table, schema_row):
    try:
        os.mkdir('migrations')
    except:
        print('Directory "migrations" already exists. Will proceed through')

    try:
        os.mkdir(os.path.join(os.getcwd(), 'migrations', 'versions'))
        os.mkdir(os.path.join(os.getcwd(), 'migrations', 'versions', 'public'))
        os.mkdir(os.path.join(os.getcwd(), 'migrations', 'versions', 'tenant'))
    except:
        print('Directory "versions" already exists. Will proceed through')

    try:
        os.mkdir(os.path.join(os.getcwd(), 'migrations', 'sql'))
        os.mkdir(os.path.join(os.getcwd(), 'migrations', 'sql', 'public'))
        os.mkdir(os.path.join(os.getcwd(), 'migrations', 'sql', 'tenant'))
    except:
        print('Directory "sql" already exists. Will proceed through')

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
        columns = await con.fetch('''
        select *
        from INFORMATION_SCHEMA.COLUMNS
        where TABLE_NAME=$1
        ''', schema_table)
        print(schema_table)

    with open(os.path.join(os.getcwd(), 'migrations', 'config.json'), 'wb') as mig_config_file:
        mig_config = {'dsn': os.environ.get(db), 'schemaTable': schema_table,
                      'schemaRow': schema_row, 'migrations': {'public': [], 'tenant': []}, 'current_public': None, 'current_tenant': None}
        mig_config_file.write(json.dumps(mig_config))


def check_for_migrations(public):
    schema = None
    sql_files = []
    existing_migration_sql = []
    if public:
        schema = 'public'
        sql_files = [os.path.join(sql_public_dir, file) for file in os.listdir(
            sql_public_dir) if file.endswith('.sql')]
    else:
        schema = 'tenant'
        sql_files = [os.path.join(sql_tenant_dir, file) for file in os.listdir(
            sql_tenant_dir) if file.endswith('.sql')]
    with open(os.path.join(migrations_dir, 'config.json'), 'rb') as mig_config_file:
        mig_config = json.loads(mig_config_file.read())
        existing_migration_sql = [os.path.join(
            migrations_dir, 'sql', schema, migration['sql']) for migration in mig_config['migrations'][schema]]
    files_to_migrate_unprioritized = [
        file for file in sql_files if file not in existing_migration_sql]
    files_to_migrate_prioritized = []
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
                files_to_migrate_prioritized.append((file, 0))
    files_to_migrate_sorted = files_to_migrate_prioritized.sort(
        key=lambda x: x[1])
    files_to_migrate_parsed = [value[0] for value in files_to_migrate_sorted]
    return files_to_migrate_parsed


def make_migrations(public):
    schema = 'tenant'
    if public:
        schema = 'public'
    migration_files = check_for_migrations(public)
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
                        raise ValueError(
                            f'''Statement {str(sqlparse.format(stmt, reindent=True))} does not belong to upgrade or downgrade.''')
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


async def upgrade(public, to: int = None):
    with open(os.path.join(migrations_dir, 'config.json')) as config_file:
        to = to
        schema = None
        current_mig = None
        migrations = None
        schema_dir = None
        config = json.loads(config_file.read())
        con: asyncpg.Connection = await asyncpg.connect(config['dsn'])
        if public:
            schema = 'public'
            schema_dir = public_versions
            current_mig = config['current_public']
            migrations = config['migrations'][schema]
        elif not public:
            schema = 'tenant'
            schema_dir = tenant_versions
            current_mig = config['current_tenant']
            migrations = config['migrations'][schema]
        indexed_files = enumerate(migrations)
        current_mig_index = [
            i for i, mig in migrations if mig['name'] == current_mig][0]
        last_mig_index = None
        files_to_migrate = [os.path.join(schema_dir, mig['name'])
                            for i, mig in indexed_files if i > current_mig_index]

        if to:
            if to.endswith('.sql'):
                last_mig_index = [
                    i for i, mig in migrations if mig['sql'] == to][0]
            elif to.endswith('.json'):
                last_mig_index = [
                    i for i, mig in migrations if mig['name'] == to][0]
            else:
                raise ValueError(f'''Optional parameter "to" must be the name of a sql file or a json migration.
            Instead "{to}" was passed
            ''')
            assert last_mig_index > current_mig_index
            files_to_migrate = [os.path.join(
                schema_dir, mig['name']) for i, mig in indexed_files if i > current_mig_index and i <= last_mig_index]

        for file in files_to_migrate:
            file_id = uuid.UUID(os.path.basename(file).split('.')[0])
            with open(file) as mig_file:
                contents = json.loads(mig_file.read())
                upgrade = contents['upgrade']
                if public:
                    await con.execute(upgrade)
                else:
                    schemas = await con.fetch(f'SELECT {config["schemaRow"]}, version FROM {config["schemaTable"]}')
                    async with con.transaction() as t:
                        for schema, version in schemas:

                            await con.execute(f'SET search_path TO {schema}')
                            await con.execute(upgrade)
