from fastapi import FastAPI


app = FastAPI(
    title="Shell Execution API",
    description="通过 HTTP API 执行 Shell 命令（带 Token 验证）",
    version="0.0.1"
)

