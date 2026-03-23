"""
White-Box Test Suite for MoneyPoly
====================================
Coverage targets
----------------
* All branches in every public and private method
* Key variable states (zero, negative, boundary, large)
* Edge cases: empty collections, exact boundaries, wrap-around

Run with:  python3 -m unittest tests.test_moneypoly -v
"""

import sys
import os
import unittest
from unittest.mock import patch

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
code_dir = os.path.join(base_dir, 'code')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

# ===========================================================================
# 1. DICE
# ===========================================================================
class TestDice(unittest.TestCase):
    """Branch + state coverage for Dice.roll(), is_doubles(), total(), reset()."""

    def setUp(self):
        from moneypoly.dice import Dice
        self.dice = Dice()

    def test_initial_values_zero(self):
        self.assertEqual(self.dice.die1, 0)
        self.assertEqual(self.dice.die2, 0)
        self.assertEqual(self.dice.doubles_streak, 0)

    def test_roll_returns_sum_of_dice(self):
        result = self.dice.roll()
        self.assertEqual(result, self.dice.die1 + self.dice.die2)

    def test_total_matches_dice_sum(self):
        self.dice.roll()
        self.assertEqual(self.dice.total(), self.dice.die1 + self.dice.die2)

    def test_reset_zeroes_all_state(self):
        self.dice.roll()
        self.dice.reset()
        self.assertEqual(self.dice.die1, 0)
        self.assertEqual(self.dice.die2, 0)
        self.assertEqual(self.dice.doubles_streak, 0)

    def test_doubles_streak_increments_on_doubles(self):
        with patch("random.randint", side_effect=[3, 3, 3, 3]):
            self.dice.roll()
            self.assertEqual(self.dice.doubles_streak, 1)
            self.dice.roll()
            self.assertEqual(self.dice.doubles_streak, 2)

    def test_non_doubles_resets_streak_to_zero(self):
        with patch("random.randint", side_effect=[3, 3, 2, 4]):
            self.dice.roll()   # doubles → streak 1
            self.dice.roll()   # non-doubles → streak 0
            self.assertEqual(self.dice.doubles_streak, 0)

    def test_is_doubles_true_when_equal(self):
        with patch("random.randint", return_value=4):
            self.dice.roll()
        self.assertTrue(self.dice.is_doubles())

    def test_is_doubles_false_when_unequal(self):
        with patch("random.randint", side_effect=[2, 5]):
            self.dice.roll()
        self.assertFalse(self.dice.is_doubles())

    def test_describe_shows_doubles_label(self):
        with patch("random.randint", return_value=3):
            self.dice.roll()
        self.assertIn("DOUBLES", self.dice.describe())

    def test_describe_no_doubles_label_when_not_doubles(self):
        with patch("random.randint", side_effect=[2, 5]):
            self.dice.roll()
        self.assertNotIn("DOUBLES", self.dice.describe())

    def test_dice_can_roll_6(self):
        saw_six = False
        for _ in range(1000):
            self.dice.roll()
            if self.dice.die1 == 6 or self.dice.die2 == 6:
                saw_six = True
                break
        self.assertTrue(saw_six, "A standard die should be able to roll a 6.")

    def test_dice_max_roll_is_12(self):
        max_seen = max(self.dice.roll() for _ in range(2000))
        self.assertEqual(max_seen, 12, "Maximum possible roll from two six-sided dice should be 12.")


