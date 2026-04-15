"""
Daily Financial Briefing Generator
실시간 시세를 가져와 HTML 보고서를 생성합니다.
"""
import yfinance as yf
import json, os, re
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
REPORT_FILE = OUTPUT_DIR / "daily_briefing.html"
HISTORY_FILE = OUTPUT_DIR / "briefing_history.json"
PORTFOLIO_FILE = OUTPUT_DIR / "portfolio_config.json"
MACRO_FILE = OUTPUT_DIR / "macro_events.json"

# ── 포트폴리오 설정 ─────────────────────────────────────────────
# 보유 종목 (ticker, 자산유형)
PORTFOLIO_HOLDINGS = [
    {'ticker': 'TSLA', 'name': '테슬라', 'type': '미국주식', 'shares': 40, 'avg_cost': 229.93},
    {'ticker': 'AAPL', 'name': '애플', 'type': '미국주식', 'shares': 15, 'avg_cost': 172.50},
    {'ticker': 'TLT', 'name': '미국 장기국채 ETF', 'type': '채권/안전자산', 'shares': 8, 'avg_cost': 86.89},
    {'ticker': 'SGOV', 'name': '미국 단기국채 ETF', 'type': '채권/안전자산', 'shares': 35, 'avg_cost': 100.52},
    {'ticker': 'SCO', 'name': '원유 2x 인버스', 'type': '원유 인버스', 'shares': 54, 'avg_cost': 7.70},
]
TOTAL_INVESTMENT_KRW = 34_320_000  # 총 투자금 약 3,432만원
USD_CASH = 419  # 보유 달러 현금

# 포트폴리오 제안에 포함할 자산들
PORTFOLIO_CANDIDATES = {
    '미국주식': [
        # ── 보유종목 (JS에서 필터링됨) ──
        {'ticker': 'TSLA', 'name': '테슬라'},
        {'ticker': 'AAPL', 'name': '애플'},
        {'ticker': 'MSFT', 'name': '마이크로소프트'},
        {'ticker': 'IONQ', 'name': '아이온큐'},
        {'ticker': 'RGTI', 'name': '리게티컴퓨팅'},
        # ── S&P500 / NASDAQ-100 대형주 ──
        {'ticker': 'NVDA', 'name': '엔비디아'},
        {'ticker': 'GOOGL', 'name': '구글'},
        {'ticker': 'AMZN', 'name': '아마존'},
        {'ticker': 'META', 'name': '메타'},
        {'ticker': 'BRK-B', 'name': '버크셔해서웨이'},
        {'ticker': 'LLY', 'name': '일라이릴리'},
        {'ticker': 'JPM', 'name': 'JP모건'},
        {'ticker': 'V', 'name': '비자'},
        {'ticker': 'UNH', 'name': '유나이티드헬스'},
        {'ticker': 'MA', 'name': '마스터카드'},
        {'ticker': 'HD', 'name': '홈디포'},
        {'ticker': 'PG', 'name': '프록터앤갬블'},
        {'ticker': 'COST', 'name': '코스트코'},
        {'ticker': 'MRK', 'name': '머크'},
        {'ticker': 'ORCL', 'name': '오라클'},
        {'ticker': 'ABBV', 'name': '애브비'},
        {'ticker': 'BAC', 'name': '뱅크오브아메리카'},
        {'ticker': 'KO', 'name': '코카콜라'},
        {'ticker': 'PEP', 'name': '펩시코'},
        {'ticker': 'NFLX', 'name': '넷플릭스'},
        {'ticker': 'CRM', 'name': '세일즈포스'},
        {'ticker': 'MCD', 'name': '맥도날드'},
        {'ticker': 'WMT', 'name': '월마트'},
        {'ticker': 'ADBE', 'name': '어도비'},
        {'ticker': 'ACN', 'name': '액센츄어'},
        {'ticker': 'TMO', 'name': '써모피셔'},
        {'ticker': 'IBM', 'name': 'IBM'},
        {'ticker': 'GS', 'name': '골드만삭스'},
        {'ticker': 'INTU', 'name': '인튜이트'},
        {'ticker': 'ISRG', 'name': '인튜이티브서지컬'},
        {'ticker': 'SPGI', 'name': 'S&P글로벌'},
        {'ticker': 'MS', 'name': '모건스탠리'},
        {'ticker': 'BLK', 'name': '블랙록'},
        {'ticker': 'NOW', 'name': '서비스나우'},
        {'ticker': 'T', 'name': 'AT&T'},
        {'ticker': 'AMGN', 'name': '암젠'},
        {'ticker': 'AXP', 'name': '아메리칸익스프레스'},
        {'ticker': 'UBER', 'name': '우버'},
        {'ticker': 'BKNG', 'name': '부킹홀딩스'},
        {'ticker': 'VRTX', 'name': '버텍스파마'},
        {'ticker': 'REGN', 'name': '리제네론'},
        {'ticker': 'PANW', 'name': '팔로알토네트웍스'},
        {'ticker': 'WFC', 'name': '웰스파고'},
        {'ticker': 'INTC', 'name': '인텔'},
        {'ticker': 'C', 'name': '씨티그룹'},
        {'ticker': 'GE', 'name': 'GE에어로스페이스'},
        {'ticker': 'HON', 'name': '허니웰'},
        {'ticker': 'CAT', 'name': '캐터필러'},
        {'ticker': 'JNJ', 'name': '존슨앤존슨'},
        {'ticker': 'PFE', 'name': '화이자'},
        {'ticker': 'CSCO', 'name': '시스코'},
        {'ticker': 'ABT', 'name': '애보트'},
        {'ticker': 'ETN', 'name': '이튼'},
        {'ticker': 'MMM', 'name': '3M'},
        {'ticker': 'DIS', 'name': '디즈니'},
        {'ticker': 'NKE', 'name': '나이키'},
        {'ticker': 'SBUX', 'name': '스타벅스'},
        {'ticker': 'BA', 'name': '보잉'},
        # ── 반도체 ──
        {'ticker': 'AMD', 'name': 'AMD'},
        {'ticker': 'AVGO', 'name': '브로드컴'},
        {'ticker': 'QCOM', 'name': '퀄컴'},
        {'ticker': 'MU', 'name': '마이크론'},
        {'ticker': 'MRVL', 'name': '마벨테크놀로지'},
        {'ticker': 'ARM', 'name': 'ARM홀딩스'},
        {'ticker': 'TSM', 'name': 'TSMC'},
        {'ticker': 'ASML', 'name': 'ASML'},
        {'ticker': 'AMAT', 'name': '어플라이드머티리얼즈'},
        {'ticker': 'LRCX', 'name': '램리서치'},
        {'ticker': 'KLAC', 'name': 'KLA'},
        {'ticker': 'ON', 'name': 'ON반도체'},
        {'ticker': 'TXN', 'name': '텍사스인스트루먼트'},
        {'ticker': 'ADI', 'name': '아날로그디바이시스'},
        {'ticker': 'SNPS', 'name': '시놉시스'},
        {'ticker': 'CDNS', 'name': '케이던스'},
        {'ticker': 'SWKS', 'name': '스카이웍스'},
        # ── AI / 클라우드 / SaaS ──
        {'ticker': 'PLTR', 'name': '팔란티어'},
        {'ticker': 'SNOW', 'name': '스노우플레이크'},
        {'ticker': 'DDOG', 'name': '데이터독'},
        {'ticker': 'NET', 'name': '클라우드플레어'},
        {'ticker': 'SHOP', 'name': '쇼피파이'},
        {'ticker': 'MDB', 'name': '몽고DB'},
        {'ticker': 'TWLO', 'name': '트윌리오'},
        {'ticker': 'ZM', 'name': '줌'},
        {'ticker': 'OKTA', 'name': '옥타'},
        {'ticker': 'HUBS', 'name': '허브스팟'},
        {'ticker': 'GTLB', 'name': '깃랩'},
        {'ticker': 'PATH', 'name': 'UiPath'},
        {'ticker': 'AI', 'name': 'C3.ai'},
        {'ticker': 'APP', 'name': '앱러빈'},
        {'ticker': 'CFLT', 'name': '컨플루언트'},
        {'ticker': 'IOT', 'name': '사이라스AI'},
        # ── 사이버보안 ──
        {'ticker': 'CRWD', 'name': '크라우드스트라이크'},
        {'ticker': 'FTNT', 'name': '포티넷'},
        {'ticker': 'ZS', 'name': '지스케일러'},
        {'ticker': 'CYBR', 'name': 'CyberArk'},
        {'ticker': 'S', 'name': '센티넬원'},
        # ── 핀테크 ──
        {'ticker': 'PYPL', 'name': '페이팔'},
        {'ticker': 'COIN', 'name': '코인베이스'},
        {'ticker': 'HOOD', 'name': '로빈후드'},
        {'ticker': 'AFRM', 'name': '어펌'},
        {'ticker': 'UPST', 'name': '업스타트'},
        {'ticker': 'SOFI', 'name': '소파이'},
        # ── 바이오 / 헬스케어 ──
        {'ticker': 'MRNA', 'name': '모더나'},
        {'ticker': 'BNTX', 'name': '바이오엔텍'},
        {'ticker': 'GILD', 'name': '길리어드'},
        {'ticker': 'BIIB', 'name': '바이오젠'},
        {'ticker': 'ILMN', 'name': '일루미나'},
        {'ticker': 'NTRA', 'name': '나테라'},
        {'ticker': 'CRSP', 'name': 'CRISPR'},
        {'ticker': 'CVS', 'name': 'CVS헬스'},
        {'ticker': 'BSX', 'name': '보스턴사이언티픽'},
        {'ticker': 'DHR', 'name': '다나허'},
        {'ticker': 'DXCM', 'name': 'DexCom'},
        {'ticker': 'GEHC', 'name': 'GE헬스케어'},
        # ── EV / 친환경 ──
        {'ticker': 'RIVN', 'name': '리비안'},
        {'ticker': 'LCID', 'name': '루시드'},
        {'ticker': 'NIO', 'name': '니오'},
        {'ticker': 'XPEV', 'name': '샤오펑'},
        {'ticker': 'LI', 'name': '리오토'},
        {'ticker': 'F', 'name': '포드'},
        {'ticker': 'GM', 'name': 'GM'},
        # ── 소비재 / 엔터 ──
        {'ticker': 'ABNB', 'name': '에어비앤비'},
        {'ticker': 'DASH', 'name': '도어대시'},
        {'ticker': 'SPOT', 'name': '스포티파이'},
        {'ticker': 'RBLX', 'name': '로블록스'},
        {'ticker': 'RDDT', 'name': '레딧'},
        {'ticker': 'PINS', 'name': '핀터레스트'},
        {'ticker': 'SNAP', 'name': '스냅'},
        {'ticker': 'U', 'name': '유니티'},
        {'ticker': 'EA', 'name': 'EA게임즈'},
        {'ticker': 'TTWO', 'name': 'Take-Two'},
        {'ticker': 'CMCSA', 'name': '컴캐스트'},
        {'ticker': 'EXPE', 'name': '익스피디아'},
        {'ticker': 'DUOL', 'name': '듀오링고'},
        # ── 항공우주 / 고성장 ──
        {'ticker': 'RKLB', 'name': '로켓랩'},
        {'ticker': 'SMCI', 'name': '슈퍼마이크로'},
        {'ticker': 'CELH', 'name': '셀시어스'},
        {'ticker': 'CAVA', 'name': 'CAVA그룹'},
        {'ticker': 'OKLO', 'name': '오클로'},
        {'ticker': 'SMR', 'name': 'NuScale파워'},
        # ── 밈주식 ──
        {'ticker': 'GME', 'name': '게임스탑'},
        {'ticker': 'AMC', 'name': 'AMC'},
        # ── REITs / 배당 ──
        {'ticker': 'O', 'name': '리얼티인컴'},
        {'ticker': 'AMT', 'name': '아메리칸타워'},
        {'ticker': 'EQIX', 'name': '이퀴닉스'},
        {'ticker': 'PLD', 'name': '프롤로지스'},
        {'ticker': 'PSA', 'name': '퍼블릭스토리지'},
        # ── 주요 ETF ──
        {'ticker': 'SPY', 'name': 'S&P500 ETF'},
        {'ticker': 'QQQ', 'name': '나스닥100 ETF'},
        {'ticker': 'IWM', 'name': '러셀2000 ETF'},
        {'ticker': 'SMH', 'name': '반도체 ETF(1x)'},
        {'ticker': 'ARKK', 'name': 'ARK이노베이션'},
        {'ticker': 'SOXL', 'name': '반도체3X ETF', 'lev': 3},
        {'ticker': 'TQQQ', 'name': '나스닥3X ETF', 'lev': 3},
        # ── 산업 / 기타 ──
        {'ticker': 'CME', 'name': 'CME그룹'},
        {'ticker': 'ICE', 'name': '인터컨티넨탈'},
        {'ticker': 'MCO', 'name': '무디스'},
        {'ticker': 'ITW', 'name': '일리노이툴웍스'},
        {'ticker': 'EMR', 'name': '에머슨일렉트릭'},
        {'ticker': 'APH', 'name': '암페놀'},
        {'ticker': 'SLB', 'name': '슐럼버거'},
        {'ticker': 'EOG', 'name': 'EOG리소시스'},
        {'ticker': 'TJX', 'name': 'TJX'},
        {'ticker': 'ZTS', 'name': '조에티스'},
        {'ticker': 'CI', 'name': '시그나'},
        {'ticker': 'MMC', 'name': '마쉬앤맥레넌'},
        {'ticker': 'NSC', 'name': '노퍽서던'},
        {'ticker': 'HCA', 'name': 'HCA헬스케어'},
    ],
    '금/은': [
        {'ticker': 'GC=F', 'name': '금 선물'},
        {'ticker': 'GLD', 'name': 'SPDR 금 ETF'},
        {'ticker': 'IAU', 'name': '아이쉐어즈 금 ETF'},
        {'ticker': 'SGOL', 'name': '애버딘 금 ETF'},
        {'ticker': 'SI=F', 'name': '은 선물'},
        {'ticker': 'SLV', 'name': '아이쉐어즈 은 ETF'},
        {'ticker': 'GDX', 'name': '금광 ETF(GDX)'},
        {'ticker': 'GDXJ', 'name': '주니어금광 ETF'},
        {'ticker': 'NEM', 'name': '뉴몬트(금광)'},
        {'ticker': 'GOLD', 'name': '배릭골드'},
        {'ticker': 'WPM', 'name': '휠튼프레셔스메탈'},
        {'ticker': 'FNV', 'name': '프랑코네바다'},
        {'ticker': 'AEM', 'name': '애그니코이글'},
    ],
    '암호화폐': [
        # 시총 상위 (대형 = tier 1)
        {'ticker': 'BTC-USD', 'name': '비트코인', 'tier': 1},
        {'ticker': 'ETH-USD', 'name': '이더리움', 'tier': 1},
        {'ticker': 'BNB-USD', 'name': '바이낸스코인', 'tier': 1},
        {'ticker': 'SOL-USD', 'name': '솔라나', 'tier': 1},
        {'ticker': 'XRP-USD', 'name': '리플', 'tier': 1},
        {'ticker': 'ADA-USD', 'name': '카르다노', 'tier': 2},
        {'ticker': 'AVAX-USD', 'name': '아발란체', 'tier': 2},
        {'ticker': 'DOGE-USD', 'name': '도지코인', 'tier': 2},
        {'ticker': 'DOT-USD', 'name': '폴카닷', 'tier': 2},
        {'ticker': 'LINK-USD', 'name': '체인링크', 'tier': 2},
        {'ticker': 'LTC-USD', 'name': '라이트코인', 'tier': 2},
        {'ticker': 'TRX-USD', 'name': '트론', 'tier': 2},
        {'ticker': 'ATOM-USD', 'name': '코스모스', 'tier': 2},
        {'ticker': 'XLM-USD', 'name': '스텔라루멘', 'tier': 2},
        {'ticker': 'BCH-USD', 'name': '비트코인캐시', 'tier': 2},
        {'ticker': 'FIL-USD', 'name': '파일코인', 'tier': 2},
        {'ticker': 'ICP-USD', 'name': '인터넷컴퓨터', 'tier': 2},
        {'ticker': 'APT-USD', 'name': '앱토스', 'tier': 2},
        {'ticker': 'SUI-USD', 'name': '수이', 'tier': 2},
        {'ticker': 'NEAR-USD', 'name': '니어프로토콜', 'tier': 2},
        # DeFi (알트 = tier 3)
        {'ticker': 'UNI-USD', 'name': '유니스왑', 'tier': 3},
        {'ticker': 'AAVE-USD', 'name': '아베', 'tier': 3},
        {'ticker': 'MKR-USD', 'name': '메이커', 'tier': 3},
        {'ticker': 'CRV-USD', 'name': '커브파이낸스', 'tier': 3},
        {'ticker': 'LDO-USD', 'name': '리도다오', 'tier': 3},
        {'ticker': 'SNX-USD', 'name': '신세틱스', 'tier': 3},
        # 레이어2 / 알트 (tier 3)
        {'ticker': 'ARB-USD', 'name': '아비트럼', 'tier': 3},
        {'ticker': 'OP-USD', 'name': '옵티미즘', 'tier': 3},
        {'ticker': 'IMX-USD', 'name': 'ImmutableX', 'tier': 3},
        {'ticker': 'SEI-USD', 'name': '세이', 'tier': 3},
        # 밈코인 (tier 3)
        {'ticker': 'SHIB-USD', 'name': '시바이누', 'tier': 3},
        {'ticker': 'PEPE-USD', 'name': '페페', 'tier': 3},
        {'ticker': 'BONK-USD', 'name': '봉크', 'tier': 3},
        # 크립토 ETF (대형 = tier 1)
        {'ticker': 'IBIT', 'name': '비트코인 ETF(IBIT)', 'tier': 1},
        {'ticker': 'ETHA', 'name': '이더리움 ETF(ETHA)', 'tier': 1},
        {'ticker': 'BITO', 'name': '비트코인 ETF(BITO)', 'tier': 1},
        {'ticker': 'GBTC', 'name': '그레이스케일 BTC', 'tier': 1},
        {'ticker': 'FBTC', 'name': '피델리티 BTC ETF', 'tier': 1},
    ],
    '원자재': [
        {'ticker': 'CL=F', 'name': 'WTI 원유 선물'},
        {'ticker': 'BZ=F', 'name': '브렌트유 선물'},
        {'ticker': 'NG=F', 'name': '천연가스 선물'},
        {'ticker': 'USO', 'name': '원유 ETF(USO)'},
        {'ticker': 'UNG', 'name': '천연가스 ETF(UNG)'},
        {'ticker': 'HG=F', 'name': '구리 선물'},
        {'ticker': 'CPER', 'name': '구리 ETF(CPER)'},
        {'ticker': 'FCX', 'name': '프리포트맥모란(구리)'},
        {'ticker': 'LIT', 'name': '리튬 ETF(LIT)'},
        {'ticker': 'ALB', 'name': '알베마를(리튬)'},
        {'ticker': 'SQM', 'name': 'SQM(리튬)'},
        {'ticker': 'URA', 'name': '우라늄 ETF(URA)'},
        {'ticker': 'CCJ', 'name': '카메코(우라늄)'},
        {'ticker': 'DBA', 'name': '농산물 ETF(DBA)'},
        {'ticker': 'DBC', 'name': '원자재종합 ETF(DBC)'},
        {'ticker': 'WEAT', 'name': '밀 ETF(WEAT)'},
    ],
    '채권/안전자산': [
        {'ticker': 'TLT', 'name': '미국 장기국채 ETF(TLT)'},
        {'ticker': 'SHY', 'name': '미국 단기국채 ETF(SHY)'},
        {'ticker': 'IEF', 'name': '미국 중기국채 ETF(IEF)'},
        {'ticker': 'BND', 'name': '총채권 ETF(BND)'},
        {'ticker': 'TIP', 'name': '물가연동채 ETF(TIP)'},
        {'ticker': 'AGG', 'name': '종합채권 ETF(AGG)'},
        {'ticker': 'VCIT', 'name': '중기회사채 ETF'},
        {'ticker': 'LQD', 'name': '투자등급회사채 ETF'},
        {'ticker': 'HYG', 'name': '하이일드회사채 ETF'},
        {'ticker': 'EMB', 'name': '신흥국채권 ETF'},
        {'ticker': 'BNDX', 'name': '국제채권 ETF'},
    ],
    '항공': [
        {'ticker': 'DAL', 'name': '델타항공'},
        {'ticker': 'UAL', 'name': '유나이티드항공'},
        {'ticker': 'AAL', 'name': '아메리칸항공'},
        {'ticker': 'LUV', 'name': '사우스웨스트항공'},
        {'ticker': 'JETS', 'name': '항공 ETF (JETS)'},
    ],
    '방위산업': [
        {'ticker': 'LMT', 'name': '록히드마틴'},
        {'ticker': 'RTX', 'name': 'RTX (레이시온)'},
        {'ticker': 'NOC', 'name': '노스롭그루먼'},
        {'ticker': 'GD', 'name': '제너럴다이내믹스'},
        {'ticker': 'ITA', 'name': '방산 ETF (ITA)'},
    ],
    '해운/물류': [
        {'ticker': 'ZIM', 'name': 'ZIM 해운'},
        {'ticker': 'FDX', 'name': 'FedEx'},
        {'ticker': 'UPS', 'name': 'UPS'},
        {'ticker': 'SBLK', 'name': '스타벌크캐리어즈'},
    ],
    '에너지(원유)': [
        {'ticker': 'XOM', 'name': '엑손모빌'},
        {'ticker': 'CVX', 'name': '쉐브론'},
        {'ticker': 'COP', 'name': '코노코필립스'},
        {'ticker': 'OXY', 'name': '옥시덴탈'},
        {'ticker': 'XLE', 'name': '에너지 ETF (XLE)'},
    ],
    '원유 인버스': [
        {'ticker': 'SCO', 'name': '원유 2x 인버스', 'lev': 2},
        {'ticker': 'DUG', 'name': '에너지 2x 인버스', 'lev': 2},
        {'ticker': 'DRIP', 'name': '에너지 3x 인버스', 'lev': 3},
        {'ticker': 'ERY', 'name': '에너지 3x 베어', 'lev': 3},
        {'ticker': 'KOLD', 'name': '천연가스 2x 인버스', 'lev': 2},
    ],
    '방산 인버스': [
        {'ticker': 'SH', 'name': 'S&P500 1x 인버스', 'lev': 1},
        {'ticker': 'SDS', 'name': 'S&P500 2x 인버스', 'lev': 2},
        {'ticker': 'SPXU', 'name': 'S&P500 3x 인버스', 'lev': 3},
        {'ticker': 'PSQ', 'name': '나스닥 1x 인버스', 'lev': 1},
        {'ticker': 'SQQQ', 'name': '나스닥 3x 인버스', 'lev': 3},
        {'ticker': 'SDOW', 'name': '다우 3x 인버스', 'lev': 3},
        {'ticker': 'SPDN', 'name': 'S&P500 베어', 'lev': 1},
    ],
    'VIX/변동성': [
        {'ticker': 'VXX', 'name': 'VIX 단기선물 ETN', 'lev': 1},
        {'ticker': 'UVXY', 'name': 'VIX 1.5x ETF', 'lev': 2},
        {'ticker': 'VIXY', 'name': 'VIX 단기 ETF', 'lev': 1},
        {'ticker': 'SVXY', 'name': 'VIX 인버스 ETF', 'lev': 1},
        {'ticker': 'UVIX', 'name': 'VIX 2x ETF', 'lev': 2},
    ],
    '테크 인버스': [
        {'ticker': 'SOXS', 'name': '반도체 3x 인버스', 'lev': 3},
        {'ticker': 'TECS', 'name': '테크 3x 인버스', 'lev': 3},
        {'ticker': 'SARK', 'name': 'ARK 인버스 ETF', 'lev': 1},
        {'ticker': 'QID', 'name': '나스닥 2x 인버스', 'lev': 2},
    ],
    '중국 인버스': [
        {'ticker': 'YANG', 'name': '중국 3x 인버스', 'lev': 3},
        {'ticker': 'FXP', 'name': '중국 2x 인버스', 'lev': 2},
        {'ticker': 'CHAD', 'name': '중국 CSI300 인버스', 'lev': 1},
    ],
    '채권 인버스': [
        {'ticker': 'TBT', 'name': '미국채 20년 2x 인버스', 'lev': 2},
        {'ticker': 'TMV', 'name': '미국채 20년 3x 인버스', 'lev': 3},
        {'ticker': 'TBF', 'name': '미국채 20년 인버스', 'lev': 1},
        {'ticker': 'TTT', 'name': '미국채 20년 3x 인버스 ETN', 'lev': 3},
    ],
    '금/은 인버스': [
        {'ticker': 'DUST', 'name': '금광 2x 인버스', 'lev': 2},
        {'ticker': 'JDST', 'name': '주니어금광 2x 인버스', 'lev': 2},
        {'ticker': 'GLL', 'name': '금 2x 인버스', 'lev': 2},
        {'ticker': 'ZSL', 'name': '은 2x 인버스', 'lev': 2},
    ],
    '레버리지 ETF': [
        {'ticker': 'UPRO', 'name': 'S&P500 3x 레버리지', 'lev': 3},
        {'ticker': 'TECL', 'name': '테크 3x 레버리지', 'lev': 3},
        {'ticker': 'FNGU', 'name': 'FANG+ 3x 레버리지', 'lev': 3},
        {'ticker': 'BULZ', 'name': '이노베이션 3x 레버리지', 'lev': 3},
        {'ticker': 'LABU', 'name': '바이오 3x 레버리지', 'lev': 3},
        {'ticker': 'CURE', 'name': '헬스케어 3x 레버리지', 'lev': 3},
        {'ticker': 'FAS', 'name': '금융 3x 레버리지', 'lev': 3},
        {'ticker': 'NUGT', 'name': '금광 2x 레버리지', 'lev': 2},
        {'ticker': 'JNUG', 'name': '주니어금광 2x 레버리지', 'lev': 2},
        {'ticker': 'YINN', 'name': '중국 3x 레버리지', 'lev': 3},
        {'ticker': 'EDC', 'name': '이머징 3x 레버리지', 'lev': 3},
    ],
    '클린에너지': [
        {'ticker': 'ENPH', 'name': '엔페이즈에너지'},
        {'ticker': 'SEDG', 'name': '솔라엣지'},
        {'ticker': 'ICLN', 'name': '클린에너지 ETF'},
        {'ticker': 'TAN', 'name': '태양광 ETF'},
        {'ticker': 'FSLR', 'name': '퍼스트솔라'},
    ],
    '이머징마켓': [
        {'ticker': 'EEM', 'name': '이머징마켓 ETF'},
        {'ticker': 'VWO', 'name': '신흥국 ETF'},
        {'ticker': 'TUR', 'name': '터키 ETF'},
        {'ticker': 'KSA', 'name': '사우디 ETF'},
        {'ticker': 'FXI', 'name': '중국 대형주 ETF'},
        {'ticker': 'EWY', 'name': '한국 ETF'},
    ],
    '농업/식량': [
        {'ticker': 'DBA', 'name': '농산물 ETF'},
        {'ticker': 'WEAT', 'name': '밀 ETF'},
        {'ticker': 'CORN', 'name': '옥수수 ETF'},
        {'ticker': 'DE', 'name': '디어앤컴퍼니'},
        {'ticker': 'ADM', 'name': 'ADM (곡물 메이저)'},
        {'ticker': 'MOS', 'name': '모자이크 (비료)'},
    ],
}

