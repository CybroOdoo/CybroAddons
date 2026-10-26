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

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged

from ..controllers import portal
from ..controllers.portal import WmSignaturePortal


@tagged('post_install', '-at_install', 'wm_base')
class TestSignatureIntegrity(TransactionCase):
    """Signature evidence cannot be forged, designer saves keep captured values, linked documents are access checked."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.role = cls.env['wm.signature.role'].create({'name': 'Integrity Signer'})
        cls.template = cls.env['wm.signature.template'].create({
            'name': 'Integrity Template',
            'document': base64.b64encode(b'%PDF-1.4 integrity'),
            'document_filename': 'integrity.pdf',
            'role_ids': [(6, 0, cls.role.ids)],
        })
        cls.item = cls.env['wm.signature.item'].create({
            'template_id': cls.template.id, 'page': 1, 'x': 10.0, 'y': 10.0,
            'width': 20.0, 'height': 5.0, 'type': 'signature', 'role_id': cls.role.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Integrity Partner', 'email': 'int@example.com'})
        cls.sig_user = new_test_user(cls.env, login='wm_integrity_sig_user',
                                     groups='base.group_user,wm_base.group_signature_user')
        cls.sig_mgr = new_test_user(cls.env, login='wm_integrity_sig_mgr',
                                    groups='base.group_user,wm_base.group_signature_manager')
        cls.request = cls.env['wm.signature.request'].create({
            'template_id': cls.template.id,
            'signer_ids': [(0, 0, {'partner_id': cls.partner.id, 'role_id': cls.role.id, 'email': 'int@example.com'})],
        })
        cls.signer = cls.request.signer_ids

    def test_signing_evidence_cannot_be_forged_by_a_user(self):
        for vals in ({'state': 'signed'}, {'signed_date': '2026-01-01 10:00:00'}, {'ip_address': '1.2.3.4'}):
            with self.assertRaises(AccessError):
                self.signer.with_user(self.sig_user).write(vals)
        with self.assertRaises(AccessError):
            self.env['wm.signature.request.signer'].with_user(self.sig_user).create({
                'request_id': self.request.id, 'partner_id': self.partner.id,
                'role_id': self.role.id, 'state': 'signed'})
        self.assertEqual(self.signer.state, 'sent')
        # The signing flow (superuser) can still record the signature
        self.signer.sudo().write({'state': 'signed'})
        self.assertEqual(self.signer.state, 'signed')

    def test_users_cannot_write_captured_values(self):
        value = self.env['wm.signature.request.item.value'].create({
            'request_id': self.request.id, 'item_id': self.item.id, 'signer_id': self.signer.id,
        })
        with self.assertRaises(AccessError):
            value.with_user(self.sig_user).write({'value': 'forged'})

    def test_item_with_captured_values_cannot_be_deleted(self):
        self.env['wm.signature.request.item.value'].create({
            'request_id': self.request.id, 'item_id': self.item.id, 'signer_id': self.signer.id,
        })
        with self.assertRaises(Exception):
            with self.cr.savepoint():
                self.item.unlink()

    def test_designer_save_keeps_items_and_their_values(self):
        value = self.env['wm.signature.request.item.value'].create({
            'request_id': self.request.id, 'item_id': self.item.id, 'signer_id': self.signer.id,
        })
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.sig_mgr)
        with patch.object(portal, 'request', mock_req):
            res = WmSignaturePortal().save_fields(self.template.id, [{
                'id': self.item.id, 'page': 1, 'x': 30.0, 'y': 40.0, 'width': 20.0, 'height': 5.0,
                'type': 'signature', 'role_id': self.role.id,
            }, {
                'id': 'new_1', 'page': 1, 'x': 5.0, 'y': 5.0, 'width': 20.0, 'height': 5.0,
                'type': 'signature', 'role_id': self.role.id,
            }])
        self.assertTrue(res['success'])
        self.assertTrue(self.item.exists())
        self.assertEqual(self.item.x, 30.0)
        self.assertTrue(value.exists())
        self.assertEqual(len(self.template.item_ids), 2)
        # Removing a field that already has captured values is refused
        with patch.object(portal, 'request', mock_req):
            res = WmSignaturePortal().save_fields(self.template.id, [])
        self.assertFalse(res['success'])
        self.assertTrue(self.item.exists())

    def test_reference_doc_requires_write_access(self):
        """Linking a document the user cannot modify is refused; sudo flows are unaffected."""
        partner = self.env['res.partner'].create({'name': 'Linked Doc Partner'})
        Request = self.env['wm.signature.request']
        with patch.object(type(Request), '_selection_target_model',
                          lambda self: [('res.partner', 'Partner')]):
            vals = {'template_id': self.template.id, 'reference_doc': 'res.partner,%d' % partner.id}
            with self.assertRaises(UserError):
                Request.with_user(self.sig_user).create(dict(vals, reference_doc='res.partner,0'))
            with self.assertRaises(AccessError):
                Request.with_user(self.sig_user).create(vals)
            self.assertTrue(Request.sudo().create(vals))

    def test_signed_request_cannot_be_cancelled_and_hash_is_verifiable(self):
        import hashlib
        request = self.env['wm.signature.request'].create({
            'template_id': self.template.id,
            'signer_ids': [(0, 0, {'partner_id': self.partner.id, 'role_id': self.role.id, 'email': 'int@example.com'})],
        })
        pdf = b'%PDF-1.4 signed copy'
        request.sudo().write({
            'state': 'signed', 'signed_document': base64.b64encode(pdf),
            'signed_document_hash': hashlib.sha256(pdf).hexdigest()})
        with self.assertRaises(UserError):
            request.action_cancel()
        with self.assertRaises(UserError):
            request.action_send()
        self.assertTrue(request.action_verify_signed_document())
        request.sudo().write({'signed_document': base64.b64encode(b'tampered')})
        self.assertFalse(request.action_verify_signed_document())