# ===========================================================================
# 2. PLAYER
# ===========================================================================
class TestPlayer(unittest.TestCase):
    """Statement, branch, and state coverage for Player."""

    def setUp(self):
        from moneypoly.player import Player
        self.p = Player("Alice")

    # ── add_money / deduct_money ─────────────────────────────────────────────

    def test_add_money_increases_balance(self):
        self.p.add_money(100)
        self.assertEqual(self.p.balance, 1600)

    def test_add_money_zero_unchanged(self):
        self.p.add_money(0)
        self.assertEqual(self.p.balance, 1500)

    def test_add_money_negative_raises(self):
        with self.assertRaises(ValueError):
            self.p.add_money(-1)

    def test_deduct_money_reduces_balance(self):
        self.p.deduct_money(300)
        self.assertEqual(self.p.balance, 1200)

    def test_deduct_money_negative_raises(self):
        with self.assertRaises(ValueError):
            self.p.deduct_money(-50)

    # ── is_bankrupt / net_worth ──────────────────────────────────────────────

    def test_is_bankrupt_false_positive_balance(self):
        self.assertFalse(self.p.is_bankrupt())

    def test_is_bankrupt_true_at_zero(self):
        self.p.balance = 0
        self.assertTrue(self.p.is_bankrupt())

    def test_is_bankrupt_true_negative(self):
        self.p.balance = -100
        self.assertTrue(self.p.is_bankrupt())

    def test_net_worth_equals_balance(self):
        self.assertEqual(self.p.net_worth(), 1500)

    # ── move() ───────────────────────────────────────────────────────────────

    def test_move_ordinary_updates_position(self):
        self.p.position = 5
        self.p.move(3)
        self.assertEqual(self.p.position, 8)

    def test_move_ordinary_no_salary(self):
        before = self.p.balance
        self.p.position = 5
        self.p.move(3)
        self.assertEqual(self.p.balance, before)

    def test_move_lands_exactly_on_go_awards_salary(self):
        from moneypoly.config import GO_SALARY, BOARD_SIZE
        self.p.position = BOARD_SIZE - 3
        before = self.p.balance
        self.p.move(3)
        self.assertEqual(self.p.position, 0)
        self.assertEqual(self.p.balance, before + GO_SALARY)

    def test_passing_go_awards_salary(self):
        from moneypoly.config import GO_SALARY
        self.p.position = 38
        before = self.p.balance
        self.p.move(4)
        self.assertEqual(self.p.position, 2)
        self.assertEqual(self.p.balance, before + GO_SALARY)

    def test_passing_go_awards_salary_alternate_roll(self):
        from moneypoly.config import GO_SALARY
        self.p.position = 37
        before = self.p.balance
        self.p.move(6)
        self.assertEqual(self.p.position, 3)
        self.assertEqual(self.p.balance, before + GO_SALARY)

    # ── go_to_jail ───────────────────────────────────────────────────────────

    def test_go_to_jail_sets_position_and_state(self):
        from moneypoly.config import JAIL_POSITION
        self.p.go_to_jail()
        self.assertEqual(self.p.position, JAIL_POSITION)
        self.assertTrue(self.p.jail_state["in_jail"])
        self.assertEqual(self.p.jail_state["turns"], 0)

    # ── properties ───────────────────────────────────────────────────────────

    def test_add_property_no_duplicate(self):
        from moneypoly.property import Property
        prop = Property("Test", 1, (60, 2), None)
        self.p.add_property(prop)
        self.p.add_property(prop)
        self.assertEqual(len(self.p.properties), 1)

    def test_remove_property_present(self):
        from moneypoly.property import Property
        prop = Property("Test", 1, (60, 2), None)
        self.p.add_property(prop)
        self.p.remove_property(prop)
        self.assertNotIn(prop, self.p.properties)

    def test_remove_property_absent_no_error(self):
        from moneypoly.property import Property
        self.p.remove_property(Property("Ghost", 5, (100, 6), None))

    def test_count_properties(self):
        from moneypoly.property import Property
        for i in range(4):
            self.p.add_property(Property(f"P{i}", i + 1, (60, 2), None))
        self.assertEqual(self.p.count_properties(), 4)

    def test_jail_state_dict_has_required_keys(self):
        for key in ("in_jail", "turns", "cards"):
            self.assertIn(key, self.p.jail_state)


