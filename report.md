# MoneyPoly White-Box Testing Report

This report outlines the comprehensive white-box testing performed on the MoneyPoly board game implementation, following the assignment specification. A total of 65 test cases were developed using `pytest`. The tests have been strictly separated into two distinct sections: **Active Code** (routines genuinely invoked during the game loop) and **Dead Code** (routines entirely unreachable during gameplay).

A total of 13 functional bugs were discovered during the testing of the active code, and 2 additional bugs were found in the dead code. These are detailed in the Bug Report sections at the end of this document.

---

# PART I: ACTIVE CODE TESTS

These tests target the core, reachable game loops and object state mechanisms.

## 1. Bank
| Test Case Group | Scenario | Expected Output | Justification |
| --- | --- | --- | --- |
| **Initialization** | Create a `Bank` instance | Balance matches `BANK_STARTING_FUNDS` | Verifies baseline internal state accuracy. |
| **Positive Collection** | Bank collects a positive cash amount | Internal funds strictly increase | Validates normal addition rules. |
| **Negative Collection** | Bank collects a negative amount | Silently ignored (balance unchanged) | Edge case explicitly defined by docstrings. |
| **Standard Payouts** | Bank pays out positive amount | Balance reduces, returns payout | Tests normal subtraction and outbound flow. |
| **Insufficient Overdraft** | Bank pays out > available funds | Raises `ValueError` | Verifies failure mode is strictly enforced. |

## 2. Player
| Test Case Group | Scenario | Expected Output | Justification |
| --- | --- | --- | --- |
| **Initialization** | Create `Player` with defaults | Balance = `1500`, Position = `0` | Base object generation state. |
| **Money Constraints**| `add_money(-10)`/`deduct(-10)` | Raises `ValueError` | Checks negative boundaries. |
| **Passing GO Reward**| Player moves from `39` to `2` | Collects `GO_SALARY` | Validates board traversal reward boundary. |
| **Direct Jail Entry**| Execute `go_to_jail()` | Position locked to `10`, `in_jail` = true | Explicit state alteration overriding standard logic. |

## 3. Properties and Board
| Test Case Group | Scenario | Expected Output | Justification |
| --- | --- | --- | --- |
| **Rent Logic (Monopoly)**| Player owns ALL group items | Rent multiplied by `2` | Validates synergistic business rule. |
| **Group Partial Ownership**| Player owns 1 of 2 properties | Rent remains `1x` | Ensures monopolies aren't prematurely triggered. |
| **Tile Resolution** | Requesting indices `0-39` | Distinct tile types correctly fetched | Ensures valid representation mapped against constants. |
| **Railroad Properties** | Get property at railroad positions (5,15,25,35) | Should return valid `Property` objects | Verifies railroad tiles are backed by purchasable property data. |

## 4. Dice
| Test Case Group | Scenario | Expected Output | Justification |
| --- | --- | --- | --- |
| **Roll Range** | Roll 1000 times, collect unique values | Values `1-6` must all appear | Validates the dice correctly simulates six-sided dice. |
| **Doubles Logic** | Mocked rolls producing doubles | `is_doubles()` correctly flagged, streak incremented | Ensures consecutive state counting behaves correctly. |

## 5. Game Engine Mechanics
| Test Case Group | Scenario | Expected Output | Justification |
| --- | --- | --- | --- |
| **Jail Turns - Mandatory**| Player serves exactly 3 consecutive turns | Fund deduction (`$50`), unlocks Jail | The absolute final boundary forcing an outcome avoiding soft-locks. |
| **Jail Turns - Pay** | Player opts to pay on turn 1/2 | Fund deduction, unlocks Jail | Voluntary exit conditions testing input decisions. |
| **Cards - Assorted** | Apply random cards (Collect, Jail) | Cash accurately altered according to action schema | Broad structural coverage of dictionary mapping. |
| **Move-To Card** | Card moves player to special tile position | Special tile logic correctly triggered | Validates `_handle_move_card` resolves non-property tiles. |
| **Auction Bidding** | Lowest bidder passes, Higher bids | Highest valid integer wins and deducts funds | Asserts standard max-value finding loop over active participants. |
| **Buying (Exact Balance)** | Player balance == property price | Purchase should succeed | Boundary condition for affordability check. |
| **Rent Transfer** | Tenant lands on owned property | Tenant pays, Owner receives | Both deduction and credit must occur. |
| **Net Worth** | Player with cash + properties | Net worth includes property values | Validates comprehensive wealth calculation. |
| **Winner Selection** | Two players with different net worths | Highest net worth player wins | Verifies correct winner determination logic. |
| **Bankruptcy Triggers**| Player drops to `< 0` cash | Eliminated, properties stripped | Ensures cleanup loops successfully over player attributes. |
| **Three Doubles Rule**| Streak hits `3` consecutive | Player instantly sent to jail | Key probability-based mechanic verification. |

