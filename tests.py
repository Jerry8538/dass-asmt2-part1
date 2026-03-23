import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from moneypoly.bank import Bank
from moneypoly.player import Player
from moneypoly.property import Property, PropertyNumbers, PropertyGroup
from moneypoly.dice import Dice
from moneypoly.cards import CardDeck
from moneypoly.board import Board
from moneypoly import ui
from moneypoly.config import BANK_STARTING_FUNDS
from moneypoly.game import Game
from moneypoly.config import (
    INCOME_TAX_AMOUNT, LUXURY_TAX_AMOUNT, JAIL_FINE, GO_SALARY
)

@pytest.fixture(autouse=True)
def prevent_hanging_inputs(monkeypatch):
    def mock_input(prompt):
        return 's'
    monkeypatch.setattr('builtins.input', mock_input)

# =========================================================================
#                          ACTIVE CODE TESTS
# =========================================================================

def test_bank_initialization():
    bank = Bank()
    assert bank._funds == BANK_STARTING_FUNDS
    assert repr(bank) == f"Bank(funds={BANK_STARTING_FUNDS})"

def test_bank_collect_positive():
    bank = Bank()
    bank.collect(500)
    assert bank._funds == BANK_STARTING_FUNDS + 500

def test_bank_collect_negative_bug():
    bank = Bank()
    bank.collect(-100)
    assert bank._funds == BANK_STARTING_FUNDS, "BUG: collect() did not ignore negative amount"

def test_bank_pay_out_success():
    bank = Bank()
    paid = bank.pay_out(500)
    assert paid == 500
    assert bank._funds == BANK_STARTING_FUNDS - 500

def test_bank_pay_out_zero_or_negative():
    bank = Bank()
    assert bank.pay_out(0) == 0
    assert bank.pay_out(-50) == 0
    assert bank._funds == BANK_STARTING_FUNDS

def test_bank_pay_out_insufficient_funds():
    bank = Bank()
    with pytest.raises(ValueError, match="Bank cannot pay"):
        bank.pay_out(BANK_STARTING_FUNDS + 100)

def test_player_initialization():
    p = Player("Bob")
    assert p.name == "Bob"
    assert p.balance == 1500
    assert p.position == 0
    assert not p.is_bankrupt()
    assert p.net_worth() == 1500
    assert p.count_properties() == 0
    assert "Bob" in repr(p)

def test_player_add_money():
    p = Player("Bob", balance=100)
    p.add_money(50)
    assert p.balance == 150
    with pytest.raises(ValueError, match="Cannot add a negative"):
        p.add_money(-10)

def test_player_deduct_money():
    p = Player("Bob", balance=100)
    p.deduct_money(40)
    assert p.balance == 60
    with pytest.raises(ValueError, match="Cannot deduct a negative"):
        p.deduct_money(-10)

@patch('builtins.print')
def test_player_move_normal(mock_print):
    p = Player("Bob", balance=0)
    pos = p.move(5)
    assert pos == 5

@patch('builtins.print')
def test_player_move_land_on_go(mock_print):
    p = Player("Bob", balance=0)
    p.position = 38
    pos = p.move(2)
    assert pos == 0
    assert p.balance == 200

@patch('builtins.print')
def test_player_move_pass_go_bug(mock_print):
    p = Player("Bob", balance=0)
    p.position = 39
    pos = p.move(3)
    assert pos == 2
    assert p.balance == 200, "BUG: move() did not reward passing GO"

def test_player_jail():
    p = Player("Bob")
    p.go_to_jail()
    assert p.position == 10
    assert p.jail_state.in_jail is True
    assert p.jail_state.jail_turns == 0

def test_player_properties():
    p = Player("Bob")
    prop = Property("Prop", PropertyNumbers(1, 100, 10))
    p.add_property(prop)
    assert p.count_properties() == 1
    p.add_property(prop)
    assert p.count_properties() == 1
    p.remove_property(prop)
    assert p.count_properties() == 0

def test_property_initialization():
    group = PropertyGroup("Blue", "blue")
    nums = PropertyNumbers(12, 100, 10)
    prop = Property("Park", nums, group=group)
    assert prop.name == "Park"
    assert prop in group.properties

