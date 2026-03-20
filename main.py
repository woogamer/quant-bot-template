"""
=============================================================
  자동매매 봇 메인 러너 (main.py)
=============================================================
실행 방법:
    python main.py

이 파일은 건드리지 않아도 됩니다.
전략을 수정하려면 my_strategy.py 만 편집하세요.
=============================================================
"""

import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule
import yaml

from core.kis_api import KISClient
from core.logger import log
from core.notifier import CompositeNotifier
from core.slack_bot import SlackNotifier
from core.telegram_bot import TelegramNotifier
from my_strategy import WATCHLIST, generate_signal, STOCK_NAMES

# ------------------------------------------------------------------ #
#  설정 로드
# ------------------------------------------------------------------ #

CONFIG_PATH = Path("config.yaml")


def load_config() -> dict:
    """config.yaml을 읽어서 반환합니다."""
    if not CONFIG_PATH.exists():
        log.error("config.yaml 파일이 없습니다! config.template.yaml을 복사해서 만들어 주세요.")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ------------------------------------------------------------------ #
#  시장 데이터 / 계좌 데이터 수집
# ------------------------------------------------------------------ #

def fetch_market_data(kis: KISClient, tickers: list[str]) -> dict:
    """관심 종목의 현재가를 조회합니다."""
    market_data = {}
    for ticker in tickers:
        try:
            raw = kis.get_price(ticker)
            output = raw.get("output", {})
            market_data[ticker] = {
                "현재가": int(output.get("stck_prpr", 0)),
                "전일대비": int(output.get("prdy_vrss", 0)),
                "등락률": float(output.get("prdy_ctrt", 0)),
            }
        except Exception as e:
            log.warning(f"{ticker} 현재가 조회 실패: {e}")
    return market_data


def fetch_account_data(kis: KISClient) -> dict:
    """계좌 잔고를 조회합니다."""
    try:
        raw = kis.get_balance()
        holdings = []
        for item in raw.get("output1", []):
            if int(item.get("hldg_qty", 0)) > 0:
                holdings.append({
                    "종목코드": item.get("pdno", ""),
                    "종목명": item.get("prdt_name", ""),
                    "수량": int(item.get("hldg_qty", 0)),
                    "평균단가": int(float(item.get("pchs_avg_pric", 0))),
                })
        summary = raw.get("output2", [{}])
        if isinstance(summary, list):
            summary = summary[0] if summary else {}
        deposit = int(summary.get("dnca_tot_amt", 0))
        return {"보유종목": holdings, "예수금": deposit}
    except Exception as e:
        log.error(f"잔고 조회 실패: {e}")
        return {"보유종목": [], "예수금": 0}


# ------------------------------------------------------------------ #
#  일일 매매 기록 및 리포트
# ------------------------------------------------------------------ #

_daily_trades: list[dict] = []
_daily_report_sent: str = ""  # "YYYY-MM-DD" 형식으로 오늘 리포트 전송 여부 추적


def _record_trade(sig: dict) -> None:
    """매매 기록을 저장합니다."""
    _daily_trades.append({
        "time": datetime.now().strftime("%H:%M"),
        "ticker": sig.get("ticker", ""),
        "name": sig.get("name", ""),
        "action": sig.get("action", ""),
        "qty": sig.get("qty", 0),
        "reason": sig.get("reason", ""),
        "pnl_pct": sig.get("pnl_pct", 0.0),
        "pnl_amt": sig.get("pnl_amt", 0),
    })


def _fetch_kospi(kis: KISClient) -> dict:
    """KOSPI 지수를 조회합니다."""
    try:
        from core.kis_api import _request_with_retry, BASE_URL
        kis._ensure_auth()
        resp = _request_with_retry(
            "GET",
            f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-index-price",
            params={"FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": "0001"},
            headers=kis._headers("FHPUP02100000"),
            timeout=10,
        )
        resp.raise_for_status()
        out = resp.json().get("output", {})
        return {
            "지수": out.get("bstp_nmix_prpr", "0"),
            "등락률": float(out.get("bstp_nmix_prdy_ctrt", 0)),
        }
    except Exception as e:
        log.warning(f"KOSPI 지수 조회 실패: {e}")
        return {}


