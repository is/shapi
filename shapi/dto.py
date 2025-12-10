from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class RequestBase(BaseModel):
    request_id:str = Field(default="_", description="请求ID")
    name:Optional[str] = Field(default=None, description="请求日志描述")
    path:Optional[str] = Field(default=None, description="请求路径")
    sign:Optional[str] = Field(default=None, description="请求签名")


class ResponseBase(BaseModel):
    request_id:str = Field(..., description="请求ID")
    status:str = Field(..., description="")
    error_message:str | None = Field(default=None, description="错误信息")
    

class ExecuteRequest(RequestBase):
    """命令执行请求"""
    command:List[str] = Field(..., description="命令行")
    use_pty: bool = Field(default=False, description="是否使用 PTY 模式")
    cwd: Optional[str] = Field(default=None, description="工作目录")
    timeout: Optional[float] = Field(default=3600.0, description="超时时间(秒)")
    user: Optional[int|str] = Field(default=None, description="执行用户")
    group: Optional[int|str] = Field(default=None, description="执行用户组")
    env: Optional[dict] = Field(default=None, description="额外的环境变量（会合并到当前环境）")
    env_replace: bool = Field(default=False, description="是否完全替换环境变量（而非合并）")
    env_var: bool = Field(default=False, description="是否对命令行中的变量做替换")
    record: bool = Field(default=False, description="是否记录日志")


class ExecuteResponse(ResponseBase):
    """命令执行响应"""
    return_code:int = Field(default=0, description="返回码")
    stdout: str|None = Field(default=None, description="标准输出")
    stderr: str|None = Field(default=None, description="标准错误输出")


class ExecuteAsyncResponse(ResponseBase):
    """命令执行响应"""
    task_id: str = Field(..., description="任务ID")

# ---
class ReadTextFileRequest(RequestBase):
    filepath:str = Field(...)

class ReadTextFileResponse(ResponseBase):
    content:str|None = Field(default=None)

class WriteTextFileRequest(RequestBase):
    filepath:str = Field(...)
    content:str = Field(...)
    mode:int = Field(default=0)

class WriteTextFileResponse(ResponseBase):
    pass
