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


@tagged('post_install', '-at_install')
class TestPurchaseOrderSignature(TransactionCase):

    def setUp(self):
        super(TestPurchaseOrderSignature, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Vendor'})
        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })

    def test_default_show_sign(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_po', 'True')
        self.assertTrue(self.purchase_order._default_show_sign())

    def test_default_enable_sign(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_enable_options_po', 'True')
        self.assertTrue(self.purchase_order._default_enable_sign())

    def test_compute_show_signature(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_po', 'True')
        self.purchase_order._compute_show_signature()
        self.assertTrue(self.purchase_order.is_show_signature)

    def test_compute_enable_others(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_enable_options_po', 'True')
        self.purchase_order._compute_enable_others()
        self.assertTrue(self.purchase_order.is_enable_others)

    def test_button_confirm_missing_signature(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_confirm_sign_po', 'True')
        self.purchase_order.digital_sign = False
        with self.assertRaisesRegex(UserError, "Signature is missing"):
            self.purchase_order.button_confirm()

    def test_button_confirm_with_signature(self):
        import base64
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_confirm_sign_po', 'True')
        self.purchase_order.digital_sign = base64.b64encode(b'signature_data')
        try:
            self.purchase_order.button_confirm()
        except UserError as e:
            self.assertNotEqual(str(e), 'Signature is missing')
