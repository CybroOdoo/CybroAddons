# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests.common import TransactionCase


class TestInterCompany(TransactionCase):
    """Test the inter company sale and purchase synchronization."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env['res.company'].create({'name': 'Company A'})
        cls.company_b = cls.env['res.company'].create({'name': 'Company B'})
        cls.partner_a = cls.company_a.partner_id
        cls.partner_b = cls.company_b.partner_id
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })
        cls.env['ir.config_parameter'].sudo().set_param(
            'inter_company_synchronization.sale_purchase_sync', 'True')
        # The synchronization requires an active transit location.
        if not cls.env['stock.location'].search(
                [('usage', '=', 'transit')], limit=1):
            cls.env['stock.location'].create({
                'name': 'Test Inter Company Transit',
                'usage': 'transit',
            })

    def _create_purchase_order(self, partner):
        """Return a purchase order of company A for the given vendor."""
        return self.env['purchase.order'].with_company(
            self.company_a).create({
                'partner_id': partner.id,
                'company_id': self.company_a.id,
                'order_line': [(0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 10,
                    'price_unit': 100,
                })],
            })

    def test_01_po_creates_so(self):
        """Confirming a PO creates a SO in the vendor company."""
        po = self._create_purchase_order(self.partner_b)
        po.button_confirm()
        so = self.env['sale.order'].search(
            [('client_order_ref', '=', po.name)])
        self.assertTrue(so, "Sale Order was not created")
        self.assertEqual(so.company_id, self.company_b)
        self.assertEqual(so.partner_id, self.partner_a)
        self.assertEqual(len(so.order_line), 1)
        self.assertEqual(so.order_line.product_id, self.product)

    def test_02_so_creates_po(self):
        """Confirming a SO creates a PO in the customer company."""
        so = self.env['sale.order'].with_company(self.company_a).create({
            'partner_id': self.partner_b.id,
            'company_id': self.company_a.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
                'price_unit': 50,
            })],
        })
        so.action_confirm()
        po = self.env['purchase.order'].search([('origin', '=', so.name)])
        self.assertTrue(po, "Purchase Order was not created")
        self.assertEqual(po.company_id, self.company_b)
        self.assertEqual(po.partner_id, self.partner_a)
        self.assertEqual(len(po.order_line), 1)
        self.assertEqual(po.order_line.product_id, self.product)

    def test_03_regular_vendor_creates_no_so(self):
        """Confirming a PO for a non-company vendor creates no SO."""
        vendor = self.env['res.partner'].create({'name': 'Regular Vendor'})
        po = self._create_purchase_order(vendor)
        po.button_confirm()
        so = self.env['sale.order'].search(
            [('client_order_ref', '=', po.name)])
        self.assertFalse(so)
