"""Regression tests for the compliance security hardening: forged evidence,
deletion after submission and the XLSX formula guard."""
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.wm_compliance.models.report_builder import _xlsx_safe


@tagged('post_install', '-at_install')
class TestComplianceSecurityHardening(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.generator = cls.env['res.partner'].create({'name': 'Sec Generator', 'is_generator': True})
        cls.transporter = cls.env['res.partner'].create({'name': 'Sec Transporter'})
        cls.facility = cls.env['wm.disposal.facility'].create({'name': 'Sec Plant', 'facility_type': 'landfill'})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Sec Waste', 'code': 'SECW'})

    def _manifest(self):
        return self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'line_ids': [(0, 0, {'waste_category_id': self.category.id, 'quantity': 10.0})],
        })

    def _officer(self):
        # TransactionCase runs as superuser, which is allowed to create evidence:
        # the guards apply to real users.
        return new_test_user(self.env, login='sec_officer', groups='wm_base.group_wm_compliance_officer')

    def test_signature_cannot_be_created_directly(self):
        officer = self._officer()
        with self.assertRaises(UserError):
            self.env['wm.digital.signature'].with_user(officer).create({
                'res_model': 'wm.compliance.manifest', 'res_id': 1,
                'signer_id': officer.id, 'pdf_hash': 'forged'})

    def test_custody_row_is_attributed_to_the_caller(self):
        officer = self._officer()
        manifest = self._manifest()
        other = self.env['res.users'].create({'name': 'Other', 'login': 'sec_other'})
        row = self.env['wm.compliance.custody'].with_user(officer).create({
            'manifest_id': manifest.id, 'action': 'generated', 'custodian_id': other.id,
            'timestamp': '2000-01-01 00:00:00'})
        self.assertEqual(row.custodian_id, officer)
        self.assertGreater(str(row.timestamp), '2020')

    def test_only_draft_manifests_can_be_deleted(self):
        officer = self._officer()
        draft = self._manifest()
        draft.with_user(officer).unlink()  # allowed
        submitted = self._manifest()
        submitted.sudo().with_context(bypass_compliance_lock=True).write({'state': 'submitted'})
        with self.assertRaises(UserError):
            submitted.with_user(officer).unlink()

    def test_xlsx_cells_cannot_be_formulas(self):
        for evil in ('=1+1', '+SUM(A1)', '-2+3', '@cmd'):
            self.assertTrue(_xlsx_safe(evil).startswith("'"))
        self.assertEqual(_xlsx_safe('Plain text'), 'Plain text')
        self.assertEqual(_xlsx_safe(5.0), 5.0)

    def test_manifest_without_lines_cannot_be_submitted(self):
        empty = self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
        })
        with self.assertRaises(UserError):
            empty.action_submit()
        self.assertEqual(empty.state, 'draft')

    def test_locked_rule_set_can_be_archived_but_not_edited(self):
        rule = self.env['wm.compliance.rule.set'].create({'name': 'Retire me'})
        rule.action_activate()
        rule.action_lock()
        self.assertEqual(rule.state, 'locked')
        with self.assertRaises(UserError):
            rule.write({'name': 'Edited while locked'})
        rule.write({'active': False})
        self.assertFalse(rule.active)

    def test_export_and_notify_signs_and_emails_only_once(self):
        manifest = self._manifest()
        manifest.generator_id.email = 'gen@example.com'
        manifest.action_submit()
        mails_before = self.env['mail.mail'].sudo().search_count([('subject', 'like', manifest.name)])
        signature = manifest.signature_id
        self.assertTrue(manifest.notified_at)
        manifest.action_export_and_notify()
        manifest.action_export_and_notify()
        self.assertEqual(manifest.signature_id, signature, "the PDF is signed only once")
        self.assertEqual(
            self.env['mail.mail'].sudo().search_count([('subject', 'like', manifest.name)]),
            mails_before, "stakeholders are emailed only once")
