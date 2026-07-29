from tool import validate_finance_content

def run_tests():
    print("--- Running Smoke Tests for validate_finance_content ---")

    # Case 1: Draft Hợp Lệ (Valid)
    valid_draft = """
    Báo cáo thị trường Bitcoin tính đến ngày 25/10/2024.
    Giá BTC hiện tại giao dịch ở mức $67,000 USD, tăng 3.5% trong 24h qua.
    Theo dữ liệu từ CoinGecko (https://coingecko.com), khối lượng giao dịch đạt 30 tỷ USD.
    Lưu ý: Báo cáo này chỉ mang tính chất thông tin, không phải là lời khuyên đầu tư.
    """
    res1 = validate_finance_content(valid_draft)
    print("\n[Test 1 - Valid Draft]")
    print(f"Pass: {res1['pass']} | Score: {res1['score']}")
    print(f"Warnings: {res1['warnings']}")
    assert res1['pass'] is True, "Test 1 Failed!"

    # Case 2: Draft Lỗi (Invalid - Khuyên mua xúi giục, thiếu disclaimer, thiếu nguồn)
    invalid_draft = "Khuyên mua BTC gấp, chắc chắn x5 tài khoản trong tháng này!"
    res2 = validate_finance_content(invalid_draft)
    print("\n[Test 2 - Invalid Draft]")
    print(f"Pass: {res2['pass']} | Score: {res2['score']}")
    print(f"Warnings: {res2['warnings']}")
    assert res2['pass'] is False, "Test 2 Failed!"

    print("\n✅ ALL SMOKE TESTS PASSED SUCCESSFULY!")

if __name__ == "__main__":
    run_tests()