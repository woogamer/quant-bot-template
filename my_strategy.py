"""
=============================================================
  데이트레이딩 전략 — 추세 적응형 진입 + 당일 청산
=============================================================

■ 전략 요약
  MA10(10일 이동평균) 기울기로 종목별 장세를 판단하고,
  장세에 맞는 방식으로 진입한 뒤 당일 안에 청산합니다.

■ 진입 조건 (매수)
  ┌─ 상승추세 (MA10 기울기 +2%↑)
  │   → 눌림목 매수: 현재가 < MA10
  ├─ 횡보장 (MA10 기울기 ±2%)
  │   → 밴드 하단 매수: 현재가 ≤ 10일 저가 + 밴드폭 × 20%
  └─ 하락추세 (MA10 기울기 -2%↓)
      → 진입 안 함

  + 거래량 필터: 당일 거래량 ≥ 10일 평균일 때만 진입
  + 비중 관리: 종목당 총자산의 최대 20%

■ 청산 조건 (매도)
  · 익절: 수익률 ≥ +2%
  · 손절: 수익률 ≤ -1.5%
  · 장마감: 15:00 이후 보유종목 전량 청산

■ 커스터마이징
  아래 '설정값' 섹션의 숫자를 바꾸면 전략을 조절할 수 있습니다.
  WATCHLIST에 종목코드를 추가/삭제하면 모니터링 대상이 바뀝니다.

=============================================================
  이 파일만 수정하세요! core/ 폴더는 건드리지 마세요.
=============================================================
"""

from datetime import datetime
from core.logger import log
from core.kis_api import BASE_URL, _request_with_retry


# ------------------------------------------------------------------ #
#  설정값 — 여기서 전략 파라미터를 조절하세요
# ------------------------------------------------------------------ #
TAKE_PROFIT = 0.02    # 익절 기준 수익률 (2%)
STOP_LOSS = -0.015    # 손절 기준 수익률 (-1.5%)
MAX_WEIGHT = 0.20     # 종목당 최대 투자 비중 (총자산의 20%)
MA_PERIOD = 10        # 이동평균 기간 (거래일)
SLOPE_THRESHOLD = 0.02  # 추세 판단 기울기 기준 (2%)
VOLUME_FILTER = 1.0   # 거래량 필터 배수 (평균 대비 1.0배 이상)
CLOSE_HOUR = 15       # 장마감 청산 시각 (시)
CLOSE_MINUTE = 0      # 장마감 청산 시각 (분)


# ------------------------------------------------------------------ #
#  일별 시세 조회
# ------------------------------------------------------------------ #

