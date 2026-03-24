import sys
from pathlib import Path

import pytest

PROJECT_CODE_ROOT = Path(__file__).resolve().parents[1] / "code" / "moneypoly"
if str(PROJECT_CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_CODE_ROOT))

from main import get_player_names
from moneypoly.board import Board
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
