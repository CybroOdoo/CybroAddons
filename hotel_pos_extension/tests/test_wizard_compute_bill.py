# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install')
class TestWizardComputeBill(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Wizard Partner'})
        cls.pricelist = cls.env['product.pricelist'].create({'name': 'Test Pricelist'})
        cls.booking = cls.env['room.booking'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
        })
        cls.session = cls.env['pos.session'].search([('state', '=', 'opened')], limit=1)
        if not cls.session:
            pos_config = cls.env['pos.config'].search([], limit=1)
            cls.session = cls.env['pos.session'].create({
                'config_id': pos_config.id if pos_config else False,
                'user_id': cls.env.user.id,
            })

    def test_compute_bill_wizard_computations(self):
        """Test wizard populating folio details and processing print action."""
        # Create an associated POS order
        order = self.env['pos.order'].create({
            'session_id': self.session.id,
            'partner_id': self.partner.id,
            'booking_id': self.booking.id,
            'amount_total': 300.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'state': 'draft',
        })
        
        wizard = self.env['compute.bill'].create({
            'booking_id': self.booking.id,
            'bill_type': 'combined',
        })
        
        # Trigger depends manually/via standard read or compute
        wizard._compute_folio_lines()
        wizard._compute_orders()
        
        self.assertIn(order, wizard.pos_order_ids)
        self.assertEqual(wizard.partner_id, self.partner)

    def test_action_print_bill(self):
        """Test the report action returned by print button."""
        wizard = self.env['compute.bill'].create({
            'booking_id': self.booking.id,
            'bill_type': 'combined',
        })
        action = wizard.action_print_bill()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'hotel_pos_extension.report_combined_bill')
