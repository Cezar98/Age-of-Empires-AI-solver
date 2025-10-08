# Constants validation log

This document captures quick sanity checks for the economy constants used by
the AoE:DE GA prototype.  The simulator runs with 10-second ticks, so train and
build times were rounded to the nearest multiple of the tick length (e.g.,
houses complete in 20s instead of 25s) to avoid partial progress artefacts.

## Scenario summaries

All scenarios were evaluated through `simulator.simulate` with hand-authored
chromosomes.

```
Scenario: all_noop
  Fitness: 578.0
  End state: villagers=3, food=200.0, wood=0.0, pop_cap=5
  TC idle seconds: 120 | Pop-block seconds: 0
  Failed actions: none

Scenario: house_before_block
  Fitness: 787.1
  End state: villagers=4, food=229.8, wood=11.3, pop_cap=10
  TC idle seconds: 90 | Pop-block seconds: 0
  Failed actions: none

Scenario: pop_blocked
  Fitness: 908.6
  End state: villagers=5, food=198.8, wood=19.8, pop_cap=5
  TC idle seconds: 60 | Pop-block seconds: 20
  Failed actions:
    - tick 9: build_house -> not enough wood
    - tick 10: train_villager -> population capped

Scenario: tc_kept_busy
  Fitness: 887.5
  End state: villagers=5, food=179.8, wood=29.7, pop_cap=5
  TC idle seconds: 60 | Pop-block seconds: 30
  Failed actions:
    - tick 5: assign_wood -> no idle villager
    - tick 8: train_villager -> town center busy
```

## Observations

- **Idle penalty feels right.** The `all_noop` case loses 120 fitness points to
  the town center idle penalty, while keeping TC busy cuts that loss in half.
- **House timing works.** In `house_before_block` a timely house lifts the pop
  cap to 10 before any training attempts are blocked, while `pop_blocked`
  demonstrates the pop-cap penalty when wood is delayed.
- **Resource saturation behaves.** The `tc_kept_busy` script banks ~30 wood and
  shows how repeated queue attempts fail if no idle villager is available.
