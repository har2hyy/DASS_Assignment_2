import sys
from pathlib import Path

import pytest

PROJECT_CODE_ROOT = Path(__file__).resolve().parents[1] / "code" / "moneypoly"
if str(PROJECT_CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_CODE_ROOT))

from main import get_player_names
from moneypoly import ui
from moneypoly.bank import Bank
from moneypoly.board import Board
from moneypoly.cards import CHANCE_CARDS, CardDeck
from moneypoly.config import GO_SALARY, JAIL_FINE, MAX_TURNS, STARTING_BALANCE
from moneypoly.dice import Dice
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup


@pytest.fixture
def game():
    return Game(["Alice", "Bob", "Cara"])


def test_get_player_names_strips_and_filters(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt: "  A, B ,, C  ")
    assert get_player_names() == ["A", "B", "C"]


def test_player_move_landing_on_go_gets_salary():
    player = Player("P")
    player.position = 35
    start_balance = player.balance

    new_pos = player.move(5)

    assert new_pos == 0
    assert player.balance == start_balance + GO_SALARY


def test_player_move_passing_go_gets_salary():
    player = Player("P")
    player.position = 38
    start_balance = player.balance

    new_pos = player.move(5)

    assert new_pos == 3
    assert player.balance == start_balance + GO_SALARY


def test_player_move_without_passing_go_no_salary():
    player = Player("P")
    player.position = 5
    start_balance = player.balance

    new_pos = player.move(6)

    assert new_pos == 11
    assert player.balance == start_balance


def test_player_net_worth_includes_property_values():
    player = Player("P")
    group = PropertyGroup("Test", "gray")
    prop1 = Property("P1", 1, 100, 10, group)
    prop2 = Property("P2", 3, 120, 12, group)
    player.add_property(prop1)
    player.add_property(prop2)

    assert player.net_worth() == player.balance + 220


def test_dice_roll_uses_full_range(monkeypatch):
    captured = []

    def fake_randint(low, high):
        captured.append((low, high))
        return 1

    monkeypatch.setattr("moneypoly.dice.random.randint", fake_randint)
    dice = Dice()
    _ = dice.roll()

    assert captured == [(1, 6), (1, 6)]


def test_dice_doubles_streak_increment_and_reset(monkeypatch):
    sequence = iter([3, 3, 2, 5])
    monkeypatch.setattr("moneypoly.dice.random.randint", lambda _l, _h: next(sequence))
    dice = Dice()

    dice.roll()
    assert dice.doubles_streak == 1

    dice.roll()
    assert dice.doubles_streak == 0


def test_property_group_all_owned_by_requires_all_members():
    group = PropertyGroup("Blue", "blue")
    owner = Player("Owner")
    other = Player("Other")
    p1 = Property("A", 1, 100, 10, group)
    p2 = Property("B", 3, 100, 10, group)
    p1.owner = owner
    p2.owner = other

    assert group.all_owned_by(owner) is False


def test_property_get_rent_double_only_for_complete_group():
    group = PropertyGroup("Blue", "blue")
    owner = Player("Owner")
    p1 = Property("A", 1, 100, 10, group)
    p2 = Property("B", 3, 100, 10, group)
    p1.owner = owner

    assert p1.get_rent() == 10

    p2.owner = owner
    assert p1.get_rent() == 20


def test_buy_property_when_balance_greater_than_price(game):
    player = game.players[0]
    prop = game.board.get_property_at(1)
    assert prop is not None

    player.balance = prop.price + 10
    ok = game.buy_property(player, prop)

    assert ok is True
    assert prop.owner == player
    assert prop in player.properties


def test_buy_property_when_balance_equals_price(game):
    player = game.players[0]
    prop = game.board.get_property_at(3)
    assert prop is not None

    player.balance = prop.price
    ok = game.buy_property(player, prop)

    assert ok is True
    assert prop.owner == player


def test_buy_property_when_balance_less_than_price(game):
    player = game.players[0]
    prop = game.board.get_property_at(6)
    assert prop is not None

    player.balance = prop.price - 1
    ok = game.buy_property(player, prop)

    assert ok is False
    assert prop.owner is None