def test_property_group_rent_and_bug():
    group = PropertyGroup("Blue", "blue")
    prop1 = Property("P1", PropertyNumbers(1, 100, 10), group=group)
    prop2 = Property("P2", PropertyNumbers(2, 100, 10), group=group)
    player1 = Player("P1")
    
    prop1.owner = player1
    assert prop1.get_rent() == 10
    
    # Bug: all_owned_by uses any() Instead of all()
    assert group.all_owned_by(player1) is False, "BUG: group uses any() instead of all()"
    assert prop1.get_rent() == 10, "Rent doubled incorrectly due to any() bug"
    
    prop2.owner = player1
    assert group.all_owned_by(player1) is True
    assert prop1.get_rent() == 20

def test_board_initialization():
    board = Board()
    assert len(board.properties) == 22
    assert board.get_property_at(1).name == "Mediterranean Avenue"
    assert board.get_property_at(99) is None

def test_board_get_tile_type():
    board = Board()
    assert board.get_tile_type(0) == "go"
    assert board.get_tile_type(1) == "property"
    assert board.get_tile_type(99) == "blank"

def test_cards_deck_draw():
    raw_cards = [{"action": "collect", "value": 10}, {"action": "pay", "value": 20}]
    deck = CardDeck(raw_cards)
    card1 = deck.draw()
    assert card1["action"] == "collect"
    card2 = deck.draw()
    assert card2["action"] == "pay"
    card3 = deck.draw()
    assert card3["action"] == "collect" # wraps around

def test_cards_empty_deck():
    deck = CardDeck([])
    assert deck.draw() is None

@patch('random.randint')
def test_dice_roll(mock_randint):
    dice = Dice()
    mock_randint.side_effect = [3, 4, 5, 5]
    res1 = dice.roll()
    assert res1 == 7
    assert dice.is_doubles() is False
    res2 = dice.roll()
    assert res2 == 10
    assert dice.is_doubles() is True

@patch('builtins.print')
def test_ui_print_active_functions(mock_print):
    ui.print_banner("Test")
    
    p = Player("Alice")
    p2 = Player("Bob", balance=2000)
    ui.print_standings([p, p2])
    
    board = Board()
    ui.print_board_ownership(board)

@patch('builtins.input')
def test_ui_inputs(mock_input):
    mock_input.side_effect = ["10", "abc", "y", "N"]
    assert ui.safe_int_input("test", 5) == 10
    assert ui.safe_int_input("test", 5) == 5
    assert ui.confirm("yes?") is True
    assert ui.confirm("no?") is False

def test_game_init():
    g = Game(["Alice", "Bob"])
    assert len(g.players) == 2
    assert g.current_player().name == "Alice"
    g.advance_turn()
    assert g.current_player().name == "Bob"

@patch('builtins.print')
def test_game_play_turn_in_jail(mock_print):
    g = Game(["Alice", "Bob"])
    p = g.players[0]
    p.go_to_jail()
    p.jail_state.jail_turns = 1
    with patch.object(g, '_handle_jail_turn') as mock_jail:
        g.play_turn()
        mock_jail.assert_called_once_with(p)

@patch('builtins.print')
@patch('moneypoly.dice.Dice.roll', return_value=5)
@patch('moneypoly.dice.Dice.is_doubles', return_value=False)
def test_game_play_turn_normal(mock_doubles, mock_roll, mock_print):
    g = Game(["Alice", "Bob"])
    p = g.players[0]
    with patch.object(g, '_move_and_resolve') as mock_resolve:
        g.play_turn()
        mock_resolve.assert_called_once_with(p, 5)

@patch('builtins.print')
@patch('moneypoly.dice.Dice.is_doubles', return_value=True)
def test_game_play_turn_doubles_jail(mock_doubles, mock_print):
    g = Game(["Alice", "Bob"])
    g.dice.doubles_streak = 2
    g.play_turn()
    assert g.players[0].jail_state.in_jail is True

@patch('builtins.print')
def test_game_move_and_resolve_special_tiles(mock_print):
    g = Game(["Alice"])
    p = g.players[0]
    
    g._move_and_resolve(p, 4) # Income Tax
    assert p.balance == 1500 - INCOME_TAX_AMOUNT
    
    p.position = 28
    g._move_and_resolve(p, 2) # Go To Jail
    assert p.jail_state.in_jail is True

    p.jail_state.in_jail = False
    p.position = 36
    g._move_and_resolve(p, 2) # Luxury Tax
    assert p.balance == 1500 - INCOME_TAX_AMOUNT - LUXURY_TAX_AMOUNT