# ── 매크로 이벤트 정의 ────────────────────────────────────────────
# 각 이벤트는:
#   - id: 고유 키
#   - name: 표시명
#   - icon: 이모지
#   - desc: 설명
#   - scenario: 시나리오 설명 (종결/완화 시)
#   - sector_boost: 수혜 섹터 → 가산점
#   - sector_drag: 피해 섹터 → 감점
#   - keywords: 뉴스 탐지용 키워드
MACRO_EVENTS = [
    {
        'id': 'iran_war',
        'name': '이란-미국 전쟁 종결',
        'icon': '🕊️',
        'desc': '호르무즈 해협 봉쇄 해제, 이란 원유 시장 복귀',
        'scenario': '유가 급락, 항공·소비재 급등, 방산·금 급락',
        'sector_boost': {'항공': 40, '원유 인버스': 35, 'VIX/변동성': 25, '이머징마켓': 25, '암호화폐': 15, '미국주식': 10},
        'sector_drag': {'에너지(원유)': -35, '금/은': -30, '방위산업': -25, '해운/물류': -15, '방산 인버스': -20},
    },
    {
        'id': 'iran_escalation',
        'name': '이란-미국 전쟁 장기화',
        'icon': '⚔️',
        'desc': '호르무즈 봉쇄 지속, 에너지 위기 심화',
        'scenario': '유가·금 추가 상승, 방산 수혜, 항공·소비재 타격',
        'sector_boost': {'에너지(원유)': 40, '금/은': 35, '방위산업': 30, '해운/물류': 20, 'VIX/변동성': 30, '방산 인버스': 25},
        'sector_drag': {'항공': -35, '원유 인버스': -30, '미국주식': -15, '이머징마켓': -10},
    },
    {
        'id': 'fed_rate_cut',
        'name': '미 연준 금리 인하',
        'icon': '📉',
        'desc': '기준금리 인하 → 유동성 확대',
        'scenario': '성장주·부동산·암호화폐 강세, 달러 약세, 채권 가격 상승',
        'sector_boost': {'미국주식': 30, '암호화폐': 35, '금/은': 20, '이머징마켓': 25, '클린에너지': 20, '레버리지 ETF': 30, '채권 인버스': 20},
        'sector_drag': {'채권/안전자산': -10, '방산 인버스': -15},
    },
    {
        'id': 'fed_rate_hike',
        'name': '미 연준 금리 인상',
        'icon': '📈',
        'desc': '인플레이션 대응 긴축 지속',
        'scenario': '채권·달러 강세, 성장주·코인 약세',
        'sector_boost': {'채권/안전자산': 30, '에너지(원유)': 10, '테크 인버스': 30, '방산 인버스': 20, 'VIX/변동성': 20},
        'sector_drag': {'암호화폐': -35, '미국주식': -20, '클린에너지': -25, '이머징마켓': -15, '레버리지 ETF': -30},
    },
    {
        'id': 'china_slowdown',
        'name': '중국 경기 둔화',
        'icon': '🇨🇳',
        'desc': '부동산 위기, 내수 부진, 디플레이션',
        'scenario': '원자재·이머징 약세, 금·채권 강세',
        'sector_boost': {'채권/안전자산': 25, '금/은': 20, '미국주식': 10, '중국 인버스': 35},
        'sector_drag': {'원자재': -30, '이머징마켓': -35, '에너지(원유)': -20, '농업/식량': -15, '금/은 인버스': -20},
    },
    {
        'id': 'china_stimulus',
        'name': '중국 대규모 경기부양',
        'icon': '🚀',
        'desc': '재정/통화 완화, 인프라 투자 확대',
        'scenario': '원자재·이머징·구리 급등',
        'sector_boost': {'원자재': 35, '이머징마켓': 35, '에너지(원유)': 20, '농업/식량': 15, '해운/물류': 15, '레버리지 ETF': 20},
        'sector_drag': {'금/은': -10, '채권/안전자산': -15, '중국 인버스': -30},
    },
    {
        'id': 'eu_recession',
        'name': '유럽 경기침체',
        'icon': '🇪🇺',
        'desc': 'EU 경제 역성장, 소비 위축',
        'scenario': '유럽 수출 의존 기업 타격, 안전자산 강세',
        'sector_boost': {'금/은': 25, '채권/안전자산': 30, '미국주식': 10},
        'sector_drag': {'이머징마켓': -15, '에너지(원유)': -15, '클린에너지': -20},
    },
    {
        'id': 'climate_crisis',
        'name': '기후위기/이상기후 심화',
        'icon': '🌡️',
        'desc': '폭염·가뭄·홍수 → 식량·에너지 위기',
        'scenario': '농산물·에너지 급등, 클린에너지 정책 가속',
        'sector_boost': {'농업/식량': 40, '클린에너지': 35, '에너지(원유)': 15, '원자재': 20},
        'sector_drag': {'항공': -15, '미국주식': -10},
    },
    {
        'id': 'ai_boom',
        'name': 'AI 산업 초호황',
        'icon': '🤖',
        'desc': 'AI 투자 폭발, 데이터센터·반도체 수요 급증',
        'scenario': 'AI 반도체·클라우드·전력주 급등',
        'sector_boost': {'미국주식': 40, '원자재': 15, '에너지(원유)': 10, '클린에너지': 15, '레버리지 ETF': 35},
        'sector_drag': {'채권/안전자산': -10, '테크 인버스': -30},
    },
    {
        'id': 'crypto_bull',
        'name': '암호화폐 강세장',
        'icon': '₿',
        'desc': 'BTC 반감기 효과, 기관 자금 유입',
        'scenario': 'BTC·ETH·알트코인 전반 급등',
        'sector_boost': {'암호화폐': 45, '미국주식': 10},
        'sector_drag': {'금/은': -10, '채권/안전자산': -10},
    },
]

