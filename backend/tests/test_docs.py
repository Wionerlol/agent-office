from html.parser import HTMLParser
from pathlib import Path


class GuideParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.anchors: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if identifier := attributes.get("id"):
            self.ids.add(identifier)
        if tag == "a" and (href := attributes.get("href")) and href.startswith("#"):
            self.anchors.add(href[1:])


def test_html_guide_has_valid_internal_navigation_and_required_commands() -> None:
    guide = Path(__file__).parents[2] / "docs" / "agent-office-user-guide.html"
    content = guide.read_text(encoding="utf-8")
    parser = GuideParser()
    parser.feed(content)

    assert parser.anchors <= parser.ids
    assert "<title>Agent Office 使用手册</title>" in content
    for command in ["uv sync", "uv run agent-office", "uv run office-run", "npm run build"]:
        assert command in content
