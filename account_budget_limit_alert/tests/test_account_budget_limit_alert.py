# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from datetime import date
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAccountBudgetLimitAlert(TransactionCase):
    """Tests for account_budget_limit_alert module.

    The module adds three computed fields to account.move:
        - budget_warning  : warning text (shown on screen)
        - budget_alert    : True when a 'stop' budget line is exceeded
        - alert_message   : popup text
    And overrides action_post() to raise ValidationError when
    budget_alert is True.

    It also adds alert_type (warning / ignore / stop) to budget.lines.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Budget Test Partner',
        })

        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.env.company.id),
        ], limit=1)

        cls.analytic_plan = cls.env['account.analytic.plan'].search([], limit=1)
        if not cls.analytic_plan:
            cls.analytic_plan = cls.env['account.analytic.plan'].create({
                'name': 'Test Plan',
            })

        cls.analytic_stop = cls.env['account.analytic.account'].create({
            'name': 'Analytic Stop Account',
            'plan_id': cls.analytic_plan.id,
        })

        cls.analytic_warning = cls.env['account.analytic.account'].create({
            'name': 'Analytic Warning Account',
            'plan_id': cls.analytic_plan.id,
        })

        # budget.budget requires date_from and date_to (NOT NULL)
        cls.budget = cls.env['budget.budget'].create({
            'name': 'Test Budget',
            'date_from': date(2026, 1, 1),
            'date_to': date(2026, 12, 31),
        })

        cls.budget_post = cls.env['account.budget.post'].create({
            'name': 'Test Budget Position',
            'account_ids': [(4, cls.env['account.account'].search(
                [('account_type', '=', 'expense')], limit=1).id)],
        })
        cls.budget_stop = cls.env['budget.lines'].create({
            'budget_id': cls.budget.id,
            'general_budget_id': cls.budget_post.id,
            'analytic_account_id': cls.analytic_stop.id,
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today(),
            'planned_amount': 100.0,
            'alert_type': 'stop',
        })
        cls.budget_warning = cls.env['budget.lines'].create({
            'budget_id': cls.budget.id,
            'general_budget_id': cls.budget_post.id,
            'analytic_account_id': cls.analytic_warning.id,
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today(),
            'planned_amount': 100.0,
            'alert_type': 'warning',
        })

    def _make_invoice(self, analytic_account=None, price_unit=200.0):
        """Return a draft invoice with one line.

        If analytic_account is given the line carries an analytic_distribution
        so the budget computation is triggered.
        """
        line_vals = {
            'name': 'Test Line',
            'quantity': 1,
            'price_unit': price_unit,
            'account_id': self.income_account.id,
        }
        if analytic_account:
            line_vals['analytic_distribution'] = {
                str(analytic_account.id): 100
            }

        return self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, line_vals)],
        })

    def test_budget_lines_alert_type_field_exists(self):
        """alert_type field must exist on budget.lines."""
        self.assertIn(
            'alert_type',
            self.env['budget.lines']._fields,
            "alert_type field is missing from budget.lines"
        )

    def test_budget_lines_alert_type_stop(self):
        """budget.lines record with alert_type='stop' is stored correctly."""
        self.assertEqual(self.budget_stop.alert_type, 'stop')

    def test_budget_lines_alert_type_warning(self):
        """budget.lines record with alert_type='warning' is stored correctly."""
        self.assertEqual(self.budget_warning.alert_type, 'warning')

    def test_budget_lines_alert_type_ignore(self):
        """budget.lines accepts alert_type='ignore'."""
        analytic = self.env['account.analytic.account'].create({
            'name': 'Analytic Ignore Account',
            'plan_id': self.analytic_plan.id,
        })
        line = self.env['budget.lines'].create({
            'budget_id': self.budget.id,
            'general_budget_id': self.budget_post.id,
            'analytic_account_id': analytic.id,
            'date_from': fields.Date.today(),
            'date_to': fields.Date.today(),
            'planned_amount': 100.0,
            'alert_type': 'ignore',
        })
        self.assertEqual(line.alert_type, 'ignore')

    def test_no_warning_without_analytic_distribution(self):
        """Invoice lines with no analytic_distribution produce no warning."""
        invoice = self._make_invoice(analytic_account=None)
        self.assertFalse(invoice.budget_warning)
        self.assertFalse(invoice.budget_alert)
        self.assertFalse(invoice.alert_message)

    def test_budget_alert_true_when_stop_exceeded(self):
        """budget_alert is True when a stop-type budget line is exceeded."""
        invoice = self._make_invoice(
            analytic_account=self.analytic_stop,
            price_unit=200.0
        )
        self.assertTrue(invoice.budget_alert)

    def test_budget_alert_false_when_stop_not_exceeded(self):
        """budget_alert is False when invoice amount stays within the limit."""
        invoice = self._make_invoice(
            analytic_account=self.analytic_stop,
            price_unit=50.0
        )
        self.assertFalse(invoice.budget_alert)

    def test_alert_message_set_when_stop_exceeded(self):
        """alert_message is populated when a stop budget is exceeded."""
        invoice = self._make_invoice(
            analytic_account=self.analytic_stop,
            price_unit=200.0
        )
        self.assertTrue(invoice.alert_message)
        self.assertIn(
            self.analytic_stop.name,
            invoice.alert_message,
            "alert_message should contain the analytic account name"
        )

    def test_budget_warning_set_when_stop_exceeded(self):
        """budget_warning is also populated for stop-type exceedances."""
        invoice = self._make_invoice(
            analytic_account=self.analytic_stop,
            price_unit=200.0
        )
        self.assertTrue(invoice.budget_warning)
        self.assertIn(self.analytic_stop.name, invoice.budget_warning)

    def test_budget_warning_set_for_warning_type(self):
        """budget_warning is set when a warning-type budget line is exceeded."""
        invoice = self._make_invoice(
            analytic_account=self.analytic_warning,
            price_unit=200.0
        )
        self.assertTrue(invoice.budget_warning)

    def test_budget_alert_false_for_warning_type(self):
        """budget_alert stays False for warning-type — only stop blocks posting."""
        invoice = self._make_invoice(
            analytic_account=self.analytic_warning,
            price_unit=200.0
        )
        self.assertFalse(invoice.budget_alert)

    def test_alert_message_empty_for_warning_type(self):
        """alert_message is NOT set for warning-type (only for stop)."""
        invoice = self._make_invoice(
            analytic_account=self.analytic_warning,
            price_unit=200.0
        )
        self.assertFalse(invoice.alert_message)

    def test_action_post_blocked_when_stop_budget_exceeded(self):
        """action_post() raises ValidationError when budget_alert is True."""
        invoice = self._make_invoice(
            analytic_account=self.analytic_stop,
            price_unit=200.0
        )
        self.assertTrue(invoice.budget_alert,
                        "Pre-condition: budget_alert should be True")
        with self.assertRaises(ValidationError):
            invoice.action_post()

    def test_action_post_allowed_within_stop_budget(self):
        """action_post() succeeds when invoice amount does not exceed limit."""
        invoice = self._make_invoice(
            analytic_account=self.analytic_stop,
            price_unit=50.0
        )
        self.assertFalse(invoice.budget_alert,
                         "Pre-condition: budget_alert should be False")
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_action_post_allowed_for_warning_type_exceeded(self):
        """action_post() succeeds even when a warning-type budget is exceeded."""
        invoice = self._make_invoice(
            analytic_account=self.analytic_warning,
            price_unit=200.0
        )
        self.assertFalse(invoice.budget_alert,
                         "Pre-condition: budget_alert should be False for warning type")
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_action_post_allowed_without_analytic(self):
        """action_post() succeeds for invoice with no analytic distribution."""
        invoice = self._make_invoice(analytic_account=None)
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_validation_error_message_contains_excess_amount(self):
        """The ValidationError message includes the amount that exceeds budget."""
        price = 250.0
        invoice = self._make_invoice(
            analytic_account=self.analytic_stop,
            price_unit=price
        )
        expected_excess = round(price - self.budget_stop.planned_amount, 2)
        try:
            invoice.action_post()
            self.fail("ValidationError was not raised")
        except ValidationError as e:
            self.assertIn(
                str(expected_excess),
                str(e),
                "Error message should contain the excess amount"
            )