#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import base64
from unittest.mock import MagicMock, patch

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ...wm_base.controllers import portal
from ...wm_base.controllers.portal import WmSignaturePortal


@tagged('post_install', '-at_install')
class TestWmCollectionOrderLineSecurity(TransactionCase):
    """Test suite verifying security fixes for wm.collection.order.line ACLs and record rules,
    and sign_now authorization on collection orders.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WmSignaturePortal()

        # Regular internal user with no waste management permissions
        cls.user_internal = cls.env['res.users'].create({
            'name': 'Internal Only User Line',
            'login': 'user_internal_only_line',
            'email': 'internal_only_line@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        # Driver 1
        cls.driver_partner_1 = cls.env['res.partner'].create({'name': 'Driver 1 Partner Line'})
        cls.user_driver_1 = cls.env['res.users'].create({
            'name': 'Driver 1 User Line',
            'login': 'user_driver_1_line',
            'partner_id': cls.driver_partner_1.id,
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('wm_base.group_wm_driver').id,
            ])],
        })

        # Driver 2
        cls.driver_partner_2 = cls.env['res.partner'].create({'name': 'Driver 2 Partner Line'})
        cls.user_driver_2 = cls.env['res.users'].create({
            'name': 'Driver 2 User Line',
            'login': 'user_driver_2_line',
            'partner_id': cls.driver_partner_2.id,
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('wm_base.group_wm_driver').id,
            ])],
        })

        # Template
        cls.template = cls.env['wm.signature.template'].create({
            'name': 'Test Contract Template Line',
            'document': base64.b64encode(b'%PDF-1.4 test template pdf content'),
            'document_filename': 'test_template.pdf',
        })

        # Customer & point
        cls.partner_customer = cls.env['res.partner'].create({'name': 'Customer Test Line'})
        cls.collection_point = cls.env['wm.collection.point'].create({
            'name': 'Point Test Line',
            'partner_id': cls.partner_customer.id,
        })
        cls.waste_cat = cls.env['wm.waste.category'].create({
            'name': 'Plastic Waste Line',
            'code': 'PLAS-LINE',
        })

        # Routes for Driver 1 and Driver 2
        cls.route_1 = cls.env['wm.route'].create({
            'name': 'Route 1 Line',
            'driver_id': cls.driver_partner_1.id,
        })
        cls.route_2 = cls.env['wm.route'].create({
            'name': 'Route 2 Line',
            'driver_id': cls.driver_partner_2.id,
        })

        # Orders for Driver 1 and Driver 2
        cls.order_1 = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner_customer.id,
            'collection_point_id': cls.collection_point.id,
            'route_id': cls.route_1.id,
            'state': 'dispatched',
        })
        cls.order_2 = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner_customer.id,
            'collection_point_id': cls.collection_point.id,
            'route_id': cls.route_2.id,
            'state': 'dispatched',
        })

    def _mock_request_user(self, user):
        mock_req = MagicMock()
        mock_req.env = self.env(user=user)
        mock_req.not_found.return_value = '404_NOT_FOUND'
        mock_req.make_response.side_effect = lambda data, headers: (data, headers)
        mock_req.render.side_effect = lambda template_name, qcontext: (template_name, qcontext)
        return mock_req

    def test_01_collection_order_line_access_restricted_from_base_user(self):
        """Fix #5: wm.collection.order.line is read-only for general internal users (base.group_user)."""
        order_line_model_user = self.env['wm.collection.order.line'].with_user(self.user_internal)
        with self.assertRaises(AccessError):
            order_line_model_user.create({
                'order_id': self.order_1.id,
                'category_id': self.waste_cat.id,
                'weight': 50.0,
            })

    def test_02_driver_order_line_record_rule_enforcement(self):
        """Fix #5: Driver can edit order lines on their own assigned orders, but not on others'."""
        line_order_1 = self.env['wm.collection.order.line'].create({
            'order_id': self.order_1.id,
            'category_id': self.waste_cat.id,
            'weight': 100.0,
        })
        line_order_2 = self.env['wm.collection.order.line'].create({
            'order_id': self.order_2.id,
            'category_id': self.waste_cat.id,
            'weight': 200.0,
        })

        # Driver 1 can write to line on their own order (order_1)
        line_order_1.with_user(self.user_driver_1).write({'weight': 120.0})
        self.assertEqual(line_order_1.weight, 120.0)

        # Driver 1 attempting to write to line on Driver 2's order (order_2) must raise AccessError
        with self.assertRaises(AccessError):
            line_order_2.with_user(self.user_driver_1).write({'weight': 999.0})

    def test_03_sign_now_verifies_target_document_access(self):
        """Fix #2: template_sign_now requires user to have write access to the order."""
        mock_driver_1 = self._mock_request_user(self.user_driver_1)
        # Driver 1 attempts to sign Driver 2's collection order -> rejected
        with patch.object(portal, 'request', mock_driver_1):
            res = self.controller.template_sign_now(self.template.id, order_id=self.order_2.id)
            self.assertFalse(res.get('success'))
            self.assertIn('not authorized', res.get('error', '').lower())

        # Driver 1 signing their own order -> authorized
        with patch.object(portal, 'request', mock_driver_1):
            res_ok = self.controller.template_sign_now(self.template.id, order_id=self.order_1.id)
            self.assertTrue(res_ok.get('success'))
            self.assertTrue(res_ok.get('redirect_url'))
