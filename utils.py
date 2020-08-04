import os
import uuid
import json

migrations_dir = os.path.join(os.getcwd(), 'migrations')
public_versions = os.path.join(migrations_dir, 'versions', 'public')
tenant_versions = os.path.join(migrations_dir, 'versions', 'tenants')


def new_migration(data, schema = 'tenant'):
    versions_dir = ''
    if schema is 'public':
        versions_dir = public_versions
    elif schema is 'tenant':
        versions_dir = tenant_versions
    else:
        raise ValueError(f'schema must be set to either "public" or "tenant". Value "{schema}" was provided instead')
    
    new_mig_name = f'{uuid.uuid4()}.json'
    with open(os.path.join(migrations_dir, 'config.json'), 'rb') as mig_config_file:
        mig_config = json.loads(mig_config_file.read())
        mig_names = [mig['name'] for mig in mig_config['migrations'][schema]]
        if new_mig_name in mig_names:
            raise ValueError(
                F' New migration "{new_mig_name}" already exists. Select another name')
    with open(os.path.join(versions_dir, new_mig_name), 'wb') as new_mig:
        new_mig.write(data)
        with open(os.path.join(os.getcwd(), 'migrations', f'{versions_dir}.json'), 'rb+') as mig_config_file:
            mig_config = json.loads(mig_config_file.read())
            mig_config['migrations'].append(new_mig_name)
            mig_config_file.write(json.dumps(mig_config))


def new_project(dsn, schema_table, schema_row):
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
        mig_config = {'dsn': dsn, 'schemaTable': schema_table,
                      'schemaRow': schema_row, 'migrations': {'public': [], 'tenant': []}, 'current_public': '', 'current_tenant': ''}
        mig_config_file.write(json.dumps(mig_config))

def read_sql()