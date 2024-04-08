import os
from typing import Dict, Optional, Union

import json5
from qwen_agent.log import logger
from qwen_agent.tools.base import BaseTool, register_tool
from qwen_agent.utils.utils import (extract_code, print_traceback, read_text_from_file,
                                    save_text_to_file)

DEFAULT_STORAGE_PATH = 'workspace/default_data_path'
SUCCESS_MESSAGE = 'SUCCESS'


@register_tool('local_cache')
class Storage(BaseTool):
    """
    This is a special tool for data storage
    """
    description = '数据在 本地缓存的实现, 读取、删除、保存、遍历， 支持txt或csv 格式'
    parameters = [{
        'name': 'operate',
        'type': 'string',
        'description':
        '数据操作类型，可选项为["put", "get", "delete", "scan"]之一，分别为存数据、取数据、删除数据、遍历数据',
        'required': True
    }, {
        'name': 'key',
        'type': 'string',
        'description': '数据的名称，是一份数据的唯一标识, 存/取/删除数据时 必须提供'
    }, {
        'name': 'value',
        'type': 'string',
        'description': '数据的内容，仅存数据时需要'
    }]

    def __init__(self, cfg: Optional[Dict] = None):
        super().__init__(cfg)
        self.root = self.cfg.get('storage_root_path', DEFAULT_STORAGE_PATH)
        os.makedirs(self.root, exist_ok=True)

    def call(self, params: Union[str, dict], **kwargs):
        """
        init one database: one folder
        :param params:
        """
        if isinstance(params, str) and params.startswith('```'):
            params = extract_code(params)

        params = self._verify_json_format_args(params)

        #path = params['path']
        #self.init(path)

        operate = params['operate']
        key = params.get('key', '/')
        if key.startswith('/'):
            key = key[1:]

        if operate == 'put':
            assert 'value' in params
            return self.put(key, params['value'])
        elif operate == 'get':
            return self.get(key)
        elif operate == 'delete':
            return self.delete(key)
        else:
            return self.scan(key)

    def put(self, key: str, value: str, path: Optional[str] = None) -> str:
        path = path or self.root

        # one file for one key value pair
        #key = hash_sha256(key)
        #path = os.path.join(path, key)
        path_dir = path[:path.rfind('/') + 1]
        if path_dir:
            os.makedirs(path_dir, exist_ok=True)

        save_text_to_file(path, value)
        return SUCCESS_MESSAGE

    def get(self, key: str, path: Optional[str] = None) -> str:
        path = path or self.root
        return read_text_from_file(os.path.join(path, key))

    def delete(self, key, path: Optional[str] = None) -> str:
        path = path or self.root
        path = os.path.join(path, key)
        if os.path.exists(path):
            os.remove(path)
            return f'Successfully deleted{key}'
        else:
            return f'Delete Failed: {key} does not exist'

    def get(self, key: str, re_load: bool = True):
        """
        get one value by key
        :param key: str
        :return: value: str
        """
        #key = hash_sha256(key)
        if key in self.data and self.data[key] and (not re_load):
            return self.data[key]
        try:
            # lazy reading
            content = read_text_from_file(os.path.join(self.root, key))
            self.data[key] = content
            return content
        except Exception:
            print_traceback()
            return ''

    def delete(self, key):
        """
        delete one key value pair
        :param key: str

        """
        #key = hash_sha256(key)
        try:
            if key in self.data:
                os.remove(os.path.join(self.root, key))
                self.data.pop(key)

            logger.info(f"Remove '{key}'")
        except OSError as ex:
            logger.error(f'Failed to remove: {ex}')

    def scan(self):
        #for key in self.data.keys():
        #    yield [key, self.get(key)]
        return '\n'.join(self.data.keys())

    def scan(self, key: str, path: Optional[str] = None) -> str:
        path = path or self.root
        path = os.path.join(path, key)
        if os.path.exists(path):
            if not os.path.isdir(path):
                return 'Scan Failed: The scan operation requires passing in a key to a folder path'
            # All key-value pairs
            kvs = {}
            for root, dirs, files in os.walk(path):
                for file in files:
                    k = os.path.join(root, file)[len(path):]
                    if not k.startswith('/'):
                        k = '/' + k
                    v = read_text_from_file(os.path.join(root, file))
                    kvs[k] = v
            return '\n'.join([f'{k}: {v}' for k, v in kvs.items()])
        else:
            return f'Scan Failed: {key} does not exist.'