# ===========================================================================
# 3. PROPERTY
# ===========================================================================
class TestProperty(unittest.TestCase):
    """Statement + branch coverage for Property."""

    def setUp(self):
        from moneypoly.property import Property, PropertyGroup
        from moneypoly.player import Player
        self.group  = PropertyGroup("Brown", "brown")
        self.p1     = Property("Mediterranean Ave", 1, (60, 2), self.group)
        self.p2     = Property("Baltic Ave", 3, (60, 4), self.group)
        self.player = Player("Alice")

    def test_rent_no_owner_returns_base_rent(self):
        self.assertEqual(self.p1.get_rent(), 2)

    def test_rent_mortgaged_returns_zero(self):
        self.p1.state["is_mortgaged"] = True
        self.assertEqual(self.p1.get_rent(), 0)

    def test_get_rent_with_full_group_ownership_doubles_rent(self):
        self.p1.state["owner"] = self.player
        self.p2.state["owner"] = self.player
        self.assertEqual(self.p1.get_rent(), 4)

    def test_mortgage_sets_flag_and_returns_payout(self):
        payout = self.p1.mortgage()
        self.assertEqual(payout, 30)
        self.assertTrue(self.p1.state["is_mortgaged"])

    def test_mortgage_already_mortgaged_returns_zero(self):
        self.p1.mortgage()
        self.assertEqual(self.p1.mortgage(), 0)

    def test_unmortgage_returns_correct_cost_and_clears_flag(self):
        self.p1.mortgage()
        cost = self.p1.unmortgage()
        self.assertEqual(cost, 33)
        self.assertFalse(self.p1.state["is_mortgaged"])

    def test_unmortgage_not_mortgaged_returns_zero(self):
        self.assertEqual(self.p1.unmortgage(), 0)

    def test_is_available_unowned_not_mortgaged(self):
        self.assertTrue(self.p1.is_available())

    def test_is_available_false_when_owned(self):
        self.p1.state["owner"] = self.player
        self.assertFalse(self.p1.is_available())

    def test_is_available_false_when_mortgaged(self):
        self.p1.state["is_mortgaged"] = True
        self.assertFalse(self.p1.is_available())


# ===========================================================================
# 4. PROPERTY GROUP
# ===========================================================================
class TestPropertyGroup(unittest.TestCase):

    def setUp(self):
        from moneypoly.property import Property, PropertyGroup
        from moneypoly.player import Player
        self.group  = PropertyGroup("Brown", "brown")
        self.p1     = Property("Mediterranean Ave", 1, (60, 2), self.group)
        self.p2     = Property("Baltic Ave", 3, (60, 4), self.group)
        self.player = Player("Alice")

    def test_all_owned_by_true_when_fully_owned(self):
        self.p1.state["owner"] = self.player
        self.p2.state["owner"] = self.player
        self.assertTrue(self.group.all_owned_by(self.player))

    def test_all_owned_by_false_on_partial_ownership(self):
        from moneypoly.player import Player
        other = Player("Bob")
        self.p1.state["owner"] = self.player
        self.p2.state["owner"] = other
        self.assertFalse(self.group.all_owned_by(self.player))

    def test_all_owned_by_none_player_returns_false(self):
        self.assertFalse(self.group.all_owned_by(None))

    def test_get_owner_counts_returns_correct_distribution(self):
        self.p1.state["owner"] = self.player
        counts = self.group.get_owner_counts()
        self.assertEqual(counts.get(self.player, 0), 1)

    def test_size_returns_property_count(self):
        self.assertEqual(self.group.size(), 2)

    def test_add_property_no_duplicate(self):
        self.group.add_property(self.p1)
        self.assertEqual(self.group.size(), 2)


