import subprocess

import anyio

async def execute_simple(
    command:list[str], 
    cwd: str|None, timeout: float) -> dict[str, str|int]:
    """普通模式执行命令"""
    
    result = await anyio.run_process(
        command=command,
        stdin=None,                            
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd)

    return {
        'return_code': result.returncode,
        'stdout': result.stdout.decode('utf-8', errors='replace'),
        'stderr': result.stderr.decode('utf-8', errors='replace')
    }
        