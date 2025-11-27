import logging
from typing import Any, Dict, List

def get_handler_details(handler: logging.Handler) -> Dict[str, Any]:
    """提取单个处理器（Handler）的详细配置"""
    details = {
        "type": handler.__class__.__name__,  # 处理器类型（如 StreamHandler）
        "level": logging.getLevelName(handler.level),  # 处理器级别（如 DEBUG）
        "formatter": None,
        "filters": [f.__class__.__name__ for f in handler.filters],  # 过滤器列表
        "extra": {}  # 额外配置（如文件路径、轮转参数）
    }

    # 提取格式器配置
    if handler.formatter:
        details["formatter"] = {
            "format": handler.formatter._fmt,
            "datefmt": handler.formatter.datefmt or "None"
        }

    # 提取特定处理器的额外配置
    if isinstance(handler, logging.FileHandler):
        details["extra"]["filename"] = handler.baseFilename  # 文件路径
        details["extra"]["mode"] = handler.mode  # 打开模式（如 'a'）
        details["extra"]["encoding"] = handler.encoding or "None"  # 编码
    elif isinstance(handler, logging.handlers.RotatingFileHandler):
        details["extra"]["filename"] = handler.baseFilename
        details["extra"]["maxBytes"] = handler.maxBytes  # 最大文件大小
        details["extra"]["backupCount"] = handler.backupCount  # 备份数量
        details["extra"]["encoding"] = handler.encoding or "None"
    elif isinstance(handler, logging.handlers.TimedRotatingFileHandler):
        details["extra"]["filename"] = handler.baseFilename
        details["extra"]["when"] = handler.when  # 轮转单位（如 'D'=天）
        details["extra"]["interval"] = handler.interval  # 轮转间隔
        details["extra"]["backupCount"] = handler.backupCount
        details["extra"]["encoding"] = handler.encoding or "None"
    elif isinstance(handler, logging.StreamHandler):
        details["extra"]["stream"] = handler.stream.name  # 输出流（如 '<stdout>'）

    return details

def get_logger_config(logger: logging.Logger) -> Dict[str, Any]:
    """提取单个日志器（Logger）的详细配置"""
    # 处理根日志器（root logger 的 name 为空字符串）
    logger_name = logger.name or "root"
    return {
        "name": logger_name,
        "level": logging.getLevelName(logger.level),  # 日志器级别
        "propagate": logger.propagate,  # 是否传播到父日志器
        "handlers": [get_handler_details(h) for h in logger.handlers],  # 绑定的处理器
        "parent": logger.parent.name if logger.parent else "None"  # 父日志器名称
    }

def get_all_logging_config() -> List[Dict[str, Any]]:
    """获取所有 logging 配置（所有日志器、处理器、格式器）"""
    all_configs = []

    # 1. 先添加根日志器（root logger）
    root_logger = logging.getLogger()
    all_configs.append(get_logger_config(root_logger))

    # 2. 遍历所有已创建的非根日志器（包括第三方库的日志器）
    for logger_name in logging.root.manager.loggerDict:
        # 避免重复添加根日志器（loggerDict 中可能包含 root，但名称为空）
        if logger_name == "root" or logger_name == "":
            continue
        logger = logging.getLogger(logger_name)
        all_configs.append(get_logger_config(logger))

    return all_configs

def print_all_logging_config(formatted: bool = True):
    """打印所有 logging 配置（支持格式化输出，便于阅读）"""
    all_configs = get_all_logging_config()
    if formatted:
        import json
        print("=" * 80)
        print("Python Logging 完整配置（JSON 格式化）")
        print("=" * 80)
        print(json.dumps(all_configs, ensure_ascii=False, indent=2))
    else:
        print("=" * 80)
        print("Python Logging 完整配置（原始格式）")
        print("=" * 80)
        for config in all_configs:
            print(f"\n日志器名称：{config['name']}")
            print(f"  级别：{config['level']}")
            print(f"  传播：{config['propagate']}")
            print(f"  父日志器：{config['parent']}")
            print(f"  处理器数量：{len(config['handlers'])}")
            for i, handler in enumerate(config['handlers'], 1):
                print(f"    处理器 {i}：{handler['type']}")
                print(f"      级别：{handler['level']}")
                print(f"      格式器：{handler['formatter']}")
                print(f"      过滤器：{handler['filters']}")
                print(f"      额外配置：{handler['extra']}")

# ------------------------------
# 测试：加载日志配置后，输出所有配置
# ------------------------------
if __name__ == "__main__":
    # 示例：先加载一个日志配置（可替换为你的实际配置）
    import os
    os.makedirs("logs", exist_ok=True)

    # 简单配置日志（模拟实际场景）
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/test.log", encoding="utf-8")
        ]
    )

    # 创建自定义日志器
    custom_logger = logging.getLogger("my_app")
    custom_logger.setLevel(logging.INFO)

    # 输出所有 logging 配置
    print_all_logging_config(formatted=True)