@patch('builtins.print')
def test_game_handle_jail_turn_pay(mock_print):
    g = Game(["Alice"])
    p = g.players[0]
    p.go_to_jail()
    
    with patch('moneypoly.ui.confirm', side_effect=[True]):
        with patch.object(g, '_move_and_resolve') as mock_resolve:
            g._handle_jail_turn(p)
            assert p.jail_state.in_jail is False
            assert p.balance == 1500 - JAIL_FINE

@patch('builtins.print')
def test_game_handle_jail_turn_card(mock_print):
    g = Game(["Alice"])
    p = g.players[0]
    p.go_to_jail()
    p.jail_state.get_out_of_jail_cards = 1
    
    with patch('moneypoly.ui.confirm', return_value=True):
        with patch.object(g, '_move_and_resolve') as mock_resolve:
            g._handle_jail_turn(p)
            assert p.jail_state.in_jail is False
            assert p.jail_state.get_out_of_jail_cards == 0

@patch('builtins.print')
def test_game_handle_jail_turn_mandatory(mock_print):
    g = Game(["Alice"])
    p = g.players[0]
    p.go_to_jail()
    p.jail_state.jail_turns = 2
    
    with patch('moneypoly.ui.confirm', return_value=False):
        with patch.object(g, '_move_and_resolve') as mock_resolve:
            g._handle_jail_turn(p)
            assert p.jail_state.in_jail is False

@patch('builtins.print')
@patch('builtins.input', return_value='b')
def test_game_buy_property(mock_input, mock_print):
    g = Game(["Alice"])
    p = g.players[0]
    prop = g.board.get_property_at(1)
    
    g._handle_property_tile(p, prop)
    assert prop.owner == p
    
    p2 = Player("Bob", balance=1)
    assert g.buy_property(p2, prop) is False

@patch('builtins.print')
@patch('builtins.input', return_value='a')
def test_game_auction_property(mock_input, mock_print):
    g = Game(["Alice", "Bob"])
    prop = g.board.get_property_at(1)
    
    with patch('moneypoly.ui.safe_int_input', side_effect=[0, 100]):
        g._handle_property_tile(g.players[0], prop)
        assert prop.owner == g.players[1]

@patch('builtins.print')
def test_game_pay_rent(mock_print):
    g = Game(["Alice", "Bob"])
    p1 = g.players[0]
    p2 = g.players[1]
    prop = g.board.get_property_at(1)
    prop.owner = p2
    
    g._handle_property_tile(p1, prop)
    assert p1.balance == 1500 - prop.get_rent()

@patch('builtins.print')
def test_game_cards(mock_print):
    g = Game(["Alice"])
    p = g.players[0]
    
    g._apply_card(p, {"description": "Col", "action": "collect", "value": 100})
    assert p.balance == 1600
    
    g._apply_card(p, {"description": "Pay", "action": "pay", "value": 200})
    assert p.balance == 1400
    
    g._apply_card(p, {"description": "Jail", "action": "jail", "value": 0})
    assert p.jail_state.in_jail is True
    
    g._apply_card(p, {"description": "Free", "action": "jail_free", "value": 0})
    
    g._apply_card(p, {"description": "Bday", "action": "birthday", "value": 10})
    g._apply_card(p, {"description": "All", "action": "collect_from_all", "value": 50})

@patch('builtins.print')
def test_game_handle_move_card(mock_print):
    g = Game(["Alice"])
    p = g.players[0]
    p.position = 39
    g._handle_move_card(p, 0)
    assert p.position == 0

@patch('builtins.print')
def test_game_bankruptcy(mock_print):
    g = Game(["Alice", "Bob"])
    p1 = g.players[0]
    prop = g.board.get_property_at(1)
    prop.owner = p1
    p1.add_property(prop)
    
    p1.balance = 0
    g._check_bankruptcy(p1)
    assert p1.is_eliminated is True
    assert prop.owner is None

@patch('builtins.print')
def test_game_run(mock_print):
    g = Game(["Alice", "Bob"])
    g.players[0].balance = 0
    with patch.object(g, 'play_turn'):
        g._check_bankruptcy(g.players[0])
        g.run()
        assert len(g.players) == 1