# ── 1. 시세 데이터 수집 ──────────────────────────────────────────

INDICES = {
    'S&P 500': ('^GSPC', 'https://www.investing.com/indices/us-spx-500'),
    'NASDAQ': ('^IXIC', 'https://www.investing.com/indices/nasdaq-composite'),
    'DOW': ('^DJI', 'https://www.investing.com/indices/us-30'),
    'KOSPI': ('^KS11', 'https://www.investing.com/indices/kospi'),
    'KOSDAQ': ('^KQ11', 'https://www.investing.com/indices/kosdaq'),
    '닛케이225': ('^N225', 'https://www.investing.com/indices/japan-ni225'),
    '상해종합': ('000001.SS', 'https://www.investing.com/indices/shanghai-composite'),
    'DAX': ('^GDAXI', 'https://www.investing.com/indices/germany-30'),
    'FTSE 100': ('^FTSE', 'https://www.investing.com/indices/uk-100'),
}

FOREX = {
    'USD/KRW': ('KRW=X', 'https://www.investing.com/currencies/usd-krw'),
    'EUR/KRW': ('EURKRW=X', 'https://www.investing.com/currencies/eur-krw'),
    'USD/JPY': ('JPY=X', 'https://www.investing.com/currencies/usd-jpy'),
    'EUR/USD': ('EURUSD=X', 'https://www.investing.com/currencies/eur-usd'),
    'USD/CNY': ('CNY=X', 'https://www.investing.com/currencies/usd-cny'),
}

COMMODITIES = {
    '금 ($/oz)': ('GC=F', 'https://www.investing.com/commodities/gold'),
    '은 ($/oz)': ('SI=F', 'https://www.investing.com/commodities/silver'),
    'WTI': ('CL=F', 'https://www.investing.com/commodities/crude-oil'),
    '브렌트': ('BZ=F', 'https://www.investing.com/commodities/brent-oil'),
    '천연가스': ('NG=F', 'https://www.investing.com/commodities/natural-gas'),
    '구리': ('HG=F', 'https://www.investing.com/commodities/copper'),
}

CRYPTO = {
    'BTC': ('BTC-USD', 'https://www.investing.com/crypto/bitcoin'),
    'ETH': ('ETH-USD', 'https://www.investing.com/crypto/ethereum'),
    'XRP': ('XRP-USD', 'https://www.investing.com/crypto/xrp'),
    'SOL': ('SOL-USD', 'https://www.investing.com/crypto/solana'),
    'DOGE': ('DOGE-USD', 'https://www.investing.com/crypto/dogecoin'),
}


def fetch_quote(symbol):
    """yfinance로 현재가, 전일대비, 변동률을 가져옴"""
    try:
        tk = yf.Ticker(symbol)
        info = tk.fast_info
        price = info.last_price
        prev = info.previous_close
        if price and prev and prev != 0:
            change = price - prev
            pct = (change / prev) * 100
            return {'price': price, 'change': change, 'pct': pct}
    except Exception:
        pass
    # fallback: history
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period='5d')
        if len(hist) >= 2:
            price = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            change = price - prev
            pct = (change / prev) * 100
            return {'price': price, 'change': change, 'pct': pct}
        elif len(hist) == 1:
            price = hist['Close'].iloc[-1]
            return {'price': price, 'change': 0, 'pct': 0}
    except Exception:
        pass
    return None


def fetch_market_data():
    """전체 시장 데이터 수집"""
    data = {}
    categories = [
        ('주요 지수', INDICES),
        ('환율', FOREX),
        ('원자재', COMMODITIES),
        ('암호화폐', CRYPTO),
    ]
    for cat_name, items in categories:
        cat_data = []
        symbols = list(items.items())
        # batch download for speed
        ticker_map = {v[0]: (k, v[1]) for k, v in symbols}
        all_symbols = [v[0] for v in items.values()]
        try:
            batch = yf.download(all_symbols, period='5d', progress=False, threads=True)
            for sym in all_symbols:
                name, url = ticker_map[sym]
                try:
                    if len(all_symbols) == 1:
                        closes = batch['Close']
                    else:
                        closes = batch['Close'][sym]
                    closes = closes.dropna()
                    if len(closes) >= 2:
                        price = closes.iloc[-1]
                        prev = closes.iloc[-2]
                        change = price - prev
                        pct = (change / prev) * 100
                        cat_data.append({'name': name, 'url': url, 'price': price, 'change': change, 'pct': pct})
                    elif len(closes) == 1:
                        cat_data.append({'name': name, 'url': url, 'price': closes.iloc[-1], 'change': 0, 'pct': 0})
                except Exception:
                    q = fetch_quote(sym)
                    if q:
                        cat_data.append({'name': name, 'url': url, **q})
        except Exception:
            for name, (sym, url) in items.items():
                q = fetch_quote(sym)
                if q:
                    cat_data.append({'name': name, 'url': url, **q})
        data[cat_name] = cat_data
        print(f"  {cat_name}: {len(cat_data)}건 수집")
    return data


# ── 2. 미국 급등락 종목 (S&P500 + NASDAQ100 기준) ───────────────

def fetch_us_movers():
    """미국 주요 종목 중 큰 변동률 종목 탐색"""
    gainers, losers = [], []
    # 주요 대형주 + 변동성 높은 종목들
    watchlist = [
        'AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','AMD','AVGO','NFLX',
        'CRM','ORCL','ADBE','INTC','QCOM','MU','MRVL','AMAT','LRCX','KLAC',
        'SMCI','ARM','PLTR','SNOW','CRWD','PANW','ZS','NET','DDOG','MDB',
        'COIN','MSTR','RIOT','MARA','HOOD','SOFI','AFRM','UPST','SQ','PYPL',
        'IONQ','RGTI','QBTS','SOUN','RKLB','LUNR','JOBY','LILM','ACHR',
        'LULU','NKE','SBUX','MCD','PEP','KO','WMT','COST','TGT','DG',
        'PFE','MRNA','LLY','NVO','ABBV','JNJ','UNH','BMY','GILD','AMGN',
        'BA','CAT','DE','GE','HON','UPS','FDX','DAL','UAL','AAL',
        'JPM','GS','MS','BAC','C','WFC','V','MA','AXP','BLK',
        'XOM','CVX','COP','OXY','SLB','DVN','FANG','MPC','VLO','PSX',
        'PLUG','FCEL','NKLA','BYND','LCID','RIVN','FSR','GOEV','WKHS',
        'GME','AMC','BB','BBBY','WISH','CLOV','SKLZ','OPEN','DKNG','PENN',
        'AI','BBAI','PRCT','PATH','DOCN','BILL','HUBS','VEEV','TWLO','U',
    ]

    try:
        batch = yf.download(watchlist, period='5d', progress=False, threads=True)
        for sym in watchlist:
            try:
                closes = batch['Close'][sym].dropna()
                if len(closes) < 2:
                    continue
                price = closes.iloc[-1]
                prev = closes.iloc[-2]
                pct = ((price - prev) / prev) * 100
                url = f"https://www.investing.com/equities/{sym.lower()}"
                naver_url = f"https://finance.yahoo.com/quote/{sym}"
                entry = {'ticker': sym, 'price': price, 'pct': pct, 'url': naver_url}
                if pct >= 20:
                    gainers.append(entry)
                elif pct <= -20:
                    losers.append(entry)
            except Exception:
                continue
    except Exception as e:
        print(f"  US movers fetch error: {e}")

    # 변동률 10% 이상도 참고용으로 수집 (20% 이상이 없을 경우)
    mid_gainers, mid_losers = [], []
    if not gainers or not losers:
        try:
            for sym in watchlist:
                try:
                    closes = batch['Close'][sym].dropna()
                    if len(closes) < 2:
                        continue
                    price = closes.iloc[-1]
                    prev = closes.iloc[-2]
                    pct = ((price - prev) / prev) * 100
                    entry = {'ticker': sym, 'price': price, 'pct': pct, 'url': f"https://finance.yahoo.com/quote/{sym}"}
                    if 5 <= pct < 20:
                        mid_gainers.append(entry)
                    elif -20 < pct <= -5:
                        mid_losers.append(entry)
                except Exception:
                    continue
        except Exception:
            pass

    gainers.sort(key=lambda x: x['pct'], reverse=True)
    losers.sort(key=lambda x: x['pct'])
    mid_gainers.sort(key=lambda x: x['pct'], reverse=True)
    mid_losers.sort(key=lambda x: x['pct'])

    print(f"  미국 급등 {len(gainers)}건, 급락 {len(losers)}건 (참고: 상승 {len(mid_gainers)}건, 하락 {len(mid_losers)}건)")
    return gainers, losers, mid_gainers[:10], mid_losers[:10]


# ── 3. 한국 상한가/하한가 ────────────────────────────────────────

# 한국 주요 종목 (KOSPI + KOSDAQ 시가총액 상위 + 테마주)
KR_STOCKS = {
    '삼성전자': '005930.KS', 'SK하이닉스': '000660.KS', 'LG에너지솔루션': '373220.KS',
    '삼성바이오로직스': '207940.KS', '현대차': '005380.KS', '기아': '000270.KS',
    'NAVER': '035420.KS', '카카오': '035720.KS', 'LG화학': '051910.KS',
    'POSCO홀딩스': '005490.KS', '삼성SDI': '006400.KS', '셀트리온': '068270.KS',
    'KB금융': '105560.KS', '신한지주': '055550.KS', '하나금융지주': '086790.KS',
    '현대모비스': '012330.KS', 'LG전자': '066570.KS', 'SK이노베이션': '096770.KS',
    '카카오뱅크': '323410.KS', '크래프톤': '259960.KS', '두산에너빌리티': '034020.KS',
    'HD현대중공업': '329180.KS', '한화에어로스페이스': '012450.KS', 'HLB': '028300.KS',
    '에코프로비엠': '247540.KQ', '에코프로': '086520.KQ', '포스코퓨처엠': '003670.KS',
    '엘앤에프': '066970.KQ', '두산로보틱스': '454910.KQ', '레인보우로보틱스': '277810.KQ',
    '알테오젠': '196170.KQ', '리가켐바이오': '141080.KQ', '삼천당제약': '000250.KQ',
    '폴라리스오피스': '041020.KQ', '위메이드': '112040.KQ', '컴투스': '078340.KQ',
    '펄어비스': '263750.KQ', '카카오게임즈': '293490.KQ', '하이브': '352820.KS',
    'JYP Ent.': '035900.KQ', 'SM': '041510.KQ', 'YG Ent.': '122870.KQ',
    '포스코DX': '222080.KQ', '한미반도체': '042700.KQ', '이수페타시스': '007660.KQ',
    '솔브레인': '357780.KQ', 'SK바이오팜': '326030.KS', '유한양행': '000100.KS',
    '한국전력': '015760.KS', 'KT': '030200.KS', 'SK텔레콤': '017670.KS',
    'LG유플러스': '032640.KS', '대한항공': '003490.KS', 'CJ제일제당': '097950.KS',
}