def send_daily_report(notifier, kis: KISClient, market_data: dict, account_data: dict) -> None:
    """장 마감 일일 리포트를 전송합니다."""
    global _daily_report_sent
    today = datetime.now().strftime("%Y-%m-%d")

    if _daily_report_sent == today:
        return
    _daily_report_sent = today

    # KOSPI 지수 조회
    kospi = _fetch_kospi(kis)

    # 오늘 매매 요약
    buys = [t for t in _daily_trades if t["action"] == "BUY"]
    sells = [t for t in _daily_trades if t["action"] == "SELL"]
    total_pnl = sum(t["pnl_amt"] for t in sells)

    # 보유종목 현황
    holdings = account_data.get("보유종목", [])
    deposit = account_data.get("예수금", 0)

    lines = [f"<b>\U0001F4CA 일일 리포트 ({today})</b>", ""]

    # 시장 현황 (KOSPI 지수)
    if kospi:
        lines.append(f"\U0001F30D <b>KOSPI</b>: {kospi['지수']} ({kospi['등락률']:+.2f}%)")
    else:
        rates = [v["등락률"] for v in market_data.values() if v.get("등락률")]
        market_avg = sum(rates) / len(rates) if rates else 0
        lines.append(f"\U0001F30D <b>시장</b>: WATCHLIST 평균 {market_avg:+.2f}%")
    lines.append("")

    # 매매 내역
    if buys or sells:
        lines.append(f"<b>\U0001F4B0 매매 내역</b> (매수 {len(buys)}건 / 매도 {len(sells)}건)")
        for t in _daily_trades:
            emoji = "\U0001F4C8" if t["action"] == "BUY" else "\U0001F4C9"
            name = t["name"] or STOCK_NAMES.get(t["ticker"], t["ticker"])
            line = f"  {emoji} {t['time']} {t['action']} {name} {t['qty']}주"
            if t["action"] == "SELL" and t["pnl_amt"]:
                sign = "+" if t["pnl_amt"] >= 0 else ""
                line += f" ({t['pnl_pct']:+.2f}% / {sign}{t['pnl_amt']:,}원)"
            if t["reason"]:
                line += f" [{t['reason']}]"
            lines.append(line)
        lines.append("")
        if sells:
            sign = "+" if total_pnl >= 0 else ""
            lines.append(f"<b>\U0001F3AF 실현 손익: {sign}{total_pnl:,}원</b>")
    else:
        lines.append("\U0001F4A4 오늘 매매 없음")

    # 보유 현황
    lines.append("")
    lines.append(f"<b>\U0001F4BC 보유 현황</b>")
    if holdings:
        for h in holdings:
            name = h.get("종목명", "") or STOCK_NAMES.get(h["종목코드"], h["종목코드"])
            price_info = market_data.get(h["종목코드"])
            if price_info and h["평균단가"] > 0:
                cur = price_info["현재가"]
                pnl = (cur - h["평균단가"]) / h["평균단가"] * 100
                lines.append(f"  {name} {h['수량']}주 ({pnl:+.2f}%)")
            else:
                lines.append(f"  {name} {h['수량']}주")
    else:
        lines.append("  없음")
    lines.append(f"  예수금: {deposit:,}원")

    notifier.send("\n".join(lines))
    log.info("일일 리포트 전송 완료")

    # 매매 기록 초기화
    _daily_trades.clear()


# ------------------------------------------------------------------ #
#  시그널 실행
# ------------------------------------------------------------------ #