def test_dice_range_bug():
    """Dice uses randint(1,5) instead of randint(1,6) — six-sided dice never roll 6."""
    dice = Dice()
    results = set()
    for _ in range(1000):
        dice.roll()
        results.add(dice.die1)
        results.add(dice.die2)
    assert 6 in results, "BUG: Dice never rolls 6 — randint(1,5) instead of randint(1,6)"

@patch('builtins.print')
def test_find_winner_bug(mock_print):
    """find_winner() uses min() instead of max() — the loser wins."""
    g = Game(["Alice", "Bob"])
    g.players[0].balance = 5000
    g.players[1].balance = 100
    winner = g.find_winner()
    assert winner.name == "Alice", "BUG: find_winner() returns min net worth instead of max"

@patch('builtins.print')
def test_buy_property_exact_balance_bug(mock_print):
    """buy_property() rejects purchase when balance == price (uses <= instead of <)."""
    g = Game(["Alice"])
    p = g.players[0]
    prop = g.board.get_property_at(1) # Mediterranean Ave, price=60
    p.balance = 60
    result = g.buy_property(p, prop)
    assert result is True, "BUG: buy_property() rejects purchase when balance equals price exactly"

@patch('builtins.print')
def test_pay_rent_owner_receives_money_bug(mock_print):
    """pay_rent() deducts from tenant but never adds to owner's balance."""
    g = Game(["Alice", "Bob"])
    p1 = g.players[0]
    p2 = g.players[1]
    prop = g.board.get_property_at(1)
    prop.owner = p2
    p2.add_property(prop)
    
    rent = prop.get_rent()
    p2_balance_before = p2.balance
    g.pay_rent(p1, prop)
    assert p2.balance == p2_balance_before + rent, "BUG: pay_rent() does not transfer rent to property owner"

def test_net_worth_ignores_properties_bug():
    """net_worth() only returns cash balance, ignoring property values."""
    p = Player("Bob", balance=100)
    prop = Property("Park", PropertyNumbers(12, 500, 10))
    prop.owner = p
    p.add_property(prop)
    # Net worth should include property values
    assert p.net_worth() > 100, "BUG: net_worth() ignores property values"

@patch('builtins.print')
def test_handle_move_card_special_tile_bug(mock_print):
    """_handle_move_card() only resolves 'property' tiles, ignoring special tiles."""
    g = Game(["Alice"])
    p = g.players[0]
    p.position = 35
    # Move to Go To Jail (position 30)
    g._handle_move_card(p, 30)
    assert p.jail_state.in_jail is True, "BUG: _handle_move_card() does not handle go_to_jail tile"

@patch('builtins.print')
def test_railroad_has_no_properties_bug(mock_print):
    """Railroad tiles (5,15,25,35) are in SPECIAL_TILES but have no Property objects."""
    board = Board()
    # Railroad positions should have purchasable Property objects
    for pos in [5, 15, 25, 35]:
        prop = board.get_property_at(pos)
        assert prop is not None, f"BUG: Railroad at position {pos} has no Property object"

@patch('builtins.print')
@patch('moneypoly.dice.Dice.is_doubles', return_value=True)
def test_doubles_streak_reset_after_jail_bug(mock_doubles, mock_print):
    """After 3 doubles sends a player to jail, the streak must be reset for the next player."""
    g = Game(["Alice", "Bob"])
    g.dice.doubles_streak = 2
    g.play_turn()  # Alice rolls doubles (streak->3), goes to jail, advance_turn to Bob
    assert g.players[0].jail_state.in_jail is True
    # The streak should be reset to 0 before Bob's turn
    assert g.dice.doubles_streak == 0, "BUG: doubles_streak not reset after sending player to jail"

# =========================================================================
#                          DEAD CODE TESTS
# =========================================================================

def test_bank_give_loan_zero_or_negative():
    bank = Bank()
    player = Player("Alice", balance=0)
    bank.give_loan(player, 0)
    bank.give_loan(player, -100)
    assert player.balance == 0

@patch('builtins.print')
def test_bank_give_loan_success_bug(mock_print):
    bank = Bank()
    player = Player("Alice", balance=0)
    bank.give_loan(player, 500)
    assert player.balance == 500
    assert bank.get_balance() == BANK_STARTING_FUNDS - 500, "BUG: give_loan() did not reduce bank funds"

@patch('builtins.print')
def test_bank_summary(mock_print):
    bank = Bank()
    bank.summary()