def fetch_kr_movers():
    """한국 종목 중 상한가(+30%)/하한가(-30%) 탐색"""
    upper, lower = [], []
    big_up, big_down = [], []  # 10%+ 이상

    symbols = list(KR_STOCKS.values())
    name_map = {v: k for k, v in KR_STOCKS.items()}

    try:
        batch = yf.download(symbols, period='5d', progress=False, threads=True)
        for sym in symbols:
            try:
                closes = batch['Close'][sym].dropna()
                if len(closes) < 2:
                    continue
                price = closes.iloc[-1]
                prev = closes.iloc[-2]
                pct = ((price - prev) / prev) * 100
                code = sym.split('.')[0]
                entry = {
                    'name': name_map[sym],
                    'code': code,
                    'price': price,
                    'pct': pct,
                    'url': f"https://finance.naver.com/item/main.naver?code={code}"
                }
                if pct >= 29:
                    upper.append(entry)
                elif pct <= -29:
                    lower.append(entry)
                elif pct >= 5:
                    big_up.append(entry)
                elif pct <= -5:
                    big_down.append(entry)
            except Exception:
                continue
    except Exception as e:
        print(f"  KR movers fetch error: {e}")

    upper.sort(key=lambda x: x['pct'], reverse=True)
    lower.sort(key=lambda x: x['pct'])
    big_up.sort(key=lambda x: x['pct'], reverse=True)
    big_down.sort(key=lambda x: x['pct'])

    print(f"  한국 상한가 {len(upper)}건, 하한가 {len(lower)}건 (참고: 상승 {len(big_up)}건, 하락 {len(big_down)}건)")
    return upper, lower, big_up[:10], big_down[:10]


# ── 4. HTML 생성 ─────────────────────────────────────────────────

def fmt_price(val, is_krw=False):
    if val is None:
        return '-'
    if is_krw:
        return f"{val:,.0f}원"
    if abs(val) >= 100:
        return f"${val:,.2f}" if not is_krw else f"{val:,.0f}원"
    elif abs(val) >= 1:
        return f"${val:,.2f}"
    else:
        return f"${val:.4f}"


def fmt_pct(pct):
    if pct is None:
        return '-', 'tag-up'
    sign = '+' if pct >= 0 else ''
    cls = 'tag-up' if pct >= 0 else 'tag-down'
    return f"{sign}{pct:.2f}%", cls


def market_row_html(name, url, price, pct):
    pct_str, cls = fmt_pct(pct)
    if price >= 100:
        price_str = f"{price:,.2f}"
    elif price >= 1:
        price_str = f"{price:.2f}"
    else:
        price_str = f"{price:.4f}"
    return f'''<div class="market-row"><a href="{url}" target="_blank"><span class="market-name">{name}</span><span class="market-vals"><span class="market-price">{price_str}</span><span class="{cls}">{pct_str}</span></span></a></div>'''


def generate_html(market_data, us_gainers, us_losers, us_mid_up, us_mid_down,
                   kr_upper, kr_lower, kr_big_up, kr_big_down, today_str, day_name):
    """HTML 보고서 생성"""
    day_id = f"day-{today_str}"
    now_str = datetime.now().strftime('%H:%M')

    # Market cards
    market_cards = ''
    for cat_name, items in market_data.items():
        rows = ''.join(market_row_html(i['name'], i['url'], i['price'], i['pct']) for i in items)
        market_cards += f'<div class="market-card"><h4>{cat_name}</h4>{rows}</div>'

    # US movers table
    def us_table(items, label):
        if not items:
            return f'<p style="color:#8b949e;font-size:12px;padding:4px 6px">{label} 20% 이상 변동 종목 없음</p>'
        rows = ''
        for i in items:
            pct_str, cls = fmt_pct(i['pct'])
            p = f"${i['price']:,.2f}" if i['price'] >= 1 else f"${i['price']:.4f}"
            rows += f'<tr><td><a href="{i["url"]}" target="_blank"><span class="ticker">{i["ticker"]}</span></a></td><td>{p}</td><td><span class="{cls}">{pct_str}</span></td><td class="reason">-</td></tr>'
        return f'''<table class="stock-table">
<tr><th style="width:70px">티커</th><th style="width:90px">현재가</th><th style="width:80px">변동률</th><th>비고</th></tr>
{rows}</table>'''

    # Mid movers (참고용)
    def mid_table(items, direction):
        if not items:
            return ''
        rows = ''
        for i in items:
            pct_str, cls = fmt_pct(i['pct'])
            p = f"${i['price']:,.2f}" if i['price'] >= 1 else f"${i['price']:.4f}"
            rows += f'<tr><td><a href="{i["url"]}" target="_blank"><span class="ticker">{i["ticker"]}</span></a></td><td>{p}</td><td><span class="{cls}">{pct_str}</span></td></tr>'
        return f'''<div id="us-mid-{direction}" class="expandable">
<table class="stock-table"><tr><th style="width:70px">티커</th><th style="width:90px">현재가</th><th style="width:80px">변동률</th></tr>{rows}</table>
</div><button class="expand-toggle" onclick="toggleExpand('us-mid-{direction}', this)">+ 주요 {direction} 종목 {len(items)}건 참고</button>'''

    # Korean movers
    def kr_table(items, is_krw=True):
        if not items:
            return '<p style="color:#8b949e;font-size:12px;padding:4px 6px">해당 종목 없음</p>'
        rows = ''
        for i in items:
            pct_str, cls = fmt_pct(i['pct'])
            rows += f'<tr><td><a href="{i["url"]}" target="_blank"><span class="ticker">{i["name"]}</span></a></td><td>{i["price"]:,.0f}원</td><td><span class="{cls}">{pct_str}</span></td><td class="reason">-</td></tr>'
        return f'''<table class="stock-table">
<tr><th style="width:110px">종목</th><th style="width:90px">현재가</th><th style="width:80px">변동률</th><th>비고</th></tr>
{rows}</table>'''

    def kr_mid_table(items, direction):
        if not items:
            return ''
        rows = ''
        for i in items:
            pct_str, cls = fmt_pct(i['pct'])
            rows += f'<tr><td><a href="{i["url"]}" target="_blank"><span class="ticker">{i["name"]}</span></a></td><td>{i["price"]:,.0f}원</td><td><span class="{cls}">{pct_str}</span></td></tr>'
        return f'''<div id="kr-mid-{direction}" class="expandable">
<table class="stock-table"><tr><th style="width:110px">종목</th><th style="width:90px">현재가</th><th style="width:80px">변동률</th></tr>{rows}</table>
</div><button class="expand-toggle" onclick="toggleExpand('kr-mid-{direction}', this)">+ 주요 {direction} 종목 {len(items)}건 참고</button>'''

    day_html = f'''
<div class="day-block" id="{day_id}">
<div class="day-header"><span>{today_str} ({day_name})</span><span class="date-label">{now_str} KST 기준 실시간 시세</span></div>

<div class="section">
  <h2>1. 주요 시장 지표</h2>
  <div class="market-grid">{market_cards}</div>
</div>

<div class="section" id="us-movers-{today_str}">
  <h2>2. 미국 증시 — 급등/급락 (20%+)</h2>
  <h3>▲ 20% 이상 상승</h3>
  {us_table(us_gainers, '당일')}
  {mid_table(us_mid_up, 'up')}
  <h3>▼ 20% 이상 하락</h3>
  {us_table(us_losers, '당일')}
  {mid_table(us_mid_down, 'down')}
</div>

<div class="section" id="kr-limits-{today_str}">
  <h2>3. 한국 증시 — 상한가/하한가</h2>
  <h3>▲ 상한가 (+29% 이상)</h3>
  {kr_table(kr_upper)}
  {kr_mid_table(kr_big_up, 'kr-up')}
  <h3>▼ 하한가 (-29% 이하)</h3>
  {kr_table(kr_lower)}
  {kr_mid_table(kr_big_down, 'kr-down')}
</div>

</div>'''

    return day_html


# ── 5. 포트폴리오 분석 ───────────────────────────────────────────

