"""Deterministic economy simulator used for GA experiments.

The simulator consumes a chromosome – a sequence of integer encoded actions –
and progresses the game state in discrete ticks.  Each tick is worth
``constants["tick_seconds"]`` seconds of in-game time.  The function returns a
fitness score together with a per-tick trace that can be used to debug build
orders or to validate constant choices.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:  # pragma: no cover - optional dependency
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fallback for execution env
    yaml = None


DEFAULT_CONSTANTS_PATH = Path("constants.yaml")


@dataclass
class GameConstants:
    tick_seconds: float
    gather_rates: dict[str, float]
    actions: dict[str, dict[str, float | int]]
    initial_state: dict[str, float | int]
    penalties: dict[str, float]
    fitness_weights: dict[str, float]

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "GameConstants":
        required_keys = {
            "tick_seconds",
            "gather_rates",
            "actions",
            "initial_state",
            "penalties",
            "fitness_weights",
        }
        missing = required_keys - data.keys()
        if missing:
            raise KeyError(f"Missing required constant entries: {sorted(missing)}")
        return cls(
            tick_seconds=float(data["tick_seconds"]),
            gather_rates={k: float(v) for k, v in data["gather_rates"].items()},
            actions={k: dict(v) for k, v in data["actions"].items()},
            initial_state={k: float(v) for k, v in data["initial_state"].items()},
            penalties={k: float(v) for k, v in data["penalties"].items()},
            fitness_weights={k: float(v) for k, v in data["fitness_weights"].items()},
        )


@dataclass
class GameState:
    time: float
    villagers: int
    idle_villagers: int
    food_workers: int
    wood_workers: int
    population_cap: int
    food: float
    wood: float
    train_progress: float | None = None
    house_progress: float | None = None
    tc_idle_time: float = 0.0
    pop_block_time: float = 0.0
    events: list[str] = field(default_factory=list)

    @classmethod
    def from_constants(cls, constants: GameConstants) -> "GameState":
        initial = constants.initial_state
        villagers = int(initial.get("villagers", 0))
        idle = int(initial.get("idle_villagers", villagers))
        food = float(initial.get("food", 0.0))
        wood = float(initial.get("wood", 0.0))
        pop_cap = int(initial.get("population_cap", max(villagers, 4)))
        return cls(
            time=0.0,
            villagers=villagers,
            idle_villagers=idle,
            food_workers=int(initial.get("food_workers", 0)),
            wood_workers=int(initial.get("wood_workers", 0)),
            population_cap=pop_cap,
            food=food,
            wood=wood,
        )


def _simple_yaml_load(text: str) -> dict[str, Any]:
    stack: list[tuple[int, dict[str, Any]]] = [(-1, {})]

    def convert(value: str) -> Any:
        value = value.strip()
        if value == "":
            return {}
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue
        indent = len(line) - len(line.lstrip())
        key, _, value = line.lstrip().partition(":")
        value = value.strip()

        while indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        parsed = convert(value)
        parent[key] = parsed if parsed != {} else {}
        if parsed == {}:
            stack.append((indent, parent[key]))

    return stack[0][1]


def load_constants(path: Path | str = DEFAULT_CONSTANTS_PATH) -> GameConstants:
    text = Path(path).read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
    else:
        data = _simple_yaml_load(text)
    return GameConstants.from_mapping(data)


def apply_action(state: GameState, action: str, target: str | None, constants: GameConstants) -> tuple[bool, str]:
    """Apply a gene action to the state.

    Returns ``(success, reason)`` where ``reason`` contains a short diagnostic
    message when an action fails (useful when validating hand-authored
    chromosomes).
    """

    state.events.clear()
    action_data = constants.actions

    match action:
        case "noop":
            return True, ""
        case "train_villager":
            data = action_data.get("train_villager", {})
            food_cost = float(data.get("food_cost", 0))
            train_time = float(data.get("train_time", 0))
            if state.train_progress is not None:
                return False, "town center busy"
            if state.food < food_cost:
                return False, "not enough food"
            if state.villagers >= state.population_cap:
                return False, "population capped"
            state.food -= food_cost
            state.train_progress = train_time
            return True, "queued villager"
        case "assign_food":
            if state.idle_villagers <= 0:
                return False, "no idle villager"
            state.idle_villagers -= 1
            state.food_workers += 1
            return True, "assigned to food"
        case "assign_wood":
            if state.idle_villagers <= 0:
                return False, "no idle villager"
            state.idle_villagers -= 1
            state.wood_workers += 1
            return True, "assigned to wood"
        case "idle_one":
            pool = target or "food"
            if pool == "wood" and state.wood_workers > 0:
                state.wood_workers -= 1
                state.idle_villagers += 1
                return True, "wood worker idled"
            if state.food_workers > 0:
                state.food_workers -= 1
                state.idle_villagers += 1
                return True, "food worker idled"
            return False, "no worker on target resource"
        case "build_house":
            data = action_data.get("build_house", {})
            wood_cost = float(data.get("wood_cost", 0))
            build_time = float(data.get("build_time", 0))
            pop_increase = int(data.get("pop_increase", 0))
            if state.house_progress is not None:
                return False, "another house in progress"
            if state.idle_villagers <= 0:
                return False, "no idle villager"
            if state.wood < wood_cost:
                return False, "not enough wood"
            state.wood -= wood_cost
            state.idle_villagers -= 1
            state.house_progress = build_time
            state.events.append(f"house(+{pop_increase}) queued")
            return True, "house queued"
        case _:
            return False, f"unknown action '{action}'"


def progress_builds(state: GameState, constants: GameConstants) -> None:
    """Advance unit training and building timers by one tick."""

    dt = constants.tick_seconds
    action_data = constants.actions

    # Villager training
    if state.train_progress is not None:
        state.train_progress -= dt
        if state.train_progress <= 0:
            state.train_progress = None
            state.villagers += 1
            state.idle_villagers += 1
            state.events.append("villager trained")
    else:
        state.tc_idle_time += dt

    # House construction
    if state.house_progress is not None:
        state.house_progress -= dt
        if state.house_progress <= 0:
            state.house_progress = None
            pop_increase = int(action_data.get("build_house", {}).get("pop_increase", 0))
            state.population_cap += pop_increase
            state.idle_villagers += 1
            state.events.append("house completed")

    if state.villagers >= state.population_cap:
        state.pop_block_time += dt


def gather_resources(state: GameState, constants: GameConstants) -> dict[str, float]:
    dt = constants.tick_seconds
    food_income = state.food_workers * constants.gather_rates.get("food", 0.0) * dt
    wood_income = state.wood_workers * constants.gather_rates.get("wood", 0.0) * dt
    state.food += food_income
    state.wood += wood_income
    return {"food": food_income, "wood": wood_income}


ACTION_LOOKUP: dict[int, tuple[str, str | None]] = {
    0: ("noop", None),
    1: ("train_villager", None),
    2: ("assign_food", None),
    3: ("assign_wood", None),
    4: ("idle_one", "food"),
    5: ("idle_one", "wood"),
    6: ("build_house", None),
}


def simulate(
    chromosome: Iterable[int],
    *,
    constants_path: Path | str = DEFAULT_CONSTANTS_PATH,
) -> tuple[float, list[dict[str, Any]]]:
    """Run the simulator for a chromosome.

    Args:
        chromosome: Iterable of integer genes describing the action to execute
            on each tick.  Values are looked up in :data:`ACTION_LOOKUP` which
            acts as an enum mapping integers to action/target pairs.
        constants_path: Path to the YAML file with balance values.

    Returns:
        A tuple ``(fitness, trace)`` where ``trace`` contains a per-tick log of
        the simulated state.
    """

    constants = load_constants(constants_path)
    state = GameState.from_constants(constants)
    trace: list[dict[str, Any]] = []

    for tick, gene in enumerate(chromosome):
        try:
            gene_action, target = ACTION_LOOKUP[int(gene)]
        except (ValueError, KeyError) as exc:  # pragma: no cover - defensive
            raise ValueError(f"unknown action index '{gene}'") from exc

        income = gather_resources(state, constants)
        progress_builds(state, constants)
        success, reason = apply_action(state, gene_action, target, constants)

        trace.append(
            {
                "tick": tick,
                "time": state.time,
                "action": gene_action,
                "success": success,
                "reason": reason,
                "food": round(state.food, 2),
                "wood": round(state.wood, 2),
                "villagers": state.villagers,
                "idle": state.idle_villagers,
                "food_workers": state.food_workers,
                "wood_workers": state.wood_workers,
                "population_cap": state.population_cap,
                "income": {k: round(v, 2) for k, v in income.items()},
                "events": list(state.events),
            }
        )

        state.time += constants.tick_seconds

    weights = constants.fitness_weights
    penalties = constants.penalties

    fitness = (
        weights.get("villagers", 0.0) * state.villagers
        + weights.get("food", 0.0) * state.food
        + weights.get("wood", 0.0) * state.wood
        - penalties.get("tc_idle_per_sec", 0.0) * state.tc_idle_time
        - penalties.get("pop_block_per_sec", 0.0) * state.pop_block_time
    )

    trace.append(
        {
            "tick": len(trace),
            "time": state.time,
            "summary": {
                "villagers": state.villagers,
                "food": round(state.food, 2),
                "wood": round(state.wood, 2),
                "population_cap": state.population_cap,
                "tc_idle_time": state.tc_idle_time,
                "pop_block_time": state.pop_block_time,
            },
        }
    )

    return fitness, trace


__all__ = ["simulate", "load_constants", "GameConstants", "GameState"]

