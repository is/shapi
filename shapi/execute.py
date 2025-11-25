from typing import Optional

import os
import subprocess

import anyio


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

async def execute_simple(
    command:list[str], 
    cwd: str|None, 
    env: dict|None,
    timeout: float) -> dict[str, str|int]:
    """普通模式执行命令"""
    
    result = await anyio.run_process(
        command=command,
        stdin=None,                            
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=env)

    return {
        'return_code': result.returncode,
        'stdout': result.stdout.decode('utf-8', errors='replace'),
        'stderr': result.stderr.decode('utf-8', errors='replace')
    }
        