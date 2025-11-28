# import json
import asyncio
import secrets
import logging
import time
from subprocess import PIPE

from fastapi import WebSocket
from pydantic import BaseModel, Field
from anyio import open_process
from anyio.abc import ByteReceiveStream

from shapi.execute import prepare_environment, execute_simple, ExecuteParams as EP

CL = logging.getLogger('console.main')

class ExecuteParams(BaseModel):
    request_id:str = Field(default='__')
    command:list[str] = Field(...)
    cwd:str = Field('.')
    env:dict|None = Field(None)
    env_replace:bool = Field(False)
    use_pty:bool = Field(False)
    user: str|int = Field(default=0)
    group: str|int = Field(default=0)
    timeout: float = Field(default=3600*10)


async def execute_websocket(websocket:WebSocket):
    await websocket.accept()
    task_id = secrets.token_hex(8)
    
    command_dict = await websocket.receive_json()
    params = ExecuteParams(**command_dict)
    # print(params.model_dump(exclude_unset=True))
    ts = time.time()
    CL.info(f'''EXEC-X {' '.join(params.command)} → {task_id}''')
  
    env = prepare_environment(params.env, params.env_replace)
    async with asyncio.TaskGroup() as task_group, \
        await open_process(params.command, 
            env=env,
            cwd=params.cwd) as process:

        async def out_forwarder(stream:ByteReceiveStream, websocket:WebSocket, channel:str):
            async with stream:
                async for item in stream:
                    await websocket.send_json({
                        'channel':channel,
                        'data': item.decode('utf-8')
                    })
        
        task_group.create_task(out_forwarder(process.stdout, websocket, 'stdout')) # type: ignore
        task_group.create_task(out_forwarder(process.stderr, websocket, 'stderr')) # type: ignore

        await process.wait()
        return_code = process.returncode

    await websocket.send_json({
        'channel': 'exit',
        'return_code': return_code
    })    
    te = time.time()
    during = te - ts
    CL.info(f'EXEC-X TASK:{task_id} / {during:.1f}s / {process.returncode}')
    await websocket.close()
    
    