---

# PART II: DEAD CODE TESTS

During white-box trace analysis, large chunks of code were found to be completely inactive—specifically the interactive pre-roll menu and its dependent functions. Tests below ensure correct mathematical behaviors on isolated modules, even though they cannot be natively triggered by `main.py`.

| Module | Tested Methods | Justification |
| --- | --- | --- |
| **Bank** | `give_loan`, `total_loans_issued`, `loan_count`, `get_balance` | Verifies loan tracking mechanisms and redundant getters. |
| **Game (Menus)**| `interactive_menu`, `_menu_mortgage`, `_menu_trade`, `trade`, `mortgage_property` | Ensures menu logic and P2P resource transfers pass successfully. |
| **Cards/Properties/Board**| `is_available`, `unmortgage`, `peek`, `is_purchasable`, `reshuffle` | Standalone property mutators and deck utilities. |

---

## Active Code Bug Report

During the white-box testing phase of the active code, 13 functional bugs were uncovered.

### Bug 1: Bank Fails to Ignore Negative Collections
- **Module/Method Tested**: `Bank.collect()`
- **Input/State**: System calls `.collect(-100)`.
- **Expected Result**: Docstring explicitly dictates: *Negative amounts are silently ignored*.
- **Actual Result**: The bank mathematically processes `-100`, destroying cash reserves instead of ignoring it.

### Bug 2: Players are not Rewarded for Passing GO
- **Module/Method Tested**: `Player.move()`
- **Input/State**: Player on pos `39` rolls a `3`, crossing index `0` to land on `2`.
- **Expected Result**: Passing properties conceptually loops back over start, mandating a `$200` traversal allowance.
- **Actual Result**: The logic asserts `if self.position == 0:`. Players must strictly end their turn natively *on* index `0` itself to be rewarded.

### Bug 3: Property Groups Wrongfully Determine Monopolies
- **Module/Method Tested**: `PropertyGroup.all_owned_by()`
- **Input/State**: Group consists of 2 properties. Player owns strictly 1.
- **Expected Result**: Monopoly requires owning all properties (`False`). Rent multiplier is standard ($1\times$).
- **Actual Result**: Code explicitly utilizes `any()` instead of `all()`. Purchasing one singular property triggers universally doubled rents across every piece of the property chain.

### Bug 4: Get Out Of Jail Free Cards Crash System
- **Module/Method Tested**: `Game._apply_card()`
- **Input/State**: Player triggers `jail_free` card.
- **Expected Result**: Card increments the `jail_state.get_out_of_jail_cards` dataclass tracker.
- **Actual Result**: Code triggers `player.get_out_of_jail_cards += 1`. This circumvents `jail_state`, causing a fatal `AttributeError` and crashing the runtime.

### Bug 5: Voluntary Jail Payment never Deducts from Player
- **Module/Method Tested**: `Game._handle_jail_turn()`
- **Input/State**: Player enters `y` on the input prompt to exit jail. 
- **Expected Result**: `self.bank.collect(50)` alongside `player.deduct_money(50)`.
- **Actual Result**: Only `self.bank.collect(50)` executes. The player's balance retains its initial amounts, enabling infinitely exploitable jail evasions with absolutely zero fund deduction.

### Bug 6: Dice Uses `randint(1, 5)` Instead of `randint(1, 6)`
- **Module/Method Tested**: `Dice.roll()`
- **Input/State**: Rolling dice 1000 times and collecting all unique outcomes.
- **Expected Result**: Docstring describes "six-sided dice". Values `1` through `6` should all appear.
- **Actual Result**: `random.randint(1, 5)` is used. The value `6` never appears on either die, and the maximum possible roll is `10` instead of `12`.

