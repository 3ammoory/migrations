import os
import uuid
import json
import re
import sqlparse

migrations_dir = os.path.join(os.getcwd(), 'migrations')
public_versions = os.path.join(migrations_dir, 'versions', 'public')
tenant_versions = os.path.join(migrations_dir, 'versions', 'tenants')
sql_public_dir = os.path.join(migrations_dir, 'sql', 'public')
sql_tenant_dir = os.path.join(migrations_dir, 'sql', 'tenant')


def new_migration(data, schema='tenant'):
    versions_dir = ''
    if schema is 'public':
        versions_dir = public_versions
    elif schema is 'tenant':
        versions_dir = tenant_versions
    else:
        raise ValueError(
            f'schema must be set to either "public" or "tenant". Value "{schema}" was provided instead')

    new_mig_name = f'{uuid.uuid4()}.json'
    with open(os.path.join(migrations_dir, 'config.json'), 'rb') as mig_config_file:
        mig_config = json.loads(mig_config_file.read())
        mig_names = [mig['name'] for mig in mig_config['migrations'][schema]]
        if new_mig_name in mig_names:
            raise ValueError(
                F' New migration "{new_mig_name}" already exists. Select another name')
    with open(os.path.join(versions_dir, new_mig_name), 'wb') as new_mig:
        new_mig.write(data)
        with open(os.path.join(migrations_dir, 'config.json'), 'rb+') as mig_config_file:
            mig_config = json.loads(mig_config_file.read())
            mig_config['migrations'][schema].append(new_mig_name)
            with open(os.path.join(migrations_dir, 'config.json.backup') as backup_file:
                backup_file.write(json.dumps(mig_config))
            mig_config_file.write(json.dumps(mig_config))


def new_project():
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

    with open(os.path.join(os.getcwd(), 'migrations', 'config.json'), 'wb') as mig_config_file:
        mig_config={'dsn': os.environ.get('DB_URL'), 'schemaTable': os.environ.get('SCHEMA_TABLE'),
                      'schemaRow': os.environ.get('SCHEMA_ROW'), 'migrations': {'public': [], 'tenant': []}, 'current_public': os.environ.get('CURRENT_PUBLIC'), 'current_tenant': os.environ.get('CURRENT_TENANT')}
        mig_config_file.write(json.dumps(mig_config))

def check_for_migrations(public):
    schema=None
    sql_files=[]
    existing_migration_sql=[]
    if public:
        schema='public'
        sql_files=[os.path.join(sql_public_dir, file) for file in os.listdir(
            sql_public_dir) if file.endswith('.sql')]
    else:
        schema='tenant'
        sql_files=[os.path.join(sql_tenant_dir, file) for file in os.listdir(
            sql_tenant_dir) if file.endswith('.sql')]
    with open(os.path.join(migrations_dir, 'config.json'), 'rb') as mig_config_file:
        mig_config=json.loads(mig_config_file.read())
        existing_migration_sql=[os.path.join(
            migrations_dir, 'sql', schema, migration['sql']) for migration in mig_config['migrations'][schema]]
    files_to_migrate_unprioritized=[
        file for file in sql_files if file not in existing_migration_sql]
    files_to_migrate_prioritized=[]
    for file in files_to_migrate_unprioritized:
        with open(file) as sql_file:
            contents=sql_file.read()
            priority_comment_match=re.match(
                r'\s*(\-\-\s*(priority):\s*\d+)', contents)
            if priority_comment_match:
                priority_comment=priority_comment_match.string
                priority_val=int(re.findall('\d+', priority_comment)[0])
                files_to_migrate_prioritized.append((file, priority_val))
            else:
                files_to_migrate_prioritized.append((file, 0))
    files_to_migrate_sorted=files_to_migrate_prioritized.sort(
        key=lambda x: x[1])
    files_to_migrate_parsed=[value[0] for value in files_to_migrate_sorted]
    return files_to_migrate_parsed

def make_migrations(public):
    migration_files=check_for_migrations(public)
    for sql_file in migration_files:
        with open(sql_file):
