from typing import Callable, Awaitable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse


from shapi.dto import ExecuteRequest, ExecuteResponse
from shapi.dto import RequestBase
from shapi.execute import execute_simple, prepare_environment
from shapi.nonce import load_key_map_from_env, token_verify

VERSION = "0.0.1"

app = FastAPI(
    title="Shell Execution API",
    description="通过 HTTP API 执行 Shell 命令（带 Token 验证）",
    version=VERSION,
)

SHAPI_SECRET_KEYS = load_key_map_from_env()

@app.middleware("http")
async def nonce_verify_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    nonce = request.headers.get("X-Shapi-Nonce")
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
    result = await execute_simple(
        request.command,
        request.cwd,
        env,
        timeout = request.timeout  # type: ignore
    )

    return ExecuteResponse(
        request_id = request.request_id,
        status = "OK",
        return_code = result['return_code'], # type: ignore
        stdout = result['stdout'], # type: ignore
        stderr = result['stderr'])