def test_pay_rent_noop_on_mortgaged_property(game):
    tenant = game.players[0]
    owner = game.players[1]
    prop = game.board.get_property_at(1)
    assert prop is not None

    prop.owner = owner
    prop.is_mortgaged = True
    b_tenant = tenant.balance
    b_owner = owner.balance

    game.pay_rent(tenant, prop)

    assert tenant.balance == b_tenant
    assert owner.balance == b_owner


def test_pay_rent_transfers_money_to_owner(game):
    tenant = game.players[0]
    owner = game.players[1]
    prop = game.board.get_property_at(3)
    assert prop is not None

    prop.owner = owner
    prop.is_mortgaged = False
    rent = prop.get_rent()
    b_tenant = tenant.balance
    b_owner = owner.balance

    game.pay_rent(tenant, prop)

    assert tenant.balance == b_tenant - rent
    assert owner.balance == b_owner + rent


def test_check_bankruptcy_eliminates_and_releases_properties(game):
    player = game.players[0]
    prop = game.board.get_property_at(1)
    assert prop is not None

    prop.owner = player
    player.add_property(prop)
    player.balance = 0

    game._check_bankruptcy(player)

    assert player not in game.players
    assert prop.owner is None
    assert prop.is_mortgaged is False


def test_find_winner_returns_highest_net_worth(game):
    game.players[0].balance = 100
    game.players[1].balance = 500
    game.players[2].balance = 300

    winner = game.find_winner()

    assert winner == game.players[1]


def test_find_winner_single_player():
    g = Game(["Solo"])
    assert g.find_winner() == g.players[0]


def test_find_winner_none_when_empty(game):
    game.players.clear()
    assert game.find_winner() is None


def test_handle_jail_turn_use_card(game, monkeypatch):
    player = game.players[0]
    player.in_jail = True
    player.get_out_of_jail_cards = 1
    called = {"move": 0}

    monkeypatch.setattr("moneypoly.game.ui.confirm", lambda _p: True)
    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game, "_move_and_resolve", lambda _pl, _roll: called.__setitem__("move", 1))

    game._handle_jail_turn(player)

    assert player.in_jail is False
    assert player.get_out_of_jail_cards == 0
    assert called["move"] == 1


def test_handle_jail_turn_mandatory_release_on_third_turn(game, monkeypatch):
    player = game.players[0]
    player.in_jail = True
    player.jail_turns = 2
    start_balance = player.balance

    monkeypatch.setattr("moneypoly.game.ui.confirm", lambda _p: False)
    monkeypatch.setattr(game.dice, "roll", lambda: 3)
    monkeypatch.setattr(game, "_move_and_resolve", lambda _pl, _roll: None)

    game._handle_jail_turn(player)

    assert player.in_jail is False
    assert player.jail_turns == 0
    assert player.balance == start_balance - JAIL_FINE


def test_apply_card_collect(game):
    player = game.players[0]
    start_balance = player.balance
    game._apply_card(player, {"description": "collect", "action": "collect", "value": 50})
    assert player.balance == start_balance + 50


def test_apply_card_pay(game):
    player = game.players[0]
    start_balance = player.balance
    game._apply_card(player, {"description": "pay", "action": "pay", "value": 60})
    assert player.balance == start_balance - 60


def test_apply_card_jail(game):
    player = game.players[0]
    game._apply_card(player, {"description": "jail", "action": "jail", "value": 0})
    assert player.in_jail is True


def test_apply_card_jail_free(game):
    player = game.players[0]
    game._apply_card(player, {"description": "jail_free", "action": "jail_free", "value": 0})
    assert player.get_out_of_jail_cards == 1


def test_apply_card_move_to_pass_go_collects_salary(game):
    player = game.players[0]
    player.position = 38
    start_balance = player.balance
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(game.board, "get_tile_type", lambda _pos: "blank")

    game._apply_card(player, {"description": "move", "action": "move_to", "value": 1})
    monkeypatch.undo()

    assert player.position == 1
    assert player.balance == start_balance + GO_SALARY