def _get_daily_prices(kis, ticker: str) -> list[dict]:
    """최근 30거래일 일별 시세를 반환합니다."""
    try:
        kis._ensure_auth()
        url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        }
        resp = _request_with_retry(
            "GET", url, params=params,
            headers=kis._headers("FHKST01010400"), timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("output", [])
        result = []
        for item in items:
            close = int(item.get("stck_clpr", 0))
            low = int(item.get("stck_lwpr", 0))
            high = int(item.get("stck_hgpr", 0))
            vol = int(item.get("acml_vol", 0))
            if close > 0:
                result.append({
                    "date": item.get("stck_bsop_date", ""),
                    "close": close,
                    "low": low,
                    "high": high,
                    "vol": vol,
                })
        return result
    except Exception as e:
        log.warning(f"{ticker} 일별 시세 조회 실패: {e}")
        return []


# ------------------------------------------------------------------ #
#  추세 / 변동성 / 거래량 분석
# ------------------------------------------------------------------ #

def _analyze(daily: list[dict]) -> dict:
    """일별 시세로 추세·밴드·거래량을 분석합니다."""
    need = MA_PERIOD + 5  # 기울기 비교를 위해 +5일 필요
    if len(daily) < need:
        return {}

    # MA10: 오늘 제외 최근 10일 종가 평균
    recent = [d["close"] for d in daily[1:MA_PERIOD + 1]]
    ma = sum(recent) / len(recent)

    # 5일 전 시점의 MA10
    past = [d["close"] for d in daily[6:MA_PERIOD + 6]]
    ma_past = sum(past) / len(past) if len(past) >= MA_PERIOD else ma

    # 기울기 → 추세 판단
    change = (ma - ma_past) / ma_past if ma_past > 0 else 0
    if change > SLOPE_THRESHOLD:
        slope = "up"
    elif change < -SLOPE_THRESHOLD:
        slope = "down"
    else:
        slope = "flat"

    # 10일 밴드 (오늘 제외)
    lows = [d["low"] for d in daily[1:MA_PERIOD + 1]]
    highs = [d["high"] for d in daily[1:MA_PERIOD + 1]]

    # 거래량
    vols = [d["vol"] for d in daily[1:MA_PERIOD + 1]]
    avg_vol = sum(vols) / len(vols)
    today_vol = daily[0]["vol"] if daily else 0

    return {
        "ma": ma,
        "slope": slope,
        "low": min(lows),
        "high": max(highs),
        "avg_vol": avg_vol,
        "today_vol": today_vol,
    }


# ------------------------------------------------------------------ #
#  매도 판단 (익절 / 손절 / 장마감 청산)
# ------------------------------------------------------------------ #

def _check_sell(보유종목: list, market_data: dict, now: datetime) -> list[dict]:
    """보유종목의 매도 조건을 확인합니다."""
    signals = []
    장마감 = now.hour >= CLOSE_HOUR and now.minute >= CLOSE_MINUTE

    for 종목 in 보유종목:
        ticker = 종목["종목코드"]
        수량 = 종목["수량"]
        평균단가 = 종목["평균단가"]

        if 수량 <= 0 or 평균단가 <= 0:
            continue

        price_info = market_data.get(ticker)
        if not price_info:
            continue

        현재가 = price_info.get("현재가", 0)
        if 현재가 <= 0:
            continue

        수익률 = (현재가 - 평균단가) / 평균단가
        reason = None

        if 수익률 >= TAKE_PROFIT:
            reason = f"익절 ({수익률:+.2%})"
        elif 수익률 <= STOP_LOSS:
            reason = f"손절 ({수익률:+.2%})"
        elif 장마감:
            reason = f"장마감 청산 ({수익률:+.2%})"

        if reason:
            name = 종목.get("종목명", "") or STOCK_NAMES.get(ticker, "")
            log.info(f"{ticker} {name} 매도: {reason}")
            signals.append({
                "ticker": ticker,
                "action": "SELL",
                "qty": 수량,
                "price": 0,
                "name": name,
                "reason": reason,
            })

    return signals


# ------------------------------------------------------------------ #
#  매수 판단
# ------------------------------------------------------------------ #

def _check_buy(market_data: dict, account_data: dict, kis, 보유종목코드: set) -> list[dict]:
    """매수 조건을 확인합니다."""
    signals = []
    예수금 = account_data.get("예수금", 0)

    # 총자산 = 예수금 + 보유종목 평가금액
    총자산 = 예수금
    for 종목 in account_data.get("보유종목", []):
        price_info = market_data.get(종목["종목코드"])
        if price_info:
            총자산 += price_info.get("현재가", 0) * 종목["수량"]
        else:
            총자산 += 종목["평균단가"] * 종목["수량"]

    종목당최대금액 = 총자산 * MAX_WEIGHT

    for ticker, price_info in market_data.items():
        현재가 = price_info.get("현재가", 0)
        if 현재가 <= 0 or ticker in 보유종목코드:
            continue

        daily = _get_daily_prices(kis, ticker)
        analysis = _analyze(daily)
        if not analysis:
            continue

        ma = analysis["ma"]
        slope = analysis["slope"]
        band_low = analysis["low"]
        band_high = analysis["high"]
        band = band_high - band_low

        # 거래량 필터
        if analysis["avg_vol"] > 0 and analysis["today_vol"] < analysis["avg_vol"] * VOLUME_FILTER:
            continue

        buy = False
        buy_reason = ""
        name = STOCK_NAMES.get(ticker, ticker)

        if slope == "up" and 현재가 < ma:
            buy = True
            buy_reason = f"상승추세 눌림목 (현재가 {현재가:,} < MA{MA_PERIOD} {ma:,.0f})"
            log.info(f"{ticker} {name} [{buy_reason}]")
        elif slope == "flat":
            threshold = band_low + band * 0.2 if band > 0 else band_low
            if 현재가 <= threshold:
                buy = True
                buy_reason = f"횡보 밴드하단 (현재가 {현재가:,} ≤ {threshold:,.0f})"
                log.info(f"{ticker} {name} [{buy_reason}]")
        elif slope == "down":
            log.info(f"{ticker} {name} [하락추세] 패스")
            continue

        if buy:
            매수가능금액 = min(예수금, 종목당최대금액)
            qty = int(매수가능금액 // 현재가)
            if qty >= 1:
                signals.append({
                    "ticker": ticker,
                    "action": "BUY",
                    "qty": qty,
                    "price": 0,
                    "name": name,
                    "reason": buy_reason,
                })
                예수금 -= 현재가 * qty
                log.info(f"{ticker} {name} 매수: {qty}주 ({현재가 * qty:,}원)")

    return signals


# ------------------------------------------------------------------ #
#  전략 메인 (main.py가 호출)
# ------------------------------------------------------------------ #

def generate_signal(market_data: dict, account_data: dict, kis=None) -> list[dict]:
    """데이트레이딩 전략 메인 함수."""
    signals = []
    now = datetime.now()

    if kis is None:
        log.warning("kis 클라이언트 없음 — 전략 실행 불가")
        return signals

    보유종목 = account_data.get("보유종목", [])
    보유종목코드 = {종목["종목코드"] for 종목 in 보유종목}

    # 1) 매도 먼저 (익절 / 손절 / 장마감 청산)
    sell_signals = _check_sell(보유종목, market_data, now)
    signals.extend(sell_signals)

    # 2) 15:00 이후 신규 매수 차단
    if now.hour >= CLOSE_HOUR and now.minute >= CLOSE_MINUTE:
        if sell_signals:
            log.info("장마감 청산 완료. 신규 매수 없음.")
        return signals

    # 3) 매수
    buy_signals = _check_buy(market_data, account_data, kis, 보유종목코드)
    signals.extend(buy_signals)

    return signals


# ======================================================================
#  관심 종목 — KOSPI 시총 상위 30
# ======================================================================
STOCK_NAMES = {
    "005930": "삼성전자",    "000660": "SK하이닉스",  "005380": "현대차",
    "207940": "삼성바이오",  "000270": "기아",        "068270": "셀트리온",
    "105560": "KB금융",      "005490": "POSCO홀딩스", "006400": "삼성SDI",
    "055550": "신한지주",    "035420": "NAVER",       "051910": "LG화학",
    "003550": "LG",          "066570": "LG전자",      "032830": "삼성생명",
    "017670": "SK텔레콤",    "030200": "KT",          "035720": "카카오",
    "086790": "하나금융",    "316140": "우리금융",    "012330": "현대모비스",
    "034730": "SK",          "010130": "고려아연",    "009150": "삼성전기",
    "028260": "삼성물산",    "018260": "삼성SDS",     "033780": "KT&G",
    "036570": "NC소프트",    "015760": "한국전력",    "003490": "대한항공",
}

WATCHLIST = list(STOCK_NAMES.keys())
