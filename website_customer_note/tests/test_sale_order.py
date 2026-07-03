# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests import TransactionCase, tagged


@tagged('-at_install', 'post_install')
class TestSaleOrderCustomerNote(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Website Note Customer',
        })
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Website Note Pricelist',
            'currency_id': cls.env.company.currency_id.id,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
            'company_id': cls.env.company.id,
            'currency_id': cls.env.company.currency_id.id,
        })

    def test_write_customer_note_updates_sale_order(self):
        result = self.env['sale.order'].write_customer_note(
            self.sale_order.id,
            '  Stored note  ',
        )

        self.assertTrue(result)
        self.sale_order.invalidate_recordset(['customer_note'])
        self.assertEqual(self.sale_order.customer_note, '  Stored note  ')
