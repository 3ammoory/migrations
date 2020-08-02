import os
import uuid
import json


def new_migration(versions_dir, data):
    new_mig_name = f'{uuid.uuid4()}.json'
    with open(os.path.join(os.getcwd(), 'migrations', 'config.json'), 'rb') as mig_config_file:
        mig_config = json.loads(mig_config_file.read())
        if new_mig_name in mig_config['migrations']:
            raise ValueError(
                F'migration {new_mig_name} already exists. Select another name')
    with open(os.path.join(os.getcwd(), 'migrations', 'versions', versions_dir, new_mig_name), 'wb') as new_mig:
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

    with open(os.path.join(os.getcwd(), 'migrations', 'config.json'), 'wb') as mig_config_file:
        mig_config = {'dsn': dsn, 'schemaTable': schema_table,
                      'schemaRow': schema_row, 'migrations': [], 'cwm': ''}
        mig_config_file.write(json.dumps(mig_config))
