import base64
import io
from unittest.mock import MagicMock, patch

from PIL import Image as PILImage

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged

from ..controllers import portal
from ..controllers.portal import WmSignaturePortal


def _png_b64():
    buf = io.BytesIO()
    PILImage.new('RGBA', (10, 10), (0, 0, 0, 255)).save(buf, format='PNG')
    return base64.b64encode(buf.getvalue())


@tagged('post_install', '-at_install', 'wm_base')
class TestSignatureCoverage(TransactionCase):
    """Signature request/template/wizard behaviour not covered elsewhere."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.role = cls.env['wm.signature.role'].create({'name': 'Coverage Signer'})
        cls.template = cls.env['wm.signature.template'].create({
            'name': 'Coverage Template',
            'role_ids': [(6, 0, cls.role.ids)],
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Cov Partner', 'email': 'cov@example.com'})

    def _request(self, **extra):
        vals = {
            'template_id': self.template.id,
            'signer_ids': [(0, 0, {'partner_id': self.partner.id, 'role_id': self.role.id})],
        }
        vals.update(extra)
        return self.env['wm.signature.request'].create(vals)

    # ---- signer ----
    def test_signer_email_defaults_from_partner(self):
        signer = self._request().signer_ids
        self.assertEqual(signer.email, 'cov@example.com')
        other = self.env['res.partner'].create({'name': 'Other', 'email': 'other@example.com'})
        signer.partner_id = other
        self.assertEqual(signer.email, 'other@example.com')

    def test_signer_urls_and_token_unique(self):
        req = self._request()
        signer = req.signer_ids
        self.assertTrue(signer.access_token)
        self.assertTrue(req._get_signer_url(signer.id).endswith('/wm_signature/sign/%s' % signer.access_token))
        self.assertEqual(req._get_signer_url(False), '')
        action = signer.action_sign_signer()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['url'], '/wm_signature/sign/%s' % signer.access_token)
        req2 = self._request()
        self.assertNotEqual(req2.signer_ids.access_token, signer.access_token)

    def test_signer_token_cannot_be_changed_by_user(self):
        user = new_test_user(self.env, login='wm_cov_sig_user',
                             groups='base.group_user,wm_base.group_signature_user')
        signer = self._request().signer_ids
        with self.assertRaises(AccessError):
            signer.with_user(user).write({'access_token': 'forged'})

    def test_signature_image_compute(self):
        req = self._request()
        signer = req.signer_ids
        self.assertFalse(signer.signature_image)
        item = self.env['wm.signature.item'].create({
            'template_id': self.template.id, 'page': 1, 'x': 1, 'y': 1, 'width': 10, 'height': 5,
            'type': 'signature', 'role_id': self.role.id})
        img = _png_b64()
        self.env['wm.signature.request.item.value'].create({
            'request_id': req.id, 'item_id': item.id, 'signer_id': signer.id, 'signature_image': img})
        signer.invalidate_recordset()
        self.assertTrue(signer.signature_image)

    # ---- request actions ----
    def test_action_send_state_guards(self):
        req = self._request()
        req.action_send()
        self.assertEqual(req.state, 'sent')
        req.action_send()  # resending an open request is allowed
        req.action_cancel()
        self.assertEqual(req.state, 'cancel')
        with self.assertRaises(UserError):
            req.action_send()

    def test_action_send_requires_signers(self):
        req = self.env['wm.signature.request'].create({'template_id': self.template.id})
        with self.assertRaises(UserError):
            req.action_send()
        self.assertEqual(req.state, 'draft')

    def test_action_send_posts_mail_per_signer(self):
        partner2 = self.env['res.partner'].create({'name': 'Second', 'email': 'second@example.com'})
        req = self._request()
        req.write({'signer_ids': [(0, 0, {'partner_id': partner2.id, 'role_id': self.role.id})]})
        req.action_send()
        self.assertIn('Signature request sent', req.message_ids[0].body)

    def test_action_cancel_draft_and_sent(self):
        for state in ('draft', 'sent'):
            req = self._request(state=state)
            req.action_cancel()
            self.assertEqual(req.state, 'cancel')

    def test_sequence_name_generated(self):
        self.assertNotEqual(self._request().name, 'New')

    def test_action_view_reference_doc(self):
        req = self._request()
        self.assertFalse(req.action_view_reference_doc())
        if 'wm.collection.order' not in self.env:
            return
        order = self.env['wm.collection.order'].search([], limit=1)
        if order:
            req.reference_doc = order
            action = req.action_view_reference_doc()
            self.assertEqual(action['res_model'], 'wm.collection.order')
            self.assertEqual(action['res_id'], order.id)

    def test_reference_doc_invalid_values(self):
        user = new_test_user(self.env, login='wm_cov_ref_user',
                             groups='base.group_user,wm_base.group_signature_user')
        Request = self.env['wm.signature.request'].with_user(user)
        for bad in ('res.partner,', 'res.partner,999999999', 'no.such.model,1'):
            with self.assertRaises(UserError):
                Request._check_reference_doc_access(bad)
        # empty value is a no-op, and so is the superuser
        Request._check_reference_doc_access(False)
        self.env['wm.signature.request']._check_reference_doc_access('res.partner,999999999')

    # ---- pdf generation / completion ----
    def test_document_pdf_fallbacks(self):
        req = self._request()
        self.assertFalse(req._get_document_pdf())
        self.assertFalse(req._render_reference_pdf())
        self.template.action_design_template()
        self.assertTrue(req._get_document_pdf().startswith(b'%PDF'))

    def test_generate_certificate_without_pdf_raises(self):
        tmpl = self.env['wm.signature.template'].create({
            'name': 'NoDoc', 'role_ids': [(6, 0, self.role.ids)]})
        req = self.env['wm.signature.request'].create({
            'template_id': tmpl.id,
            'signer_ids': [(0, 0, {'partner_id': self.partner.id, 'role_id': self.role.id})]})
        with self.assertRaises(UserError):
            req._generate_signed_certificate()

    def test_full_completion_generates_hash_and_overlay(self):
        self.template.action_design_template()
        items = self.env['wm.signature.item'].create([
            {'template_id': self.template.id, 'page': 1, 'x': 5, 'y': 5, 'width': 20, 'height': 5,
             'type': t, 'role_id': self.role.id}
            for t in ('signature', 'name', 'email', 'date', 'text')])
        req = self._request()
        req.action_send()
        signer = req.signer_ids
        img = _png_b64()
        for item in items:
            self.env['wm.signature.request.item.value'].create({
                'request_id': req.id, 'item_id': item.id, 'signer_id': signer.id,
                'value': 'abc', 'signature_image': img if item.type == 'signature' else False})
        signer.sudo().write({'state': 'signed'})
        req._check_request_completion()
        self.assertEqual(req.state, 'signed')
        self.assertTrue(req.date_signed)
        self.assertTrue(req.signed_document_hash)
        self.assertTrue(req.action_verify_signed_document())
        # a completed request serves its frozen copy
        self.assertEqual(req._get_document_pdf(), base64.b64decode(req.signed_document))
        # tampering is detected
        req.sudo().signed_document_hash = 'deadbeef'
        self.assertFalse(req.action_verify_signed_document())
        with self.assertRaises(UserError):
            req.action_cancel()

    def test_incomplete_signers_do_not_complete(self):
        partner2 = self.env['res.partner'].create({'name': 'P2', 'email': 'p2@example.com'})
        self.template.action_design_template()
        req = self._request()
        req.write({'signer_ids': [(0, 0, {'partner_id': partner2.id, 'role_id': self.role.id})]})
        req.action_send()
        req.signer_ids[0].sudo().write({'state': 'signed'})
        req._check_request_completion()
        self.assertEqual(req.state, 'sent')
        self.assertFalse(req.signed_document_hash)

    def test_verify_signed_document_without_document(self):
        self.assertFalse(self._request().action_verify_signed_document())

    # ---- templates ----
    def test_design_template_adds_role_and_document(self):
        tmpl = self.env['wm.signature.template'].create({'name': 'Designer Tpl'})
        # role_ids is required at UI level only; action ensures one exists
        action = tmpl.action_design_template()
        self.assertTrue(tmpl.role_ids)
        self.assertTrue(tmpl.document)
        self.assertEqual(tmpl.document_filename, 'Designer Tpl.pdf')
        self.assertIn('/wm_signature/template/edit/%s?back_url=' % tmpl.id, action['url'])
        self.assertEqual(action['type'], 'ir.actions.act_url')

    def test_design_template_keeps_existing_document(self):
        doc = base64.b64encode(b'%PDF-1.4 mine')
        tmpl = self.env['wm.signature.template'].create({
            'name': 'Keep', 'document': doc, 'role_ids': [(6, 0, self.role.ids)]})
        tmpl.action_design_template()
        self.assertEqual(tmpl.document, doc)

    def test_default_pdf_and_sample_template(self):
        pdf = base64.b64decode(self.template._generate_default_pdf_document())
        self.assertTrue(pdf.startswith(b'%PDF'))
        tmpl_id = self.env['wm.signature.template'].create_sample_template()
        tmpl = self.env['wm.signature.template'].browse(tmpl_id)
        self.assertEqual(tmpl.document_filename, 'Sample_Contract.pdf')
        self.assertTrue(tmpl.role_ids)
        self.assertTrue(base64.b64decode(tmpl.document).startswith(b'%PDF'))

    def test_create_from_pdf_creates_role_when_missing(self):
        Role = self.env['wm.signature.role']
        # Existing roles are referenced by signature items and cannot be
        # deleted, so hide them from the lookup instead.
        with patch.object(type(Role), 'search', return_value=Role):
            tid = self.env['wm.signature.template'].create_from_pdf(
                '', base64.b64encode(b'%PDF'), 'f.pdf')
        tmpl = self.env['wm.signature.template'].browse(tid)
        self.assertEqual(tmpl.name, 'f.pdf')
        self.assertEqual(tmpl.role_ids.name, 'Signer')

    # ---- wizards ----
    def test_request_wizard_onchange_and_confirm(self):
        wiz = self.env['wm.signature.request.wizard'].new({
            'template_id': self.template.id, 'res_model': 'res.partner', 'res_id': self.partner.id})
        wiz._onchange_template_id()
        self.assertEqual(len(wiz.signer_ids), 1)
        self.assertEqual(wiz.signer_ids.role_id, self.role)
        wiz.template_id = False
        wiz._onchange_template_id()
        self.assertFalse(wiz.signer_ids)

    def test_request_wizard_signer_onchange(self):
        line = self.env['wm.signature.request.wizard.signer'].new({
            'role_id': self.role.id, 'partner_id': self.partner.id})
        line._onchange_partner_id()
        self.assertEqual(line.email, 'cov@example.com')

    def test_request_wizard_confirm_validations(self):
        Wiz = self.env['wm.signature.request.wizard']
        wiz = Wiz.create({'template_id': self.template.id, 'res_model': 'res.partner',
                          'res_id': self.partner.id})
        with self.assertRaises(UserError):
            wiz.action_confirm()
        wiz.signer_ids = [(0, 0, {'role_id': self.role.id, 'partner_id': self.partner.id, 'email': False})]
        with self.assertRaises(UserError):
            wiz.action_confirm()

    def test_request_wizard_confirm_creates_and_sends(self):
        wiz = self.env['wm.signature.request.wizard'].create({
            'template_id': self.template.id, 'res_model': 'res.partner', 'res_id': self.partner.id,
            'signer_ids': [(0, 0, {'role_id': self.role.id, 'partner_id': self.partner.id,
                                   'email': 'typed@example.com'})]})
        # wm_base alone offers no linkable models; allow res.partner for this flow
        with patch.object(type(self.env['wm.signature.request']), '_selection_target_model',
                          lambda self: [('res.partner', 'Partner')]):
            res = wiz.action_confirm()
        self.assertEqual(res['tag'], 'display_notification')
        req = self.env['wm.signature.request'].search([('template_id', '=', self.template.id)],
                                                      order='id desc', limit=1)
        self.assertEqual(req.state, 'sent')
        self.assertEqual(req.signer_ids.email, 'typed@example.com')
        self.assertEqual(req.reference_doc, self.partner)

    def test_sign_now_wizard_creates_template(self):
        wiz = self.env['wm.signature.sign.now.wizard'].create({
            'name': 'Uploaded', 'document': base64.b64encode(b'%PDF-1.4 x'),
            'document_filename': 'up.pdf'})
        action = wiz.action_upload_and_design()
        tmpl = self.env['wm.signature.template'].search([('name', '=', 'Uploaded')])
        self.assertEqual(len(tmpl), 1)
        self.assertTrue(tmpl.role_ids)
        self.assertEqual(action['url'], '/wm_signature/template/edit/%s?sign_now=1' % tmpl.id)

    def test_sign_now_wizard_requires_signature_manager(self):
        user = new_test_user(self.env, login='wm_cov_sign_user',
                             groups='base.group_user,wm_base.group_signature_user')
        wiz = self.env['wm.signature.sign.now.wizard'].with_user(user).create({
            'name': 'Blocked', 'document': base64.b64encode(b'%PDF-1.4 x'),
            'document_filename': 'up.pdf'})
        with self.assertRaises(AccessError):
            wiz.action_upload_and_design()
        self.assertFalse(self.env['wm.signature.template'].search([('name', '=', 'Blocked')]))

    # ---- controller routes ----
    def _mock_request(self, user):
        mock_req = MagicMock()
        mock_req.env = self.env(user=user)
        mock_req.httprequest.remote_addr = '127.0.0.1'
        mock_req.httprequest.headers = {'User-Agent': 'test'}
        return mock_req

    def test_controller_template_creation_routes(self):
        ctrl = WmSignaturePortal()
        mgr = new_test_user(self.env, login='wm_cov_mgr',
                            groups='base.group_user,wm_base.group_signature_manager')
        plain = new_test_user(self.env, login='wm_cov_plain', groups='base.group_user')
        with patch.object(portal, 'request', self._mock_request(plain)):
            self.assertFalse(ctrl.template_create_sample()['success'])
            self.assertFalse(ctrl.template_create_from_pdf('n', 'data', 'f.pdf')['success'])
        with patch.object(portal, 'request', self._mock_request(mgr)):
            self.assertFalse(ctrl.template_create_from_pdf('n', '', 'f.pdf')['success'])
            res = ctrl.template_create_sample()
            self.assertTrue(res['success'])
            res = ctrl.template_create_from_pdf(
                'Up', 'data:application/pdf;base64,' + base64.b64encode(b'%PDF-1.4').decode(), 'u.pdf')
            self.assertTrue(res['success'])
            tmpl = self.env['wm.signature.template'].browse(res['template_id'])
            self.assertEqual(tmpl.name, 'Up')
            self.assertEqual(base64.b64decode(tmpl.document), b'%PDF-1.4')

    def test_reference_doc_check_rejects_unknown_model(self):
        user = new_test_user(self.env, login='wm_cov_ref_user', groups='base.group_user,wm_base.group_signature_user')
        with self.assertRaises(UserError):
            self.env['wm.signature.request'].with_user(user)._check_reference_doc_access('no.such.model,1')

    def test_default_pdf_failure_returns_false(self):
        with patch('reportlab.pdfgen.canvas.Canvas', side_effect=ValueError('broken')):
            self.assertFalse(self.template._generate_default_pdf_document())
