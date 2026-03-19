"""Telegram 알림 모듈.

봇 시작/종료, 주문 체결, 에러 발생 시 메시지를 보냅니다.
(이 파일은 건드리지 않아도 됩니다)
"""

import requests
from core.logger import log


class TelegramNotifier:
    """Telegram Bot API를 통해 메시지를 전송합니다."""

    def __init__(self, bot_token: str, chat_id: int) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._base_url = f"https://api.telegram.org/bot{bot_token}"

    def send(self, message: str) -> bool:
        """텔레그램으로 메시지를 전송합니다.

        Returns:
            True면 전송 성공, False면 실패.
        """
        if not self._bot_token or not self._chat_id:
            log.warning("텔레그램 설정이 없어 알림을 건너뜁니다.")
            return False

        url = f"{self._base_url}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as e:
            log.error(f"텔레그램 전송 실패: {e}")
            return False

    def notify_start(self) -> None:
        """봇 시작 알림."""
        self.send("*[봇 시작]* 자동매매 봇이 실행되었습니다.")

    def notify_stop(self) -> None:
        """봇 종료 알림."""
        self.send("*[봇 종료]* 자동매매 봇이 종료되었습니다.")

    def notify_order(self, ticker: str, action: str, qty: int, name: str = "", reason: str = "") -> None:
        """주문 체결 알림."""
        label = f"{name}({ticker})" if name else ticker
        emoji = "📈" if action.upper() == "BUY" else "📉"
        msg = f"{emoji} *[{action.upper()}]* {label} / {qty}주"
        if reason:
            msg += f"\n└ {reason}"
        self.send(msg)

    def notify_error(self, error_msg: str) -> None:
        """에러 알림."""
        self.send(f"*[에러]* {error_msg}")