def test_player_status_line():
    p = Player("Bob", balance=100)
    p.go_to_jail()
    status = p.status_line()
    assert "JAILED" in status

def test_property_mortgage():
    nums = PropertyNumbers(12, 100, 10)
    prop = Property("Park", nums)
    assert prop.mortgage() == 50
    assert prop.is_mortgaged is True

def test_property_unmortgage():
    nums = PropertyNumbers(12, 100, 10)
    prop = Property("Park", nums)
    prop.mortgage()
    assert prop.unmortgage() == 55

def test_property_is_available():
    nums = PropertyNumbers(12, 100, 10)
    prop = Property("Park", nums)
    assert prop.is_available() is True
    prop.owner = Player("P1")
    assert prop.is_available() is False

def test_property_group_methods():
    group = PropertyGroup("Blue", "blue")
    assert group.size() == 0
    assert len(group.get_owner_counts()) == 0

def test_board_methods():
    board = Board()
    assert board.is_special_tile(0) is True
    assert board.is_purchasable(1) is True
    assert len(board.properties_owned_by(Player("P"))) == 0
    assert len(board.unowned_properties()) == 22

def test_cards_deck_dead_methods():
    raw_cards = [{"action": "collect", "value": 10}, {"action": "pay", "value": 20}]
    deck = CardDeck(raw_cards)
    
    assert len(deck) == 2
    assert deck.cards_remaining() == 2
    assert deck.peek()["action"] == "collect"
    deck.reshuffle()
    assert deck.index == 0

def test_dice_reset():
    dice = Dice()
    dice.die1 = 5
    dice.reset()
    assert dice.die1 == 0

@patch('builtins.print')
def test_ui_print_dead_functions(mock_print):
    ui.print_player_card(Player("Alice"))
    assert ui.format_currency(1500) == "$1,500"

@patch('builtins.print')
def test_game_mortgage_unmortgage(mock_print):
    g = Game(["Alice", "Bob"])
    p1 = g.players[0]
    prop = g.board.get_property_at(1)
    
    prop.owner = p1
    p1.add_property(prop)
    
    assert g.mortgage_property(p1, prop) is True
    assert g.unmortgage_property(p1, prop) is True

@patch('builtins.print')
def test_game_trade(mock_print):
    g = Game(["Alice", "Bob"])
    p1 = g.players[0]
    p2 = g.players[1]
    prop = g.board.get_property_at(1)
    prop.owner = p1
    p1.add_property(prop)
    
    assert g.trade(p1, p2, prop, 500) is True

@patch('builtins.print')
def test_game_trade_seller_receives_cash_bug(mock_print):
    """trade() deducts cash from buyer but never adds it to seller."""
    g = Game(["Alice", "Bob"])
    p1 = g.players[0]
    p2 = g.players[1]
    prop = g.board.get_property_at(1)
    prop.owner = p1
    p1.add_property(prop)
    
    p1_balance_before = p1.balance
    g.trade(p1, p2, prop, 500)
    assert p1.balance == p1_balance_before + 500, "BUG: trade() does not give seller the cash"

@patch('builtins.print')
@patch('moneypoly.ui.safe_int_input', side_effect=[0])
def test_game_interactive_menu_exit(mock_input, mock_print):
    g = Game(["Alice", "Bob"])
    g.interactive_menu(g.players[0])

@patch('builtins.print')
@patch('moneypoly.ui.safe_int_input', side_effect=[1, 2, 6, 100, 0])
def test_game_interactive_menu_misc(mock_input, mock_print):
    g = Game(["Alice"])
    g.interactive_menu(g.players[0])

@patch('builtins.print')
@patch('moneypoly.ui.safe_int_input', side_effect=[3, 1, 4, 1, 0])
def test_game_interactive_menu_mortgage(mock_input, mock_print):
    g = Game(["Alice"])
    p = g.players[0]
    prop = g.board.get_property_at(1)
    prop.owner = p
    p.add_property(prop)
    g.interactive_menu(p)

@patch('builtins.print')
@patch('moneypoly.ui.safe_int_input', side_effect=[5, 1, 1, 100, 0])
def test_game_interactive_menu_trade(mock_input, mock_print):
    g = Game(["Alice", "Bob"])
    p1 = g.players[0]
    prop = g.board.get_property_at(1)
    prop.owner = p1
    p1.add_property(prop)
    g.interactive_menu(p1)
