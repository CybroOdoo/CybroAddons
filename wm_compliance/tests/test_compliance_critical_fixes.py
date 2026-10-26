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
import datetime
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_compliance')
class TestComplianceCriticalFixes(TransactionCase):
    """Regression tests for mandatory codes, draft rule sets, certificate issue and expiry reminders."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env.ref('base.us')
        cls.state = cls.env.ref('base.state_us_5')
        cls.generator = cls.env['res.partner'].create({
            'name': 'Fix Generator', 'is_generator': True,
            'country_id': cls.country.id, 'state_id': cls.state.id,
        })
        cls.transporter = cls.env['res.partner'].create({'name': 'Fix Transporter', 'is_transporter': True})
        cls.facility = cls.env['wm.disposal.facility'].create({'name': 'Fix Plant', 'facility_type': 'landfill'})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Fix Solvent Waste', 'code': 'FXSOLV'})
        cls.code_a = cls.env['wm.compliance.code'].create({'name': 'FIX-A', 'manifest_type': 'hazardous'})
        cls.code_b = cls.env['wm.compliance.code'].create({'name': 'FIX-B', 'manifest_type': 'hazardous'})
        cls.rule = cls.env['wm.compliance.rule.set'].create({
            'name': 'Fix Solvent Rule',
            'state': 'active',
            'country_id': cls.country.id,
            'state_id': cls.state.id,
            'waste_category_id': cls.category.id,
            'required_code_ids': [(6, 0, (cls.code_a | cls.code_b).ids)],
            'requires_manifest': True,
            'sequence': 1,
        })

    def _manifest(self, codes):
        return self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'compliance_code_ids': [(6, 0, codes.ids)],
            'line_ids': [(0, 0, {'waste_category_id': self.category.id, 'quantity': 100.0})],
        })

    def test_all_required_codes_are_mandatory(self):
        """Attaching only one of the required codes no longer passes submission."""
        partial = self._manifest(self.code_a)
        with self.assertRaises(UserError):
            partial.action_submit()
        self.assertEqual(partial.state, 'draft')

        complete = self._manifest(self.code_a | self.code_b)
        complete.action_submit()
        self.assertEqual(complete.state, 'submitted')

    def test_draft_rule_set_not_applied(self):
        """A rule set still in Draft is never returned for enforcement."""
        draft_rule = self.env['wm.compliance.rule.set'].create({
            'name': 'Fix Draft Rule',
            'waste_category_id': self.category.id,
            'state': 'draft',
            'sequence': 0,
        })
        rules = self.env['wm.compliance.rule.set']._get_applicable_rules(
            waste_category=self.category, country=self.country, state=self.state)
        self.assertNotIn(draft_rule, rules)
        self.assertIn(self.rule, rules)

    def test_failed_certificate_issue_keeps_disposal(self):
        """If the certificate cannot be issued, the disposal stands and the certificate stays draft."""
        manifest = self._manifest(self.code_a | self.code_b)
        manifest.action_submit()
        manifest.action_collect()
        Certificate = type(self.env['wm.compliance.certificate'])
        with patch.object(Certificate, 'action_issue', side_effect=UserError("PDF engine unavailable")):
            manifest.action_dispose()
        self.assertEqual(manifest.state, 'disposed')
        cert = self.env['wm.compliance.certificate'].search([('manifest_id', '=', manifest.id)])
        self.assertEqual(cert.state, 'draft')

    def test_expiry_reminder_not_recreated_after_done(self):
        """Marking the expiry To-Do done does not spawn a new one the next day."""
        doc = self.env['wm.compliance.document'].create({
            'name': 'Fix Permit',
            'document_type': 'permit',
            'expiry_date': fields.Date.today() + datetime.timedelta(days=5),
            'reminder_days': 30,
            'attachment_file': base64.b64encode(b'permit'),
            'attachment_filename': 'permit.pdf',
        })
        Document = self.env['wm.compliance.document']
        Activity = self.env['mail.activity']
        domain = [('res_model', '=', 'wm.compliance.document'), ('res_id', '=', doc.id)]

        Document.cron_check_document_expiry()
        activity = Activity.search(domain)
        self.assertEqual(len(activity), 1)
        activity.action_done()

        Document.cron_check_document_expiry()
        self.assertFalse(Activity.search(domain), "No new reminder for the same expiry date")

        # Renewal: a new expiry date gets a new reminder
        doc.expiry_date = fields.Date.today() + datetime.timedelta(days=10)
        Document.cron_check_document_expiry()
        self.assertEqual(len(Activity.search(domain)), 1)

    def test_status_cannot_be_forced_by_rpc_write(self):
        """A normal user cannot jump a draft manifest to Disposed, even with a bypass context key."""
        user = self.env['res.users'].create({
            'name': 'Fix Officer', 'login': 'fix_manifest_officer',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('wm_base.group_wm_compliance_officer').id])],
        })
        manifest = self._manifest(self.code_a | self.code_b)
        with self.assertRaises(UserError):
            manifest.with_user(user).write({'state': 'disposed'})
        with self.assertRaises(UserError):
            manifest.with_user(user).with_context(bypass_compliance_lock=True).write({'state': 'disposed'})
        self.assertEqual(manifest.state, 'draft')
        # The workflow buttons still work for the same user
        manifest.with_user(user).action_submit()
        self.assertEqual(manifest.state, 'submitted')