def execute_signals(
    kis: KISClient,
    notifier: TelegramNotifier,
    signals: list[dict],
) -> None:
    """시그널 리스트를 받아서 실제 주문을 실행합니다."""
    for sig in signals:
        ticker = sig.get("ticker", "")
        action = sig.get("action", "").upper()
        qty = sig.get("qty", 0)
        price = sig.get("price", 0)
        name = sig.get("name", "")
        reason = sig.get("reason", "")
        pnl_pct = sig.get("pnl_pct", 0.0)
        pnl_amt = sig.get("pnl_amt", 0)

        if not ticker or not action or qty <= 0:
            log.warning(f"잘못된 시그널 무시: {sig}")
            continue

        try:
            if action == "BUY":
                kis.buy(ticker, qty, price)
            elif action == "SELL":
                kis.sell(ticker, qty, price)
            else:
                log.warning(f"알 수 없는 action: {action}")
                continue
            notifier.notify_order(
                ticker, action, qty,
                name=name, reason=reason,
                pnl_pct=pnl_pct, pnl_amt=pnl_amt,
            )
            _record_trade(sig)
        except Exception as e:
            log.error(f"주문 실패 ({ticker} {action}): {e}")
            notifier.notify_error(f"주문 실패: {ticker} {action} - {e}")


# ------------------------------------------------------------------ #
#  메인 사이클
# ------------------------------------------------------------------ #

def is_market_open(market_open: str, market_close: str) -> bool:
    """현재 시각이 장 운영 시간인지 확인합니다."""
    now = datetime.now().strftime("%H:%M")
    return market_open <= now <= market_close


def run_cycle(
    kis: KISClient,
    notifier: TelegramNotifier,
    bot_config: dict,
) -> None:
    """전략 1회 실행 사이클."""
    market_open = bot_config.get("market_open", "09:00")
    market_close = bot_config.get("market_close", "15:30")

    if not is_market_open(market_open, market_close):
        log.info("장 운영 시간이 아닙니다. 대기 중...")
        return

    log.info("=== 전략 실행 시작 ===")

    # 1) 데이터 수집
    market_data = fetch_market_data(kis, WATCHLIST)
    account_data = fetch_account_data(kis)
    log.info(f"관심종목 {len(market_data)}개 조회 완료")

    # 2) 전략 호출
    try:
        signals = generate_signal(market_data, account_data, kis)
    except Exception as e:
        log.error(f"전략 실행 에러: {e}")
        notifier.notify_error(f"전략 에러: {e}")
        return

    if not signals:
        log.info("시그널 없음. 대기.")
        return

    log.info(f"시그널 {len(signals)}개 생성됨")

    # 3) 주문 실행
    execute_signals(kis, notifier, signals)

    # 4) 장 마감 청산 후 일일 리포트
    now = datetime.now()
    if now.hour >= 15:
        send_daily_report(notifier, kis, market_data, account_data)

    log.info("=== 전략 실행 완료 ===")


# ------------------------------------------------------------------ #
#  엔트리포인트
# ------------------------------------------------------------------ #

def main() -> None:
    """봇을 시작합니다."""
    config = load_config()
    kis_cfg = config.get("kis", {})
    tg_cfg = config.get("telegram", {})
    bot_cfg = config.get("bot", {})

    # 클라이언트 초기화
    kis = KISClient(
        app_key=kis_cfg["app_key"],
        app_secret=kis_cfg["app_secret"],
        account_no=kis_cfg["account_no"],
    )
    slack_cfg = config.get("slack", {})
    notifier = CompositeNotifier([
        TelegramNotifier(
            bot_token=tg_cfg.get("bot_token", ""),
            chat_id=tg_cfg.get("chat_id", 0),
        ),
        SlackNotifier(
            webhook_url=slack_cfg.get("webhook_url", ""),
        ),
    ])

    interval = bot_cfg.get("interval_minutes", 10)

    # 종료 시그널 처리
    def handle_shutdown(signum, frame):
        log.info("종료 시그널 수신. 봇을 종료합니다.")
        notifier.notify_stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # 시작 알림
    log.info(f"자동매매 봇 시작 (실행 주기: {interval}분)")
    notifier.notify_start()

    # 스케줄 등록
    schedule.every(interval).minutes.do(run_cycle, kis, notifier, bot_cfg)

    # 시작 시 1회 즉시 실행
    run_cycle(kis, notifier, bot_cfg)

    # 메인 루프
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
