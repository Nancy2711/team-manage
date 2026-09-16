import pytest

from app.utils.token_parser import TokenParser

parser = TokenParser()


def test_extract_single_email():
    """能提取出单个邮箱"""
    assert parser.extract_emails("test@example.com") == ["test@example.com"]


def test_extract_email_from_text():
    """能从一段文字中间把邮箱揪出来"""
    assert parser.extract_emails("联系我 test@example.com 谢谢") == ["test@example.com"]


def test_extract_multiple_emails():
    """多个邮箱都能提取，顺序不保证所以排序后比较"""
    result = parser.extract_emails("a@x.com 或 b@y.org")
    assert sorted(result) == ["a@x.com", "b@y.org"]


def test_duplicate_emails_are_deduplicated():
    """同一个邮箱出现两次，只返回一个"""
    result = parser.extract_emails("test@example.com 和 test@example.com")
    assert len(result) == 1


def test_uppercase_email_is_kept_as_is():
    """大写邮箱也能识别，且保持原样输出"""
    assert parser.extract_emails("TEST@EXAMPLE.COM") == ["TEST@EXAMPLE.COM"]


@pytest.mark.parametrize("text", [
    "",
    "这段文字里没有邮箱",
    "@example.com",
    "test@",
])
def test_invalid_input_returns_empty(text):
    """各种不完整或没有邮箱的输入，都应该返回空列表"""
    assert parser.extract_emails(text) == []


@pytest.mark.parametrize("text, expected", [
    ("a@b.c", []),                  # 顶级域名只有 1 位 → 不匹配
    ("a@b.co", ["a@b.co"]),         # 顶级域名 2 位 → 匹配（边界）
])
def test_tld_length_boundary(text, expected):
    """顶级域名长度的边界：1 位不认，2 位才认"""
    assert parser.extract_emails(text) == expected