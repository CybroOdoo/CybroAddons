# -*- coding: utf-8 -*-
##############################################################################
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
###############################################################################
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from unittest.mock import patch


@tagged('post_install', '-at_install')
class TestStockPickingSignature(TransactionCase):

    def setUp(self):
        super(TestStockPickingSignature, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        self.stock_picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })

    def test_default_show_sign(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_inventory', 'True')
        self.assertTrue(self.stock_picking._default_show_sign())

    def test_default_enable_options(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_enable_options_inventory', 'True')
        self.assertTrue(self.stock_picking._default_enable_options())

    def test_compute_show_sign(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_inventory', 'True')
        self.stock_picking._compute_show_sign()
        self.assertTrue(self.stock_picking.is_show_sign)

    def test_compute_enable_option(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_enable_options_inventory', 'True')
        self.stock_picking._compute_enable_option()
        self.assertTrue(self.stock_picking.is_enable_option)

    def test_compute_sign_applicable(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.sign_applicable', 'delivery')
        self.stock_picking._compute_sign_applicable()
        self.assertEqual(self.stock_picking.sign_applicable, 'delivery')

    @patch('odoo.addons.stock.models.stock_picking.StockPicking.button_validate')
    def test_button_validate_missing_signature(self, mock_super_validate):
        mock_super_validate.return_value = True
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_confirm_sign_inventory', 'True')
        self.stock_picking.digital_sign = False
        with self.assertRaisesRegex(UserError, "Signature is missing"):
            self.stock_picking.button_validate()

    @patch('odoo.addons.stock.models.stock_picking.StockPicking.button_validate')
    def test_button_validate_with_signature(self, mock_super_validate):
        mock_super_validate.return_value = True
        import base64
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_confirm_sign_inventory', 'True')
        self.stock_picking.digital_sign = base64.b64encode(b'signature_data')
        try:
            self.stock_picking.button_validate()
        except UserError as e:
            self.assertNotEqual(str(e), 'Signature is missing')
