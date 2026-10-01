# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo.tests import common


class TestPickingInvoice(common.TransactionCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Test Data setup
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner'
        })
        
        # Fetch test accounts
        cls.company = cls.env.user.company_id
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'), ('company_ids', 'in', cls.company.id)
        ], limit=1)
        cls.expense_account = cls.env['account.account'].search([
            ('account_type', '=', 'expense'), ('company_ids', 'in', cls.company.id)
        ], limit=1)
        
        # Odoo 19 uses 'consu' type for general consumable without stock tracking
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'lst_price': 100.0,
            'property_account_income_id': cls.income_account.id if cls.income_account else False,
            'property_account_expense_id': cls.expense_account.id if cls.expense_account else False,
        })
        
        # Get or Create Sales Journal
        cls.sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'), ('company_id', '=', cls.company.id)
        ], limit=1)
        if not cls.sale_journal:
            cls.sale_journal = cls.env['account.journal'].create({
                'name': 'Sales Test Journal',
                'type': 'sale',
                'code': 'STJ',
                'company_id': cls.company.id,
                'nacha_entry_class_code': 'CCD',
            })
        
        # Get or Create Purchase Journal
        cls.purchase_journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'), ('company_id', '=', cls.company.id)
        ], limit=1)
        if not cls.purchase_journal:
            cls.purchase_journal = cls.env['account.journal'].create({
                'name': 'Purchase Test Journal',
                'type': 'purchase',
                'code': 'PTJ',
                'company_id': cls.company.id,
                'nacha_entry_class_code': 'CCD',
            })
        
        # Set config params
        cls.env['ir.config_parameter'].sudo().set_param(
            'stock_move_invoice.customer_journal_id', cls.sale_journal.id)
        cls.env['ir.config_parameter'].sudo().set_param(
            'stock_move_invoice.vendor_journal_id', cls.purchase_journal.id)

    def _create_picking(self, picking_type_code):
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', picking_type_code),
            ('company_id', 'in', [self.company.id, False])
        ], limit=1)
        
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
        })
        
        # Odoo 19: do not pass 'name' to stock.move
        self.env['stock.move'].create({
            'picking_id': picking.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        return picking

    def test_01_create_customer_invoice(self):
        """Test creating an invoice from an outgoing picking"""
        picking = self._create_picking('outgoing')
        
        # Validate picking
        picking.action_confirm()
        picking.button_validate()
        
        # Generate Invoice
        invoice = picking.action_create_invoice()
        
        self.assertTrue(invoice, "Invoice should be created")
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.partner_id.id, self.partner.id)
        self.assertEqual(picking.invoice_count, 1)

    def test_02_create_vendor_bill(self):
        """Test creating a vendor bill from an incoming picking"""
        picking = self._create_picking('incoming')
        
        # Validate picking
        picking.action_confirm()
        picking.button_validate()
        
        # Generate Bill
        bill = picking.action_create_bill()
        
        self.assertTrue(bill, "Vendor bill should be created")
        self.assertEqual(bill.move_type, 'in_invoice')
        self.assertEqual(bill.partner_id.id, self.partner.id)
        self.assertEqual(picking.invoice_count, 1)
