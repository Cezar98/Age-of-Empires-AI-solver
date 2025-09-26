from dataclasses import dataclass
from enum import Enum, auto
import random

class Action(Enum):
    NOOP   = auto()
    CREATE = auto()   # costs 50 food, +1 villager, +1 idle villager
    FOOD   = auto()   # assign one idle villager to gather food (+10/step)
    WOOD   = auto()   # assign one idle villager to gather wood (+10/step)
    HOUSE  = auto()   # costs 30 wood, +4 pop cap, (tries to “consume” one 10-gather tick)
    IDLE = auto() # make a villager idle
ACTIONS = list(Action)  # for random choice

@dataclass
class GameState:
    n_villagers: int = 0
    idle_villagers: int = 0
    population_cap: int = 4
    dt: int = 10  # seconds per tick (kept for readability)
    food: int = 50
    wood: int = 0
    food_counter: int = 0   # per-tick income (10 food / tick per assigned worker)
    wood_counter: int = 0   # per-tick income (10 wood / tick per assigned worker)

def can_do(state: GameState, action: Action) -> bool:
    if action == Action.NOOP:
        return True
    if action == Action.CREATE:
        # Need 50 food and room for a new villager
        return state.food >= 50 and state.n_villagers < state.population_cap
    if action in (Action.FOOD, Action.WOOD):
        # Need an idle villager to assign
        return state.idle_villagers > 0
    if action == Action.HOUSE:
        # Need 30 wood
        return state.wood >= 30
    if action == Action.IDLE:
        return state.food_counter + state.wood_counter > 0 and state.n_villagers > state.idle_villagers

    return False

def apply_effect(state: GameState, action: Action) -> GameState:
    # Work on a copy so the function is pure (easy to test)
    s = GameState(**vars(state))

    if action == Action.CREATE:
        s.food -= 50
        s.n_villagers += 1
        s.idle_villagers += 1

    elif action == Action.FOOD:
        s.food_counter += 10
        s.idle_villagers -= 1

    elif action == Action.WOOD:
        s.wood_counter += 10
        s.idle_villagers -= 1

    elif action == Action.HOUSE:
        s.population_cap += 4
        s.wood -= 30
        # Your original logic seemed to “free” a worker upon house completion
        s.idle_villagers += 1
        # Consume one 10-resource “tick” worth from counters if available
        if s.wood_counter > 0:
            s.wood_counter = max(0, s.wood_counter - 10)
        elif s.food_counter > 0:
            s.food_counter = max(0, s.food_counter - 10)
    elif action == Action.IDLE:
        s.idle_villagers += 1
        if s.food_counter > 0:
            s.food_counter = s.food_counter - 10
        else:
            s.wood_counter = s.wood_counter - 10
    # NOOP does nothing

    return s

def tick_income(state: GameState) -> GameState:
    """Apply per-tick passive income from counters."""
    s = GameState(**vars(state))
    s.food += s.food_counter
    s.wood += s.wood_counter
    return s

def choose_valid_action(state: GameState) -> Action:
    # Always possible to do NOOP, so loop will terminate
    while True:
        a = random.choice(ACTIONS)
        if can_do(state, a):
            return a

def simulate(seed: int | None = None, total_time: int = 200, dt: int = 10):
    if seed is not None:
        random.seed(seed)

    state = GameState(dt=dt)
    fitness = lambda s: s.n_villagers  # same fitness you used

    for t in range(0, total_time, state.dt):
        # 1) income
        state = tick_income(state)

        # 2) choose & apply action
        action = choose_valid_action(state)
        state = apply_effect(state, action)

        # 3) report
        print(
            f"[t={t:>3}s] Do: {action.name:6} | "
            f"Villagers: {state.n_villagers:2d} (idle {state.idle_villagers:2d}) | "
            f"Food {state.food:3d} (+{state.food_counter}) | "
            f"Wood {state.wood:3d} (+{state.wood_counter}) | "
            f"PopCap {state.population_cap:2d} | "
            f"Fitness {fitness(state)}"
        )

if __name__ == "__main__":
    simulate(seed=42, total_time=200, dt=10)