def fetch_portfolio_data(usd_krw):
    """현재 보유 종목 + 후보 자산 시세 수집"""
    # 보유 종목 현재가
    holdings = []
    h_symbols = [h['ticker'] for h in PORTFOLIO_HOLDINGS]

    try:
        batch = yf.download(h_symbols, period='1mo', progress=False, threads=True)
        for h in PORTFOLIO_HOLDINGS:
            sym = h['ticker']
            shares = h.get('shares', 0)
            avg_cost = h.get('avg_cost', 0)
            try:
                if len(h_symbols) == 1:
                    closes = batch['Close'].dropna()
                else:
                    closes = batch['Close'][sym].dropna()
                price_usd = closes.iloc[-1]
                price_1w = closes.iloc[-5] if len(closes) >= 5 else closes.iloc[0]
                price_1m = closes.iloc[0]
                pct_1d = ((closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100) if len(closes) >= 2 else 0
                pct_1w = ((price_usd - price_1w) / price_1w * 100)
                pct_1m = ((price_usd - price_1m) / price_1m * 100)
                price_krw = price_usd * usd_krw
                est_value = shares * price_krw
                cost_total = shares * avg_cost * usd_krw
                pnl = est_value - cost_total
                pnl_pct = ((price_usd - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0
                holdings.append({
                    **h,
                    'price_usd': price_usd,
                    'price_krw': price_krw,
                    'pct_1d': pct_1d,
                    'pct_1w': pct_1w,
                    'pct_1m': pct_1m,
                    'est_shares': shares,
                    'est_value': est_value,
                    'avg_cost': avg_cost,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                })
            except Exception:
                holdings.append({**h, 'price_usd': 0, 'price_krw': 0, 'pct_1d': 0, 'pct_1w': 0, 'pct_1m': 0, 'est_shares': shares, 'est_value': 0, 'avg_cost': avg_cost, 'pnl': 0, 'pnl_pct': 0})
    except Exception as e:
        print(f"  포트폴리오 보유종목 fetch error: {e}")

    # 후보 자산 시세
    candidates = {}
    for cat, items in PORTFOLIO_CANDIDATES.items():
        cat_data = []
        syms = [i['ticker'] for i in items]
        name_map = {i['ticker']: i['name'] for i in items}
        lev_map = {i['ticker']: i.get('lev', 1) for i in items}
        tier_map = {i['ticker']: i.get('tier', 0) for i in items}
        try:
            batch = yf.download(syms, period='3mo', progress=False, threads=True)
            for sym in syms:
                try:
                    if len(syms) == 1:
                        closes = batch['Close'].dropna()
                    else:
                        closes = batch['Close'][sym].dropna()
                    if len(closes) < 2:
                        continue
                    price = closes.iloc[-1]
                    pct_1d = ((closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100)
                    pct_1w = ((price - closes.iloc[-5]) / closes.iloc[-5] * 100) if len(closes) >= 5 else 0
                    pct_1m = ((price - closes.iloc[-22]) / closes.iloc[-22] * 100) if len(closes) >= 22 else ((price - closes.iloc[0]) / closes.iloc[0] * 100)
                    pct_3m = ((price - closes.iloc[0]) / closes.iloc[0] * 100)
                    # 변동성 (30일 표준편차 연환산)
                    all_returns = closes.pct_change().dropna()
                    if len(all_returns) >= 22:
                        returns_30 = all_returns.tail(22)
                        vol_30d = returns_30.std() * (252 ** 0.5) * 100
                    else:
                        vol_30d = 0

                    # ── 고도화 지표 ──
                    # 샤프 유사비율: 1개월 수익률 / 변동성
                    sharpe_1m = (pct_1m / vol_30d) if vol_30d > 0 else 0

                    # RSI 유사값 (14일 기준)
                    rsi = 50  # 기본값
                    if len(all_returns) >= 14:
                        recent14 = all_returns.tail(14)
                        gains = recent14[recent14 > 0].sum()
                        losses = -recent14[recent14 < 0].sum()
                        if losses > 0:
                            rs = gains / losses
                            rsi = 100 - (100 / (1 + rs))
                        elif gains > 0:
                            rsi = 100
                        else:
                            rsi = 50

                    # 추세 가속도: 1개월 vs 3개월 월평균
                    avg_3m_monthly = pct_3m / 3 if pct_3m != 0 else 0
                    accel = pct_1m - avg_3m_monthly  # 양수=가속, 음수=둔화

                    # 최고점 대비 하락률 (drawdown)
                    peak = closes.max()
                    drawdown = ((price - peak) / peak * 100) if peak > 0 else 0

                    cat_data.append({
                        'ticker': sym,
                        'name': name_map[sym],
                        'price': price,
                        'pct_1d': pct_1d,
                        'pct_1w': pct_1w,
                        'pct_1m': pct_1m,
                        'pct_3m': pct_3m,
                        'vol_30d': vol_30d,
                        'sharpe': sharpe_1m,
                        'rsi': rsi,
                        'accel': accel,
                        'drawdown': drawdown,
                        'lev': lev_map.get(sym, 1),
                        'tier': tier_map.get(sym, 0),
                    })
                except Exception:
                    continue
        except Exception:
            pass
        candidates[cat] = cat_data

    print(f"  포트폴리오: 보유 {len(holdings)}건, 후보 {sum(len(v) for v in candidates.values())}건")
    return holdings, candidates


def generate_portfolio_suggestion(holdings, candidates, usd_krw):
    """간단한 룰 기반 포트폴리오 제안 생성"""
    suggestions = []

    # 1. 현재 포트폴리오 분석
    total_val = sum(h['est_value'] for h in holdings)
    avg_1m = sum(h['pct_1m'] for h in holdings) / len(holdings) if holdings else 0
    avg_vol = 0

    # 2. 각 후보 자산에서 best pick
    for cat, items in candidates.items():
        if not items:
            continue
        # 모멘텀 + 낮은 변동성 점수
        for item in items:
            # 기존 보유 종목이면 skip
            if item['ticker'] in [h['ticker'] for h in holdings]:
                continue
            score = item['pct_1m'] * 0.4 + item['pct_3m'] * 0.3 - item['vol_30d'] * 0.1 + item['pct_1w'] * 0.2
            item['score'] = score

        ranked = sorted([i for i in items if 'score' in i], key=lambda x: x['score'], reverse=True)
        if ranked:
            suggestions.append({'category': cat, 'picks': ranked[:3]})

    # 3. 포트폴리오 배분 제안 (현재 100% 미국주식 → 분산)
    allocation = []
    if avg_1m > 5:
        # 강세장: 주식 비중 유지, 일부 금/코인
        allocation = [
            ('현재 보유 미국주식', 55, '모멘텀 유지'),
            ('금/은', 15, '인플레이션 헤지'),
            ('암호화폐', 15, '고성장 포트폴리오'),
            ('원자재', 10, '분산 효과'),
            ('채권/안전자산', 5, '리스크 완충'),
        ]
    elif avg_1m > 0:
        # 보통장: 균형 배분
        allocation = [
            ('현재 보유 미국주식', 45, '핵심 보유'),
            ('금/은', 20, '안전자산 비중 확대'),
            ('암호화폐', 10, '성장 기회'),
            ('원자재', 10, '인플레이션 대비'),
            ('채권/안전자산', 15, '안정성 강화'),
        ]
    else:
        # 약세장: 방어적 배분
        allocation = [
            ('현재 보유 미국주식', 30, '비중 축소'),
            ('금/은', 25, '안전자산 확대'),
            ('암호화폐', 5, '최소 배분'),
            ('원자재', 10, '실물자산'),
            ('채권/안전자산', 30, '방어 최우선'),
        ]

    return suggestions, allocation, avg_1m


def generate_portfolio_html(holdings, candidates, suggestions, allocation, avg_1m, usd_krw):
    """포트폴리오 탭 HTML 생성 — 목표 수익률 + 기간 슬라이더, 동적 추천"""
    total_val = sum(h['est_value'] for h in holdings)
    total_manwon = int(TOTAL_INVESTMENT_KRW / 10000)

    # 현재 보유 테이블
    holding_rows = ''
    total_pnl = sum(h.get('pnl', 0) for h in holdings)
    for h in holdings:
        pct_1d_str, cls_1d = fmt_pct(h['pct_1d'])
        pct_1m_str, cls_1m = fmt_pct(h['pct_1m'])
        weight = (h['est_value'] / total_val * 100) if total_val > 0 else 20
        pnl = h.get('pnl', 0)
        pnl_pct = h.get('pnl_pct', 0)
        pnl_cls = 'up' if pnl >= 0 else 'down'
        avg_cost = h.get('avg_cost', 0)
        holding_rows += f'''<tr>
<td><a href="https://finance.yahoo.com/quote/{h['ticker']}" target="_blank"><span class="ticker">{h['name']}</span></a></td>
<td>{h['ticker']}</td>
<td>${avg_cost:,.2f}</td>
<td>${h['price_usd']:,.2f}</td>
<td>{h['est_shares']}주</td>
<td>{h['est_value']:,.0f}원</td>
<td><span class="{pnl_cls}">{pnl:+,.0f}원</span></td>
<td><span class="{pnl_cls}">{pnl_pct:+.1f}%</span></td>
<td><span class="{cls_1d}">{pct_1d_str}</span></td>
<td><span class="{cls_1m}">{pct_1m_str}</span></td>
<td>{weight:.1f}%</td>
</tr>'''

    # 시장 상황 판단
    if avg_1m > 5:
        market_state = '강세장'
        market_color = '#3fb950'
    elif avg_1m > 0:
        market_state = '보합장'
        market_color = '#f0883e'
    else:
        market_state = '약세장'
        market_color = '#f85149'

    # 모든 후보 종목 데이터를 JSON으로 직렬화 (JS에서 동적 정렬용)
    all_candidates_json = {}
    for cat, items in candidates.items():
        all_candidates_json[cat] = []
        for p in items:
            # 보유 종목은 제외
            if p['ticker'] in [h['ticker'] for h in holdings]:
                continue
            url = f"https://finance.yahoo.com/quote/{p['ticker']}"
            all_candidates_json[cat].append({
                'name': p['name'],
                'ticker': p['ticker'],
                'price': round(p['price'], 4),
                'pct_1m': round(p['pct_1m'], 2),
                'pct_3m': round(p['pct_3m'], 2),
                'vol': round(p['vol_30d'], 2),
                'sharpe': round(p.get('sharpe', 0), 3),
                'rsi': round(p.get('rsi', 50), 1),
                'accel': round(p.get('accel', 0), 2),
                'dd': round(p.get('drawdown', 0), 2),
                'lev': p.get('lev', 1),
                'tier': p.get('tier', 0),
                'url': url,
            })
    candidates_json_str = json.dumps(all_candidates_json, ensure_ascii=False)

    # 매크로 이벤트 데이터를 JS용 JSON으로 직렬화
    macro_json_data = []
    for ev in MACRO_EVENTS:
        macro_json_data.append({
            'id': ev['id'],
            'name': ev['name'],
            'icon': ev['icon'],
            'desc': ev['desc'],
            'scenario': ev['scenario'],
            'boost': ev['sector_boost'],
            'drag': ev['sector_drag'],
        })
    macro_json_str = json.dumps(macro_json_data, ensure_ascii=False)

    portfolio_html = f'''
<div id="page-portfolio" class="page-content" style="display:none">
<div class="container">

<div class="section" style="border-left:3px solid {market_color}">
  <h2>시장 진단 &amp; 현재 상태</h2>
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;flex-wrap:wrap">
    <span style="background:{market_color};color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:700">{market_state}</span>
    <span style="color:#8b949e;font-size:12px">보유종목 1개월 평균: <span class="{'up' if avg_1m>=0 else 'down'}">{avg_1m:+.2f}%</span></span>
    <span style="color:#8b949e;font-size:12px">환율: $1 = {usd_krw:,.2f}원</span>
    <span style="color:#8b949e;font-size:12px">총 투자금: <b>{total_manwon:,}만원</b></span>
    <span style="color:#f0883e;font-size:12px">현재 배분: 미국주식 100%</span>
  </div>
</div>

<div class="section">
  <h2>현재 보유 포트폴리오</h2>
  <table class="stock-table">
  <tr><th>종목</th><th>티커</th><th>매입($)</th><th>현재($)</th><th>수량</th><th>평가액</th><th>손익</th><th>수익률</th><th>1일</th><th>1개월</th><th>비중</th></tr>
  {holding_rows}
  <tr style="border-top:2px solid #30363d;font-weight:700">
    <td colspan="5" style="text-align:right">합계</td>
    <td>{total_val:,.0f}원</td>
    <td><span class="{'up' if total_pnl>=0 else 'down'}">{total_pnl:+,.0f}원</span></td>
    <td colspan="3"></td>
    <td>100%</td>
  </tr>
  </table>
  <div class="info-note">* 실제 보유 수량·매입가 기준 | 보유 달러: ${USD_CASH} ({USD_CASH * usd_krw:,.0f}원)</div>
</div>

<!-- ── 투자 목표 설정 ── -->
<div class="section" id="goal-section">
  <h2>투자 목표 설정</h2>

  <!-- 프리셋 -->
  <div class="preset-row">
    <button class="preset-btn" data-target="5" data-period="36" onclick="setPreset(5,36)">안정 추구</button>
    <button class="preset-btn" data-target="10" data-period="24" onclick="setPreset(10,24)">균형 투자</button>
    <button class="preset-btn active" data-target="20" data-period="12" onclick="setPreset(20,12)">성장 투자</button>
    <button class="preset-btn" data-target="40" data-period="6" onclick="setPreset(40,6)">공격 투자</button>
    <button class="preset-btn" data-target="70" data-period="3" onclick="setPreset(70,3)">고위험 투기</button>
  </div>

  <!-- 목표 수익률 -->
  <div class="slider-row">
    <span class="slider-label">목표 연수익률</span>
    <input type="range" id="targetSlider" min="3" max="100" value="20"
      style="flex:1;accent-color:#58a6ff;height:6px;min-width:0" oninput="onTargetChange(this.value)">
    <span id="targetValue" class="slider-value" style="color:#58a6ff">20%</span>
  </div>

  <!-- 투자 기간 -->
  <div class="slider-row">
    <span class="slider-label">목표 달성 기간</span>
    <input type="range" id="periodSlider" min="1" max="60" value="12"
      style="flex:1;accent-color:#f0883e;height:6px;min-width:0" oninput="onPeriodChange(this.value)">
    <span id="periodValue" class="slider-value" style="color:#f0883e">12개월</span>
  </div>

  <!-- 종합 위험 점수 -->
  <div style="background:#0d1117;border-radius:6px;padding:10px 14px;margin-top:8px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
      <span style="font-size:12px;color:#8b949e">종합 공격성 점수</span>
      <span id="riskScore" style="font-size:16px;font-weight:700;color:#f0883e">50 / 100</span>
    </div>
    <div style="height:8px;background:#21262d;border-radius:4px;overflow:hidden">
      <div id="riskBar" style="height:100%;width:50%;border-radius:4px;transition:all .3s;background:linear-gradient(90deg,#3fb950,#f0883e,#f85149)"></div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:4px">
      <span style="font-size:10px;color:#3fb950">안전</span>
      <span id="riskDesc" style="font-size:11px;color:#8b949e;text-align:center">주식+원자재 중심 균형 포트폴리오</span>
      <span style="font-size:10px;color:#f85149">위험</span>
    </div>
  </div>
</div>

<!-- ── 매크로 이벤트 시나리오 ── -->
<div class="section" id="macro-section">
  <h2>글로벌 이벤트 시나리오 <span style="font-size:11px;color:#8b949e;font-weight:400">— 예상되는 이벤트를 ON하면 추천이 바뀝니다</span></h2>
  <div id="macroToggles" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:8px"></div>
  <div id="macroSummary" style="margin-top:10px;padding:8px 12px;background:#0d1117;border-radius:6px;display:none">
    <div style="font-size:11px;color:#8b949e;margin-bottom:4px">이벤트 반영 섹터 영향</div>
    <div id="macroImpact"></div>
  </div>
</div>

<!-- ── 동적 배분 결과 ── -->
<div class="section">
  <h2>제안 포트폴리오 배분 <span id="allocLabel" style="font-size:12px;color:#8b949e;font-weight:400"></span></h2>
  <div id="allocBar" style="display:flex;gap:2px;margin-bottom:10px;height:28px;border-radius:4px;overflow:hidden"></div>
  <table class="stock-table">
  <tr><th>자산군</th><th style="width:50px">배분</th><th style="width:120px">비율</th><th style="width:90px">금액</th><th>전략 설명</th><th>위험도</th></tr>
  <tbody id="allocTable"></tbody>
  </table>
</div>

<!-- ── 동적 추천 종목 ── -->
<div class="section">
  <h2>추천 종목 <span id="picksLabel" style="font-size:12px;color:#8b949e;font-weight:400"></span></h2>
  <div id="picksContainer"></div>
</div>

<!-- ── 리밸런싱 액션 플랜 ── -->
<div class="section">
  <h2>리밸런싱 액션 플랜</h2>
  <table class="stock-table">
  <tr><th style="width:50px">순서</th><th>액션</th><th>상세</th></tr>
  <tbody id="actionTable"></tbody>
  </table>
  <div class="info-note">* 목표 수익률이 높고 기간이 짧을수록 위험이 비례합니다. 투자 판단의 최종 책임은 본인에게 있습니다.</div>
</div>

</div>
</div>'''

    # All JS in raw string
    portfolio_js = '''
<script>
const TOTAL = ''' + str(TOTAL_INVESTMENT_KRW) + ''';
const CANDIDATES = ''' + candidates_json_str + ''';
const MACRO_EVENTS = ''' + macro_json_str + ''';

// Active macro events (toggled by user)
let activeMacros = new Set();

const ALLOC_PROFILES = {
  3:  [15, 25,  0, 5, 55],
  5:  [20, 25,  0, 5, 50],
  7:  [25, 25,  2, 8, 40],
  10: [35, 20,  5, 10, 30],
  15: [45, 18,  8, 12, 17],
  20: [50, 15, 10, 15, 10],
  25: [50, 12, 13, 18, 7],
  30: [48, 10, 15, 22, 5],
  40: [45,  8, 18, 24, 5],
  50: [42,  5, 22, 26, 5],
  60: [40,  5, 25, 25, 5],
  70: [38,  3, 28, 26, 5],
  80: [35,  2, 30, 28, 5],
  90: [30,  2, 33, 30, 5],
  100:[28,  0, 35, 32, 5],
};

const CATS = [
  {name:'미국주식 (보유)', color:'#3fb950', key:'미국주식'},
  {name:'금/은',          color:'#58a6ff', key:'금/은'},
  {name:'암호화폐',       color:'#f0883e', key:'암호화폐'},
  {name:'원자재',         color:'#8b949e', key:'원자재'},
  {name:'채권/안전자산',   color:'#bc8cff', key:'채권/안전자산'},
];

const DESC = {
  '미국주식 (보유)': {
    safe:'대형 우량주 위주 보유 유지', mid:'성장주 비중 유지, 모멘텀 활용', aggr:'소형 성장주·테마주 집중, 변동성 감수'
  },
  '금/은': {
    safe:'인플레이션 헤지, 포트폴리오 핵심 안전장치', mid:'금 ETF 중심 분산', aggr:'최소 비중 유지'
  },
  '암호화폐': {
    safe:'배분 없음 (고위험 회피)', mid:'BTC·ETH ETF 위주 제한적 참여', aggr:'알트코인 포함 고수익 추구, 손실 가능성 큼'
  },
  '원자재': {
    safe:'소량 분산 (원자재 ETF)', mid:'에너지+금속 균형 배분', aggr:'원자재 레버리지·선물 포함'
  },
  '채권/안전자산': {
    safe:'포트폴리오 핵심, 원금 보존 최우선', mid:'금리 수익 + 하락장 완충', aggr:'최소한의 안전판'
  },
};

function interpolate(target) {
  const keys = Object.keys(ALLOC_PROFILES).map(Number).sort((a,b)=>a-b);
  if (target <= keys[0]) return [...ALLOC_PROFILES[keys[0]]];
  if (target >= keys[keys.length-1]) return [...ALLOC_PROFILES[keys[keys.length-1]]];
  let lo, hi;
  for (let i = 0; i < keys.length-1; i++) {
    if (target >= keys[i] && target <= keys[i+1]) { lo=keys[i]; hi=keys[i+1]; break; }
  }
  const t = (target-lo)/(hi-lo);
  return ALLOC_PROFILES[lo].map((v,i) => Math.round(v + t*(ALLOC_PROFILES[hi][i]-v)));
}

function normalize(arr) {
  const s = arr.reduce((a,b)=>a+b,0);
  if (s===100) return arr;
  arr[arr.indexOf(Math.max(...arr))] += 100-s;
  return arr;
}

// 공격성 점수 (0~100): 높은 목표 + 짧은 기간 = 높은 점수
function calcRisk(target, months) {
  const targetScore = Math.min(target / 100, 1) * 60;
  const periodScore = Math.max(0, (1 - months / 60)) * 40;
  return Math.round(targetScore + periodScore);
}

// 매크로 이벤트 → 섹터별 합산 보너스 계산
function calcMacroBonus() {
  const bonus = {};
  activeMacros.forEach(id => {
    const ev = MACRO_EVENTS.find(e => e.id === id);
    if (!ev) return;
    for (const [sec, val] of Object.entries(ev.boost || {})) {
      bonus[sec] = (bonus[sec] || 0) + val;
    }
    for (const [sec, val] of Object.entries(ev.drag || {})) {
      bonus[sec] = (bonus[sec] || 0) + val;
    }
  });
  return bonus;
}

// 종목 점수 계산 — 공격성 + 매크로 이벤트 반영
function scoreItem(item, risk, catKey) {
  // ── 1) 샤프 비율 기반 효율성 점수 (위험 대비 수익) ──
  const sharpe = item.sharpe || 0;
  const sharpeScore = Math.max(-10, Math.min(15, sharpe * 10));

  // ── 2) RSI 기반 과열/과매도 보정 ──
  const rsi = item.rsi || 50;
  let rsiAdj = 0;
  if (risk <= 30) {
    // 안전: 과열 종목 강하게 감점, 적정 구간 가점
    rsiAdj = rsi > 75 ? -8 : rsi > 65 ? -3 : rsi < 30 ? 4 : rsi < 45 ? 2 : 0;
  } else if (risk <= 60) {
    // 균형: 과열 약간 감점, 과매도 약간 가점
    rsiAdj = rsi > 80 ? -5 : rsi > 70 ? -2 : rsi < 25 ? 5 : rsi < 40 ? 2 : 0;
  } else {
    // 공격: 과열은 모멘텀으로 해석, 과매도 = 반등 기대
    rsiAdj = rsi > 85 ? -3 : rsi < 20 ? 8 : rsi < 35 ? 4 : 0;
  }

  // ── 3) 추세 가속도 (1개월 vs 3개월 월평균) ──
  const accel = item.accel || 0;
  const accelScore = Math.max(-5, Math.min(8, accel * 0.3));

  // ── 4) 낙폭과대 반등 기대 (drawdown) ──
  const dd = item.dd || 0; // 음수값 (예: -25%)
  let ddScore = 0;
  if (risk <= 30) {
    ddScore = dd < -20 ? -3 : 0; // 안전투자: 큰 낙폭 = 위험 신호
  } else if (risk <= 60) {
    ddScore = dd < -30 ? 3 : dd < -15 ? 1 : 0; // 균형: 적당한 낙폭 = 기회
  } else {
    ddScore = dd < -40 ? 8 : dd < -25 ? 5 : dd < -15 ? 2 : 0; // 공격: 큰 낙폭 = 반등 기대
  }

  // ── 5) 기존 모멘텀 (비중 축소) ──
  let momScore;
  if (risk <= 30) {
    momScore = item.pct_1m * 0.1 + item.pct_3m * 0.15 - item.vol * 0.3;
  } else if (risk <= 60) {
    momScore = item.pct_1m * 0.15 + item.pct_3m * 0.15 - item.vol * 0.08;
  } else {
    momScore = item.pct_1m * 0.2 + item.pct_3m * 0.1 + item.vol * 0.05;
  }

  // ── 종합 ──
  let base = sharpeScore + rsiAdj + accelScore + ddScore + momScore;

  // ── 6) 매크로 이벤트 보너스 (종목별 차별화) ──
  const macroBonus = calcMacroBonus();
  const sectorBonus = macroBonus[catKey] || 0;
  if (sectorBonus !== 0) {
    // 변동성 높은 종목 = 이벤트에 더 민감
    const volAmp = 1 + (item.vol / 100) * 0.8;
    // 샤프가 높은 종목 = 효율적으로 이벤트 수혜
    const effFactor = sharpe > 0.5 ? 1.3 : sharpe > 0 ? 1.1 : 0.9;
    // 추세 가속 종목 = 이벤트 방향과 시너지
    const accelFactor = sectorBonus > 0
      ? (accel > 2 ? 1.3 : accel > 0 ? 1.1 : 0.85)
      : (accel < -2 ? 1.3 : accel < 0 ? 1.1 : 0.85);
    // 낙폭과대 + 수혜 이벤트 = 강한 반등 기대
    const ddFactor = (sectorBonus > 0 && dd < -20) ? 1.25 : 1;
    base += sectorBonus * volAmp * effFactor * accelFactor * ddFactor;
  }
  return base;
}

function fmtPct(v) {
  const s = v >= 0 ? '+' : '';
  const c = v >= 0 ? 'tag-up' : 'tag-down';
  return `<span class="${c}">${s}${v.toFixed(2)}%</span>`;
}

function fmtPrice(v) {
  if (v >= 100) return '$' + v.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
  if (v >= 1) return '$' + v.toFixed(2);
  return '$' + v.toFixed(4);
}

let currentTarget = 20;
let currentPeriod = 12;

function updateAll() {
  const target = currentTarget;
  const months = currentPeriod;
  const risk = calcRisk(target, months);

  // 기간 보정: 짧은 기간이면 더 공격적으로 배분 조정
  const periodMultiplier = months <= 3 ? 1.3 : months <= 6 ? 1.15 : months <= 12 ? 1.0 : months <= 24 ? 0.9 : 0.8;
  const adjustedTarget = Math.min(100, Math.round(target * periodMultiplier));

  let alloc = interpolate(adjustedTarget);

  // ── 데이터 기반 배분 재조정 ──
  // 각 기본 카테고리의 실제 기대수익률(top3 평균 3개월 수익률)을 계산
  // 주식으로도 목표 달성 가능하면 암호화폐를 줄이고 주식 비중을 높임
  const catKeys = ['미국주식','금/은','암호화폐','원자재','채권/안전자산'];
  const catExpReturn = catKeys.map(k => {
    const items = CANDIDATES[k];
    if (!items || items.length === 0) return 0;
    const sorted = [...items].sort((a,b) => b.pct_3m - a.pct_3m);
    const top = sorted.slice(0, Math.min(5, sorted.length));
    return top.reduce((s,it) => s + it.pct_3m, 0) / top.length;
  });
  // 연환산 기대수익률
  const annualized = catExpReturn.map(r => r * 4);
  // 주식의 기대수익률이 목표에 가까우면 주식 비중 강화
  const stockReturn = annualized[0]; // 미국주식
  const cryptoReturn = annualized[2]; // 암호화폐
  if (stockReturn > 0 && target > 20) {
    // 주식이 목표 수익률의 몇 %를 달성 가능한지
    const stockCoverage = Math.min(1, stockReturn / target);
    // 주식이 충분히 성장 가능하면, 암호화폐에서 주식으로 비중 이동
    if (stockCoverage > 0.5) {
      const shift = Math.round((stockCoverage - 0.5) * 30); // 최대 15%p 이동
      alloc[0] = alloc[0] + shift; // 주식 증가
      alloc[2] = Math.max(5, alloc[2] - shift); // 암호화폐 감소
    }
  }
  alloc = normalize(alloc);

  const macroBonus = calcMacroBonus();

  // 매크로 이벤트 활성 시, 확장 카테고리에 배분 생성 + 기본 카테고리 조정
  let extAlloc = {}; // 확장 카테고리별 배분 %
  if (activeMacros.size > 0) {
    // 확장 카테고리: 매크로 수혜 시 기본 카테고리에서 떼어서 배분
    const extCats = ['항공','방위산업','해운/물류','에너지(원유)','원유 인버스','클린에너지','이머징마켓','농업/식량','방산 인버스','VIX/변동성','테크 인버스','중국 인버스','채권 인버스','금/은 인버스','레버리지 ETF'];
    const parentMap = {
      '항공':0, '방위산업':0, '클린에너지':0, '이머징마켓':0, '테크 인버스':0, '레버리지 ETF':0,
      '해운/물류':3, '에너지(원유)':3, '원유 인버스':3, '농업/식량':3,
      '방산 인버스':0, 'VIX/변동성':4, '중국 인버스':0, '채권 인버스':4, '금/은 인버스':1,
    };
    // 기본 5카테고리 매크로 이벤트 기반 배분 조정 (강화)
    const catMapping = ['미국주식','금/은','암호화폐','원자재','채권/안전자산'];
    const baseAdj = [0,0,0,0,0];
    for (const [sec, val] of Object.entries(macroBonus)) {
      const idx = catMapping.indexOf(sec);
      if (idx >= 0) {
        if (val <= -25) {
          // 강한 드래그: 현재 비중의 30~50% 감소
          const reduction = Math.round(alloc[idx] * Math.min(0.5, Math.abs(val) / 70));
          baseAdj[idx] -= reduction;
          // 감소분을 다른 카테고리에 분배
          const others = [0,1,2,3,4].filter(j => j !== idx && alloc[j] > 0);
          if (others.length > 0) {
            const each = Math.round(reduction / others.length);
            others.forEach(j => { baseAdj[j] += each; });
          }
        } else if (val >= 25) {
          // 강한 부스트: 최대 15%p 증가
          const boost = Math.min(15, Math.round(val / 4));
          baseAdj[idx] += boost;
        } else {
          // 약한 보너스/페널티: 기존 로직
          baseAdj[idx] += val * 0.2;
        }
      }
    }
    alloc = alloc.map((v, i) => Math.max(0, Math.round(v + baseAdj[i])));

    // 확장 카테고리 배분 산출
    extCats.forEach(cat => {
      const bonus = macroBonus[cat] || 0;
      if (bonus > 5) {
        const pct = Math.round(Math.min(bonus * 0.2, 15)); // 최대 15%
        extAlloc[cat] = pct;
        // 부모 카테고리에서 차감
        const pi = parentMap[cat];
        if (pi !== undefined) alloc[pi] = Math.max(0, alloc[pi] - Math.round(pct * 0.6));
      }
    });
  }
  alloc = normalize(alloc);

  // Risk bar
  document.getElementById('riskScore').textContent = risk + ' / 100';
  document.getElementById('riskScore').style.color = risk<=30?'#3fb950':risk<=60?'#f0883e':'#f85149';
  document.getElementById('riskBar').style.width = risk+'%';
  const riskDescs = [
    [20, '채권·금 중심 안정형 포트폴리오'],
    [35, '안전자산 비중 높은 균형 포트폴리오'],
    [50, '주식+원자재 중심 균형 포트폴리오'],
    [65, '주식+코인 성장형 포트폴리오'],
    [80, '암호화폐 중심 공격형 포트폴리오'],
    [101,'초고위험 투기형 — 원금 손실 가능성 높음'],
  ];
  document.getElementById('riskDesc').textContent = riskDescs.find(d => risk < d[0])?.[1] || '';

  // 전체 배분 목록 구성 (기본 5 + 확장 카테고리)
  const EXT_COLORS = {'항공':'#e0af68','방위산업':'#7dcfff','해운/물류':'#73daca','에너지(원유)':'#ff9e64','원유 인버스':'#bb9af7','클린에너지':'#9ece6a','이머징마켓':'#2ac3de','농업/식량':'#c0caf5','방산 인버스':'#f7768e','VIX/변동성':'#ff757f','테크 인버스':'#c53b53','중국 인버스':'#ffc777','채권 인버스':'#82aaff','금/은 인버스':'#c3e88d','레버리지 ETF':'#fca7ea'};
  const fullAlloc = [];
  CATS.forEach((cat, i) => fullAlloc.push({name:cat.name, key:cat.key, pct:alloc[i], color:cat.color}));
  Object.entries(extAlloc).forEach(([k, pct]) => {
    if (pct > 0) fullAlloc.push({name:k, key:k, pct:pct, color:EXT_COLORS[k]||'#8b949e', isExt:true});
  });

  // Alloc bar
  const bar = document.getElementById('allocBar');
  bar.innerHTML = '';
  fullAlloc.forEach(fa => {
    if (fa.pct<=0) return;
    const d = document.createElement('div');
    d.style.cssText = `width:${fa.pct}%;background:${fa.color};display:flex;align-items:center;justify-content:center;font-size:${fa.pct>=8?'10':'8'}px;font-weight:700;color:#fff;transition:width .3s`;
    d.textContent = fa.pct>=5 ? fa.pct+'%' : '';
    d.title = fa.name+' '+fa.pct+'%';
    bar.appendChild(d);
  });

  // Alloc table
  const tbody = document.getElementById('allocTable');
  tbody.innerHTML = '';
  const riskLevel = risk<=30?'safe':risk<=60?'mid':'aggr';
  fullAlloc.forEach(fa => {
    const amt = Math.round(TOTAL*fa.pct/100);
    const amtStr = (amt/10000).toLocaleString()+'만원';
    const desc = DESC[fa.name]?.[riskLevel] || (fa.isExt ? `이벤트 수혜 — 매크로 시나리오 기반 추천` : '');
    const riskLabels = {safe:['낮음','#3fb950'], mid:['중','#f0883e'], aggr:['높음','#f85149']};
    const catRisk = (fa.key==='채권/안전자산'||fa.key==='금/은') ? riskLabels.safe : (fa.key==='암호화폐'||fa.key==='원유 인버스') ? (risk>50?riskLabels.aggr:riskLabels.mid) : fa.isExt ? riskLabels.mid : riskLabels.mid;
    const eventTag = fa.isExt ? ` <span style="color:#f0883e;font-size:9px">EVENT</span>` : '';
    const tr = document.createElement('tr');
    tr.innerHTML = `<td style="font-weight:600;color:${fa.color}">${fa.name}${eventTag}</td><td style="text-align:center">${fa.pct}%</td><td><div style="display:flex;align-items:center;gap:4px"><div style="width:${fa.pct*1.5}px;height:12px;background:${fa.color};border-radius:2px"></div></div></td><td>${amtStr}</td><td class="reason">${desc}</td><td style="color:${catRisk[1]};font-size:11px">${catRisk[0]}</td>`;
    tbody.appendChild(tr);
  });

  // Label
  const profile = risk<=20?'안정 추구':risk<=40?'균형 투자':risk<=60?'성장 투자':risk<=80?'공격 투자':'고위험 투기';
  document.getElementById('allocLabel').textContent = `— 연 ${target}% / ${months}개월 (${profile})`;

  // ── 동적 추천 종목 ──
  const container = document.getElementById('picksContainer');
  container.innerHTML = '';
  document.getElementById('picksLabel').textContent = `— 공격성 ${risk}점 기준 정렬`;

  // 모든 카테고리를 매크로 보너스 + 공격성 기반으로 동적 정렬
  const allCatKeys = Object.keys(CANDIDATES);
  const catScores = allCatKeys.map(k => {
    let baseScore = 0;
    if (risk <= 30) {
      baseScore = {'채권/안전자산':50,'금/은':40,'원자재':20,'미국주식':10,'암호화폐':-10}[k] || 0;
    } else if (risk <= 60) {
      baseScore = {'미국주식':50,'금/은':30,'암호화폐':20,'원자재':15,'채권/안전자산':5}[k] || 10;
    } else {
      baseScore = {'암호화폐':50,'미국주식':40,'원자재':20,'금/은':5,'채권/안전자산':-5}[k] || 15;
    }
    return { key: k, score: baseScore + (macroBonus[k] || 0) };
  });
  catScores.sort((a,b) => b.score - a.score);
  const catOrder = catScores.filter(c => c.score > -30).map(c => c.key);

  catOrder.forEach(catKey => {
    let items = CANDIDATES[catKey];
    if (!items || items.length === 0) return;
    // 기본 카테고리: 배분 0%이면 건너뛰기
    const catIdx = CATS.findIndex(c => c.key === catKey);
    const isExt = catIdx < 0;
    // 확장 카테고리: 매크로 배분 없으면 이벤트 비활성 시 숨기기
    if (isExt && !(extAlloc[catKey] > 0) && !(macroBonus[catKey] > 0)) return;
    if (!isExt && alloc[catIdx] <= 0) return;

    // ── 레버리지 필터: 리스크 수준에 따라 고배율 상품 제외 ──
    const maxLev = risk <= 30 ? 1 : risk <= 60 ? 2 : 9;
    items = items.filter(it => (it.lev || 1) <= maxLev);

    // ── 암호화폐 티어 필터: 낮은 리스크에서 알트코인 제외 ──
    if (catKey === '암호화폐') {
      const maxTier = risk <= 30 ? 1 : risk <= 60 ? 2 : 9;
      items = items.filter(it => (it.tier || 1) <= maxTier);
    }

    if (items.length === 0) return;

    const scored = items.map(it => ({...it, score: scoreItem(it, risk, catKey)}));
    scored.sort((a,b) => b.score - a.score);
    const top = scored.slice(0, risk > 60 ? 5 : 3);

    const catColor = isExt ? (EXT_COLORS[catKey]||'#8b949e') : CATS[catIdx].color;
    const sectorBonus = macroBonus[catKey] || 0;
    const bonusTag = sectorBonus > 0 ? ` <span style="color:#3fb950;font-size:10px;font-weight:700">▲ 이벤트 수혜 +${sectorBonus}</span>` : sectorBonus < 0 ? ` <span style="color:#f85149;font-size:10px;font-weight:700">▼ 이벤트 리스크 ${sectorBonus}</span>` : '';
    let rows = '';
    top.forEach((p,idx) => {
      const medal = idx===0 ? ' style="border-left:3px solid '+catColor+'"' : '';
      const tag = idx===0 ? `<span style="background:${catColor};color:#fff;padding:0 6px;border-radius:3px;font-size:9px;font-weight:700;margin-left:6px">TOP</span>` : '';
      // RSI 시그널 뱃지
      const rsi = p.rsi||50;
      const rsiBadge = rsi > 75 ? `<span style="color:#f85149;font-size:9px">과열</span>` : rsi < 30 ? `<span style="color:#3fb950;font-size:9px">과매도</span>` : `<span style="color:#8b949e;font-size:9px">${rsi.toFixed(0)}</span>`;
      // 추세 가속 뱃지
      const ac = p.accel||0;
      const acBadge = ac > 3 ? `<span class="tag-up" style="font-size:9px">가속↑</span>` : ac < -3 ? `<span class="tag-down" style="font-size:9px">둔화↓</span>` : `<span style="color:#8b949e;font-size:9px">${ac>0?'+':''}${ac.toFixed(1)}</span>`;
      // 낙폭
      const dd = p.dd||0;
      const ddStr = dd < -10 ? `<span style="color:#f0883e;font-size:9px">${dd.toFixed(0)}%</span>` : `<span style="color:#8b949e;font-size:9px">${dd.toFixed(0)}%</span>`;
      // 레버리지 뱃지
      const lv = p.lev || 1;
      const levBadge = lv >= 3 ? `<span style="background:#f85149;color:#fff;padding:0 4px;border-radius:2px;font-size:8px;font-weight:700;margin-left:4px">${lv}x</span>` : lv === 2 ? `<span style="background:#f0883e;color:#fff;padding:0 4px;border-radius:2px;font-size:8px;font-weight:700;margin-left:4px">${lv}x</span>` : '';
      // 암호화폐 티어 뱃지
      const tierBadge = (catKey === '암호화폐' && p.tier === 3) ? `<span style="background:#8b949e;color:#fff;padding:0 4px;border-radius:2px;font-size:8px;margin-left:4px">ALT</span>` : '';
      rows += `<tr${medal}>
<td><a href="${p.url}" target="_blank"><span class="ticker">${p.name}</span></a>${tag}${levBadge}${tierBadge}</td>
<td>${p.ticker}</td>
<td>${fmtPrice(p.price)}</td>
<td>${fmtPct(p.pct_1m)}</td>
<td>${fmtPct(p.pct_3m)}</td>
<td>${p.vol.toFixed(1)}%</td>
<td style="text-align:center">${rsiBadge}</td>
<td style="text-align:center">${acBadge}</td>
<td style="text-align:center">${ddStr}</td>
<td style="font-weight:600;color:${p.score>0?'#3fb950':'#f85149'}">${p.score.toFixed(1)}</td>
</tr>`;
    });

    const allocPct = isExt ? (extAlloc[catKey]||0) : alloc[catIdx];
    const allocAmt = Math.round(TOTAL * allocPct / 100 / 10000);
    const eventBadge = isExt && allocPct > 0 ? ' <span style="background:#f0883e;color:#fff;padding:0 5px;border-radius:3px;font-size:9px;font-weight:700">EVENT</span>' : '';
    container.innerHTML += `
<div style="margin-bottom:10px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
    <span style="font-size:13px;font-weight:600;color:${catColor}">${catKey}${eventBadge}${bonusTag}</span>
    <span style="font-size:11px;color:#8b949e">${allocPct > 0 ? `배분 ${allocPct}% (${allocAmt.toLocaleString()}만원)` : '매크로 수혜 섹터'}</span>
  </div>
  <table class="stock-table">
  <tr><th>종목</th><th>티커</th><th>현재가</th><th>1개월</th><th>3개월</th><th>변동성</th><th>RSI</th><th>추세</th><th>낙폭</th><th>적합도</th></tr>
  ${rows}
  </table>
</div>`;
  });

  // ── 액션 플랜 ──
  const actions = document.getElementById('actionTable');
  actions.innerHTML = '';
  const stockPct = alloc[0];
  const reducePct = 100 - stockPct;
  const reduceAmt = Math.round(TOTAL*reducePct/100/10000);

  let step = 1;
  if (reducePct > 0) {
    actions.innerHTML += `<tr><td style="text-align:center;font-weight:700;color:#f85149">${step}</td><td>미국주식 비중 조정</td><td class="reason">100% → ${stockPct}%로 축소. 약 ${reduceAmt.toLocaleString()}만원 매도</td></tr>`;
    step++;
  }

  // 기본 카테고리 액션
  const actionCats = ['금/은','암호화폐','원자재','채권/안전자산'];
  alloc.slice(1).forEach((pct,idx) => {
    if (pct <= 0) return;
    const catKey = actionCats[idx];
    const amt = Math.round(TOTAL*pct/100/10000);
    const items = CANDIDATES[catKey];
    let topName = '해당 ETF';
    if (items && items.length > 0) {
      const scored = items.map(it => ({...it, sc: scoreItem(it, risk, catKey)}));
      scored.sort((a,b) => b.sc - a.sc);
      topName = scored[0].name;
    }
    actions.innerHTML += `<tr><td style="text-align:center;font-weight:700;color:#3fb950">${step}</td><td>${catKey} 매수</td><td class="reason">${amt.toLocaleString()}만원 — 1순위 추천: ${topName}</td></tr>`;
    step++;
  });

  // 확장 카테고리 액션 (이벤트 기반)
  Object.entries(extAlloc).forEach(([catKey, pct]) => {
    if (pct <= 0) return;
    const amt = Math.round(TOTAL*pct/100/10000);
    const items = CANDIDATES[catKey];
    let topName = '해당 ETF';
    if (items && items.length > 0) {
      const scored = items.map(it => ({...it, sc: scoreItem(it, risk, catKey)}));
      scored.sort((a,b) => b.sc - a.sc);
      topName = scored[0].name;
    }
    actions.innerHTML += `<tr><td style="text-align:center;font-weight:700;color:#f0883e">${step}</td><td>${catKey} 매수 <span style="font-size:9px;color:#f0883e">[이벤트]</span></td><td class="reason">${amt.toLocaleString()}만원 — 1순위 추천: ${topName}</td></tr>`;
    step++;
  });
}

function setPreset(target, period) {
  currentTarget = target;
  currentPeriod = period;
  document.getElementById('targetSlider').value = target;
  document.getElementById('targetValue').textContent = target + '%';
  document.getElementById('periodSlider').value = period;
  document.getElementById('periodValue').textContent = period + '개월';
  document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`.preset-btn[data-target="${target}"]`);
  if (btn) btn.classList.add('active');
  updateAll();
}

function onTargetChange(val) {
  currentTarget = parseInt(val);
  document.getElementById('targetValue').textContent = currentTarget + '%';
  document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
  updateAll();
}

function onPeriodChange(val) {
  currentPeriod = parseInt(val);
  document.getElementById('periodValue').textContent = currentPeriod + '개월';
  document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
  updateAll();
}

function renderMacroToggles() {
  const container = document.getElementById('macroToggles');
  container.innerHTML = '';
  MACRO_EVENTS.forEach(ev => {
    const boostTags = Object.entries(ev.boost||{}).map(([s,v]) => `<span class="mc-tag boost">+${v} ${s}</span>`).join('');
    const dragTags = Object.entries(ev.drag||{}).map(([s,v]) => `<span class="mc-tag drag">${v} ${s}</span>`).join('');
    const card = document.createElement('div');
    card.className = 'macro-card';
    card.id = 'mc-' + ev.id;
    card.onclick = () => toggleMacro(ev.id);
    card.innerHTML = `<div class="mc-head"><span><span class="mc-icon">${ev.icon}</span> <span class="mc-name">${ev.name}</span></span><div class="mc-toggle"></div></div><div class="mc-desc">${ev.desc}</div><div class="mc-scenario">${ev.scenario}</div><div class="mc-tags">${boostTags}${dragTags}</div>`;
    container.appendChild(card);
  });
}

function toggleMacro(id) {
  if (activeMacros.has(id)) activeMacros.delete(id);
  else activeMacros.add(id);
  const card = document.getElementById('mc-' + id);
  if (card) card.classList.toggle('active', activeMacros.has(id));
  updateMacroSummary();
  updateAll();
}

function updateMacroSummary() {
  const box = document.getElementById('macroSummary');
  const impact = document.getElementById('macroImpact');
  if (activeMacros.size === 0) { box.style.display = 'none'; return; }
  box.style.display = 'block';
  const bonus = calcMacroBonus();
  const sorted = Object.entries(bonus).sort((a,b) => b[1] - a[1]);
  impact.innerHTML = sorted.map(([sec, val]) => {
    const c = val > 0 ? '#3fb950' : '#f85149';
    const sign = val > 0 ? '+' : '';
    return `<span style="display:inline-block;margin:2px 4px;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;color:${c};background:${val>0?'rgba(63,185,80,.1)':'rgba(248,81,73,.1)'}">${sec} ${sign}${val}</span>`;
  }).join('');
}

document.addEventListener('DOMContentLoaded', () => { renderMacroToggles(); updateAll(); });
</script>'''

    return portfolio_html + portfolio_js


def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return []


def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding='utf-8')


def build_full_html(all_days_html, date_tabs_html, portfolio_html=''):
    CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI','Malgun Gothic',sans-serif;background:#0a0e14;color:#e6edf3;line-height:1.35;font-size:13px}
.top-bar{position:sticky;top:0;z-index:100;background:rgba(13,17,23,0.96);backdrop-filter:blur(10px);border-bottom:1px solid #30363d;padding:6px 20px;display:flex;justify-content:space-between;align-items:center}
.top-bar h1{font-size:16px;color:#58a6ff}
.btn{padding:5px 12px;border-radius:6px;border:1px solid #30363d;background:#161b22;color:#c9d1d9;font-size:12px;cursor:pointer;transition:all .15s;display:inline-flex;align-items:center;gap:5px;text-decoration:none}
.btn:hover{background:#1f2937;border-color:#58a6ff;color:#58a6ff}
.btn-primary{background:#1a7f37;border-color:#1a7f37;color:#fff}
.btn-primary:hover{background:#238636}
.btn svg{width:14px;height:14px;fill:currentColor}
.date-nav{display:flex;gap:6px;padding:6px 20px;overflow-x:auto;-webkit-overflow-scrolling:touch;background:#0d1117;border-bottom:1px solid #21262d}
.date-tab{padding:3px 10px;border-radius:12px;background:#161b22;border:1px solid #30363d;color:#8b949e;font-size:11px;cursor:pointer;white-space:nowrap;transition:all .15s;text-decoration:none}
.date-tab:hover,.date-tab.active{background:#1f6feb;border-color:#1f6feb;color:#fff}
.container{max-width:1280px;margin:0 auto;padding:12px 16px}
.day-block{margin-bottom:24px;scroll-margin-top:80px}
.day-header{font-size:16px;color:#58a6ff;margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #1f6feb;display:flex;justify-content:space-between;align-items:center}
.day-header .date-label{font-size:11px;color:#8b949e}
.section{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 14px;margin-bottom:10px}
.section h2{color:#58a6ff;font-size:14px;margin-bottom:8px;padding-bottom:5px;border-bottom:1px solid #30363d}
.section h3{color:#c9d1d9;font-size:12px;margin:8px 0 5px;font-weight:600}
.market-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
@media(max-width:900px){.market-grid{grid-template-columns:repeat(2,1fr)}}
.market-card{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:8px 10px}
.market-card h4{color:#8b949e;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.market-row{display:flex;justify-content:space-between;align-items:center;padding:2px 0;border-bottom:1px solid #1c2028}
.market-row:last-child{border-bottom:none}
.market-row a{text-decoration:none;display:flex;justify-content:space-between;align-items:center;width:100%}
.market-row a:hover .market-name{color:#79c0ff}
.market-name{font-weight:600;color:#c9d1d9;font-size:11px}
.market-vals{display:flex;gap:6px;align-items:center}
.market-price{font-weight:500;color:#e6edf3;font-size:11px}
.up{color:#3fb950}.down{color:#f85149}
.tag-up{background:rgba(63,185,80,.12);color:#3fb950;padding:1px 5px;border-radius:3px;font-size:10px;font-weight:600}
.tag-down{background:rgba(248,81,73,.12);color:#f85149;padding:1px 5px;border-radius:3px;font-size:10px;font-weight:600}
.stock-table{width:100%;border-collapse:collapse}
.stock-table th{text-align:left;font-size:10px;color:#8b949e;padding:3px 6px;border-bottom:1px solid #30363d;font-weight:600}
.stock-table td{padding:3px 6px;font-size:12px;border-bottom:1px solid #1c2028}
.stock-table tr:hover{background:#131920}
.stock-table a{text-decoration:none;color:inherit}
.stock-table a:hover{color:#79c0ff}
.stock-table .ticker{font-weight:700}
.stock-table .reason{color:#8b949e;font-size:11px}
.expand-toggle{background:none;border:1px solid #30363d;color:#58a6ff;font-size:11px;padding:2px 10px;border-radius:4px;cursor:pointer;margin-top:4px}
.expand-toggle:hover{background:#161b22;border-color:#58a6ff}
.expandable{max-height:0;overflow:hidden;transition:max-height .3s ease}
.expandable.open{max-height:2000px}
.day-divider{border:none;height:1px;background:linear-gradient(90deg,transparent,#30363d,transparent);margin:16px 0}
footer{text-align:center;color:#484f58;font-size:11px;padding:16px 0;border-top:1px solid #30363d;margin-top:10px}
.scroll-top{position:fixed;bottom:16px;right:16px;width:36px;height:36px;border-radius:50%;background:#1f6feb;color:#fff;border:none;cursor:pointer;font-size:16px;display:none;align-items:center;justify-content:center;box-shadow:0 3px 8px rgba(0,0,0,.4);z-index:99}
.scroll-top.show{display:flex}
.info-note{color:#8b949e;font-size:11px;font-style:italic;padding:4px 6px}
.main-tabs{display:flex;gap:0;background:#0d1117;border-bottom:2px solid #30363d;padding:0 20px}
.main-tab{padding:8px 20px;color:#8b949e;font-size:13px;font-weight:600;cursor:pointer;border:none;background:none;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .15s}
.main-tab:hover{color:#c9d1d9}
.main-tab.active{color:#58a6ff;border-bottom-color:#58a6ff}
.page-content{display:none}
.page-content.active{display:block}
.preset-btn{padding:5px 14px;border-radius:6px;border:1px solid #30363d;background:#0d1117;color:#8b949e;font-size:12px;cursor:pointer;transition:all .15s}
.preset-btn:hover{border-color:#58a6ff;color:#58a6ff}
.preset-btn.active{background:#1f6feb;border-color:#1f6feb;color:#fff;font-weight:600}
.slider-row{display:flex;align-items:center;gap:14px;margin-bottom:10px}
.slider-label{color:#8b949e;font-size:12px;min-width:90px;flex-shrink:0}
.slider-value{font-size:20px;font-weight:700;min-width:55px;text-align:right;flex-shrink:0}
.preset-row{display:flex;gap:6px;margin-bottom:14px;overflow-x:auto;-webkit-overflow-scrolling:touch;padding-bottom:4px}
.macro-card{background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:10px 12px;cursor:pointer;transition:all .2s;user-select:none}
.macro-card:hover{border-color:#58a6ff;background:#131920}
.macro-card.active{border-color:#1f6feb;background:rgba(31,111,235,.1);box-shadow:0 0 0 1px #1f6feb}
.macro-card .mc-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.macro-card .mc-icon{font-size:18px}
.macro-card .mc-name{font-size:12px;font-weight:700;color:#c9d1d9}
.macro-card .mc-toggle{width:36px;height:18px;border-radius:9px;background:#30363d;position:relative;transition:background .2s}
.macro-card.active .mc-toggle{background:#1f6feb}
.macro-card .mc-toggle::after{content:'';position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;background:#fff;transition:transform .2s}
.macro-card.active .mc-toggle::after{transform:translateX(18px)}
.macro-card .mc-desc{font-size:10px;color:#8b949e;line-height:1.3;margin-bottom:4px}
.macro-card .mc-scenario{font-size:10px;color:#f0883e;line-height:1.3}
.macro-card .mc-tags{display:flex;flex-wrap:wrap;gap:3px;margin-top:6px}
.macro-card .mc-tag{font-size:9px;padding:1px 5px;border-radius:3px;font-weight:600}
.mc-tag.boost{background:rgba(63,185,80,.12);color:#3fb950}
.mc-tag.drag{background:rgba(248,81,73,.12);color:#f85149}

/* ── 모바일 반응형 ── */
@media(max-width:600px){
  body{font-size:12px}
  .top-bar{padding:6px 10px}
  .top-bar h1{font-size:13px}
  .date-nav{padding:4px 8px;gap:4px}
  .date-tab{font-size:10px;padding:3px 8px}
  .main-tabs{padding:0 8px;overflow-x:auto;-webkit-overflow-scrolling:touch}
  .main-tab{padding:8px 12px;font-size:12px;white-space:nowrap}
  .container{padding:8px 8px}
  .section{padding:8px 10px;margin-bottom:8px}
  .section h2{font-size:13px;margin-bottom:6px}
  .market-grid{grid-template-columns:1fr !important;gap:6px}
  .market-card{padding:6px 8px}
  .market-name{font-size:10px}
  .market-price{font-size:10px}
  .stock-table{display:block;overflow-x:auto;-webkit-overflow-scrolling:touch;white-space:nowrap}
  .stock-table th{font-size:9px;padding:3px 4px}
  .stock-table td{font-size:11px;padding:3px 4px}
  .btn{padding:4px 8px;font-size:11px}
  .macro-card{padding:8px 10px}
  .macro-card .mc-name{font-size:11px}
  .macro-card .mc-desc{font-size:9px}
  .macro-card .mc-scenario{font-size:9px}
  .macro-card .mc-tag{font-size:8px}
  .preset-btn{padding:4px 10px;font-size:11px}
  .day-header{font-size:14px}
  footer{font-size:10px;padding:12px 8px}
  .scroll-top{bottom:12px;right:12px;width:32px;height:32px;font-size:14px}
  .slider-row{gap:8px}
  .slider-label{min-width:70px;font-size:11px}
  .slider-value{font-size:16px;min-width:48px}
  .preset-btn{padding:4px 8px;font-size:10px}
  input[type="range"]{height:8px}
}
@media(max-width:420px){
  .market-grid{grid-template-columns:1fr !important}
  .top-bar h1{font-size:12px}
  .stock-table th{font-size:8px;padding:2px 3px}
  .stock-table td{font-size:10px;padding:2px 3px}
}"""

    JS = r"""
function toggleExpand(id,btn){const el=document.getElementById(id);el.classList.toggle('open');btn.textContent=el.classList.contains('open')?'- 접기':btn.getAttribute('data-label')||btn.textContent}
document.querySelectorAll('.expand-toggle').forEach(b=>b.setAttribute('data-label',b.textContent));
const dayBlocks=document.querySelectorAll('.day-block'),dateTabs=document.querySelectorAll('.date-tab');
const obs=new IntersectionObserver(e=>e.forEach(en=>{if(en.isIntersecting){dateTabs.forEach(t=>t.classList.remove('active'));const t=document.querySelector(`.date-tab[href="#${en.target.id}"]`);if(t)t.classList.add('active')}}),{rootMargin:'-80px 0px -60% 0px'});
dayBlocks.forEach(b=>obs.observe(b));
dateTabs.forEach(t=>t.addEventListener('click',e=>{e.preventDefault();document.querySelector(t.getAttribute('href'))?.scrollIntoView({behavior:'smooth'})}));
window.addEventListener('scroll',()=>document.getElementById('scrollTop').classList.toggle('show',window.scrollY>300));
function downloadExcel(){
  const wb=XLSX.utils.book_new();
  const day=document.querySelector('.day-block');
  const ind=[];
  day.querySelectorAll('.market-card').forEach(c=>{const cat=c.querySelector('h4').textContent;c.querySelectorAll('.market-row').forEach(r=>ind.push([cat,r.querySelector('.market-name')?.textContent||'',r.querySelector('.market-price')?.textContent||'',(r.querySelector('.tag-up,.tag-down'))?.textContent||'']))});
  const ws1=XLSX.utils.aoa_to_sheet([['구분','항목','현재가','변동률'],...ind]);
  ws1['!cols']=[{wch:12},{wch:14},{wch:14},{wch:10}];
  XLSX.utils.book_append_sheet(wb,ws1,'주요지표');
  let si=0;
  day.querySelectorAll('table.stock-table').forEach((tbl)=>{const ws=XLSX.utils.table_to_sheet(tbl);XLSX.utils.book_append_sheet(wb,ws,['미국급등락','한국상하한가','참고1','참고2','참고3'][si]||('Sheet'+(si+2)));si++});
  XLSX.writeFile(wb,`briefing_${new Date().toISOString().slice(0,10)}.xlsx`);
}
"""

    SVG_ICON = '<svg viewBox="0 0 16 16"><path d="M2.75 14A1.75 1.75 0 0 1 1 12.25v-2.5a.75.75 0 0 1 1.5 0v2.5c0 .138.112.25.25.25h10.5a.25.25 0 0 0 .25-.25v-2.5a.75.75 0 0 1 1.5 0v2.5A1.75 1.75 0 0 1 13.25 14ZM7.25 7.689V2a.75.75 0 0 1 1.5 0v5.689l1.97-1.969a.749.749 0 1 1 1.06 1.06l-3.25 3.25a.749.749 0 0 1-1.06 0L4.22 6.78a.749.749 0 1 1 1.06-1.06l1.97 1.969Z"/></svg>'

    TAB_JS = r"""
function switchTab(tabName){
  document.querySelectorAll('.main-tab').forEach(t=>t.classList.remove('active'));
  document.querySelector(`.main-tab[data-tab="${tabName}"]`).classList.add('active');
  document.querySelectorAll('.page-content').forEach(p=>p.style.display='none');
  document.getElementById('page-'+tabName).style.display='block';
  if(tabName==='briefing'){
    document.getElementById('dateNav').style.display='flex';
  } else {
    document.getElementById('dateNav').style.display='none';
  }
  window.scrollTo({top:0});
}
"""

    # PWA manifest (인라인 data URI로 삽입 — 별도 파일 불필요)
    PWA_META = """<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Finance">
<meta name="theme-color" content="#0a0e14">
<meta name="mobile-web-app-capable" content="yes">
<link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect fill='%230a0e14' width='100' height='100' rx='20'/><text x='50' y='62' font-size='50' text-anchor='middle' fill='%2358a6ff'>$</text></svg>">
<link rel="manifest" href="data:application/manifest+json,%7B%22name%22%3A%22Daily%20Financial%20Briefing%22%2C%22short_name%22%3A%22Finance%22%2C%22start_url%22%3A%22.%2Fdaily_briefing.html%22%2C%22display%22%3A%22standalone%22%2C%22background_color%22%3A%22%230a0e14%22%2C%22theme_color%22%3A%22%230a0e14%22%2C%22icons%22%3A%5B%7B%22src%22%3A%22data%3Aimage%2Fsvg%2Bxml%2C%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20viewBox%3D%270%200%20100%20100%27%3E%3Crect%20fill%3D%27%25230a0e14%27%20width%3D%27100%27%20height%3D%27100%27%20rx%3D%2720%27%2F%3E%3Ctext%20x%3D%2750%27%20y%3D%2762%27%20font-size%3D%2750%27%20text-anchor%3D%27middle%27%20fill%3D%2758a6ff%27%3E%24%3C%2Ftext%3E%3C%2Fsvg%3E%22%2C%22sizes%22%3A%22any%22%2C%22type%22%3A%22image%2Fsvg%2Bxml%22%7D%5D%7D">"""

    # Service Worker (캐시 + 오프라인 지원)
    SW_SCRIPT = r"""<script>
if('serviceWorker' in navigator){
  const sw=`data:text/javascript,
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(clients.claim()));
self.addEventListener('fetch',e=>{
  e.respondWith(fetch(e.request).then(r=>{
    if(r.ok){const c=r.clone();caches.open('fb-v1').then(cache=>cache.put(e.request,c))}
    return r;
  }).catch(()=>caches.match(e.request)))
});`;
  navigator.serviceWorker.register(sw,{scope:'.'}).catch(()=>{});
}
</script>"""

    return (
        '<!DOCTYPE html>\n<html lang="ko">\n<head>\n'
        '<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        + PWA_META + '\n'
        '<title>Daily Financial Briefing</title>\n'
        '<script src="https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js"></script>\n'
        '<style>' + CSS + '</style>\n</head>\n<body>\n'
        '<div class="top-bar"><h1>Daily Financial Briefing</h1>'
        '<div style="display:flex;gap:8px;align-items:center">'
        '<button class="btn btn-primary" onclick="downloadExcel()">' + SVG_ICON + ' Excel</button>'
        '</div></div>\n'
        '<div class="main-tabs">'
        '<button class="main-tab active" data-tab="briefing" onclick="switchTab(\'briefing\')">Daily Briefing</button>'
        '<button class="main-tab" data-tab="portfolio" onclick="switchTab(\'portfolio\')">Portfolio</button>'
        '</div>\n'
        '<div class="date-nav" id="dateNav">' + date_tabs_html + '</div>\n'
        '<div id="page-briefing" class="page-content active">'
        '<div class="container">\n' + all_days_html + '\n</div></div>\n'
        + portfolio_html + '\n'
        '<footer>본 보고서는 AI가 생성한 참고 자료이며, 투자 판단의 최종 책임은 본인에게 있습니다.<br>'
        'Powered by Claude Code &mdash; 실시간 시세 (yfinance)</footer>\n'
        '<button class="scroll-top" id="scrollTop" onclick="window.scrollTo({top:0,behavior:\'smooth\'})">&#8593;</button>\n'
        '<script>' + TAB_JS + JS + '</script>\n'
        + SW_SCRIPT + '\n'
        '</body>\n</html>'
    )


def main():
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    day_name = day_names[today.weekday()]

    print(f"=== Financial Briefing 생성: {today_str} ({day_name}) ===")

    print("[1/4] 시장 지표 수집...")
    market_data = fetch_market_data()

    # USD/KRW 환율 추출
    usd_krw = 1400  # fallback
    for item in market_data.get('환율', []):
        if item['name'] == 'USD/KRW':
            usd_krw = item['price']
            break

    print("[2/4] 미국 급등락 종목 탐색...")
    us_gainers, us_losers, us_mid_up, us_mid_down = fetch_us_movers()

    print("[3/4] 한국 상한가/하한가 탐색...")
    kr_upper, kr_lower, kr_big_up, kr_big_down = fetch_kr_movers()

    print("[4/4] 포트폴리오 분석...")
    holdings, candidates = fetch_portfolio_data(usd_krw)
    suggestions, allocation, avg_1m = generate_portfolio_suggestion(holdings, candidates, usd_krw)
    portfolio_html = generate_portfolio_html(holdings, candidates, suggestions, allocation, avg_1m, usd_krw)

    # 오늘 HTML 블록 생성
    today_html = generate_html(
        market_data, us_gainers, us_losers, us_mid_up, us_mid_down,
        kr_upper, kr_lower, kr_big_up, kr_big_down, today_str, day_name
    )

    # 히스토리 로드 및 업데이트
    history = load_history()
    # 같은 날짜 데이터가 있으면 교체
    history = [h for h in history if h.get('date') != today_str]
    history.insert(0, {'date': today_str, 'day': day_name, 'html': today_html})
    # 최근 30일만 유지
    history = history[:30]
    save_history(history)

    # 전체 HTML 조합
    all_days_html = ''
    date_tabs_html = ''
    for idx, h in enumerate(history):
        if idx > 0:
            all_days_html += '<hr class="day-divider">'
        all_days_html += h['html']
        active = ' active' if idx == 0 else ''
        label = f"{h['date'][5:]} ({h['day']})"
        if idx == 0:
            label += ' - 최신'
        date_tabs_html += f'<a class="date-tab{active}" href="#day-{h["date"]}">{label}</a>'

    full_html = build_full_html(all_days_html, date_tabs_html, portfolio_html)
    REPORT_FILE.write_text(full_html, encoding='utf-8')

    print(f"\n=== 완료! {REPORT_FILE} ===")
    print(f"  시장지표: {sum(len(v) for v in market_data.values())}건")
    print(f"  미국 20%+ 상승: {len(us_gainers)}건 / 하락: {len(us_losers)}건")
    print(f"  한국 상한가: {len(kr_upper)}건 / 하한가: {len(kr_lower)}건")
    print(f"  히스토리: {len(history)}일분 보관중")


if __name__ == '__main__':
    main()
