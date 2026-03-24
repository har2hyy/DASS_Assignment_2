# White Box Testing Report - MoneyPoly

## 1. Scope and Objective

This report documents Part 1 (White Box Testing) for the MoneyPoly game implementation.

Target codebase:
- `whitebox/code/moneypoly/main.py`
- `whitebox/code/moneypoly/moneypoly/*.py`

Deliverables covered in this report:
1. Control Flow Graph (CFG)
2. Iterative code-quality analysis using pylint
3. White-box test-suite design and implementation
4. Bug discovery and fixes with commit traceability
5. Final verification (tests, coverage, lint)

---

## 2. Control Flow Graph (CFG)

CFG artifacts generated:
- `whitebox/diagrams/control_flow_graph.dot`
- `whitebox/diagrams/control_flow_graph.png`
- `whitebox/diagrams/control_flow_graph.svg`
- `whitebox/diagrams/control_flow_graph.pdf`

Rendering commands used:

```bash
cd whitebox/diagrams
dot -Tpng control_flow_graph.dot -o control_flow_graph.png
dot -Tsvg control_flow_graph.dot -o control_flow_graph.svg
dot -Tpdf control_flow_graph.dot -o control_flow_graph.pdf
```

CFG design notes:
- Uses block-level granularity for readability.
- Uses function clusters and typed nodes (`ENTRY`, `COND`, `PROC`, `CALL`, `EXIT`).
- Captures major loops and branch paths in:
  - `main()` / `get_player_names()`
  - `Game.run()` / `Game.play_turn()`
  - tile resolution in `Game._move_and_resolve()`
  - property/jail/card subsystems
  - bankruptcy/winner logic
- No visual bug highlighting was used, per constraint.

---

## 3. Pylint Iterations

### 3.1 Baseline and Progress

Initial lint pass during whitebox work identified style and structural warnings (docstrings, line length, bare `except`, unused imports, and complexity warnings).

Final pylint command:

```bash
cd whitebox/code/moneypoly
/home/harshyy/Desktop/DASS/Ass2/.venv/bin/python -m pylint moneypoly main.py --output-format=text
```

Final pylint score:
- **9.91 / 10**

### 3.2 Iteration Commits

- `598b6a3` Iteration 1: Fix pylint warnings for imports, input handling, and style
- `0391307` Iteration 2: Add missing cards and config modules to whitebox code
- `1e5e221` Iteration 4: Improve docstrings and cleanup lint warnings in core modules
- `ca0e575` Iteration 5: Reformat card tables to resolve line-length pylint issues

### 3.3 Remaining Lint Warnings (Final)

The remaining warnings are primarily complexity/design thresholds:
- `too-many-instance-attributes` in `Game`, `Player`, `Property`
- `too-many-arguments`/`too-many-positional-arguments` in `Property.__init__`
- `too-many-branches` in `Game._apply_card`

These are acceptable for this assignment submission because:
- They represent domain modeling complexity, not functional defects.
- Refactoring them aggressively risks behavior regressions.

---

## 4. White-Box Test Design and Coverage

Primary test file:
- `whitebox/tests/test_whitebox.py`

Test strategy:
1. Branch coverage for turn flow, jail flow, tile dispatch, and card actions.
2. Boundary tests for money and ownership logic.
3. Bug-directed tests for all critical known defects.
4. State-transition tests (mortgage/unmortgage, bankruptcy, menu paths, auction logic).

Final test command:

```bash
cd whitebox/code/moneypoly
/home/harshyy/Desktop/DASS/Ass2/.venv/bin/python -m pytest ../../tests/test_whitebox.py --cov=moneypoly --cov-report=term-missing -q
```

Final test result:
- **61 passed**

Final coverage summary:
- **Total line coverage: 97%**

Module-wise final coverage:
- `moneypoly/bank.py`: 91%
- `moneypoly/board.py`: 92%
- `moneypoly/cards.py`: 100%
- `moneypoly/config.py`: 100%
- `moneypoly/dice.py`: 96%
- `moneypoly/game.py`: 97%
- `moneypoly/player.py`: 100%
- `moneypoly/property.py`: 95%
- `moneypoly/ui.py`: 95%

Coverage goal status:
- Target >90% achieved.

---

## 5. Bugs Identified and Fixed

### 5.1 Planned 7 Bugs

1. Dice range bug (`randint(1, 5)` instead of `randint(1, 6)`)
	- Fix commit: `cf0d7f3`

2. GO salary only on landing, not passing
	- Fix commit: `6affffe`

3. `net_worth()` ignoring property values
	- Fix commit: `022f67b`

4. `PropertyGroup.all_owned_by()` using `any()` instead of `all()`
	- Fix commit: `93230ac`

5. `buy_property()` rejects exact-balance purchases (`<=`)
	- Fix commit: `3524afb`

6. `pay_rent()` did not transfer rent to owner
	- Fix commit: `063035e`

7. `find_winner()` using `min()` instead of `max()`
	- Fix commit: `ab7058f`

### 5.2 Additional Real Bug Found During Iteration

8. Failed unmortgage attempt cleared mortgage state due to early mutation order
	- Fix: validate affordability before changing mortgage status
	- Fix commit: `b9fb335`

---

## 6. Verification Evidence

### 6.1 Functional Verification

- All whitebox tests pass (`61/61`).
- All bug-target tests pass after fixes.
- No regressions observed in subsequent iterations.

### 6.2 Quality Verification

- Final pylint score: **9.91/10**
- Major style issues reduced through iterative cleanup.

### 6.3 CFG Verification

- DOT source rendered successfully to PNG/SVG/PDF using Graphviz.
- CFG captures core game-loop and decision points used for test planning.

---

## 7. Commit Timeline (Whitebox Part)

- `8e971dd` Add control flow graph for MoneyPoly game
- `a296564` Add comprehensive white box test suite
- `cf0d7f3` Error 1: Fix dice to roll 1-6 instead of 1-5
- `6affffe` Error 2: Award GO_SALARY when passing Go, not just landing on it
- `022f67b` Error 3: Include property values in net_worth calculation
- `93230ac` Error 4: Fix all_owned_by to use all() instead of any()
- `3524afb` Error 5: Allow buying property with exact balance (use < not <=)
- `063035e` Error 6: Transfer rent payment to property owner
- `ab7058f` Error 7: Use max() instead of min() to find winner
- `598b6a3` Iteration 1: Fix pylint warnings for imports, input handling, and style
- `0391307` Iteration 2: Add missing cards and config modules to whitebox code
- `b9fb335` Error 8: Prevent failed unmortgage from clearing mortgage state
- `ffd8928` Iteration 3: Expand whitebox tests to achieve high branch and path coverage
- `1e5e221` Iteration 4: Improve docstrings and cleanup lint warnings in core modules
- `ca0e575` Iteration 5: Reformat card tables to resolve line-length pylint issues

---

## 8. Final Outcome

All required whitebox objectives are satisfied:

1. CFG created and rendered.
2. Pylint-driven quality improvement completed with high final score.
3. Comprehensive whitebox suite implemented.
4. All planned critical bugs fixed and verified.
5. Additional bug discovered during iteration and fixed.
6. Final tests pass with very high coverage.

Final measurable status:
- Tests: **61 passed**
- Coverage: **97% total**
- Pylint: **9.91/10**

