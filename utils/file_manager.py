import configparser
import os
import json
import glob

script_dir = ''

def config_loc():
    return script_dir + '/config.ini'

def owners_loc():
    return script_dir + '/owners.json'

def logs_dir():
    return script_dir + '/logs/'

def make_config(path):
    config = configparser.ConfigParser()
    if not os.path.exists(path):
        config['discord'] = {'token': '', 'default_prefix': 'f!', 'channel_id': '0', 'guild_id': '0', 'role_id': '0'}
        config['twitch'] = {'key': '', 'token': '', 'user_id': ''}
        config['python'] = {'generate_logs': True}
        config.write(open(path, 'w'))
        print('Config generated. Please edit it with your token.')
        quit()

def make_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)

def make_json(path, data):
    with open(path, 'w') as w:
        json.dump(data, w, indent=4)

def delete_contents(path):
    for file in glob.glob(path + '*'):
        os.remove(file)