### Bug 7: `find_winner()` Returns the Loser
- **Module/Method Tested**: `Game.find_winner()`
- **Input/State**: Two players: Alice with `$5000`, Bob with `$100`.
- **Expected Result**: Docstring says "Return the player with the highest net worth". Alice should win.
- **Actual Result**: Code uses `min()` instead of `max()`. Bob (the poorest player) is declared the winner.

### Bug 8: `buy_property()` Rejects Purchase at Exact Balance
- **Module/Method Tested**: `Game.buy_property()`
- **Input/State**: Player has exactly `$60` and attempts to buy Mediterranean Avenue (price `$60`).
- **Expected Result**: Purchase succeeds since the player can exactly afford it.
- **Actual Result**: The guard `player.balance <= prop.numbers.price` uses `<=` instead of `<`, rejecting the purchase when the player has exactly enough money.

### Bug 9: `pay_rent()` Does not Transfer Rent to Property Owner
- **Module/Method Tested**: `Game.pay_rent()`
- **Input/State**: Player 1 lands on Player 2's property. Rent is deducted from Player 1.
- **Expected Result**: Player 2's balance increases by the rent amount.
- **Actual Result**: `player.deduct_money(rent)` is called, but `prop.owner.add_money(rent)` is never invoked. The rent money vanishes entirely.

### Bug 10: `net_worth()` Ignores Property Values
- **Module/Method Tested**: `Player.net_worth()`
- **Input/State**: Player with `$100` cash and a property worth `$500`.
- **Expected Result**: Net worth should incorporate property holdings (e.g., `$600`).
- **Actual Result**: `net_worth()` simply returns `self.balance`. A player with enormous real estate holdings but low cash is valued as nearly bankrupt.

### Bug 11: `_handle_move_card()` Ignores Non-Property Special Tiles
- **Module/Method Tested**: `Game._handle_move_card()`
- **Input/State**: A card moves the player to position `30` (Go To Jail).
- **Expected Result**: The player should be sent to jail.
- **Actual Result**: The method only checks `if tile == "property"`. All non-property special tiles (income tax, go to jail, etc.) are silently ignored at the destination.

### Bug 12: Railroad Tiles Have No Property Objects
- **Module/Method Tested**: `Board.get_property_at()` for positions `5, 15, 25, 35`
- **Input/State**: Player lands on a railroad tile during gameplay.
- **Expected Result**: Railroad positions should map to purchasable `Property` objects.
- **Actual Result**: No `Property` objects are created for railroad positions. `get_property_at()` returns `None`, and the `if prop is not None` guard silently skips. Railroads are effectively blank tiles.

### Bug 13: `doubles_streak` Never Reset After Player is Sent to Jail
- **Module/Method Tested**: `Game.play_turn()` / `Dice.is_doubles()` usage
- **Input/State**: Player A rolls 3 consecutive doubles and is sent to jail. The turn advances to Player B.
- **Expected Result**: The `doubles_streak` counter should automatically reset to `0` for Player B.
- **Actual Result**: The `doubles_streak` retains the value of `3`. If Player B rolls doubles on their very first attempt, the counter increments to `4`, immediately triggering the 3-doubles jail rule on Player B.

---

## Dead Code Bug Report

These bugs exist strictly within the interactive menu flow, which currently constitutes dead code unable to be executed naturally by the core game loop.

### Bug 1: Emergency Loans do not Drain Bank Funds
- **Module/Method Tested**: `Bank.give_loan()`
- **Input/State**: The pre-roll menu issues a $500 emergency loan to the Player.
- **Expected Result**: Player `balance` correctly increases by 500, and the Bank `_funds` logically decrease by 500.
- **Actual Result**: The player correctly receives the 500, but the bank's internal balance is never decreased, creating synthetic money.

### Bug 2: Trades Delete Player Cash Assets without Delivery
- **Module/Method Tested**: `Game.trade()`
- **Input/State**: Player 1 sells property to Player 2 strictly for $100 via the pre-roll menu.
- **Expected Result**: Player 2 loses property and gains $100. Player 1 loses $100.
- **Actual Result**: The initial loop calls `buyer.deduct_money(...)` as usual, but systemically lacks an invocation to `seller.add_money(...)`, causing the cash to vanish into the void rather than arriving in the seller's wallet.
