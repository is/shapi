from fastapi import FastAPI

from shapi.dto import ExecuteRequest, ExecuteResponse
from shapi.execute import execute_simple

VERSION = "0.0.1"

app = FastAPI(
    title="Shell Execution API",
    description="通过 HTTP API 执行 Shell 命令（带 Token 验证）",
    version=VERSION,
)

@app.get("/")
def index():
    return {"message": "Hello, World 2!"}

@app.post("/v1/execute", response_model=ExecuteResponse)
async def execute_command(
    request: ExecuteRequest,
):
    result = await execute_simple(
        request.command,
        request.cwd,
        request.timeout  # type: ignore
    )

    return ExecuteResponse(
        request_id = request.request_id,
        status = "OK",
        return_code = result['return_code'], # type: ignore
        stdout = result['stdout'], # type: ignore
        stderr = result['stderr'], # type: ignore
        error_message = None) 