# ===========================================================================
# 5. BANK
# ===========================================================================
class TestBank(unittest.TestCase):

    def setUp(self):
        from moneypoly.bank import Bank
        from moneypoly.config import BANK_STARTING_FUNDS
        self.bank  = Bank()
        self.start = BANK_STARTING_FUNDS

    def test_initial_balance_correct(self):
        self.assertEqual(self.bank.get_balance(), self.start)

    def test_collect_positive_increases_funds(self):
        self.bank.collect(200)
        self.assertEqual(self.bank.get_balance(), self.start + 200)

    def test_collect_negative_reduces_funds(self):
        self.bank.collect(-100)
        self.assertEqual(self.bank.get_balance(), self.start - 100)

    def test_pay_out_success_reduces_funds(self):
        paid = self.bank.pay_out(500)
        self.assertEqual(paid, 500)
        self.assertEqual(self.bank.get_balance(), self.start - 500)

    def test_pay_out_zero_no_change(self):
        self.assertEqual(self.bank.pay_out(0), 0)
        self.assertEqual(self.bank.get_balance(), self.start)

    def test_pay_out_negative_returns_zero(self):
        self.assertEqual(self.bank.pay_out(-10), 0)

    def test_pay_out_insufficient_raises(self):
        with self.assertRaises(ValueError):
            self.bank.pay_out(self.start + 1)

    def test_give_loan_credits_player(self):
        from moneypoly.player import Player
        p = Player("Alice")
        before = p.balance
        self.bank.give_loan(p, 300)
        self.assertEqual(p.balance, before + 300)
        self.assertEqual(self.bank.loan_count(), 1)
        self.assertEqual(self.bank.total_loans_issued(), 300)

    def test_give_loan_zero_ignored(self):
        from moneypoly.player import Player
        p = Player("Alice")
        before = p.balance
        self.bank.give_loan(p, 0)
        self.assertEqual(p.balance, before)
        self.assertEqual(self.bank.loan_count(), 0)

    def test_give_loan_negative_ignored(self):
        from moneypoly.player import Player
        p = Player("Alice")
        before = p.balance
        self.bank.give_loan(p, -50)
        self.assertEqual(p.balance, before)


# ===========================================================================
# 6. CARD DECK
# ===========================================================================
class TestCardDeck(unittest.TestCase):

    def setUp(self):
        from moneypoly.cards import CardDeck
        self.cards = [{"desc": f"c{i}", "action": "collect", "value": i}
                      for i in range(5)]
        self.deck = CardDeck(self.cards)

    def test_draw_cycles_all_cards_in_order(self):
        drawn = [self.deck.draw() for _ in range(5)]
        self.assertEqual([c["desc"] for c in drawn], ["c0","c1","c2","c3","c4"])

    def test_draw_wraps_to_start_after_exhaustion(self):
        for _ in range(5):
            self.deck.draw()
        self.assertEqual(self.deck.draw()["desc"], "c0")

    def test_peek_does_not_advance_index(self):
        self.assertEqual(self.deck.peek(), self.deck.peek())
        self.assertEqual(self.deck.index, 0)

    def test_reshuffle_resets_index(self):
        self.deck.draw()
        self.deck.draw()
        self.deck.reshuffle()
        self.assertEqual(self.deck.index, 0)

    def test_cards_remaining_decreases_on_draw(self):
        before = self.deck.cards_remaining()
        self.deck.draw()
        self.assertEqual(self.deck.cards_remaining(), before - 1)

    def test_draw_empty_deck_returns_none(self):
        from moneypoly.cards import CardDeck
        self.assertIsNone(CardDeck([]).draw())

    def test_peek_empty_deck_returns_none(self):
        from moneypoly.cards import CardDeck
        self.assertIsNone(CardDeck([]).peek())

    def test_len_equals_card_count(self):
        self.assertEqual(len(self.deck), 5)


# ===========================================================================
# 7. BOARD
# ===========================================================================
class TestBoard(unittest.TestCase):

    def setUp(self):
        from moneypoly.board import Board
        self.board = Board()

    def test_22_properties_exist(self):
        self.assertEqual(len(self.board.properties), 22)

    def test_get_property_at_valid(self):
        prop = self.board.get_property_at(1)
        self.assertIsNotNone(prop)
        self.assertEqual(prop.name, "Mediterranean Avenue")

    def test_get_property_at_special_tile_returns_none(self):
        self.assertIsNone(self.board.get_property_at(0))

    def test_tile_types(self):
        expected = {0: "go", 10: "jail", 5: "railroad",
                    7: "chance", 2: "community_chest", 1: "property", 12: "blank"}
        for pos, tile in expected.items():
            self.assertEqual(self.board.get_tile_type(pos), tile, f"pos {pos}")

    def test_is_purchasable_unowned(self):
        self.assertTrue(self.board.is_purchasable(1))

    def test_is_purchasable_mortgaged_false(self):
        self.board.get_property_at(1).state["is_mortgaged"] = True
        self.assertFalse(self.board.is_purchasable(1))

    def test_is_purchasable_owned_false(self):
        from moneypoly.player import Player
        self.board.get_property_at(1).state["owner"] = Player("Alice")
        self.assertFalse(self.board.is_purchasable(1))

    def test_is_purchasable_special_tile_false(self):
        self.assertFalse(self.board.is_purchasable(0))

    def test_unowned_properties_all_at_start(self):
        self.assertEqual(len(self.board.unowned_properties()), 22)

    def test_properties_owned_by_filters_correctly(self):
        from moneypoly.player import Player
        p = Player("Alice")
        self.board.properties[0].state["owner"] = p
        self.assertEqual(len(self.board.properties_owned_by(p)), 1)

    def test_is_special_tile_true_and_false(self):
        self.assertTrue(self.board.is_special_tile(0))
        self.assertFalse(self.board.is_special_tile(1))


