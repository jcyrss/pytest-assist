import subprocess, os, threading, time, platform
import asyncio,websockets,json,traceback
from dataclasses import is_dataclass,asdict
from .shared import Settings, LIB_PATH
from urllib.parse import unquote


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)
    
# **** 1 **** >>>> HTML Static File Server


def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.1)
        return s.connect_ex(('127.0.0.1', port)) == 0
    

if is_port_in_use(Settings.http_port):        
    print(f'HTTP PORT {Settings.http_port} already in use, exit')
    os._exit(0)

if is_port_in_use(Settings.ws_port):        
    print(f'WS PORT {Settings.ws_port} already in use, exit')
    os._exit(0)


def runHttpServer():


    from http.server import  ThreadingHTTPServer, SimpleHTTPRequestHandler


    class Handler(SimpleHTTPRequestHandler):
        PTC_URL = '/' + Settings.PTC_DIR

        def __init__(self, *args, **kwargs):
            self.log_message = lambda *_, **__: None
            super().__init__( *args, 
                             directory=os.path.join(LIB_PATH,'z_dist'),
                             **kwargs)
    

        # find request file in differnt root dirs
        # refer to https://stackoverflow.com/a/20409103
        def translate_path(self, path):
            # print(path)
            if self.path.startswith(self.PTC_URL):
                targetPath = unquote('.' + self.path)
                return targetPath
            else:
                return SimpleHTTPRequestHandler.translate_path(self, path)



        def _set_headers(self, code=200, ctype=None, length=None):
            self.send_response(code)
            if ctype=='json':
                self.send_header('Content-type', 'application/json')
            if length:
                self.send_header("Content-length", length)
            self.end_headers()


        def do_POST(self):
         
            content_len = int(self.headers.get('Content-Length'))
            post_body = self.rfile.read(content_len)

            try:
                rObj = json.loads(post_body.decode())
            except:
                
                print(traceback.format_exc())
                self._set_headers(code=400)
                return

            if rObj['cmd'] == 'get_ws_port':
                # print('http::get_ws_port')
                
                self._set_headers(ctype='json')
                resp = {
                    'ws_port': Settings.ws_port
                }         

            elif rObj['cmd'] == 'open_new_test':
                params = rObj['params']
                
                self._set_headers(ctype='json')
                resp = {
                    'ret': 0
                }         
           

            else:
                self._set_headers(code=400)
            
            self.wfile.write(json.dumps(resp).encode())   
            # self.finish()
            return


    httpd = ThreadingHTTPServer((Settings.host, Settings.http_port), Handler)
    
    print(f"HTTP Server running at {Settings.host}:{Settings.http_port}")

    httpd.serve_forever()


# **** 2 **** >>>> web socket Server

wssocket_ok = False
wsc_clients = set()
runningLoop = None


# for other thread to add task in asyncio loop
def broadcastToClients(info): 

    # this task will be exec in asyncio loop
    def task(msg):
        # print('to send', msg)
        if not wsc_clients:
            return
        
        try:
            websockets.broadcast(wsc_clients, msg)
        except:
            raise

    if runningLoop:
        runningLoop.call_soon_threadsafe(task, json.dumps(info, cls=EnhancedJSONEncoder))

clientMsgHandlers = {}
def registClientMsgHandler(event,handler):
    clientMsgHandlers[event] = handler




def runWebSocketServer():    

    async def router(connection, path):
        print(f'client connected from', connection.remote_address)
        if path == "/client":
            wsc_clients.add(connection)
        # elif path == "/runner":
        #     await get_shaded_area(websocket)
        else:
            return

        while True:
            try:
                message = await connection.recv()  
            except Exception as e:
                print(repr(e))
                break

            # handle received message
            # print(message)
            try:
                msg = json.loads(message)
                event = msg['event']
                
                if event not in clientMsgHandlers:
                    print('websocket ** unknown event from client:', event)
                    continue
                handler = clientMsgHandlers[event]
                
                ret = handler(msg)
                if ret is not None:
                    await connection.send(json.dumps(ret, cls=EnhancedJSONEncoder))

            except Exception as e:
                print(traceback.format_exc())

        wsc_clients.remove(connection)
        await connection.close()
        print(f'disconnected with', connection.remote_address)

    async def main():
        global wssocket_ok, runningLoop

        runningLoop = asyncio.get_running_loop()
        
        async with websockets.serve(router, Settings.host, Settings.ws_port):
            wssocket_ok = True
            await asyncio.Future()

    print(f"WebSocket Server running at {Settings.host}:{Settings.ws_port}" )
    asyncio.run(main())
    
    


# **** 3 **** >>>> launch browser

def openBrowser(accessHost):
    
    time.sleep(.5)
    print(f'\nYou could access pytest assist at : http://{accessHost}:{Settings.http_port} \n')

    # wait 1 seconds to see if there is client already connected
    time.sleep(1.5)
    if wsc_clients:
        return    
    


    # no clients, open new one

    def windows_getBrowserPath(browser='Edge'): # Chrome or  Edge
        edge_sufix = 'Microsoft\Edge\Application\msedge.exe'
        chrome_suffix = 'Google\Chrome\Application\chrome.exe'    
        
        suffix = edge_sufix if browser == 'Edge' else chrome_suffix
        
        Envfolders = [
            'LocalAppData',
            'ProgramFiles',
            'ProgramFiles(x86)',
        ]
        
        for ef in Envfolders:
            folder = os.environ.get(ef)
            if not folder:
                continue
            path = os.path.join(folder, suffix)
            if os.path.exists(path):
                return path
        
        print(f'{browser} not found!')
        return None


    appOpenOK = False
    if platform.system() == 'Windows':
        browserPath = windows_getBrowserPath('Edge')
        if browserPath is None :
            exit()
            
        # print(browserPath)

        try:    
            po = subprocess.Popen(
                [   browserPath, '--new-window', 
                    f'--app=http://{accessHost}:{Settings.http_port}',
                    '-window-size=800,800',
                    '--window-position=0,0',
                    '--disable-application-cache',
                    '--incognito',
                    # f'''--user-data-dir="{os.environ['tmp']}/chrome_tmp_user_dir_23"'''
                ])
            appOpenOK = True
        except:
            pass

    if not appOpenOK:
        try:
            import webbrowser
            webbrowser.open(f'http://{accessHost}:{Settings.http_port}', 
                            new=1, 
                            autoraise=True)
        except:
            pass


def runServers():    

    accessHost = Settings.host 
    if accessHost == '0.0.0.0':
        accessHost = '127.0.0.1'
    
    threading.Thread(target=runHttpServer, daemon=True).start()   
    threading.Thread(target=openBrowser, daemon=True, args=(accessHost,)).start()

    # threading.Thread(target=runWebSocketServer, daemon=True).start()
    runWebSocketServer()
    
    # # wait for websocket server OK
    # while not wssocket_ok:
    #     time.sleep(0.3)

    # openBrowser(app)
          
    # while True:
    #     cmd = input()
    #     if cmd == 'exit':
    #         break