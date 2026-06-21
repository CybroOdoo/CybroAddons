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
class TestAccountMoveSignature(TransactionCase):

    def setUp(self):
        super(TestAccountMoveSignature, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.out_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': '2026-01-01',
        })
        self.in_invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': '2026-01-01',
        })

    def test_default_show_sign(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_invoice', 'True')
        self.assertTrue(self.out_invoice._default_show_sign())

    def test_default_enable_sign(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_enable_options_invoice', 'True')
        self.assertTrue(self.out_invoice._default_enable_sign())

    def test_default_show_sign_bill(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_bill', 'True')
        self.assertTrue(self.out_invoice._default_show_sign_bill())

    def test_compute_show_signature(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_invoice', 'True')
        self.out_invoice._compute_show_signature()
        self.assertTrue(self.out_invoice.is_show_signature)

    def test_compute_enable_others(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_enable_options_invoice', 'True')
        self.out_invoice._compute_enable_others()
        self.assertTrue(self.out_invoice.is_enable_others)

    def test_compute_show_sign_bill(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_bill', 'True')
        self.in_invoice._compute_show_sign_bill()
        self.assertTrue(self.in_invoice.is_show_sign_bill)

    def test_action_post_out_invoice_missing_signature(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_confirm_sign_invoice', 'True')
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_invoice', 'True')
        
        self.out_invoice.digital_sign = False
        with self.assertRaises(UserError):
            self.out_invoice.action_post()

    def test_action_post_in_invoice_missing_signature(self):
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_confirm_sign_invoice', 'True')
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_bill', 'True')
        
        self.in_invoice.digital_sign = False
        with self.assertRaises(UserError):
            self.in_invoice.action_post()

    def test_action_post_out_invoice_with_signature(self):
        import base64
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_confirm_sign_invoice', 'True')
        self.env['ir.config_parameter'].sudo().set_param('digital_signature.is_show_digital_sign_invoice', 'True')
        
        self.out_invoice.digital_sign = base64.b64encode(b'signature_data')

        try:
            self.out_invoice.action_post()
        except UserError as e:
            self.assertNotEqual(str(e), 'Signature is missing')
