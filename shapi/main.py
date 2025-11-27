from typing import Callable, Awaitable

import asyncio
import os
import logging
from binascii import b2a_base64, a2b_base64
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from shapi.dto import ExecuteRequest, ExecuteResponse, ExecuteAsyncResponse, \
    ReadTextFileResponse, ReadTextFileRequest, WriteTextFileRequest, WriteTextFileResponse
from shapi.execute import execute_simple, prepare_environment, ExecuteTasks, ExecuteParams
from shapi.auth import load_key_map_from_env, token_verify

VERSION = "0.0.3"

SHAPI_SECRET_KEYS = load_key_map_from_env()
BACKGROUND_TASKS = []
EXECUTE_TASKS = ExecuteTasks()

CL = logging.getLogger('console.main')

async def execute_task_cleaner(tasks:ExecuteTasks):
    while True:
        await asyncio.sleep(3)
        await tasks.clean_tasks()


@asynccontextmanager
async def lifespan(app:FastAPI):
    # import shapi.misc.logutils
    # print("---")
    # shapi.misc.logutils.print_all_logging_config(formatted=True)
    # print("---")
    
    BACKGROUND_TASKS.append(asyncio.create_task(execute_task_cleaner(EXECUTE_TASKS)))
    yield
    for task in BACKGROUND_TASKS:
        task.cancel()


app = FastAPI(
    lifespan=lifespan,
    title="Shell Execution API",
    description="通过 HTTP API 执行 Shell 命令（带 Token 验证）",
    version=VERSION,
)


@app.middleware("http")
async def auth_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    nonce = request.headers.get("X-Shapi-Auth")
    nonce_key = None
    if nonce != None:
        nonce_key = token_verify(nonce, SHAPI_SECRET_KEYS)
    if nonce_key == None:
        return JSONResponse(status_code=400, content={"status": "ERROR", "error_message": "Invalid nonce"})
    request.state.nonce_key = nonce_key
    return await call_next(request)



@app.get("/")
def index():
    return {"message": "Hello, World 2!"}


@app.post("/v1/execute", response_model=ExecuteResponse, response_model_exclude_unset=True)
async def execute_command(
    request: ExecuteRequest,
):
    env = prepare_environment(request.env, request.env_replace)
    params = ExecuteParams(
        command=request.command,
        cwd=request.cwd or "/root",
        env=env,
        timeout=request.timeout or 3600*10)
    result = await execute_simple(params)

    return ExecuteResponse(
        request_id = request.request_id,
        status = "OK",
        return_code = result['return_code'], # type: ignore
        stdout = result['stdout'], # type: ignore
        stderr = result['stderr']) # type: ignore


@app.get("/v1/aexecute/{task_id}", response_model=ExecuteResponse, response_model_exclude_unset=True)
async def execute_async_task_info(task_id:str) -> ExecuteResponse:
    task_info = EXECUTE_TASKS.task_infos.get(task_id)
    if task_info == None:
        return ExecuteResponse(
            request_id='__',
            status='ERROR',
            error_message='invalid task token',
            return_code=-1)
    
    if task_info.process == None:
        return ExecuteResponse(
            request_id='__',
            status='CONTINUE',
            return_code=0)
    
    EXECUTE_TASKS.task_infos.pop(task_id)
    process = task_info.process
    return ExecuteResponse(
        request_id='__',
        status='OK',
        return_code=process.returncode,
        stdout=process.stdout.decode('utf-8', errors='replace'),
        stderr=process.stderr.decode('utf-8', errors='replace'))  


@app.post("/v1/aexecute", response_model=ExecuteAsyncResponse, response_model_exclude_unset=True)
async def execute_command_async(
    request: ExecuteRequest) -> ExecuteAsyncResponse:
    env = prepare_environment(request.env, request.env_replace)
    params = ExecuteParams(
        command=request.command,
        cwd=request.cwd or "/root",
        env=env)
    task_id, exc = await EXECUTE_TASKS.add_task(
        params)

    if exc != None:
        return ExecuteAsyncResponse(
            request_id=request.request_id,
            status="ERROR",
            error_message=str(exc),
            task_id='_')
    
    return ExecuteAsyncResponse(
        request_id=request.request_id,
        status="OK",
        task_id=task_id)



@app.post("/v1/fs/read", response_model=ReadTextFileResponse, response_model_exclude_unset=True)
async def read_text_from_file(request:ReadTextFileRequest) -> ReadTextFileResponse:
    try:
        with open(request.filepath, 'rb') as f:
            content = f.read()
        return ReadTextFileResponse(
            request_id=request.request_id,
            status="OK",
            content=b2a_base64(content).decode('utf-8'))
    except Exception as e:
        return ReadTextFileResponse(
            request_id=request.request_id,
            status="ERROR", error_message=str(e))


@app.post("/v1/fs/write", response_model=WriteTextFileResponse, response_model_exclude_unset=True)
async def write_text_to_file(request:WriteTextFileRequest) -> WriteTextFileResponse:
    try:
        with open(request.filepath, 'wb') as f:
            f.write(a2b_base64(request.content))
        if request.mode != 0:
            os.chmod(request.filepath, request.mode)
        return WriteTextFileResponse(
            request_id=request.request_id,
            status="OK")
    except Exception as e:
        return WriteTextFileResponse(
            request_id=request.request_id,
            status="ERROR", error_message=str(e))
