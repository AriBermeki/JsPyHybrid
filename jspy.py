import asyncio
from queue import Queue
from threading import Event
import json
from logging import getLogger, ERROR
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_socketio import SocketManager
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import mimetypes
import random

getLogger('fastapi').setLevel(ERROR)
log = getLogger(__name__)

class EventRegistry:
    def __init__(self, socket_manager):
        self.functions = {}
        self.classmethods = {}
        self.jsfunctionregistry = {}
        self.javascript_respons_ = {}
        self.socketid = {}
        self.socket_manager = socket_manager
        self.log = getLogger(__name__)
        self.loop = asyncio.get_event_loop()

    async def javascript_respons(self, res):
        if res is not None:
            dd_dd = res.get('msg')
            self.javascript_respons_['javascript_respons'] = dd_dd

    def pyfunction(self, func_name, func):
        self.functions[func_name] = func

    async def __jsfunction(self, func_name, args):
        self.jsfunctionregistry[func_name] = func_name
        data = {'func_name': func_name, 'args': args}
        result = json.dumps(data, default=lambda o: o.__class__.__name__)
        await self.socket_manager.emit('call_javascript_func', result)

    async def __cjsfunction(self, func_name, args, result):
        await self.__jsfunction(func_name, args)
        return self.javascript_respons_.get('javascript_respons', result)

    def register_class_method(self, method_name, class_instance, method):
        bound_method = getattr(class_instance, method_name, None)
        if bound_method:
            self.classmethods[method_name] = bound_method
        else:
            raise AttributeError(f"Class {class_instance.__class__.__name__} has no method named {method_name}")

    async def spawn(self, function, client_required=None, *args, **kwargs):
        if client_required == True:
            while True:
                if asyncio.iscoroutinefunction(function):
                    result = await function(*args, **kwargs)
                else:
                    if kwargs:
                        raise Exception('cannot convey kwargs')
                    result = await self.loop.run_in_executor(None, function, *args)

                await self.socket_manager.emit('spawn_message', {'result': result})
                await asyncio.sleep(1)
        else:
            while True:
                if asyncio.iscoroutinefunction(function):
                    result = await function(*args, **kwargs)
                else:
                    if kwargs:
                        raise Exception('cannot convey kwargs')
                    result = await self.loop.run_in_executor(None, function, *args)
                await asyncio.sleep(1)

    async def handle_client(self, sid, data):
        func_name = data.get('func_name', None)
        args = data.get('args', [])

        if func_name and (func_name in self.functions or func_name in self.classmethods):
            result_queue = Queue()
            task_completed = Event()

            async def execute_function():
                try:
                    if func_name in self.functions:
                        if asyncio.iscoroutinefunction(self.functions[func_name]):
                            result = await self.functions[func_name](*args)
                        else:
                            result = self.functions[func_name](*args)
                    else:
                        # Assuming func_name is a class method
                        result = await self.loop.run_in_executor(None, self.classmethods[func_name], *args)

                    result_queue.put(result)
                except Exception as e:
                    self.log.error(f"Error executing function {func_name}: {str(e)}")
                    result_queue.put(str(e) + ': ' + '    @python Server')
                finally:
                    task_completed.set()

            asyncio.create_task(execute_function())
            await asyncio.to_thread(task_completed.wait)

            result = result_queue.get()
            send_back_to_client = {'func_name': func_name, 'result': result}

            await self.socket_manager.emit('server_respons', send_back_to_client, room=sid)
        else:
            raise RuntimeError("""
                There is no predefined function with this name that the 
                client asks the server to do. Please register this function on the server side.
                """)

    async def calljs(self, func_name, args, result=None):
        return asyncio.create_task(self.__cjsfunction(func_name=func_name, args=args, result=result))

    async def js_response(self):
        responsa = self.javascript_respons_.get('javascript_respons')
        if responsa is not None:
            return responsa
        else:
            return 'die resultat ist noch nicht da'
