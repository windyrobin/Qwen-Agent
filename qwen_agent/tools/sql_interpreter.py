import asyncio
import atexit
import base64
import glob
import io
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union

import json5
import matplotlib
import PIL.Image
from jupyter_client import BlockingKernelClient

from qwen_agent.log import logger
from qwen_agent.tools.base import BaseTool, register_tool
from qwen_agent.utils.utils import (extract_code, print_traceback,
                                    save_url_to_local_work_dir)

#WORK_DIR = os.getenv('M6_CODE_INTERPRETER_WORK_DIR',
#                     os.getcwd() + '/workspace/ci_workspace/')


def _do_sql(code: str) -> List[Tuple]:
    import sqlite3
    conn = sqlite3.connect('/root/test.db')
    cs = conn.cursor()
    cs.execute(code)
    result = cs.fetchall()
    conn.close()
    return result

def _convert_list_of_tuple_to_csv(data):
    rows = []
    for row in data: 
        row_str = '|'.join(str(col) for col in row)
        rows.append(row_str)
    return '\n'.join(rows)


def _execute_code(code: str) -> str:
    result = ''
    while True:
        text = ''
        #msg_type = 'error'
        msg_type = 'display_data'
        try:
            rows = _do_sql(code)
            text = _convert_list_of_tuple_to_csv(rows) 
        except Exception:
            text = 'The code interpreter encountered an unexpected error.'
            print_traceback()
        finished = True
        #try:
        #    #msg_type = msg['msg_type']
        #    if msg_type == 'status':
        #        if msg['content'].get('execution_state') == 'idle':
        #            finished = True
        #    elif msg_type == 'execute_result':
        #        text = msg['content']['data'].get('text/plain', '')
        #        if 'image/png' in msg['content']['data']:
        #            image_b64 = msg['content']['data']['image/png']
        #            image_url = _serve_image(image_b64)
        #            image_idx += 1
        #            image = '![fig-%03d](%s)' % (image_idx, image_url)
        #    elif msg_type == 'display_data':
        #        if 'image/png' in msg['content']['data']:
        #            image_b64 = msg['content']['data']['image/png']
        #            image_url = _serve_image(image_b64)
        #            image_idx += 1
        #            image = '![fig-%03d](%s)' % (image_idx, image_url)
        #        else:
        #            text = msg['content']['data'].get('text/plain', '')
        #    elif msg_type == 'stream':
        #        msg_type = msg['content']['name']  # stdout, stderr
        #        text = msg['content']['text']
        #    elif msg_type == 'error':
        #        text = _escape_ansi('\n'.join(msg['content']['traceback']))
        #        if 'M6_CODE_INTERPRETER_TIMEOUT' in text:
        #            text = 'Timeout: Code execution exceeded the time limit.'
        #except queue.Empty:
        #    text = 'Timeout: Code execution exceeded the time limit.'
        #    finished = True
        #except Exception:
        #    text = 'The code interpreter encountered an unexpected error.'
        #    print_traceback()
        #    finished = True
        if text:
            result += f'\n\n{msg_type}:\n\n```\n{text}\n```'
        if finished:
            break
    result = result.lstrip('\n')
    return result


@register_tool('sql_interpreter')
class SQLInterpreter(BaseTool):
    description = 'sql 执行代理，可用于执行sql代码。'
    parameters = [{
        'name': 'code',
        'type': 'string',
        'description': '待执行的sql',
        'required': True
    }]

    def __init__(self, cfg: Optional[Dict] = None):
        self.args_format = '此工具的输入应为Markdown代码块。'
        super().__init__(cfg)
        self.file_access = True

    def call(self,
             params: Union[str, dict],
             files: List[str] = None,
             timeout: Optional[int] = 30,
             **kwargs) -> str:
        try:
            params = json5.loads(params)
            code = params['code']
        except Exception:
            code = extract_code(params)

        print('code is :', code)
        if not code.strip():
            return ''
        # download file
        #if files:
        #    for file in files:
        #        try:
        #            save_url_to_local_work_dir(file, WORK_DIR)
        #        except Exception:
        #            print_traceback()
        #            # Since the file may not be useful, do not directly report an error
        #            # logger.warning(f'Failed to download file {file}')
        result = _execute_code(code)
        return result if result.strip() else 'Finished execution.'


def _get_multiline_input(hint: str) -> str:
    logger.info(
        '// Press ENTER to make a new line. Press CTRL-D to end input.')
    lines = []
    while True:
        try:
            line = input()
        except EOFError:  # CTRL-D
            break
        lines.append(line)
    logger.info('// Input received.')
    if lines:
        return '\n'.join(lines)
    else:
        return ''


if __name__ == '__main__':
    tool = SQLInterpreter()
    while True:
        logger.info(tool.call(_get_multiline_input('Enter sql code:')))
