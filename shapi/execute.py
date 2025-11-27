from typing import Optional, Tuple, Awaitable, Any

import os
import subprocess
import asyncio
import secrets
import time
import logging

from pydantic import BaseModel, Field, ConfigDict

import anyio


CL = logging.getLogger("console.main")
def L_(msg:str):
    CL.info(msg)

def prepare_environment(env: Optional[dict], env_replace: bool) -> Optional[dict]:
    """
    准备进程环境变量
    
    Args:
        env: 额外的环境变量字典
        env_replace: 是否完全替换环境变量（而非合并）
        
    Returns:
        处理后的环境变量字典，如果不需要设置则返回 None
    """
    if env is None:
        return None
    
    if env_replace:
        # 完全替换：只使用提供的环境变量
        return env
    else:
        # 合并模式：继承当前环境变量并添加/覆盖新的
        process_env = os.environ.copy()
        process_env.update(env)
        return process_env


class ExecuteParams(BaseModel):
    command:list[str] = Field(...)
    cwd:str = Field(...)
    env:dict|None = Field(None)
    user: str|int = Field(default=0)
    group: str|int = Field(default=0)
    timeout: float = Field(default=3600*10)


class TaskInfo(BaseModel):
    task_id:str = Field(...)
    process:Optional[subprocess.CompletedProcess] = Field(default=None)
    task:Optional[asyncio.Task[subprocess.CompletedProcess]] = Field(default=None)
    params:ExecuteParams = Field(...)
    timeout:float = Field(default=3600*10)
    start_at:float = Field(default=0)
    finished_at:float = Field(default=0)
    model_config = ConfigDict(arbitrary_types_allowed=True)


# ---
async def execute_simple(
    params:ExecuteParams) -> dict[str, str|int]:
    """普通模式执行命令"""
    
    ts = time.time()
    result = await anyio.run_process(
        command=params.command,
        stdin=None,                            
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=params.cwd,
        env=params.env,
        user=params.user,
        group=params.group)
    te = time.time()
    L_(f'EXEC-S {' '.join(params.command)} / {te-ts:.1f}s')

    return {
        'return_code': result.returncode,
        'stdout': result.stdout.decode('utf-8', errors='replace'),
        'stderr': result.stderr.decode('utf-8', errors='replace')
    }


async def execute_task_runner(ti:TaskInfo, acp:Awaitable[subprocess.CompletedProcess]) -> subprocess.CompletedProcess:
    ti.start_at = time.time()
    ti.process = await acp
    ti.finished_at = time.time()
    return ti.process


class ExecuteTasks():
    def __init__(self):
        self.task_infos = {}

    async def add_task(self, params:ExecuteParams) -> Tuple[str, Exception|None]:
        """
        输入TaskParams, 返回task_id, 
        """

        task_id = self.gen_task_id()
        try:
            cp = anyio.run_process(
                params.command,
                cwd=params.cwd,
                env=params.env,
                user=params.user,
                group=params.group)
        except Exception as e:
            return ("_", e)
        
        ti = TaskInfo(task_id=task_id, params=params)
        ti.task = asyncio.create_task(execute_task_runner(ti, cp), name=f"execute_task_{task_id}")
        self.task_infos[task_id] = ti
        L_(f'EXEC-A {' '.join(params.command)} → {task_id}')
        return (task_id, None)
        
    
    async def clean_tasks(self):
        cur = time.time()
        
        for task_id in list(self.task_infos):
            task_info = self.task_infos[task_id]
            if task_info.finished_at > 0 and cur - task_info.finished_at > 300:
                print(f'== EXECUTE TASKS CLEANER: {task_id}')
                self.task_infos.pop(task_id)

    def gen_task_id(self):
        return secrets.token_hex(8)