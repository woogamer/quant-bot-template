"""한국투자증권(KIS) 모의투자 API 래퍼.

토큰 자동 발급/갱신, 현재가 조회, 잔고 조회, 매수/매도 주문을 제공합니다.
(이 파일은 건드리지 않아도 됩니다)
"""

import time
from typing import Any

import requests
from core.logger import log

# 모의투자 서버 URL
BASE_URL = "https://openapivts.koreainvestment.com:29443"

# 모의투자 서버 500 에러 대응 — 최대 3회 재시도 (1초 간격)
_MAX_RETRIES = 3
_RETRY_DELAY = 1.0


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    """requests 호출을 감싸서 5xx 에러 시 재시도합니다."""
    last_resp = None
    for attempt in range(_MAX_RETRIES):
        resp = requests.request(method, url, **kwargs)
        if resp.status_code < 500:
            return resp
        last_resp = resp
        if attempt < _MAX_RETRIES - 1:
            time.sleep(_RETRY_DELAY)
    return last_resp


class KISClient:
    """KIS REST API 클라이언트."""

    def __init__(self, app_key: str, app_secret: str, account_no: str) -> None:
        self._app_key = app_key
        self._app_secret = app_secret
        self._account_no = account_no
        self._access_token: str = ""
        self._token_expires_at: float = 0

    # ------------------------------------------------------------------ #
    #  인증
    # ------------------------------------------------------------------ #

    def authenticate(self) -> str:
        """OAuth 토큰을 발급받습니다. (자동 호출되므로 직접 호출할 필요 없음)"""
        url = f"{BASE_URL}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self._app_key,
            "appsecret": self._app_secret,
        }
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data.get("access_token", "")
        self._token_expires_at = time.time() + 86000  # ~24시간
        log.info("KIS 인증 완료")
        return self._access_token

    def _ensure_auth(self) -> None:
        """토큰이 없거나 만료되었으면 자동 재인증합니다."""
        if not self._access_token or time.time() >= self._token_expires_at:
            self.authenticate()

    def _headers(self, tr_id: str) -> dict[str, str]:
        """API 요청 헤더를 생성합니다."""
        return {
            "authorization": f"Bearer {self._access_token}",
            "appkey": self._app_key,
            "appsecret": self._app_secret,
            "tr_id": tr_id,
        }

    # ------------------------------------------------------------------ #
    #  현재가 조회
    # ------------------------------------------------------------------ #

    def get_price(self, ticker: str) -> dict[str, Any]:
        """종목의 현재가를 조회합니다.

        Args:
            ticker: 종목코드 (예: "005930")

        Returns:
            API 응답 딕셔너리. output['stck_prpr'] 에 현재가가 들어 있습니다.
        """
        self._ensure_auth()
        url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
        }
        resp = _request_with_retry(
            "GET", url,
            params=params,
            headers=self._headers("FHKST01010100"),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    #  잔고 조회
    # ------------------------------------------------------------------ #

    def get_balance(self) -> dict[str, Any]:
        """계좌 잔고를 조회합니다.

        Returns:
            API 응답 딕셔너리. output1에 보유종목, output2에 계좌잔고 요약.
        """
        self._ensure_auth()
        url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance"
        params = {
            "CANO": self._account_no[:8],
            "ACNT_PRDT_CD": self._account_no[8:],
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        resp = _request_with_retry(
            "GET", url,
            params=params,
            headers=self._headers("VTTC8434R"),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    #  매수 / 매도 주문
    # ------------------------------------------------------------------ #

    def buy(self, ticker: str, qty: int, price: int = 0) -> dict[str, Any]:
        """매수 주문을 실행합니다.

        Args:
            ticker: 종목코드 (예: "005930")
            qty: 주문 수량
            price: 지정가 (0이면 시장가 주문)

        Returns:
            API 응답 딕셔너리.
        """
        return self._place_order(ticker, qty, price, side="buy")

    def sell(self, ticker: str, qty: int, price: int = 0) -> dict[str, Any]:
        """매도 주문을 실행합니다.

        Args:
            ticker: 종목코드 (예: "005930")
            qty: 주문 수량
            price: 지정가 (0이면 시장가 주문)

        Returns:
            API 응답 딕셔너리.
        """
        return self._place_order(ticker, qty, price, side="sell")

    # ------------------------------------------------------------------ #
    #  투자자별 매매동향 조회
    # ------------------------------------------------------------------ #

    def get_investor_trend(self, ticker: str) -> dict[str, Any]:
        """종목의 투자자별 매매동향을 조회합니다.

        Args:
            ticker: 종목코드 (예: "005930")

        Returns:
            API 응답 딕셔너리. output 리스트의 첫 번째 항목이 당일 데이터.
        """
        self._ensure_auth()
        url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
        }
        resp = _request_with_retry(
            "GET", url,
            params=params,
            headers=self._headers("FHKST01010900"),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    #  매수 / 매도 주문 (내부)
    # ------------------------------------------------------------------ #

    def _place_order(
        self, ticker: str, qty: int, price: int, *, side: str
    ) -> dict[str, Any]:
        """내부 주문 실행 메서드."""
        self._ensure_auth()
        tr_id = "VTTC0802U" if side == "buy" else "VTTC0801U"
        url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/order-cash"
        # 시장가: ORD_DVSN="01", 가격 0  /  지정가: ORD_DVSN="00"
        ord_dvsn = "01" if price == 0 else "00"
        payload = {
            "CANO": self._account_no[:8],
            "ACNT_PRDT_CD": self._account_no[8:],
            "PDNO": ticker,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price),
        }
        resp = _request_with_retry(
            "POST", url,
            json=payload,
            headers=self._headers(tr_id),
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        action = "매수" if side == "buy" else "매도"
        log.info(f"주문 완료: {action} {ticker} {qty}주 (가격: {price or '시장가'})")
        return result
