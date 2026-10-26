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
import json
from unittest.mock import MagicMock, patch

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged

from ..controllers import portal
from ..controllers.portal import WmSignaturePortal, _json_for_script


@tagged('post_install', '-at_install', 'wm_base')
class TestBaseCriticalFixes(TransactionCase):
    """Regression tests for signature access, signing state checks, XSS and category dedup."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WmSignaturePortal()
        cls.role = cls.env['wm.signature.role'].create({'name': 'Fix Customer'})
        cls.template = cls.env['wm.signature.template'].create({
            'name': 'Fix Template',
            'role_ids': [(6, 0, cls.role.ids)],
            'document': base64.b64encode(b'%PDF-1.4 not a real pdf'),
            'document_filename': 'fix.pdf',
        })
        cls.customer = cls.env['res.partner'].create({'name': 'Fix Customer', 'email': 'fix.customer@example.com'})
        cls.portal_user = new_test_user(cls.env, login='wm_base_fix_portal', groups='base.group_portal')
        cls.driver = new_test_user(cls.env, login='wm_base_fix_driver', groups='wm_base.group_wm_driver')

    def _request(self, partner=None, state='sent'):
        req = self.env['wm.signature.request'].create({
            'template_id': self.template.id,
            'signer_ids': [(0, 0, {'partner_id': (partner or self.customer).id, 'role_id': self.role.id})],
        })
        req.state = state
        return req

    def _mock_request(self, user=None):
        mock_req = MagicMock()
        mock_req.env = self.env(user=user) if user else self.env
        mock_req.httprequest.remote_addr = '127.0.0.1'
        mock_req.httprequest.headers = {'User-Agent': 'test'}
        return mock_req

    def test_portal_user_has_no_direct_signature_access(self):
        """Portal users cannot read signer tokens or signature requests over RPC."""
        self._request()
        for model in ('wm.signature.request', 'wm.signature.request.signer'):
            with self.assertRaises(AccessError):
                self.env[model].with_user(self.portal_user).search_read([], ['id'])

    def test_json_for_script_cannot_close_script_tag(self):
        """Signer values inlined in the signing page cannot break out of the script block."""
        payload = {'value': '</script><script>alert(1)</script>'}
        out = str(_json_for_script(payload))
        self.assertNotIn('<', out)
        self.assertNotIn('>', out)
        self.assertEqual(json.loads(out), payload)

    def test_cannot_sign_cancelled_request(self):
        """Tokens of cancelled requests are dead; completion never revives them."""
        req = self._request(state='cancel')
        signer = req.signer_ids
        with patch.object(portal, 'request', self._mock_request()):
            res = self.controller.signature_submit(signer.access_token, [])
        self.assertFalse(res['success'])
        self.assertEqual(signer.state, 'sent')

        signer.state = 'signed'
        req._check_request_completion()
        self.assertEqual(req.state, 'cancel')

    def test_failed_signing_is_rolled_back(self):
        """If the certificate cannot be generated, the signature is not recorded."""
        req = self._request()
        signer = req.signer_ids
        with patch.object(portal, 'request', self._mock_request()):
            res = self.controller.signature_submit(signer.access_token, [])
        self.assertFalse(res['success'])
        req.invalidate_recordset()
        signer.invalidate_recordset()
        self.assertEqual(signer.state, 'sent')
        self.assertEqual(req.state, 'sent')

    def test_portal_user_cannot_use_template_endpoints(self):
        """Template creation and sending are not available to portal users."""
        with patch.object(portal, 'request', self._mock_request(self.portal_user)):
            self.assertFalse(self.controller.template_create_sample()['success'])
            self.assertFalse(self.controller.template_create_from_pdf('x', 'eA==', 'x.pdf')['success'])
            res = self.controller.template_send_request(
                self.template.id, [{'role_id': self.role.id, 'name': 'X', 'email': 'x@example.com'}])
            self.assertFalse(res['success'])
            self.assertFalse(self.controller.template_sign_now(self.template.id)['success'])

    def test_driver_sees_only_own_signature_requests(self):
        """Non-manager signature users only see requests they created or must sign."""
        others = self._request()
        own = self._request(partner=self.driver.partner_id)
        Request = self.env['wm.signature.request'].with_user(self.driver)
        visible = Request.search([('id', 'in', (others | own).ids)])
        self.assertEqual(visible, own)
        self.assertFalse(self.env['wm.signature.request.signer'].with_user(self.driver).search(
            [('id', 'in', others.signer_ids.ids)]))

    def test_category_dedup_never_deletes_referencing_rows(self):
        """The duplicate-category cleanup repoints products instead of deleting them."""
        Category = self.env['wm.waste.category']
        keep = Category.create({'name': 'Fix Dedup Glass', 'code': 'FXDDG'})
        self.env.cr.execute(
            "INSERT INTO wm_waste_category (name, code, active, company_id) "
            "SELECT 'fix dedup glass', 'FXDDG2', true, company_id FROM wm_waste_category WHERE id = %s RETURNING id",
            (keep.id,))
        dup_id = self.env.cr.fetchone()[0]
        products = self.env['product.template'].create([
            {'name': 'Fix Dedup Keep', 'wm_waste_category_id': keep.id},
            {'name': 'Fix Dedup Dup', 'wm_waste_category_id': dup_id},
        ])
        self.env.flush_all()

        Category._merge_duplicate_categories()
        self.env.invalidate_all()

        self.assertEqual(len(products.exists()), 2, "Products must never be deleted by the cleanup")
        self.assertEqual(products.mapped('wm_waste_category_id'), keep)
        self.assertFalse(Category.browse(dup_id).exists())
