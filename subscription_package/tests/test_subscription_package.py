# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo import fields
from datetime import timedelta

class TestSubscriptionPackage(TransactionCase):
    """Test Subscription Package Model"""

    def setUp(self):
        """Setup test variables"""
        super(TestSubscriptionPackage, self).setUp()
        self.SubPackage = self.env['subscription.package']
        self.Partner = self.env['res.partner']
        self.Plan = self.env['subscription.package.plan']
        self.Stage = self.env['subscription.package.stage']

        if not self.env.company.country_id:
            self.env.company.country_id = self.env.ref('base.us')

        self.sale_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        if not self.sale_journal:
            self.sale_journal = self.env['account.journal'].create({
                'name': 'Customer Invoices',
                'code': 'INV',
                'type': 'sale',
                'company_id': self.env.company.id,
            })
        self.income_account = self.env['account.account'].search([
            ('account_type', 'in', ('income', 'income_other')),
            ('company_ids', 'in', self.env.company.id)
        ], limit=1)
        if not self.income_account:
            self.income_account = self.env['account.account'].create({
                'name': 'Test Income Account',
                'code': 'INCTEST',
                'account_type': 'income',
                'company_ids': [(6, 0, [self.env.company.id])],
            })
        if not self.sale_journal.default_account_id:
            self.sale_journal.default_account_id = self.income_account

        self.receivable_account = self.env['account.account'].search([
            ('account_type', '=', 'asset_receivable'),
            ('company_ids', 'in', self.env.company.id)
        ], limit=1)
        if not self.receivable_account:
            self.receivable_account = self.env['account.account'].create({
                'name': 'Test Receivable Account',
                'code': 'RECTEST',
                'account_type': 'asset_receivable',
                'company_ids': [(6, 0, [self.env.company.id])],
            })

        self.partner = self.Partner.create({
            'name': 'Test Partner',
            'property_account_receivable_id': self.receivable_account.id,
        })
        if hasattr(self.env.company.partner_id, 'property_account_receivable_id'):
            self.env.company.partner_id.property_account_receivable_id = self.receivable_account
        self.plan = self.Plan.create({
            'name': 'Monthly Plan',
            'renewal_value': '1',
            'renewal_period': 'months',
            'limit_choice': 'ones',
            'journal_id': self.sale_journal.id,
        })
        self.draft_stage = self.Stage.search([('category', '=', 'draft')], limit=1) or self.Stage.create({'name': 'Draft', 'category': 'draft', 'sequence': 1})
        self.progress_stage = self.Stage.search([('category', '=', 'progress')], limit=1) or self.Stage.create({'name': 'In Progress', 'category': 'progress', 'sequence': 2})
        self.closed_stage = self.Stage.search([('category', '=', 'closed')], limit=1) or self.Stage.create({'name': 'Closed', 'category': 'closed', 'sequence': 3})

    def test_button_start_date(self):
        """Test starting a subscription package"""
        product = self.env['product.product'].create({'name': 'Sub Product', 'is_subscription': True})
        sub = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'product_line_ids': [(0, 0, {
                'product_id': product.id,
                'product_qty': 1,
                'unit_price': 100.0
            })]
        })
        
        self.assertEqual(sub.stage_id, self.draft_stage)
        sub.button_start_date()
        
        self.assertEqual(sub.stage_id, self.progress_stage)
        self.assertEqual(sub.date_started, fields.Date.today())
        self.assertEqual(sub.start_date, fields.Date.today())

    def test_button_start_date_empty(self):
        """Test starting a subscription without products should fail"""
        sub = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id
        })
        with self.assertRaises(UserError):
            sub.button_start_date()

    def test_button_sale_order(self):
        """Test manually creating a sale order from subscription"""
        product = self.env['product.product'].create({'name': 'Sub Product', 'is_subscription': True})
        sub = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'product_line_ids': [(0, 0, {
                'product_id': product.id,
                'product_qty': 1,
                'unit_price': 100.0
            })]
        })
        
        sub.button_sale_order()
        self.assertTrue(sub.sale_order_id)
        self.assertEqual(sub.sale_order_id.partner_id, self.partner)
        self.assertEqual(len(sub.sale_order_id.order_line), 1)

    def test_close_limit_cron(self):
        """Test cron logic for renewal and closing"""
        product = self.env['product.product'].create({
            'name': 'Sub Product',
            'is_subscription': True,
            'property_account_income_id': self.income_account.id,
        })
        self.partner.email = 'customer@test.com'
        self.env.company.email = 'company@test.com'
        today = fields.Date.today()
        start = today - timedelta(days=28)
        sub = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'product_line_ids': [(0, 0, {
                'product_id': product.id,
                'product_qty': 1,
                'unit_price': 100.0
            })],
            'stage_id': self.progress_stage.id,
            'start_date': start,
            'date_started': start,
        })
        self.assertEqual(sub.next_invoice_date, today)

        # Execute close_limit_cron
        sub.close_limit_cron()

        # Check invoice was generated in draft state
        moves = self.env['account.move'].search([('subscription_id', '=', sub.id)])
        self.assertTrue(moves, "An invoice should have been created for the subscription.")
        self.assertEqual(moves.state, 'draft')
        self.assertEqual(moves.move_type, 'out_invoice')
        self.assertEqual(moves.journal_id, self.sale_journal)
        self.assertEqual(sub.start_date, today)

        # Test limit exceeded condition: when today == end_date
        sub.write({
            'date_started': today - timedelta(days=sub.plan_id.days_to_end),
            'start_date': today,
            'stage_id': self.progress_stage.id,
            'is_closed': False,
        })
        sub.close_limit_cron()
        self.assertTrue(sub.is_closed, "Subscription should be closed when renewal limit is exceeded.")
        self.assertEqual(sub.stage_id.category, 'closed')

    def test_product_line_company_tax_filtering(self):
        """Case 1: When selecting a product, only taxes belonging to that subscription's company are taken"""
        country = self.env.ref('base.us')
        company_a = self.env['res.company'].create({'name': 'Company A', 'country_id': country.id})
        company_b = self.env['res.company'].create({'name': 'Company B', 'country_id': country.id})
        tax_group_a = self.env['account.tax.group'].create({'name': 'Tax Group A', 'company_id': company_a.id, 'country_id': country.id})
        tax_group_b = self.env['account.tax.group'].create({'name': 'Tax Group B', 'company_id': company_b.id, 'country_id': country.id})
        tax_a = self.env['account.tax'].create({
            'name': 'Tax 10% A',
            'amount': 10.0,
            'company_id': company_a.id,
            'country_id': country.id,
            'tax_group_id': tax_group_a.id,
            'type_tax_use': 'sale',
        })
        tax_b = self.env['account.tax'].create({
            'name': 'Tax 20% B',
            'amount': 20.0,
            'company_id': company_b.id,
            'country_id': country.id,
            'tax_group_id': tax_group_b.id,
            'type_tax_use': 'sale',
        })
        product = self.env['product.product'].create({
            'name': 'Multi-Company Tax Product',
            'is_subscription': True,
            'taxes_id': [(6, 0, [tax_a.id, tax_b.id])],
        })

        sub_a = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'company_id': company_a.id,
        })
        line = self.env['subscription.package.product.line'].create({
            'subscription_id': sub_a.id,
            'product_id': product.id,
        })
        self.assertIn(tax_a, line.tax_ids)
        self.assertNotIn(tax_b, line.tax_ids)

    def test_subscription_customer_action_context(self):
        """Case 2: Contacts created through subscription customers view have boolean true and are listed"""
        action = self.env.ref('subscription_package.res_partner_action')
        context = safe_eval(str(action.context)) if isinstance(action.context, str) else (action.context or {})
        self.assertTrue(context.get('default_is_subscription_customer'))
        self.assertTrue(context.get('default_is_active_subscription'))

        # Create partner using action context
        partner = self.Partner.with_context(context).create({'name': 'Sub Customer Via Action'})
        self.assertTrue(partner.is_subscription_customer)
        self.assertTrue(partner.is_active_subscription)

        # Check partner is found in action domain
        domain = safe_eval(str(action.domain)) if isinstance(action.domain, str) else (action.domain or [])
        found_partner = self.Partner.search(domain + [('id', '=', partner.id)])
        self.assertEqual(found_partner, partner)

    def test_order_customer_selection_domain(self):
        """Case 3: Only subscription customers are selected inside order/subscription"""
        sub_partner = self.Partner.create({
            'name': 'Regular Sub Customer',
            'is_subscription_customer': True,
        })
        regular_partner = self.Partner.create({
            'name': 'Regular Non-Sub Customer',
            'is_subscription_customer': False,
            'is_active_subscription': False,
        })

        field_domain = self.SubPackage._fields['partner_id'].domain
        domain = safe_eval(str(field_domain)) if isinstance(field_domain, str) else (field_domain or [])
        allowed_partners = self.Partner.search(domain + [('id', 'in', [sub_partner.id, regular_partner.id])])
        self.assertIn(sub_partner, allowed_partners)
        self.assertNotIn(regular_partner, allowed_partners)

    def test_account_move_subscription_origin(self):
        """Test account move creation with subscription sale order origin"""
        product = self.env['product.product'].create({
            'name': 'Origin Sub Product',
            'is_subscription': True,
            'property_account_income_id': self.income_account.id,
        })
        sub = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'start_date': fields.Date.today(),
            'product_line_ids': [(0, 0, {
                'product_id': product.id,
                'product_qty': 1,
                'unit_price': 100.0,
            })]
        })
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_subscription': True,
            'subscription_id': sub.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })]
        })
        sub.sale_order_id = so
        old_next_date = sub.next_invoice_date

        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_date_due': fields.Date.today(),
            'invoice_origin': so.name,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': 1,
                'price_unit': 100.0,
                'account_id': self.income_account.id,
            })],
        })
        self.assertTrue(move.is_subscription)
        self.assertEqual(move.subscription_id, sub)
        self.assertEqual(sub.start_date, old_next_date)

    def test_subscription_buttons_and_actions(self):
        """Test button_invoice_count, button_sale_count, button_close, set_close, and action_renew"""
        product = self.env['product.product'].create({
            'name': 'Button Sub Product',
            'is_subscription': True,
            'property_account_income_id': self.income_account.id,
        })
        sub = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'product_line_ids': [(0, 0, {
                'product_id': product.id,
                'product_qty': 2,
                'unit_price': 50.0,
            })]
        })
        # Test invoice count and button
        sub._compute_invoice_count()
        act_inv = sub.button_invoice_count()
        self.assertEqual(act_inv['res_model'], 'account.move')

        # Test sale count and button
        sub._compute_sale_count()
        act_sale = sub.button_sale_count()
        self.assertEqual(act_sale['res_model'], 'sale.order')

        # Test button close wizard action
        act_close = sub.button_close()
        self.assertEqual(act_close['res_model'], 'subscription.close')

        # Test set_close
        sub.set_close()
        self.assertEqual(sub.stage_id.category, 'closed')
        self.assertFalse(sub.is_to_renew)

        # Test action_renew
        sub.action_renew()
        self.assertTrue(sub.sale_order_id)

    def test_button_start_date_with_sale_order_and_multiple_draft_stages(self):
        """Test button_start_date error with multiple draft stages and link with sale order"""
        product = self.env['product.product'].create({
            'name': 'Start Sub Product',
            'is_subscription': True,
        })
        sub = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'product_line_ids': [(0, 0, {
                'product_id': product.id,
                'product_qty': 1,
                'unit_price': 100.0,
            })]
        })
        # Create second draft stage to test UserError
        second_draft = self.Stage.create({'name': 'Draft 2', 'category': 'draft'})
        try:
            with self.assertRaises(UserError):
                sub.button_start_date()
        finally:
            second_draft.unlink()

        # Link sale order and test start date
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 3,
                'price_unit': 100.0,
            })]
        })
        sub.sale_order_id = so
        sub.button_start_date()
        self.assertEqual(sub.stage_id.category, 'progress')
        self.assertTrue(so.is_subscription)
        self.assertEqual(so.subscription_id, sub)
        line = so.order_line.filtered(lambda x: x.product_template_id.is_subscription)
        self.assertEqual(line.qty_to_invoice, 3)

    def test_subscription_naming_combinations(self):
        """Test _compute_name under various combinations"""
        product = self.env['product.product'].create({
            'name': 'Name Test Product',
            'is_subscription': True,
        })
        plan_with_code = self.Plan.create({
            'name': 'Standard Plan',
            'short_code': 'STD',
            'renewal_value': '1',
            'renewal_period': 'months',
        })
        # 1. short_code, reference_code, and partner_id.name
        sub1 = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': plan_with_code.id,
            'reference_code': 'REF01',
            'product_line_ids': [(0, 0, {'product_id': product.id})],
        })
        self.assertEqual(sub1.name, f"STD/REF01-{self.partner.name}")

        # 2. reference_code and partner_id.name without short_code
        plan_no_code = self.Plan.create({
            'name': 'No Code',
            'renewal_value': '1',
            'renewal_period': 'months',
        })
        plan_no_code.short_code = False
        sub2 = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': plan_no_code.id,
            'reference_code': 'REF02',
            'product_line_ids': [(0, 0, {'product_id': product.id})],
        })
        self.assertEqual(sub2.name, f"REF02-{self.partner.name}")

        # 3. Only partner_id.name or default fallback
        sub3 = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': plan_no_code.id,
            'product_line_ids': [(0, 0, {'product_id': product.id})],
        })
        # Default reference_code is generated, so name has f"{ref}-{partner_name}"
        self.assertEqual(sub3.name, f"{sub3.reference_code}-{self.partner.name}")

        # When reference_code is cleared
        sub3.reference_code = False
        sub3._compute_name()
        self.assertEqual(sub3.name, self.partner.name)

        # When partner is also empty
        sub3.partner_id = False
        sub3._compute_name()
        self.assertEqual(sub3.name, 'Subscription')

    def test_subscription_tax_and_total_recurring_price(self):
        """Test recurring price calculation with tax and product line compute methods"""
        country = self.env.company.country_id or self.env.ref('base.us')
        tax_group = self.env['account.tax.group'].search([('company_id', '=', self.env.company.id)], limit=1)
        if not tax_group:
            tax_group = self.env['account.tax.group'].create({
                'name': 'Test Tax Group',
                'company_id': self.env.company.id,
                'country_id': country.id,
            })
        elif not tax_group.country_id:
            tax_group.country_id = country.id
        tax = self.env['account.tax'].create({
            'name': '10% Tax',
            'amount': 10.0,
            'company_id': self.env.company.id,
            'country_id': country.id,
            'tax_group_id': tax_group.id,
            'type_tax_use': 'sale',
        })
        product = self.env['product.product'].create({
            'name': 'Taxed Sub Product',
            'is_subscription': True,
            'taxes_id': [(6, 0, [tax.id])],
        })
        sub = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'product_line_ids': [(0, 0, {
                'product_id': product.id,
                'product_qty': 2,
                'unit_price': 100.0,
                'discount': 10.0,
            })]
        })
        line = sub.product_line_ids[0]
        # Unit price = 100, discount = 10% -> 90 * 2 = 180 total_amount
        self.assertEqual(line.total_amount, 180.0)
        self.assertEqual(line.price_tax, 18.0)
        self.assertEqual(line.price_total, 198.0)

        # Subscription totals
        sub._compute_total_recurring_price()
        self.assertEqual(sub.total_recurring_price, 180.0)
        self.assertEqual(sub.tax_total, 18.0)
        self.assertEqual(sub.total_with_tax, 198.0)

        # Test empty product line tax_ids compute fallback
        empty_line = self.env['subscription.package.product.line'].new({'product_id': False, 'company_id': False})
        empty_line._compute_tax_ids()
        self.assertFalse(empty_line.tax_ids)

    def test_read_group_stage_ids_and_find_renew_date(self):
        """Test _read_group_stage_ids and find_renew_date with end = 0"""
        stages = self.SubPackage._read_group_stage_ids(self.Stage, [])
        self.assertTrue(len(stages) >= 3)

        sub = self.SubPackage.create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
        })
        today = fields.Date.today()
        dates = sub.find_renew_date(today, False, 0)
        self.assertEqual(dates['end_date'], today)
        self.assertEqual(dates['close_date'], today)

        # Hit branch when next_invoice is False
        dates_no_next = sub.find_renew_date(False, today, 10)
        self.assertTrue(dates_no_next['end_date'])

        # Test _inverse_next_invoice_date
        sub.start_date = today
        future_date = today + timedelta(days=56)
        sub.next_invoice_date = future_date
        sub._inverse_next_invoice_date()
        self.assertEqual(sub.start_date, future_date - timedelta(days=self.plan.renewal_time))