def test_apply_card_birthday_collects_from_others(game):
    player = game.players[0]
    start_balance = player.balance

    game._apply_card(player, {"description": "birthday", "action": "birthday", "value": 10})

    assert player.balance == start_balance + 20


def test_apply_card_collect_from_all(game):
    player = game.players[0]
    start_balance = player.balance

    game._apply_card(
        player,
        {"description": "collect from all", "action": "collect_from_all", "value": 20},
    )

    assert player.balance == start_balance + 40


def test_move_and_resolve_routes_tiles(game, monkeypatch):
    player = game.players[0]
    calls = {"property": 0, "card": 0}

    monkeypatch.setattr(player, "move", lambda _steps: None)
    monkeypatch.setattr(game.board, "get_property_at", lambda _pos: game.board.properties[0])
    monkeypatch.setattr(game, "_check_bankruptcy", lambda _p: None)
    monkeypatch.setattr(game, "_handle_property_tile", lambda _p, _prop: calls.__setitem__("property", calls["property"] + 1))
    monkeypatch.setattr(game, "_apply_card", lambda _p, _card: calls.__setitem__("card", calls["card"] + 1))

    for tile in ["chance", "community_chest", "property", "railroad", "blank"]:
        monkeypatch.setattr(game.board, "get_tile_type", lambda _pos, t=tile: t)
        game._move_and_resolve(player, 4)

    assert calls["card"] == 2
    assert calls["property"] == 2


def test_play_turn_triple_doubles_sends_to_jail(game, monkeypatch):
    player = game.current_player()
    game.dice.doubles_streak = 3
    monkeypatch.setattr(game.dice, "roll", lambda: 6)
    monkeypatch.setattr(game.dice, "is_doubles", lambda: True)
    monkeypatch.setattr(game, "_move_and_resolve", lambda _p, _r: None)

    game.play_turn()

    assert player.in_jail is True


def test_play_turn_doubles_grants_extra_turn(game, monkeypatch):
    start_index = game.current_index
    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game.dice, "is_doubles", lambda: True)
    monkeypatch.setattr(game, "_move_and_resolve", lambda _p, _r: None)

    game.play_turn()

    assert game.current_index == start_index


def test_play_turn_non_doubles_advances(game, monkeypatch):
    start_index = game.current_index
    monkeypatch.setattr(game.dice, "roll", lambda: 5)
    monkeypatch.setattr(game.dice, "is_doubles", lambda: False)
    monkeypatch.setattr(game, "_move_and_resolve", lambda _p, _r: None)

    game.play_turn()

    assert game.current_index != start_index


def test_run_stops_at_max_turns(monkeypatch):
    g = Game(["A", "B"])
    g.turn_number = MAX_TURNS
    called = {"play": 0}

    monkeypatch.setattr(g, "play_turn", lambda: called.__setitem__("play", called["play"] + 1))

    g.run()

    assert called["play"] == 0


def test_bank_collect_pay_out_and_balance():
    bank = Bank()
    start = bank.get_balance()

    bank.collect(100)
    assert bank.get_balance() == start + 100

    paid = bank.pay_out(40)
    assert paid == 40
    assert bank.get_balance() == start + 60


def test_bank_pay_out_insufficient_funds_raises():
    bank = Bank()
    with pytest.raises(ValueError):
        bank.pay_out(bank.get_balance() + 1)


def test_bank_loan_and_summary(capsys):
    bank = Bank()
    player = Player("Loaned")
    start_balance = player.balance

    bank.give_loan(player, 120)
    bank.summary()

    out = capsys.readouterr().out
    assert player.balance == start_balance + 120
    assert bank.loan_count() == 1
    assert bank.total_loans_issued() == 120
    assert "Bank reserves" in out


def test_board_tile_lookup_and_special_flags():
    board = Board()

    assert board.get_tile_type(0) == "go"
    assert board.get_tile_type(1) == "property"
    assert board.get_tile_type(12) == "blank"
    assert board.is_special_tile(7) is True
    assert board.is_special_tile(1) is False


