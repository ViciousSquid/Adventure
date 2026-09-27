from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Iterable

TERM = re.compile(
    r"(?P<sign>[+-]?)\s*(?:(?P<count>\d+)d(?P<size>\d+)|(?P<number>\d+))"
)


@dataclass(frozen=True, slots=True)
class DiceResult:
    expression: str
    individual_rolls: tuple[int, ...]
    modifier: int
    total: int
    target: int | None = None
    success: bool | None = None

    @property
    def roll_details(self) -> tuple[int, ...]:
        return self.individual_rolls

    def to_dict(self) -> dict:
        return {
            "expression": self.expression,
            "individual_rolls": list(self.individual_rolls),
            "modifier": self.modifier,
            "total": self.total,
            "target": self.target,
            "success": self.success,
            "dice_notation": self.expression,
            "roll_details": list(self.individual_rolls),
            "roll_result": self.total,
        }


class DiceEngine:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def roll(self, expression: str, target: int | None = None) -> DiceResult:
        terms = list(self._parse(expression))
        if not terms:
            raise ValueError(f"Invalid dice expression: {expression!r}")

        rolls: list[int] = []
        modifier = 0
        total = 0

        for sign, count, size, number in terms:
            direction = -1 if sign == "-" else 1
            if count is not None:
                component = [self.rng.randint(1, size) for _ in range(count)]
                rolls.extend(component)
                total += direction * sum(component)
            else:
                modifier += direction * number
                total += direction * number

        return DiceResult(
            expression=expression,
            individual_rolls=tuple(rolls),
            modifier=modifier,
            total=total,
            target=target,
            success=None if target is None else total >= target,
        )

    @staticmethod
    def _parse(expression: str) -> Iterable[tuple[str, int | None, int | None, int | None]]:
        position = 0
        while position < len(expression):
            match = TERM.match(expression, position)
            if not match:
                if expression[position].isspace():
                    position += 1
                    continue
                raise ValueError(
                    f"Invalid dice expression component near {expression[position:]!r}"
                )
            sign = match.group("sign")
            if match.group("count") is not None:
                yield sign, int(match.group("count")), int(match.group("size")), None
            else:
                yield sign, None, None, int(match.group("number"))
            position = match.end()
