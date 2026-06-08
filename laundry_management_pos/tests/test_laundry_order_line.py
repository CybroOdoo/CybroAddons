# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tests.common import TransactionCase

class TestLaundryOrderLine(TransactionCase):

    def setUp(self):
        super(TestLaundryOrderLine, self).setUp()
        self.laundry_person = self.env['res.users'].create({
            'name': 'Laundry Person',
            'login': 'laundry_person_line',
            'email': 'laundry_line@example.com',
            'group_ids': [(4, self.env.ref('base.group_user').id)],
        })
        self.washing_type = self.env['washing.type'].create({
            'name': 'Test Wash',
            'amount': 50,
            'assigned_person_id': self.laundry_person.id,
        })
        self.partner = self.env['res.partner'].create({'name': 'Test'})
        self.laundry_order = self.env['laundry.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'laundry_person_id': self.laundry_person.id,
        })

    def test_compute_price_tax(self):
        """Test _compute_price_tax"""
        line = self.env['laundry.order.line'].create({
            'laundry_id': self.laundry_order.id,
            'product_id': self.env['product.product'].create({'name': 'Test'}).id,
            'qty': 1,
            'washing_type_id': self.washing_type.id,
        })
        tax = self.env['account.tax'].create({
            'name': 'Test Tax',
            'amount': 10,
        })
        line.tax_ids = [(4, tax.id)]
        line._compute_price_tax()
        self.assertEqual(line.price_tax, 5.0)
        self.assertEqual(line.washing_type_id.name, 'Test Wash')
