# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase

class TestPickingInvoiceWizard(TransactionCase):
    def setUp(self):
        super(TestPickingInvoiceWizard, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu', 'is_storable': True,
            'lst_price': 100.0,
        })
        self.picking_type_out = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        self.location_src = self.picking_type_out.default_location_src_id
        self.location_dest = self.picking_type_out.default_location_dest_id
        
        self.picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'state': 'done',
        })
        self.env['stock.move'].create({
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': 1.0,
            'quantity': 1.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'picking_id': self.picking.id,
            'state': 'done',
        })
        
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        self.env['ir.config_parameter'].sudo().set_param('stock_move_invoice.customer_journal_id', journal.id)

    def test_picking_multi_invoice(self):
        wizard = self.env['picking.invoice.wizard'].with_context(active_ids=[self.picking.id]).create({})
        wizard.picking_multi_invoice()
        
        # Verify invoice was created
        self.picking._compute_invoice_count()
        self.assertEqual(self.picking.invoice_count, 1)