def test_board_purchasable_and_owner_lists():
    board = Board()
    player = Player("Owner")
    prop = board.get_property_at(1)
    assert prop is not None

    assert board.is_purchasable(1) is True
    prop.owner = player
    assert board.is_purchasable(1) is False
    prop.owner = None
    prop.is_mortgaged = True
    assert board.is_purchasable(1) is False

    prop.is_mortgaged = False
    prop.owner = player
    assert prop in board.properties_owned_by(player)
    assert prop not in board.unowned_properties()


def test_card_deck_draw_peek_and_reshuffle(monkeypatch):
    deck = CardDeck(CHANCE_CARDS[:2])

    first = deck.peek()
    drawn1 = deck.draw()
    drawn2 = deck.draw()
    drawn3 = deck.draw()

    assert first == drawn1
    assert drawn1 != drawn2
    assert drawn3 == drawn1
    assert len(deck) == 2

    called = {"shuffled": False}
    monkeypatch.setattr("moneypoly.cards.random.shuffle", lambda cards: called.__setitem__("shuffled", True))
    deck.reshuffle()
    assert called["shuffled"] is True
    assert deck.cards_remaining() == 2


def test_ui_helpers_and_rendering(monkeypatch, capsys):
    player = Player("UI")
    board = Board()
    prop = board.get_property_at(1)
    assert prop is not None
    prop.owner = player
    player.add_property(prop)

    ui.print_banner("Title")
    ui.print_player_card(player)
    ui.print_standings([player])
    ui.print_board_ownership(board)
    text = capsys.readouterr().out

    assert "Title" in text
    assert "Standings" in text
    assert "Property Register" in text
    assert ui.format_currency(1500) == "$1,500"

    monkeypatch.setattr("builtins.input", lambda _p: "42")
    assert ui.safe_int_input("x", default=0) == 42
    monkeypatch.setattr("builtins.input", lambda _p: "abc")
    assert ui.safe_int_input("x", default=7) == 7
    monkeypatch.setattr("builtins.input", lambda _p: "y")
    assert ui.confirm("x") is True


def test_game_mortgage_and_unmortgage_paths(game):
    owner = game.players[0]
    other = game.players[1]
    prop = game.board.get_property_at(1)
    assert prop is not None

    assert game.mortgage_property(other, prop) is False

    prop.owner = owner
    owner.add_property(prop)
    start_balance = owner.balance
    assert game.mortgage_property(owner, prop) is True
    assert owner.balance == start_balance + prop.mortgage_value
    assert game.mortgage_property(owner, prop) is False

    prop.is_mortgaged = True
    owner.balance = 0
    assert game.unmortgage_property(owner, prop) is False
    owner.balance = STARTING_BALANCE
    assert game.unmortgage_property(owner, prop) is True
    assert prop.is_mortgaged is False


def test_game_trade_paths(game):
    seller = game.players[0]
    buyer = game.players[1]
    prop = game.board.get_property_at(3)
    assert prop is not None

    assert game.trade(seller, buyer, prop, 100) is False

    prop.owner = seller
    seller.add_property(prop)
    buyer.balance = 0
    assert game.trade(seller, buyer, prop, 100) is False

    buyer.balance = STARTING_BALANCE
    assert game.trade(seller, buyer, prop, 100) is True
    assert prop.owner == buyer
    assert prop in buyer.properties


def test_auction_property_selects_highest_valid_bid(game, monkeypatch):
    prop = game.board.get_property_at(6)
    assert prop is not None
    bids = iter([100, 80, 150])

    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", lambda *_args, **_kwargs: next(bids))
    game.auction_property(prop)

    assert prop.owner == game.players[2]


