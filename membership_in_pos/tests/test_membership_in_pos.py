# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distribute d in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from datetime import timedelta
from odoo import fields
from odoo.tests import common, tagged
from odoo.tests.common import mute_logger
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install')
class TestMembershipInPos(common.TransactionCase):
    """Test cases for the membership_in_pos module.

    Covers:
        - customer.membership CRUD and uniqueness constraint
        - membership.card lifecycle (draft → confirm → cancel → draft)
        - Code generation and validation
        - Validity and expiry date computation
        - membership_card_check RPC method
        - res.config.settings get/set values
        - POS session model extension (_load_pos_data_models)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Customer membership types ──────────────────────────────────────────
        cls.membership_gold = cls.env['customer.membership'].create({
            'name': 'Gold',
        })
        cls.membership_silver = cls.env['customer.membership'].create({
            'name': 'Silver',
        })

        # ── Partners ───────────────────────────────────────────────────────────
        cls.partner_alice = cls.env['res.partner'].create({
            'name': 'Alice Test',
            'email': 'alice@test.com',
        })
        cls.partner_bob = cls.env['res.partner'].create({
            'name': 'Bob Test',
            'email': 'bob@test.com',
        })

        # ── Membership product (reuse pos_discount consumable if available) ───
        try:
            cls.membership_product = cls.env.ref(
                'pos_discount.product_product_consumable')
        except Exception:
            cls.membership_product = cls.env['product.product'].create({
                'name': 'Membership Discount',
                'type': 'service',
                'available_in_pos': True,
                'sale_ok': True,
            })

        # Store the product id in ir.config_parameter (mirrors set_values)
        cls.env['ir.config_parameter'].sudo().set_param(
            'pos_membership_product_id', cls.membership_product.id)

        # ── Dates ──────────────────────────────────────────────────────────────
        cls.today = fields.Date.today()
        cls.future_date = cls.today + timedelta(days=180)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. CustomerMembership model
    # ─────────────────────────────────────────────────────────────────────────

    def test_01_customer_membership_creation(self):
        """CustomerMembership record is created with correct defaults."""
        self.assertEqual(self.membership_gold.name, 'Gold')
        self.assertEqual(self.membership_gold.default_period, 1.0,
                         "Default validity period should be 1 year")

    def test_02_customer_membership_unique_name(self):
        """Duplicate membership names must raise a constraint error."""
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.cr.savepoint():
                    self.env['customer.membership'].create({'name': 'Gold'})

    # ─────────────────────────────────────────────────────────────────────────
    # 2. MembershipCard – creation and field defaults
    # ─────────────────────────────────────────────────────────────────────────

    def test_03_membership_card_creation_defaults(self):
        """MembershipCard is created in draft state with correct defaults."""
        partner = self.env['res.partner'].create({'name': 'Test Defaults'})
        card = self.env['membership.card'].create({
            'membership_id': self.membership_gold.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,
            'discount': 10.0,
        })
        self.assertEqual(card.state, 'draft',
                         "Newly created card should be in draft state")
        self.assertFalse(card.code, "Code should be empty before generation")
        self.assertFalse(card.membership_code_button,
                         "Code button flag should be False initially")

    def test_04_membership_card_unique_customer(self):
        """A customer cannot have more than one membership card."""
        partner = self.env['res.partner'].create({'name': 'Test Unique Card'})
        self.env['membership.card'].create({
            'membership_id': self.membership_gold.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,
            'discount': 10.0,
        })
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.cr.savepoint():
                    self.env['membership.card'].create({
                        'membership_id': self.membership_silver.id,
                        'customer_id': partner.id,
                        'expiry_date': self.future_date,
                        'discount': 5.0,
                    })

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Code generation
    # ─────────────────────────────────────────────────────────────────────────

    def test_05_generate_code(self):
        """generate_code() populates the code field and sets the button flag."""
        partner = self.env['res.partner'].create({'name': 'Test Generate Code'})
        card = self.env['membership.card'].create({
            'membership_id': self.membership_gold.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,
            'discount': 15.0,
        })
        card.generate_code()
        self.assertTrue(card.code, "Code should be set after generate_code()")
        self.assertTrue(card.code.startswith('550'),
                        "Generated code must start with '550'")
        self.assertTrue(card.membership_code_button,
                        "membership_code_button should be True after code generation")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. State transitions
    # ─────────────────────────────────────────────────────────────────────────

    def _make_confirmed_card(self, partner, membership, discount=10.0):
        """Helper: create a card, generate code and confirm it."""
        card = self.env['membership.card'].create({
            'membership_id': membership.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,
            'discount': discount,
        })
        card.generate_code()
        card.action_membership_confirm()
        return card

    def test_06_confirm_without_code_raises(self):
        """Confirming a card without a code should raise UserError."""
        partner = self.env['res.partner'].create({'name': 'Test No Code Confirm'})
        card = self.env['membership.card'].create({
            'membership_id': self.membership_silver.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,
            'discount': 5.0,
        })
        with self.assertRaises(UserError):
            card.action_membership_confirm()

    def test_07_confirm_with_code(self):
        """After generating code and confirming, state must be 'confirm'."""
        # Use partner_alice (unique customer constraint, so use fresh partner)
        partner = self.env['res.partner'].create({'name': 'Test Confirm'})
        card = self._make_confirmed_card(partner, self.membership_gold)
        self.assertEqual(card.state, 'confirm')

    def test_08_cancel_membership(self):
        """action_membership_canceled() should move state to 'cancel'."""
        partner = self.env['res.partner'].create({'name': 'Test Cancel'})
        card = self._make_confirmed_card(partner, self.membership_gold)
        card.action_membership_canceled()
        self.assertEqual(card.state, 'cancel')

    def test_09_reset_to_draft(self):
        """action_reset_to_draft() should move state back to 'draft'."""
        partner = self.env['res.partner'].create({'name': 'Test Reset'})
        card = self._make_confirmed_card(partner, self.membership_gold)
        card.action_membership_canceled()
        card.action_reset_to_draft()
        self.assertEqual(card.state, 'draft')

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Validity computation
    # ─────────────────────────────────────────────────────────────────────────

    def test_10_compute_validity(self):
        """_compute_validity() returns correct number of days between dates."""
        issue = self.today
        expiry = self.today + timedelta(days=90)
        partner = self.env['res.partner'].create({'name': 'Test Validity'})
        card = self.env['membership.card'].create({
            'membership_id': self.membership_silver.id,
            'customer_id': partner.id,
            'issue_date': issue,
            'expiry_date': expiry,
            'discount': 5.0,
        })
        self.assertEqual(card.validity, 90.0,
                         "Validity should be 90 days")

    def test_11_compute_validity_no_dates(self):
        """Validity should be 0 when dates are not set."""
        partner = self.env['res.partner'].create({'name': 'Test No Dates'})
        card = self.env['membership.card'].create({
            'membership_id': self.membership_silver.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,
            'discount': 5.0,
        })
        # Manually clear the issue_date to test edge case
        card.write({'issue_date': False})
        card._compute_validity()
        self.assertEqual(card.validity, 0.0)

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Expiry date onchange validation
    # ─────────────────────────────────────────────────────────────────────────

    def test_12_onchange_expiry_date_past_raises(self):
        """Setting expiry_date in the past should raise ValidationError."""
        partner = self.env['res.partner'].create({'name': 'Test Past Expiry'})
        card = self.env['membership.card'].create({
            'membership_id': self.membership_gold.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,
            'discount': 10.0,
        })
        card.expiry_date = self.today - timedelta(days=1)
        with self.assertRaises(ValidationError):
            card._onchange_expiry_date()

    def test_13_onchange_expiry_date_exceeds_one_year_raises(self):
        """Expiry date more than 1 year from issue date should raise ValidationError."""
        from dateutil.relativedelta import relativedelta
        partner = self.env['res.partner'].create({'name': 'Test Over Year'})
        card = self.env['membership.card'].create({
            'membership_id': self.membership_gold.id,
            'customer_id': partner.id,
            'issue_date': self.today,
            'expiry_date': self.future_date,
            'discount': 10.0,
        })
        card.expiry_date = self.today + relativedelta(years=1, days=1)
        with self.assertRaises(ValidationError):
            card._onchange_expiry_date()

    # ─────────────────────────────────────────────────────────────────────────
    # 7. membership_card_check RPC method
    # ─────────────────────────────────────────────────────────────────────────

    def test_14_membership_card_check_valid(self):
        """membership_card_check returns correct info for a valid card/code."""
        partner = self.env['res.partner'].create({'name': 'Test Check Valid'})
        discount_val = 20.0
        card = self.env['membership.card'].create({
            'membership_id': self.membership_gold.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,
            'discount': discount_val,
        })
        card.generate_code()
        card.action_membership_confirm()

        result = self.env['membership.card'].membership_card_check([{
            'customer': partner.id,
            'customerInput': card.code,
        }])

        self.assertIsInstance(result, dict,
                              "Should return a dict for a valid card")
        self.assertEqual(result['customer_name'], partner.name)
        self.assertEqual(result['membership'], self.membership_gold.name)
        self.assertEqual(result['discount'], discount_val)
        self.assertEqual(result['product_id'], self.membership_product.id)

    def test_15_membership_card_check_invalid_code(self):
        """membership_card_check returns 0 for a wrong code."""
        partner = self.env['res.partner'].create({'name': 'Test Check Invalid'})
        self.env['membership.card'].create({
            'membership_id': self.membership_silver.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,
            'discount': 5.0,
        })

        result = self.env['membership.card'].membership_card_check([{
            'customer': partner.id,
            'customerInput': 'WRONG_CODE_99999',
        }])
        self.assertEqual(result, 0,
                         "Should return 0 for an invalid/unmatched code")

    def test_16_membership_card_check_expired_card(self):
        """membership_card_check returns 0 for an expired card."""
        partner = self.env['res.partner'].create({'name': 'Test Expired'})
        # Create card with a past expiry date directly in DB (bypass onchange)
        past_date = self.today - timedelta(days=10)
        card = self.env['membership.card'].create({
            'membership_id': self.membership_gold.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,  # start valid
            'discount': 10.0,
        })
        card.generate_code()
        card.action_membership_confirm()
        # Force-set past expiry directly (bypass onchange validation)
        self.env.cr.execute(
            "UPDATE membership_card SET expiry_date = %s WHERE id = %s",
            (past_date, card.id)
        )
        card.invalidate_recordset()

        result = self.env['membership.card'].membership_card_check([{
            'customer': partner.id,
            'customerInput': card.code,
        }])
        self.assertEqual(result, 0,
                         "Expired card should return 0")

    def test_17_membership_card_check_unconfirmed_card(self):
        """membership_card_check returns 0 for a draft (unconfirmed) card."""
        partner = self.env['res.partner'].create({'name': 'Test Unconfirmed'})
        card = self.env['membership.card'].create({
            'membership_id': self.membership_gold.id,
            'customer_id': partner.id,
            'expiry_date': self.future_date,
            'discount': 10.0,
        })
        card.generate_code()
        # Do NOT confirm — state remains 'draft'

        result = self.env['membership.card'].membership_card_check([{
            'customer': partner.id,
            'customerInput': card.code,
        }])
        self.assertEqual(result, 0,
                         "Draft card should not be valid for discount")

    # ─────────────────────────────────────────────────────────────────────────
    # 8. res.config.settings – get_values / set_values
    # ─────────────────────────────────────────────────────────────────────────

    def test_18_config_settings_set_and_get_values(self):
        """set_values() persists params; get_values() retrieves them."""
        config = self.env['res.config.settings'].create({
            'is_pos_module_pos_membership': True,
        })
        config.pos_membership_product_id = self.membership_product.id
        config.set_values()

        # Now read back via get_values
        result = config.get_values()
        self.assertTrue(result.get('is_pos_module_pos_membership'),
                        "is_pos_module_pos_membership should be True after set_values")
        self.assertEqual(result.get('pos_membership_product_id'),
                         self.membership_product.id,
                         "Product id should be persisted correctly")

    def test_19_config_settings_product_not_in_pos_raises(self):
        """set_values() raises UserError when product is not available in POS."""
        product_not_in_pos = self.env['product.product'].create({
            'name': 'Not In POS Product',
            'type': 'service',
            'available_in_pos': False,
        })
        config = self.env['res.config.settings'].create({
            'is_pos_module_pos_membership': True,
        })
        config.pos_membership_product_id = product_not_in_pos.id
        with self.assertRaises(UserError):
            config.set_values()

    def test_20_config_settings_membership_disabled_clears_product(self):
        """Disabling pos membership should clear the membership product field."""
        config = self.env['res.config.settings'].create({
            'is_pos_module_pos_membership': False,
        })
        # Trigger compute
        config._compute_pos_membership_discount_product_id()
        self.assertFalse(config.pos_membership_product_id,
                         "Product should be cleared when membership is disabled")

    # ─────────────────────────────────────────────────────────────────────────
    # 9. POS Session – _load_pos_data_models extension
    # ─────────────────────────────────────────────────────────────────────────

    def test_21_pos_session_loads_res_config_settings(self):
        """_load_pos_data_models includes res.config.settings from this module."""
        # We need a pos.config to call the method
        pos_config = self.env['pos.config'].search([], limit=1)
        if not pos_config:
            self.skipTest("No POS config found; skipping POS session test")

        result = self.env['pos.session']._load_pos_data_models(pos_config.id)
        self.assertIn('res.config.settings', result,
                      "'res.config.settings' should be included in POS data models")

    # ─────────────────────────────────────────────────────────────────────────
    # 10. res.config.settings – _load_pos_data_fields
    # ─────────────────────────────────────────────────────────────────────────

    def test_22_load_pos_data_fields_includes_membership_flag(self):
        """_load_pos_data_fields includes is_pos_module_pos_membership."""
        pos_config = self.env['pos.config'].search([], limit=1)
        if not pos_config:
            self.skipTest("No POS config found; skipping POS data fields test")

        result = self.env['res.config.settings']._load_pos_data_fields(
            pos_config.id)
        self.assertIn('is_pos_module_pos_membership', result,
                      "'is_pos_module_pos_membership' must be loaded for POS")
