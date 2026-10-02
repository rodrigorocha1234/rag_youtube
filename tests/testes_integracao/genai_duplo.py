from collections.abc import Mapping, Sequence


class GenaiDuplo:
    def __init__(self) -> None:
        self.chamadas = 0

    def evaluate(self, *, data: Sequence[Mapping[str, object]], scorers: Sequence[object]) -> object:
        self.chamadas += 1
        return {"linhas": len(data), "scorers": len(scorers)}
