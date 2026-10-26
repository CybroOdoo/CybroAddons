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
from odoo.http import Response
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..controllers import portal
from ..controllers.portal import WmSignaturePortal


@tagged('post_install', '-at_install')
class TestWmSignatureSecurity(TransactionCase):
    """Test suite verifying security fixes for signature controller routes (wm_base)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WmSignaturePortal()

        # Regular internal user with no signature manager permissions
        cls.user_internal = cls.env['res.users'].create({
            'name': 'Internal Only User Sig',
            'login': 'user_internal_only_sig',
            'email': 'internal_only_sig@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        # Signature Manager user
        cls.user_sig_mgr = cls.env['res.users'].create({
            'name': 'Signature Manager User',
            'login': 'user_sig_mgr',
            'email': 'sig_mgr@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('wm_base.group_signature_manager').id,
            ])],
        })

        # Template
        cls.template = cls.env['wm.signature.template'].create({
            'name': 'Test Contract Template Base',
            'document': base64.b64encode(b'%PDF-1.4 test template pdf content'),
            'document_filename': 'test_template.pdf',
        })

    def _mock_request_user(self, user):
        mock_req = MagicMock()
        mock_req.env = self.env(user=user)
        mock_req.not_found.side_effect = lambda: Response('Not Found', status=404)
        mock_req.make_response.side_effect = lambda data, headers: Response(data, headers=headers)
        mock_req.render.side_effect = lambda template_name, qcontext: Response(f"rendered {template_name}", status=200)
        return mock_req

    def test_01_nonexistent_template_returns_clean_error_not_missing_error(self):
        """Fix #4: Non-existent IDs must return 404 / structured error instead of crashing with MissingError."""
        mock_req = self._mock_request_user(self.user_sig_mgr)
        with patch.object(portal, 'request', mock_req):
            res_pdf = self.controller.get_template_pdf(999999)
            self.assertEqual(res_pdf.status_code, 404)

            res_edit = self.controller.edit_template(999999)
            self.assertEqual(res_edit.status_code, 404)

            res_save = self.controller.save_fields(999999, [])
            self.assertEqual(res_save.get('success'), False)
            self.assertEqual(res_save.get('error'), 'Template not found')

            res_sign = self.controller.template_sign_now(999999)
            self.assertEqual(res_sign.get('success'), False)
            self.assertEqual(res_sign.get('error'), 'Template not found')

            res_send = self.controller.template_send_request(999999, [{'role_id': 1, 'name': 'A', 'email': 'a@a.com'}])
            self.assertEqual(res_send.get('success'), False)
            self.assertEqual(res_send.get('error'), 'Template not found')

    def test_02_edit_template_and_save_fields_authorization(self):
        """Fix #3: Only signature managers can access template editor and save fields."""
        # Internal user without signature manager role should be blocked
        mock_internal = self._mock_request_user(self.user_internal)
        with patch.object(portal, 'request', mock_internal):
            with self.assertRaises(AccessError):
                self.controller.edit_template(self.template.id)

            res_save_denied = self.controller.save_fields(self.template.id, [])
            self.assertEqual(res_save_denied.get('success'), False)
            self.assertIn('Access Denied', res_save_denied.get('error', ''))

        # Signature manager can access and save
        mock_mgr = self._mock_request_user(self.user_sig_mgr)
        role = self.env['wm.signature.role'].create({'name': 'Client Signer Base'})
        field_payload = [{
            'page': 1,
            'x': 10.0,
            'y': 20.0,
            'width': 100.0,
            'height': 50.0,
            'type': 'signature',
            'role_id': role.id,
        }]
        with patch.object(portal, 'request', mock_mgr):
            res_save_ok = self.controller.save_fields(self.template.id, field_payload)
            self.assertTrue(res_save_ok.get('success'))
            self.assertEqual(len(self.template.item_ids), 1)

    def test_03_get_template_pdf_returns_pdf_for_authorized_user(self):
        """Fix #1: get_template_pdf streams template document under auth='user' without sudo leakage."""
        mock_mgr = self._mock_request_user(self.user_sig_mgr)
        with patch.object(portal, 'request', mock_mgr):
            res = self.controller.get_template_pdf(self.template.id)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'%PDF-1.4', res.data)