def test_menu_helpers_cover_paths(game, monkeypatch):
    player = game.players[0]
    prop = game.board.get_property_at(1)
    assert prop is not None
    prop.owner = player
    player.add_property(prop)

    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", lambda *_args, **_kwargs: 1)
    called = {"mort": 0, "unmort": 0, "trade": 0}
    monkeypatch.setattr(game, "mortgage_property", lambda _p, _prop: called.__setitem__("mort", 1))
    monkeypatch.setattr(game, "unmortgage_property", lambda _p, _prop: called.__setitem__("unmort", 1))
    monkeypatch.setattr(game, "trade", lambda *_args: called.__setitem__("trade", 1))

    game._menu_mortgage(player)
    prop.is_mortgaged = True
    game._menu_unmortgage(player)

    inputs = iter([1, 1, 200])
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", lambda *_args, **_kwargs: next(inputs))
    game._menu_trade(player)

    assert called["mort"] == 1
    assert called["unmort"] == 1
    assert called["trade"] == 1


def test_interactive_menu_routes_options(game, monkeypatch):
    player = game.players[0]
    choices = iter([1, 2, 3, 4, 5, 6, 75, 0])
    called = {"mort": 0, "unmort": 0, "trade": 0, "loan": 0}

    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", lambda *_args, **_kwargs: next(choices))
    monkeypatch.setattr(game, "_menu_mortgage", lambda _p: called.__setitem__("mort", 1))
    monkeypatch.setattr(game, "_menu_unmortgage", lambda _p: called.__setitem__("unmort", 1))
    monkeypatch.setattr(game, "_menu_trade", lambda _p: called.__setitem__("trade", 1))
    monkeypatch.setattr(game.bank, "give_loan", lambda _p, _amt: called.__setitem__("loan", 1))

    game.interactive_menu(player)

    assert called == {"mort": 1, "unmort": 1, "trade": 1, "loan": 1}


def test_play_turn_handles_in_jail_path(game, monkeypatch):
    player = game.current_player()
    player.in_jail = True
    called = {"jail": 0}

    monkeypatch.setattr(game, "_handle_jail_turn", lambda _p: called.__setitem__("jail", 1))
    game.play_turn()

    assert called["jail"] == 1


def test_move_and_resolve_covers_tax_and_jail_tiles(game, monkeypatch):
    player = game.players[0]
    player.position = 0

    tile_positions = {
        "go_to_jail": 30,
        "income_tax": 4,
        "luxury_tax": 38,
        "free_parking": 20,
    }
    for tile, pos in tile_positions.items():
        monkeypatch.setattr(player, "move", lambda _steps, p=pos: setattr(player, "position", p))
        game._move_and_resolve(player, 1)
        if tile == "go_to_jail":
            assert player.in_jail is True
            player.in_jail = False
            player.position = 0
        else:
            assert game.board.get_tile_type(player.position) == tile


def test_handle_property_tile_ownership_and_choice_paths(game, monkeypatch):
    player = game.players[0]
    other = game.players[1]
    prop = game.board.get_property_at(1)
    assert prop is not None

    called = {"buy": 0, "auction": 0, "rent": 0}
    monkeypatch.setattr(game, "buy_property", lambda *_args: called.__setitem__("buy", 1))
    monkeypatch.setattr(game, "auction_property", lambda *_args: called.__setitem__("auction", 1))
    monkeypatch.setattr(game, "pay_rent", lambda *_args: called.__setitem__("rent", 1))

    prop.owner = None
    monkeypatch.setattr("builtins.input", lambda _p: "b")
    game._handle_property_tile(player, prop)

    prop.owner = None
    monkeypatch.setattr("builtins.input", lambda _p: "a")
    game._handle_property_tile(player, prop)

    prop.owner = player
    game._handle_property_tile(player, prop)

    prop.owner = other
    game._handle_property_tile(player, prop)

    assert called == {"buy": 1, "auction": 1, "rent": 1}


def test_pay_rent_owner_none_returns(game):
    player = game.players[0]
    prop = game.board.get_property_at(1)
    assert prop is not None
    prop.owner = None
    before = player.balance

    game.pay_rent(player, prop)

    assert player.balance == before


def test_auction_property_all_passes(game, monkeypatch):
    prop = game.board.get_property_at(8)
    assert prop is not None
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", lambda *_args, **_kwargs: 0)

    game.auction_property(prop)

    assert prop.owner is None


