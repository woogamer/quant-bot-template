"""로그 기록 모듈.

봇 실행 중 발생하는 이벤트를 콘솔과 파일에 동시에 기록합니다.
(이 파일은 건드리지 않아도 됩니다)
"""

import logging
import os

def setup_logger(name: str = "quant-bot") -> logging.Logger:
    """로거를 생성하고 반환합니다."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 콘솔 출력
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 파일 출력 (logs/ 폴더)
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler("logs/bot.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

log = setup_logger()
