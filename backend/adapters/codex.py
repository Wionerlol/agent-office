from backend.adapters.generic import GenericProcessAdapter


class CodexAdapter(GenericProcessAdapter):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(command_names={"codex"}, provider="codex", **kwargs)


class ClaudeAdapter(GenericProcessAdapter):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(command_names={"claude"}, provider="claude", **kwargs)


class OpenCodeAdapter(GenericProcessAdapter):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(command_names={"opencode"}, provider="opencode", **kwargs)