def test_auction_property_rejects_unaffordable_bid(game, monkeypatch):
    prop = game.board.get_property_at(9)
    assert prop is not None
    game.players[0].balance = 10
    bids = iter([5000, 0, 0])
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", lambda *_args, **_kwargs: next(bids))

    game.auction_property(prop)

    assert prop.owner is None


def test_handle_jail_turn_pay_fine_path(game, monkeypatch):
    player = game.players[0]
    player.in_jail = True
    player.get_out_of_jail_cards = 0
    calls = {"moved": 0}

    monkeypatch.setattr("moneypoly.game.ui.confirm", lambda _p: True)
    monkeypatch.setattr(game.dice, "roll", lambda: 7)
    monkeypatch.setattr(game, "_move_and_resolve", lambda *_args: calls.__setitem__("moved", 1))

    game._handle_jail_turn(player)

    assert player.in_jail is False
    assert calls["moved"] == 1


def test_apply_card_none_and_move_to_property(game, monkeypatch):
    player = game.players[0]
    called = {"property": 0}
    monkeypatch.setattr(game, "_handle_property_tile", lambda *_args: called.__setitem__("property", 1))

    game._apply_card(player, None)
    game._apply_card(player, {"description": "mv", "action": "move_to", "value": 1})

    assert called["property"] == 1


def test_check_bankruptcy_resets_current_index(game):
    victim = game.players[-1]
    game.current_index = len(game.players) - 1
    victim.balance = 0

    game._check_bankruptcy(victim)

    assert game.current_index == 0


def test_run_prints_no_winner_message(capsys):
    g = Game(["A", "B"])
    g.players.clear()

    g.run()

    assert "no players remaining" in capsys.readouterr().out


def test_menu_empty_paths(game, capsys):
    player = game.players[0]

    game._menu_mortgage(player)
    game._menu_unmortgage(player)
    game.players = [player]
    game._menu_trade(player)

    out = capsys.readouterr().out
    assert "No properties available" in out
    assert "No mortgaged properties" in out
    assert "No other players" in out


def test_menu_trade_invalid_indices(game, monkeypatch):
    player = game.players[0]
    prop = game.board.get_property_at(1)
    assert prop is not None
    prop.owner = player
    player.add_property(prop)

    # invalid partner index
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", lambda *_args, **_kwargs: 99)
    game._menu_trade(player)

    # valid partner, invalid property index
    sequence = iter([1, 99])
    monkeypatch.setattr("moneypoly.game.ui.safe_int_input", lambda *_args, **_kwargs: next(sequence))
    game._menu_trade(player)


def test_player_negative_money_ops_raise():
    player = Player("P")
    with pytest.raises(ValueError):
        player.add_money(-1)
    with pytest.raises(ValueError):
        player.deduct_money(-1)


def test_player_status_and_repr():
    player = Player("P")
    player.in_jail = True
    status = player.status_line()
    text = repr(player)

    assert "[JAILED]" in status
    assert "Player(" in text


def test_property_core_helpers_and_repr():
    group = PropertyGroup("T", "gray")
    prop = Property("X", 5, 100, 10, group)

    assert prop.is_available() is True
    assert "Property(" in repr(prop)

    payout = prop.mortgage()
    assert payout == 50
    assert prop.mortgage() == 0
    assert prop.unmortgage() == 55
    assert prop.unmortgage() == 0


def test_property_group_helpers_and_repr():
    group = PropertyGroup("T", "gray")
    p1 = Property("A", 1, 100, 10, group)
    p2 = Property("B", 2, 100, 10, group)
    owner = Player("Owner")
    p1.owner = owner

    group.add_property(p1)
    counts = group.get_owner_counts()

    assert counts[owner] == 1
    assert group.size() == 2
    assert "PropertyGroup(" in repr(group)


def test_card_deck_empty_and_repr():
    deck = CardDeck([])

    assert deck.draw() is None
    assert deck.peek() is None

    non_empty = CardDeck(CHANCE_CARDS[:1])
    assert "CardDeck(" in repr(non_empty)
