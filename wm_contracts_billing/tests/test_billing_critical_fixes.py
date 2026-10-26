#############################################################################
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import datetime, time

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_billing')
class TestBillingCriticalFixes(TransactionCase):
    """Regression tests for double invoicing, per-collection pricing, taxes and portal access."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = fields.Date.today()
        cls.period_start = today.replace(day=1) - relativedelta(months=1)
        cls.period_end = today.replace(day=1) - relativedelta(days=1)

        cls.partner = cls.env['res.partner'].create({
            'name': 'Billing Fix Partner',
            'billing_mode': 'consolidated',
        })
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Billing Fix Point',
            'partner_id': cls.partner.id,
        })
        cls.cat_paper = cls.env['wm.waste.category'].create({'name': 'Fix Paper', 'code': 'FXPAP'})
        cls.cat_glass = cls.env['wm.waste.category'].create({'name': 'Fix Glass', 'code': 'FXGLS'})
        cls.tax = cls.env['account.tax'].create({
            'name': 'Fix VAT 10%',
            'amount': 10.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
        })
        cls.prod_paper = cls.env['product.product'].create({
            'name': 'Fix Paper Waste',
            'is_waste_material': True,
            'wm_waste_category_id': cls.cat_paper.id,
            'taxes_id': [(6, 0, cls.tax.ids)],
        })
        cls.prod_glass = cls.env['product.product'].create({
            'name': 'Fix Glass Waste',
            'is_waste_material': True,
            'wm_waste_category_id': cls.cat_glass.id,
            'taxes_id': [(6, 0, cls.tax.ids)],
        })
        cls.sla = cls.env['wm.sla'].create({
            'name': 'Billing Fix SLA',
            'terms_and_conditions': 'Terms',
        })
        cls.contract = cls.env['wm.partner.contract'].create({
            'name': 'WM-BILLING-FIX-001',
            'partner_id': cls.partner.id,
            'sla_id': cls.sla.id,
            'from_date': cls.period_start - relativedelta(months=1),
            'to_date': today + relativedelta(years=1),
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 500.0,
            'overweight_price': 10.0,
            'state': 'ongoing',
        })

    def _create_order(self, day_offset=5, weights=(200.0, 100.0)):
        start = datetime.combine(self.period_start + relativedelta(days=day_offset), time(10, 0))
        end = start + relativedelta(hours=1)
        return self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'contract_id': self.contract.id,
            'scheduled_start': start,
            'scheduled_end': end,
            'actual_start': start,
            'actual_end': end,
            'state': 'completed',
            'order_line_ids': [
                (0, 0, {'category_id': self.cat_paper.id, 'product_id': self.prod_paper.id, 'weight': weights[0]}),
                (0, 0, {'category_id': self.cat_glass.id, 'product_id': self.prod_glass.id, 'weight': weights[1]}),
            ],
        })

    def test_direct_invoice_not_billed_again(self):
        """An order invoiced from its form is excluded from both billing pipelines."""
        order = self._create_order()
        order.action_create_invoice()
        self.assertTrue(order.direct_invoice_id)

        billable = self.env['wm.collection.order']._get_billable_orders(
            self.partner, self.period_start, self.period_end)
        self.assertNotIn(order, billable)

        self.env['wm.consolidated.invoice']._cron_generate_monthly_invoices()
        self.assertFalse(order.consolidated_invoice_id)

    def test_per_collection_fee_charged_once_per_order(self):
        """A per-collection contract bills its fee per order, not per category or per kg."""
        order = self._create_order()
        order.action_create_invoice()
        # 300 kg is under the 500 kg allowance: one collection at 100, no surcharge
        self.assertAlmostEqual(order.direct_invoice_id.amount_untaxed, 100.0)

        orders = self._create_order(day_offset=6) | self._create_order(day_offset=7, weights=(400.0, 200.0))
        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'date_from': self.period_start,
            'date_to': self.period_end,
            'order_ids': [fields.Command.set(orders.ids)],
        })
        consolidated.action_generate_invoice()
        # Each collection is priced on its own weight (never pooled): 2 x 100, plus the
        # second order's 600 kg against its own 500 kg allowance = 100 kg over -> 100
        self.assertAlmostEqual(consolidated.invoice_id.amount_untaxed, 300.0)

    def test_consolidated_invoice_keeps_product_taxes(self):
        """Consolidated invoice lines keep the product's sales taxes."""
        self.contract.with_context(wm_contract_price_override=True).write({'billing_basis': 'category_rate', 'contract_line_ids': [
            (0, 0, {'category_id': self.cat_paper.id, 'price': 2.0}),
            (0, 0, {'category_id': self.cat_glass.id, 'price': 3.0}),
        ]})
        order = self._create_order()
        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'date_from': self.period_start,
            'date_to': self.period_end,
            'order_ids': [fields.Command.set(order.ids)],
        })
        consolidated.action_generate_invoice()
        product_lines = consolidated.invoice_id.invoice_line_ids.filtered(lambda ln: ln.display_type == 'product')
        self.assertTrue(product_lines)
        for line in product_lines:
            self.assertIn(self.tax, line.tax_ids)
        self.assertGreater(consolidated.invoice_id.amount_tax, 0.0)

    def test_event_only_partner_is_invoiced_by_cron(self):
        """A consolidated customer with only billable events still gets invoiced."""
        partner = self.env['res.partner'].create({'name': 'Event Only', 'billing_mode': 'consolidated'})
        event = self.env['wm.billable.event'].create({
            'partner_id': partner.id,
            'event_type': 'emergency_callout',
            'event_date': self.period_start + relativedelta(days=3),
            'price_unit': 75.0,
            'state': 'confirmed',
        })
        self.env['wm.consolidated.invoice']._cron_generate_monthly_invoices()
        self.assertEqual(event.state, 'invoiced')
        self.assertTrue(event.invoice_id)

    def test_portal_user_restricted_to_own_requests(self):
        """Portal users see only their own requests and cannot approve them."""
        portal_user = new_test_user(self.env, login='wm_fix_portal', groups='base.group_portal')
        other = self.env['res.partner'].create({'name': 'Other Customer'})
        Request = self.env['wm.portal.service.request']
        own_point = self.env['wm.collection.point'].create({'name': 'Portal Site', 'partner_id': portal_user.partner_id.id})
        other_point = self.env['wm.collection.point'].create({'name': 'Other Site', 'partner_id': other.id})
        own_req = Request.create({
            'partner_id': portal_user.partner_id.id,
            'collection_point_id': own_point.id,
            'requested_date': fields.Date.today(),
        })
        other_req = Request.create({
            'partner_id': other.id,
            'collection_point_id': other_point.id,
            'requested_date': fields.Date.today(),
        })

        visible = Request.with_user(portal_user).search([])
        self.assertIn(own_req, visible)
        self.assertNotIn(other_req, visible)

        with self.assertRaises(AccessError):
            own_req.with_user(portal_user).action_approve()
