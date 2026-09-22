# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.info)
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
from unittest.mock import patch

class TestPosReceiptUI(TransactionCase):

    def setUp(self):
        super(TestPosReceiptUI, self).setUp()
        self.pos_receipt = self.env['pos.receipt'].create({
            'name': 'Test Receipt',
            'design_receipt': '<xml>Test Design</xml>',
            'design_receipt_font_style': 'Verdana',
            'qr_size': 150,
            'qr_position': 'left',
            'selected_product_fields': '["name", "qty"]'
        })
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test POS shop',
            'receipt_design_id': self.pos_receipt.id
        })
        self.partner = self.env['res.partner'].search([], limit=1)
        self.product = self.env['product.product'].search([('available_in_pos', '=', True)], limit=1)
        if not self.product:
            product_vals = {
                'name': 'Test Product',
                'list_price': 100.0,
                'available_in_pos': True,
            }
            if 'publish_date' in self.env['product.template']._fields:
                product_vals['publish_date'] = '2026-06-08'
            self.product = self.env['product.product'].create(product_vals)

    def test_01_receipt_creation(self):
        self.assertEqual(self.pos_receipt.name, 'Test Receipt')
        self.assertEqual(self.pos_receipt.design_receipt, '<xml>Test Design</xml>')
        self.assertEqual(self.pos_receipt.design_receipt_font_style, 'Verdana')

    def test_02_receipt_defaults(self):
        new_receipt = self.env['pos.receipt'].create({'name': 'Default Receipt'})
        self.assertEqual(new_receipt.design_receipt_font_style, 'Arial')
        self.assertEqual(new_receipt.qr_size, 120)
        self.assertEqual(new_receipt.qr_position, 'center')

    def test_03_receipt_client_action(self):
        action = self.pos_receipt.action_open_receipt_layout()
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'pos_receipt_layout_client_action')
        self.assertEqual(action['params']['receipt_id'], self.pos_receipt.id)

    def test_04_pos_config_integration(self):
        self.assertEqual(self.pos_config.receipt_design_id, self.pos_receipt)
        self.assertEqual(self.pos_config.design_receipt, '<xml>Test Design</xml>')
        self.assertEqual(self.pos_config.design_receipt_font_style, 'Verdana')

    def test_05_pos_config_compute_fields(self):
        self.pos_config._compute_selected_product_fields()
        self.assertEqual(self.pos_config.selected_product_fields, '["name", "qty"]')

    def test_06_pos_config_client_action(self):
        action = self.pos_config.action_open_receipt_editor()
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'pos_receipt_layout_client_action')
        self.assertEqual(action['params']['receipt_id'], self.pos_receipt.id)

    def test_07_pos_order_qr_generation(self):
        pos_order = self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'partner_id': self.partner.id,
            'session_id': self.env['pos.session'].create({
                'config_id': self.pos_config.id,
                'user_id': self.env.user.id
            }).id,
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })
        pos_order.generate_custom_qr()
        self.assertTrue(pos_order.custom_receipt_token)
        self.assertTrue(pos_order.custom_qr_image)

    def test_08_pos_order_paid_auto_qr(self):
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
            'user_id': self.env.user.id
        })
        pos_order = self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'partner_id': self.partner.id,
            'session_id': session.id,
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
        })
        pos_order.action_pos_order_paid()
        self.assertTrue(pos_order.custom_receipt_token)
        self.assertTrue(pos_order.custom_qr_image)

    def test_09_pos_session_ui_models(self):
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
            'user_id': self.env.user.id
        })

        with patch('odoo.addons.point_of_sale.models.pos_session.PosSession._pos_ui_models_to_load', create=True, return_value=[]):
            models = session._pos_ui_models_to_load()
            self.assertIn('pos.receipt', models)
            params = session._loader_params_pos_receipt()
            self.assertIn('design_receipt', params['search_params']['fields'])

