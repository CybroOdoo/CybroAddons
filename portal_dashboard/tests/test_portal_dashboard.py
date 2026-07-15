# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Megha A P (odoo@cybrosys.com)
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
from odoo.tests import common

class TestPortalDashboard(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal User Test',
            'login': 'portal_user_test',
            'email': 'portal_user_test@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Internal User Test',
            'login': 'internal_user_test',
            'email': 'internal_user_test@example.com',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('account.group_account_invoice').id,
            ])],
        })
        cls.partner = cls.portal_user.partner_id
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.portal_user.id,
            'state': 'sale',
        })
        cls.quotation = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.portal_user.id,
            'state': 'sent',
        })
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.portal_user.id,
            'state': 'purchase',
        })
        cls.rfq = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.portal_user.id,
            'state': 'sent',
        })
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'test line',
                'quantity': 1.0,
                'price_unit': 100.0,
            })]
        })
        cls.invoice.action_post()

    def test_datafetch_portal_user(self):
        data_model = self.env['portal.dashboard.data'].with_user(self.portal_user)
        res = data_model.datafetch()
        self.assertEqual(res['target'][0], 1)
        self.assertEqual(res['target'][1], 1)
        self.assertEqual(res['target_po'][0], 1)
        self.assertEqual(res['target_po'][1], 1)
        self.assertEqual(res['target_accounting'][0], 1)

    def test_datafetch_internal_user(self):
        data_model = self.env['portal.dashboard.data'].with_user(self.internal_user)
        res = data_model.datafetch()
        self.assertEqual(res['target'][0], 0)
        self.assertEqual(res['target'][1], 0)
        self.assertEqual(res['target_po'][0], 0)
        self.assertEqual(res['target_po'][1], 0)
        self.assertGreaterEqual(res['target_accounting'][0], 1)

    def test_config_settings(self):
        settings = self.env['res.config.settings'].create({
            'is_show_recent_so_q': True,
            'sale_count': 5,
        })
        settings.execute()
        param_show = self.env['ir.config_parameter'].sudo().get_param('portal_dashboard.is_show_recent_so_q')
        param_count = self.env['ir.config_parameter'].sudo().get_param('portal_dashboard.sale_count')
        self.assertEqual(param_show, 'True')
        self.assertEqual(int(param_count), 5)