# ===========================================================================
# 8. GAME — CORE MECHANICS
# ===========================================================================
class TestGameCoreMechanics(unittest.TestCase):
    """Tests for Game core mechanics."""

    def setUp(self):
        from moneypoly.game import Game
        self.game  = Game(["Alice", "Bob"])
        self.alice = self.game.players[0]
        self.bob   = self.game.players[1]

    # ── turn management ──────────────────────────────────────────────────────

    def test_current_player_starts_as_first(self):
        self.assertEqual(self.game.current_player().name, "Alice")

    def test_advance_turn_moves_to_next_player(self):
        self.game.advance_turn()
        self.assertEqual(self.game.current_player().name, "Bob")

    def test_advance_turn_wraps_around(self):
        self.game.state["index"] = 1
        self.game.advance_turn()
        self.assertEqual(self.game.state["index"], 0)

    def test_advance_turn_increments_counter(self):
        before = self.game.state["turn"]
        self.game.advance_turn()
        self.assertEqual(self.game.state["turn"], before + 1)

    # ── buy_property ─────────────────────────────────────────────────────────

    def test_buy_property_success_transfers_ownership(self):
        prop = self.game.board.get_property_at(1)
        self.alice.balance = 500
        self.assertTrue(self.game.buy_property(self.alice, prop))
        self.assertEqual(prop.state["owner"], self.alice)
        self.assertIn(prop, self.alice.properties)

    def test_buy_property_insufficient_funds_fails(self):
        prop = self.game.board.get_property_at(1)
        self.alice.balance = 30
        self.assertFalse(self.game.buy_property(self.alice, prop))
        self.assertIsNone(prop.state["owner"])

    def test_buy_property_with_exact_balance_succeeds(self):
        prop = self.game.board.get_property_at(1)
        self.alice.balance = prop.price
        result = self.game.buy_property(self.alice, prop)
        self.assertTrue(result)
        self.assertEqual(prop.state["owner"], self.alice)

    # ── pay_rent ─────────────────────────────────────────────────────────────

    def test_pay_rent_mortgaged_property_no_charge(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        prop.state["is_mortgaged"] = True
        before = self.bob.balance
        self.game.pay_rent(self.bob, prop)
        self.assertEqual(self.bob.balance, before)

    def test_pay_rent_unowned_property_no_charge(self):
        prop = self.game.board.get_property_at(1)
        before = self.bob.balance
        self.game.pay_rent(self.bob, prop)
        self.assertEqual(self.bob.balance, before)

    def test_pay_rent_charges_the_renter(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        before = self.bob.balance
        self.game.pay_rent(self.bob, prop)
        self.assertLess(self.bob.balance, before)

    def test_pay_rent_credits_owner_balance(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        alice_before = self.alice.balance
        bob_before   = self.bob.balance
        self.game.pay_rent(self.bob, prop)
        rent = prop.base_rent
        self.assertEqual(self.bob.balance, bob_before - rent)
        self.assertEqual(self.alice.balance, alice_before + rent)

    # ── mortgage_property ────────────────────────────────────────────────────

    def test_mortgage_property_success(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.alice.add_property(prop)
        before = self.alice.balance
        self.assertTrue(self.game.mortgage_property(self.alice, prop))
        self.assertTrue(prop.state["is_mortgaged"])
        self.assertEqual(self.alice.balance, before + 30)

    def test_mortgage_property_wrong_owner_fails(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.assertFalse(self.game.mortgage_property(self.bob, prop))

    def test_mortgage_property_already_mortgaged_fails(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.alice.add_property(prop)
        self.game.mortgage_property(self.alice, prop)
        self.assertFalse(self.game.mortgage_property(self.alice, prop))

    # ── unmortgage_property ──────────────────────────────────────────────────

    def test_unmortgage_property_success(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.alice.add_property(prop)
        self.game.mortgage_property(self.alice, prop)
        self.alice.balance = 500
        self.assertTrue(self.game.unmortgage_property(self.alice, prop))
        self.assertFalse(prop.state["is_mortgaged"])

    def test_unmortgage_property_wrong_owner_fails(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        prop.state["is_mortgaged"] = True
        self.assertFalse(self.game.unmortgage_property(self.bob, prop))

    def test_unmortgage_property_not_mortgaged_fails(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.alice.add_property(prop)
        self.assertFalse(self.game.unmortgage_property(self.alice, prop))

    def test_unmortgage_insufficient_funds_keeps_mortgage_active(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.alice.add_property(prop)
        self.game.mortgage_property(self.alice, prop)
        self.alice.balance = 1   # cost = $33; player can't pay
        result = self.game.unmortgage_property(self.alice, prop)
        self.assertFalse(result)
        self.assertTrue(prop.state["is_mortgaged"])

    # ── trade ────────────────────────────────────────────────────────────────

    def test_trade_success(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.alice.add_property(prop)
        self.bob.balance = 500
        self.assertTrue(self.game.trade(self.alice, self.bob, prop, 200))
        self.assertEqual(prop.state["owner"], self.bob)

    def test_trade_seller_not_owner_fails(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.bob
        self.assertFalse(self.game.trade(self.alice, self.bob, prop, 50))

    def test_trade_buyer_cannot_afford_fails(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.alice.add_property(prop)
        self.bob.balance = 10
        self.assertFalse(self.game.trade(self.alice, self.bob, prop, 500))

    def test_trade_zero_cash_gift_succeeds(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.alice.add_property(prop)
        self.assertTrue(self.game.trade(self.alice, self.bob, prop, 0))

    # ── find_winner ──────────────────────────────────────────────────────────

    def test_find_winner_no_players_returns_none(self):
        self.game.players.clear()
        self.assertIsNone(self.game.find_winner())

    def test_find_winner_single_player(self):
        self.game.players = [self.alice]
        self.assertEqual(self.game.find_winner().name, "Alice")

    def test_find_winner_returns_player_with_highest_net_worth(self):
        self.alice.balance = 3000
        self.bob.balance   = 200
        winner = self.game.find_winner()
        self.assertEqual(winner.name, "Alice")

    # ── _check_bankruptcy ────────────────────────────────────────────────────

    def test_bankruptcy_eliminates_player_and_releases_properties(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.alice.add_property(prop)
        self.alice.balance = -1
        self.game._check_bankruptcy(self.alice)
        self.assertNotIn(self.alice, self.game.players)
        self.assertIsNone(prop.state["owner"])

    def test_bankruptcy_solvent_player_unaffected(self):
        self.game._check_bankruptcy(self.alice)
        self.assertIn(self.alice, self.game.players)

    def test_bankruptcy_index_wraps_when_last_eliminated(self):
        self.game.state["index"] = 1
        self.bob.balance = -1
        self.game._check_bankruptcy(self.bob)
        self.assertEqual(self.game.state["index"], 0)

    def test_bankruptcy_at_exactly_zero(self):
        self.alice.balance = 0
        self.game._check_bankruptcy(self.alice)
        self.assertNotIn(self.alice, self.game.players)

    # ── _apply_card ──────────────────────────────────────────────────────────

    def test_apply_card_collect_credits_player(self):
        before = self.alice.balance
        self.game._apply_card(self.alice,
                              {"description": "x", "action": "collect", "value": 50})
        self.assertEqual(self.alice.balance, before + 50)

    def test_apply_card_pay_debits_player(self):
        before = self.alice.balance
        self.game._apply_card(self.alice,
                              {"description": "x", "action": "pay", "value": 30})
        self.assertEqual(self.alice.balance, before - 30)

    def test_apply_card_jail_sends_to_jail(self):
        from moneypoly.config import JAIL_POSITION
        self.game._apply_card(self.alice,
                              {"description": "x", "action": "jail", "value": 0})
        self.assertEqual(self.alice.position, JAIL_POSITION)
        self.assertTrue(self.alice.jail_state["in_jail"])

    def test_apply_card_jail_free_increments_count(self):
        before = self.alice.jail_state["cards"]
        self.game._apply_card(self.alice,
                              {"description": "x", "action": "jail_free", "value": 0})
        self.assertEqual(self.alice.jail_state["cards"], before + 1)

    def test_apply_card_none_does_not_crash(self):
        self.game._apply_card(self.alice, None)

    def test_apply_card_collect_from_all(self):
        self.alice.balance = 1500
        self.bob.balance   = 1500
        self.game._apply_card(self.alice,
                              {"description":"x","action":"collect_from_all","value":50})
        self.assertEqual(self.bob.balance, 1450)
        self.assertEqual(self.alice.balance, 1550)

    def test_apply_card_birthday(self):
        self.alice.balance = 1500
        self.bob.balance   = 1500
        self.game._apply_card(self.alice,
                              {"description":"x","action":"birthday","value":10})
        self.assertEqual(self.bob.balance, 1490)
        self.assertEqual(self.alice.balance, 1510)

    # ── _handle_special_tile ─────────────────────────────────────────────────

    def test_income_tax_debits_player(self):
        from moneypoly.config import INCOME_TAX_AMOUNT
        before = self.alice.balance
        self.game._handle_special_tile(self.alice, "income_tax")
        self.assertEqual(self.alice.balance, before - INCOME_TAX_AMOUNT)

    def test_luxury_tax_debits_player(self):
        from moneypoly.config import LUXURY_TAX_AMOUNT
        before = self.alice.balance
        self.game._handle_special_tile(self.alice, "luxury_tax")
        self.assertEqual(self.alice.balance, before - LUXURY_TAX_AMOUNT)

    def test_free_parking_no_balance_change(self):
        before = self.alice.balance
        self.game._handle_special_tile(self.alice, "free_parking")
        self.assertEqual(self.alice.balance, before)

    def test_chance_draws_card(self):
        before = self.game.decks["chance"].index
        self.game._handle_special_tile(self.alice, "chance")
        self.assertEqual(self.game.decks["chance"].index, before + 1)

    def test_community_chest_draws_card(self):
        before = self.game.decks["community"].index
        self.game._handle_special_tile(self.alice, "community_chest")
        self.assertEqual(self.game.decks["community"].index, before + 1)

    # ── _handle_card_move ────────────────────────────────────────────────────

    def test_card_move_forward_no_go_bonus(self):
        self.alice.position = 5
        before = self.alice.balance
        self.game._handle_card_move(self.alice, 10)
        self.assertEqual(self.alice.balance, before)

    def test_card_move_backward_awards_go_salary(self):
        from moneypoly.config import GO_SALARY
        self.alice.position = 30
        before = self.alice.balance
        self.game._handle_card_move(self.alice, 0)
        self.assertEqual(self.alice.balance, before + GO_SALARY)

    # ── auction ──────────────────────────────────────────────────────────────

    def test_auction_no_bids_property_unowned(self):
        prop = self.game.board.get_property_at(1)
        with patch("moneypoly.ui.safe_int_input", return_value=0):
            self.game.auction_property(prop)
        self.assertIsNone(prop.state["owner"])

    def test_auction_winner_owns_property(self):
        prop = self.game.board.get_property_at(1)
        with patch("moneypoly.ui.safe_int_input", side_effect=[100, 0]):
            self.game.auction_property(prop)
        self.assertEqual(prop.state["owner"], self.alice)

    def test_auction_low_bid_rejected(self):
        prop = self.game.board.get_property_at(1)
        # Alice 100, Bob 105 (below 100+10 minimum), Bob passes
        with patch("moneypoly.ui.safe_int_input", side_effect=[100, 105, 0]):
            self.game.auction_property(prop)
        self.assertEqual(prop.state["owner"], self.alice)


# ===========================================================================
# 9. GAME — JAIL INTERACTIONS
# ===========================================================================
class TestGameJailInteractions(unittest.TestCase):
    """Tests for Game methods involving jail logic."""

    def setUp(self):
        from moneypoly.game import Game
        self.game  = Game(["Alice", "Bob"])
        self.alice = self.game.players[0]

    def test_play_turn_when_in_jail_handles_jail_logic(self):
        self.alice.go_to_jail()
        with patch("moneypoly.dice.Dice.roll", return_value=6):
            self.game.play_turn()
        self.assertEqual(self.game.current_player().name, "Bob")

    def test_handle_jail_turn_prompts_for_actions(self):
        self.alice.go_to_jail()
        with patch("moneypoly.ui.confirm", return_value=False):
            self.game._handle_jail_turn(self.alice)
        self.assertEqual(self.alice.jail_state["turns"], 1)


# ===========================================================================
# 10. EDGE CASES & INTEGRATION
# ===========================================================================
class TestEdgeCases(unittest.TestCase):

    def setUp(self):
        from moneypoly.game import Game
        self.game  = Game(["Alice", "Bob"])
        self.alice = self.game.players[0]
        self.bob   = self.game.players[1]

    def test_landing_on_go_to_jail_sends_to_jail(self):
        from moneypoly.config import GO_TO_JAIL_POSITION
        self.game._move_and_resolve(self.alice, GO_TO_JAIL_POSITION)
        self.assertTrue(self.alice.jail_state["in_jail"])

    def test_collect_from_all_skips_player_with_insufficient_balance(self):
        self.alice.balance = 1500
        self.bob.balance   = 5
        self.game._apply_card(self.alice,
            {"description":"x","action":"collect_from_all","value":50})
        self.assertEqual(self.bob.balance, 5)

    def test_birthday_card_player_does_not_pay_themselves(self):
        self.alice.balance = 1000
        self.bob.balance   = 1000
        self.game._apply_card(self.alice,
            {"description":"x","action":"birthday","value":50})
        self.assertNotEqual(self.alice.balance, 950)

    def test_all_22_properties_held_by_one_player(self):
        for prop in self.game.board.properties:
            prop.state["owner"] = self.alice
            self.alice.add_property(prop)
        self.assertEqual(self.alice.count_properties(), 22)

    def test_mortgaged_property_zero_rent_on_landing(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        prop.state["is_mortgaged"] = True
        before = self.bob.balance
        self.game.pay_rent(self.bob, prop)
        self.assertEqual(self.bob.balance, before)

    def test_zero_balance_causes_bankruptcy(self):
        self.alice.balance = 0
        self.game._check_bankruptcy(self.alice)
        self.assertNotIn(self.alice, self.game.players)

    def test_large_add_and_deduct(self):
        self.alice.add_money(1_000_000)
        self.alice.deduct_money(999_999)
        self.assertEqual(self.alice.balance, 1500 + 1)

    def test_bank_exact_balance_pay_out(self):
        remaining = self.game.bank.get_balance()
        self.assertEqual(self.game.bank.pay_out(remaining), remaining)
        self.assertEqual(self.game.bank.get_balance(), 0)

    def test_trade_property_back_and_forth_state_consistent(self):
        prop = self.game.board.get_property_at(1)
        prop.state["owner"] = self.alice
        self.alice.add_property(prop)
        self.bob.balance = 500
        self.game.trade(self.alice, self.bob, prop, 100)
        self.alice.balance = 500
        self.game.trade(self.bob, self.alice, prop, 100)
        self.assertEqual(prop.state["owner"], self.alice)


if __name__ == "__main__":
    unittest.main(verbosity=2)