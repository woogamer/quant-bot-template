"""알림 통합 모듈.

여러 알림 채널(Telegram, Slack 등)을 하나로 묶어서
동일한 인터페이스로 사용할 수 있게 합니다.
"""

from core.logger import log


class CompositeNotifier:
    """여러 notifier를 묶어서 동시에 알림을 보냅니다."""

    def __init__(self, notifiers: list) -> None:
        self._notifiers = notifiers

    def send(self, message: str) -> None:
        for n in self._notifiers:
            try:
                n.send(message)
            except Exception as e:
                log.error(f"알림 전송 실패: {e}")

    def notify_start(self) -> None:
        for n in self._notifiers:
            try:
                n.notify_start()
            except Exception as e:
                log.error(f"시작 알림 실패: {e}")

    def notify_stop(self) -> None:
        for n in self._notifiers:
            try:
                n.notify_stop()
            except Exception as e:
                log.error(f"종료 알림 실패: {e}")

    def notify_order(self, ticker: str, action: str, qty: int, **kwargs) -> None:
        for n in self._notifiers:
            try:
                n.notify_order(ticker, action, qty, **kwargs)
            except Exception as e:
                log.error(f"주문 알림 실패: {e}")

    def notify_error(self, error_msg: str) -> None:
        for n in self._notifiers:
            try:
                n.notify_error(error_msg)
            except Exception as e:
                log.error(f"에러 알림 실패: {e}")
