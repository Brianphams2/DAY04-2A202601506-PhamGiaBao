import re
from typing import Dict, Any, List

# Danh sách nguồn uy tín & nguồn MXH
HIGH_QUALITY_DOMAINS = [
    "reuters.com", "bloomberg.com", "ft.com", "sec.gov", "coingecko.com",
    "alphavantage.co", "wsj.com", "investopedia.com", "vietstock.vn", "cafef.vn"
]
SOCIAL_DOMAINS = ["twitter.com", "x.com", "reddit.com", "facebook.com", "tiktok.com"]

# Từ khóa khuyến nghị tài chính
ADVICE_KEYWORDS = [
    "nên mua ngay", "khuyên mua", "cam kết lợi nhuận", "x5 tài khoản",
    "all in", "mức giá phải bán", "buy now", "guaranteed return", "target price"
]

def validate_finance_content(draft_text: str, min_words: int = 30) -> Dict[str, Any]:
    """
    Kiểm tra một bản nháp phân tích tài chính trước khi xuất bản.
    """
    checks = {}
    warnings: List[str] = []
    
    if not draft_text or not isinstance(draft_text, str):
        return {
            "pass": False,
            "score": 0.0,
            "checks": {},
            "warnings": ["INVALID_INPUT: Draft text is empty or not a string."]
        }

    # 1. Kiểm tra độ dài (Length check)
    words = draft_text.split()
    word_count = len(words)
    checks["length_check"] = word_count >= min_words
    if not checks["length_check"]:
        warnings.append(f"WORD_COUNT_LOW: Draft length ({word_count} words) is below minimum required ({min_words} words).")

    # 2. Trích dẫn & Nguồn (Citation coverage)
    urls = re.findall(r'https?://[^\s]+', draft_text)
    citation_brackets = re.findall(r'\[\d+\]|\[source:?.*?\]', draft_text, re.IGNORECASE)
    has_citations = len(urls) > 0 or len(citation_brackets) > 0
    checks["citation_coverage"] = has_citations
    if not has_citations:
        warnings.append("MISSING_CITATIONS: No clear links or reference citations found.")

    # 3 & 4. Chất lượng & Nguồn chính thống (Source Quality & Official Source)
    has_high_quality = any(domain in draft_text.lower() for domain in HIGH_QUALITY_DOMAINS)
    has_social_only = any(domain in draft_text.lower() for domain in SOCIAL_DOMAINS) and not has_high_quality
    
    checks["has_quality_sources"] = has_high_quality or not has_citations
    checks["official_source_check"] = not has_social_only
    
    if has_social_only:
        warnings.append("UNRELIABLE_SOURCES: Content relies solely on social media sources without official data verification.")

    # 5. Đơn vị tiền tệ & số liệu (Currency & Unit check)
    # Tìm các con số độc lập không có ký hiệu đi kèm
    currency_pattern = re.compile(r'(\$|USD|VND|EUR|%|tỷ|triệu|billion|trillion)\s*\d+|\d+\s*(\$|USD|VND|EUR|%|tỷ|triệu|billion|trillion)', re.IGNORECASE)
    has_currency_or_units = bool(currency_pattern.search(draft_text))
    checks["currency_and_units"] = has_currency_or_units
    if not has_currency_or_units:
        warnings.append("MISSING_UNITS: Financial numbers appear to lack explicit currency or percentage units.")

    # 6. Thời điểm dữ liệu (As of Date check)
    date_pattern = re.compile(
        r'(as of|tính đến|ngày|tháng|quý|Q[1-4]|202[0-9])', re.IGNORECASE
    )
    has_as_of_date = bool(date_pattern.search(draft_text))
    checks["as_of_date_present"] = has_as_of_date
    if not has_as_of_date:
        warnings.append("MISSING_DATE_CONTEXT: Draft lacks data freshness timestamp or 'as of' date context.")

    # 7. Cảnh báo khuyến nghị mua bán (Financial Advice Warning)
    found_advice_terms = [kw for kw in ADVICE_KEYWORDS if kw in draft_text.lower()]
    has_disclaimer = "disclaimer" in draft_text.lower() or "không phải là lời khuyên" in draft_text.lower()
    
    if found_advice_terms and not has_disclaimer:
        checks["financial_advice_safety"] = False
        warnings.append(f"UNSAFE_ADVICE_LANGUAGE: Draft contains direct buy/sell phrases ({', '.join(found_advice_terms)}) without a legal disclaimer.")
    else:
        checks["financial_advice_safety"] = True

    # --- Tính điểm & Kết luận ---
    passed_checks_count = sum(1 for v in checks.values() if v is True)
    total_checks = len(checks)
    score = round((passed_checks_count / total_checks) * 10, 1) if total_checks > 0 else 0.0

    # Tiêu chí Pass: Không dính vi phạm nghiêm trọng (advice safety & official source) và điểm >= 7.0
    is_passed = score >= 7.0 and checks.get("financial_advice_safety", False) and checks.get("official_source_check", False)

    return {
        "pass": is_passed,
        "score": score,
        "checks": checks,
        "warnings": warnings
    }