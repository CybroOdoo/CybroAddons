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

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_compliance')
class TestComplianceInternalsCoverage(TransactionCase):
    """Coverage for manifest line UoM maths, locks, auto certificate, vault and constraints."""

    def setUp(self):
        super().setUp()
        self.generator = self.env['res.partner'].create({'name': 'Cov Gen', 'is_generator': True})
        self.transporter = self.env['res.partner'].create({'name': 'Cov Trans', 'is_transporter': True})
        self.facility = self.env['wm.disposal.facility'].create({'name': 'Cov Facility'})
        self.category = self.env['wm.waste.category'].create({'name': 'Cov Cat', 'code': 'COV_CAT_X'})
        self.kg = self.env.ref('uom.product_uom_kgm')
        self.gram = self.env.ref('uom.product_uom_gram')
        self.litre = self.env.ref('uom.product_uom_litre')

    def _manifest(self, lines=None):
        return self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'line_ids': [(0, 0, dict({'waste_category_id': self.category.id}, **ln))
                         for ln in (lines or [{'quantity': 10.0, 'uom_id': self.kg.id}])],
        })

    # ---- UoM conversion / total quantity ----
    def test_convert_quantity_to_kg(self):
        Line = self.env['wm.compliance.manifest.line']
        self.assertAlmostEqual(Line._convert_quantity_to_kg(2000.0, self.gram), 2.0)
        self.assertEqual(Line._convert_quantity_to_kg(5.0, self.kg), 5.0)
        self.assertEqual(Line._convert_quantity_to_kg(7.0, self.env['uom.uom']), 7.0)
        self.assertEqual(Line._convert_quantity_to_kg(0.0, self.gram), 0.0)
        # Incompatible category: returned unchanged
        self.assertEqual(Line._convert_quantity_to_kg(3.0, self.litre), 3.0)

    def test_total_quantity_normalised_and_recomputed(self):
        manifest = self._manifest([
            {'quantity': 1000.0, 'uom_id': self.gram.id},
            {'quantity': 4.0, 'uom_id': self.kg.id},
            {'quantity': 2.0},
        ])
        self.assertAlmostEqual(manifest.total_quantity, 7.0)
        self.assertAlmostEqual(manifest.line_ids[0]._get_quantity_kg(), 1.0)
        manifest.line_ids[1].quantity = 10.0
        self.assertAlmostEqual(manifest.total_quantity, 13.0)
        manifest.line_ids[2].unlink()
        self.assertAlmostEqual(manifest.total_quantity, 11.0)

    # ---- line / manifest locks ----
    def test_lines_locked_after_submit_for_normal_user(self):
        officer = new_test_user(self.env, login='cov_officer', groups='wm_base.group_wm_compliance_officer')
        manifest = self._manifest()
        manifest.action_submit()
        line = manifest.line_ids
        with self.assertRaises(UserError):
            line.with_user(officer).write({'quantity': 99.0})
        with self.assertRaises(UserError):
            line.with_user(officer).unlink()
        with self.assertRaises(UserError):
            self.env['wm.compliance.manifest.line'].with_user(officer).create({
                'manifest_id': manifest.id, 'waste_category_id': self.category.id, 'quantity': 1.0})

    def test_state_cannot_be_written_directly_by_normal_user(self):
        officer = new_test_user(self.env, login='cov_officer2', groups='wm_base.group_wm_compliance_officer')
        manifest = self._manifest()
        with self.assertRaises(UserError):
            manifest.with_user(officer).write({'state': 'collected'})

    def test_lock_bypass_ignored_without_superuser(self):
        officer = new_test_user(self.env, login='cov_officer3', groups='wm_base.group_wm_compliance_officer')
        manifest = self._manifest()
        manifest.action_submit()
        self.assertFalse(manifest.with_user(officer).with_context(
            bypass_compliance_lock=True)._compliance_lock_bypassed())
        self.assertTrue(manifest.sudo().with_context(bypass_compliance_lock=True)._compliance_lock_bypassed())
        self.assertFalse(manifest.sudo()._compliance_lock_bypassed())

    def test_invalid_workflow_transitions(self):
        manifest = self._manifest()
        with self.assertRaises(UserError):
            manifest.action_collect()
        with self.assertRaises(UserError):
            manifest.action_dispose()
        manifest.action_submit()
        with self.assertRaises(UserError):
            manifest.action_submit()
        with self.assertRaises(UserError):
            manifest.action_dispose()
        manifest.action_collect()
        with self.assertRaises(UserError):
            manifest.action_collect()

    # ---- auto certificate ----
    def test_dispose_auto_issues_single_certificate(self):
        manifest = self._manifest([{'quantity': 500.0, 'uom_id': self.gram.id}])
        manifest.action_submit()
        manifest.action_collect()
        manifest.action_dispose()
        cert = self.env['wm.compliance.certificate'].search([('manifest_id', '=', manifest.id)])
        self.assertEqual(len(cert), 1)
        self.assertEqual(cert.certificate_type, 'destruction')
        self.assertAlmostEqual(cert.quantity, 0.5)
        self.assertEqual(cert.facility_id, self.facility)
        self.assertEqual(cert.state, 'issued')
        self.assertTrue(cert.issued_date)
        # Idempotent
        manifest._auto_issue_compliance_certificate()
        self.assertEqual(self.env['wm.compliance.certificate'].search_count(
            [('manifest_id', '=', manifest.id)]), 1)

    def test_certificate_issue_twice_and_copy(self):
        cert = self.env['wm.compliance.certificate'].create({
            'name': 'Cert A', 'facility_id': self.facility.id, 'quantity': 1.0})
        self.assertNotEqual(cert.certificate_no, 'New')
        cert.action_issue()
        with self.assertRaises(UserError):
            cert.action_issue()
        self.assertTrue(cert.signature_id.hash_verified)
        dup = cert.copy()
        self.assertEqual(dup.state, 'draft')
        self.assertTrue(dup.name.endswith('(Copy)'))
        self.assertTrue(dup.certificate_no.endswith('(Copy)'))
        self.assertFalse(dup.signature_id)

    # ---- digital signature ----
    def test_digital_signature_integrity(self):
        Sig = self.env['wm.digital.signature']
        with self.assertRaises(UserError):
            Sig.sign_document(self.facility, b'', 'x.pdf')
        sig = Sig.sign_document(self.facility, b'%PDF-test', 'x.pdf')
        self.assertEqual(len(sig.pdf_hash), 64)
        self.assertTrue(sig.hash_verified)
        self.assertIn('Signature by', sig.display_name)
        with self.assertRaises(UserError):
            sig.write({'pdf_hash': 'a' * 64})
        with self.assertRaises(UserError):
            sig.unlink()
        # Tampering with the attachment breaks verification
        sig.pdf_attachment_id.raw = b'tampered'
        sig.invalidate_recordset(['hash_verified'])
        self.assertFalse(sig.hash_verified)

    # ---- document vault ----
    def test_document_attachment_inverse_and_compute(self):
        import base64
        doc = self.env['wm.compliance.document'].create({
            'name': 'Permit X', 'expiry_date': fields.Date.today() + timedelta(days=100),
            'attachment_file': base64.b64encode(b'hello'), 'attachment_filename': 'p.txt'})
        self.assertTrue(doc.attachment_id)
        self.assertEqual(doc.attachment_filename, 'p.txt')
        self.assertEqual(base64.b64decode(doc.attachment_file), b'hello')
        att = doc.attachment_id
        doc.write({'attachment_file': base64.b64encode(b'bye'), 'attachment_filename': 'q.txt'})
        self.assertEqual(doc.attachment_id, att)
        self.assertEqual(att.name, 'q.txt')
        doc.write({'attachment_file': False})
        self.assertFalse(doc.attachment_id)
        self.assertFalse(att.exists())

    def test_document_expiry_cron_creates_one_reminder(self):
        Doc = self.env['wm.compliance.document']
        soon = Doc.create({'name': 'Soon', 'expiry_date': fields.Date.today() + timedelta(days=5),
                           'reminder_days': 10, 'attachment_file': 'aGk='})
        far = Doc.create({'name': 'Far', 'expiry_date': fields.Date.today() + timedelta(days=200),
                          'reminder_days': 10, 'attachment_file': 'aGk='})
        Doc.cron_check_document_expiry()
        Doc.cron_check_document_expiry()
        Act = self.env['mail.activity'].with_context(active_test=False)
        self.assertEqual(Act.search_count([('res_model', '=', 'wm.compliance.document'),
                                           ('res_id', '=', soon.id)]), 1)
        self.assertEqual(Act.search_count([('res_model', '=', 'wm.compliance.document'),
                                           ('res_id', '=', far.id)]), 0)

    # ---- constraints ----
    def test_safety_incident_regulatory_deadline_constraint(self):
        vals = {'description': 'Spill', 'incident_datetime': fields.Datetime.now(),
                'regulatory_report_required': True}
        with self.assertRaises(ValidationError):
            self.env['wm.safety.incident'].create(vals)
        inc = self.env['wm.safety.incident'].create(dict(
            vals, regulatory_deadline=fields.Date.today() + timedelta(days=3)))
        with self.assertRaises(ValidationError):
            inc.regulatory_deadline = False

    def test_report_builder_date_range_constraint(self):
        today = fields.Date.today()
        with self.assertRaises(ValidationError):
            self.env['wm.compliance.report'].create({
                'date_from': today, 'date_to': today - timedelta(days=1)})
