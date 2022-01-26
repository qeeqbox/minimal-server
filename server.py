from http import HTTPStatus
from mimetypes import guess_type
from urllib.parse import urljoin, urlparse
from os import path, getcwd
from contextlib import suppress
from asyncio import run as arun
from asyncio import gather
from websockets import serve

ALLOWED = ['text/html','application/javascript','text/css']

async def check_path(_path):
    with suppress(Exception):
        _path = path.relpath(_path, start=getcwd())
        _path = path.abspath(_path)
        if not any(detect in _path for detect in ['\\..','/..','..']):
            if _path.startswith(getcwd()):
                if path.isfile(_path):
                    return True
    return False

async def http_task(path, headers):
    response_content = ''
    response_status = HTTPStatus.NOT_FOUND
    response_headers = [('Connection', 'close')]
    if 'User-Agent' in headers and 'Host' in headers:
        print("Host: {} User-Agent: {}".format(headers['Host'],headers['User-Agent']))
    if 'Accept' in headers:
        with suppress(Exception):
            if path == '/':
                path = getcwd()+'/index.html'
            else:
                path = getcwd()+urljoin(path, urlparse(path).path)
            good_path = await check_path(path)
            if good_path:
                mime_type = guess_type(path)[0]
                if mime_type in ALLOWED:
                    if mime_type in headers['Accept'] or '*/*' in headers['Accept']:
                        response_content = open(path, 'rb').read()
                        response_headers.append(('Content-Type', mime_type))
                        response_headers.append(('Content-Length', str(len(response_content))))
                        response_status = HTTPStatus.OK
                    else:
                        print("Mismatch {} type {} with {}".format(path,mime_type, headers['Accept']))
                else:
                    print("File is not supported {} type {}".format(path,mime_type))
            else:
                print("File is not supported or does not exist {}".format(path))
    else:
        print("Needs [Accept] from server")
    return response_status, response_headers, response_content

async def run_servers():
    server_1 = await serve(lambda x: None, '127.0.0.1', '8000', process_request=http_task)
    print("Server: {}".format(server_1.server.sockets[0].getsockname()))
    await gather(server_1.wait_closed())

arun(run_servers())