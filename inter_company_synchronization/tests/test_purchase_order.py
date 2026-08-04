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
from odoo.tests.common import TransactionCase
from odoo import Command


class TestPurchaseOrderInterCompany(TransactionCase):
    """Test suite for the purchase.order model inter-company integration."""

    @classmethod
    def setUpClass(cls):
        super(TestPurchaseOrderInterCompany, cls).setUpClass()
        
        # Enable the synchronization configuration parameter
        cls.env['ir.config_parameter'].sudo().set_param(
            'inter_company_synchronization.sale_purchase_sync', 'True')

        # Ensure a transit location exists
        cls.transit_location = cls.env['stock.location'].search(
            [('active', '=', True), ('usage', '=', 'transit')], limit=1)
        if not cls.transit_location:
            cls.transit_location = cls.env['stock.location'].create({
                'name': 'Test Transit',
                'usage': 'transit',
                'active': True
            })
            
        # Create two companies
        cls.company_a = cls.env['res.company'].create({'name': 'Company A'})
        cls.company_b = cls.env['res.company'].create({'name': 'Company B'})
        
        # Ensure they have partner_ids
        cls.partner_a = cls.company_a.partner_id
        cls.partner_b = cls.company_b.partner_id
        
        # Create a product
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.product = cls.env['product.product'].create({
            'name': 'Inter-Company Product PO',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
        })

    def test_purchase_order_creates_sale_order(self):
        """Test that confirming a purchase order in Company A creates a sale order in Company B."""
        # Create PO in Company A from Partner B (meaning Company A is buying from Company B)
        po = self.env['purchase.order'].with_company(self.company_a).create({
            'partner_id': self.partner_b.id,
            'company_id': self.company_a.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_qty': 15.0,
                    'price_unit': 45.0,
                })
            ]
        })
        
        # Confirm PO
        po.button_confirm()
        
        # Check if SO was created
        so = self.env['sale.order'].search([('client_order_ref', '=', po.name)])
        self.assertTrue(so, "A Sale Order should have been created")
        self.assertEqual(so.company_id.id, self.company_b.id, "SO should belong to Company B")
        self.assertEqual(so.partner_id.id, self.partner_a.id, "SO customer should be Company A")
        
        # Check SO lines
        self.assertEqual(len(so.order_line), 1)
        so_line = so.order_line[0]
        self.assertEqual(so_line.product_id.id, self.product.id)
        self.assertEqual(so_line.product_uom_qty, 15.0)
        self.assertEqual(so_line.price_unit, 45.0)

    def test_purchase_order_skips_creation_if_origin(self):
        """Test that inter-company sync is skipped if origin is provided."""
        po = self.env['purchase.order'].with_company(self.company_a).create({
            'partner_id': self.partner_b.id,
            'company_id': self.company_a.id,
            'origin': 'SO-9999',
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_qty': 5.0,
                    'price_unit': 50.0,
                })
            ]
        })
        po.button_confirm()
        
        so = self.env['sale.order'].search([('client_order_ref', '=', po.name)])
        self.assertFalse(so, "SO should not be created if origin is set")

    def test_purchase_order_section_and_note_lines(self):
        """Test syncing PO lines that are sections or notes."""
        po = self.env['purchase.order'].with_company(self.company_a).create({
            'partner_id': self.partner_b.id,
            'company_id': self.company_a.id,
            'order_line': [
                Command.create({
                    'display_type': 'line_section',
                    'name': 'Test Section',
                    'product_qty': 0.0,
                    'price_unit': 0.0,
                }),
                Command.create({
                    'display_type': 'line_note',
                    'name': 'Test Note',
                    'product_qty': 0.0,
                    'price_unit': 0.0,
                })
            ]
        })
        po.button_confirm()
        
        so = self.env['sale.order'].search([('client_order_ref', '=', po.name)])
        self.assertTrue(so)
        self.assertEqual(len(so.order_line), 2)
        self.assertEqual(so.order_line[0].display_type, 'line_section')
        self.assertEqual(so.order_line[0].name, 'Test Section')
        self.assertEqual(so.order_line[1].display_type, 'line_note')
        self.assertEqual(so.order_line[1].name, 'Test Note')
