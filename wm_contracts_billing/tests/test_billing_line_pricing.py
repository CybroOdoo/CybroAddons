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
from datetime import datetime, time, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_billing')
class TestBillingLinePricing(TransactionCase):
    """Order and line totals follow the contract's billing basis, like invoicing does."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = fields.Date.today()
        cls.partner = cls.env['res.partner'].create({'name': 'Line Pricing Customer', 'email': 'lp@example.com'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Line Pricing Point', 'partner_id': cls.partner.id})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Line Pricing Waste', 'code': 'LNPRC'})
        cls.sla = cls.env['wm.sla'].create({'name': 'Line Pricing SLA', 'terms_and_conditions': 'Terms'})
        cls.contract = cls.env['wm.partner.contract'].create({
            'name': 'WM-LINE-PRICING',
            'partner_id': cls.partner.id,
            'sla_id': cls.sla.id,
            'from_date': today - relativedelta(months=1),
            'to_date': today + relativedelta(years=1),
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 500.0,
            'overweight_price': 10.0,
            'state': 'ongoing',
        })

    def _order(self, weight):
        start = datetime.combine(fields.Date.today(), time(9, 0))
        return self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'contract_id': self.contract.id,
            'scheduled_start': start,
            'scheduled_end': start + timedelta(hours=1),
            'actual_start': start,
            'actual_end': start + timedelta(hours=1),
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': weight})],
        })

    def test_per_collection_contract_totals(self):
        """A per-collection fee is charged once per order, not per kg."""
        order = self._order(450.0)
        line = order.order_line_ids
        self.assertEqual(line.price_basis, 'contract_fee')
        self.assertEqual(line.price, 0.0)
        self.assertEqual(line.total_amount, 0.0)
        self.assertAlmostEqual(order.total_amount, 100.0)

        heavy = self._order(650.0)
        # 150 kg above the 500 kg allowance: 15 x 10 surcharge
        self.assertAlmostEqual(heavy.total_amount, 250.0)

    def test_order_total_matches_direct_invoice(self):
        """The order total and its invoice use the same fee calculation."""
        order = self._order(650.0)
        order.action_create_invoice()
        self.assertAlmostEqual(order.direct_invoice_id.amount_untaxed, order.total_amount)

    def test_category_rate_contract_is_per_kg(self):
        """Per-category contract rates stay per-kg prices."""
        self.contract.with_context(wm_contract_price_override=True).write({'billing_basis': 'category_rate', 'contract_line_ids': [
            (0, 0, {'category_id': self.category.id, 'price': 2.0}),
        ]})
        order = self._order(300.0)
        line = order.order_line_ids
        self.assertEqual(line.price_basis, 'per_kg')
        self.assertEqual(line.price, 2.0)
        self.assertAlmostEqual(order.total_amount, 600.0)

    def test_draft_contract_link_only_while_sending(self):
        """A draft contract only exposes its signing link in the send email."""
        contract = self.contract.copy({'name': 'WM-LINE-PRICING-DRAFT', 'state': 'draft',
                                       'from_date': fields.Date.today() + relativedelta(years=2),
                                       'to_date': fields.Date.today() + relativedelta(years=3)})
        role = self.env['wm.signature.role'].search([], limit=1) or self.env['wm.signature.role'].create({'name': 'Customer'})
        template = self.env['wm.signature.template'].create({'name': 'LP Template', 'role_ids': [(6, 0, role.ids)]})
        request = self.env['wm.signature.request'].create({
            'template_id': template.id,
            'reference_doc': f'wm.partner.contract,{contract.id}',
            'signer_ids': [(0, 0, {'partner_id': self.partner.id, 'role_id': role.id})],
        })
        request.state = 'sent'
        self.assertEqual(contract.get_portal_signature_url(), '')
        self.assertTrue(contract.with_context(mark_contract_as_sent=True).get_portal_signature_url())

    def test_route_admin_buttons_hidden_from_drivers(self):
        """Optimize Route and Change Driver are not offered to pure drivers."""
        driver = new_test_user(self.env, login='lp_driver', groups='wm_base.group_wm_driver')
        arch = self.env['wm.route'].with_user(driver).get_views([(False, 'form')])['views']['form']['arch']
        self.assertNotIn('action_optimize_route', arch)
        self.assertNotIn('action_change_driver_wizard', arch)
