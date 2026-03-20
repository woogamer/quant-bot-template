"""Slack 알림 모듈.

Incoming Webhook을 통해 매매 알림을 전송합니다.
config.yaml에 slack.webhook_url을 설정하면 활성화됩니다.
"""

import requests
from core.logger import log


class SlackNotifier:
    """Slack Incoming Webhook을 통해 메시지를 전송합니다."""

    def __init__(self, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    def send(self, message: str) -> bool:
        """Slack으로 메시지를 전송합니다."""
        if not self._webhook_url:
            return False

        try:
            resp = requests.post(
                self._webhook_url,
                json={"text": message},
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            log.error(f"Slack 전송 실패: {e}")
            return False

    def notify_start(self) -> None:
        """봇 시작 알림."""
        self.send("*[봇 시작]* 자동매매 봇이 실행되었습니다.")

    def notify_stop(self) -> None:
        """봇 종료 알림."""
        self.send("*[봇 종료]* 자동매매 봇이 종료되었습니다.")

    def notify_order(self, ticker: str, action: str, qty: int,
                     name: str = "", reason: str = "",
                     pnl_pct: float = 0.0, pnl_amt: int = 0) -> None:
        """주문 체결 알림."""
        label = f"{name}({ticker})" if name else ticker
        is_buy = action.upper() == "BUY"
        emoji = "\U0001F4C8" if is_buy else "\U0001F4C9"

        msg = f"{emoji} *[{action.upper()}]* {label} / {qty}주"

        if not is_buy and (pnl_pct or pnl_amt):
            sign = "+" if pnl_amt >= 0 else ""
            msg += f"\n   수익률 {pnl_pct:+.2f}% / {sign}{pnl_amt:,}원"

        if reason:
            msg += f"\n   {reason}"

        self.send(msg)

    def notify_error(self, error_msg: str) -> None:
        """에러 알림."""
        self.send(f"*[에러]* {error_msg}")
