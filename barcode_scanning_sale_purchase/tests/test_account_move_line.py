# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Fansa Jabeen A (odoo@cybrosys.com)
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
################################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAccountMoveLineBarcode(TransactionCase):
    """Test cases for account.move.line barcode scanning."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Test Invoice Product',
            'barcode': 'invoice_prod_123',
        })
        self.move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })

    def test_onchange_barcode_scan(self):
        """Test _onchange_barcode_scan method directly."""
        line = self.env['account.move.line'].new({
            'move_id': self.move.id,
            'barcode_scan': 'invoice_prod_123',
        })
        self.assertFalse(line.product_id)
        line._onchange_barcode_scan()
        self.assertEqual(line.product_id, self.product)

    def test_onchange_barcode_scan_invalid(self):
        """Test _onchange_barcode_scan with non-existent barcode."""
        line = self.env['account.move.line'].new({
            'move_id': self.move.id,
            'barcode_scan': 'non_existent_barcode',
        })
        line._onchange_barcode_scan()
        self.assertFalse(line.product_id)
