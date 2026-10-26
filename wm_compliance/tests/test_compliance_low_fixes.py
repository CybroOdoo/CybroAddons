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

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_compliance')
class TestComplianceLowFixes(TransactionCase):
    """Regression tests for the wm_compliance low-severity fixes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.generator = cls.env['res.partner'].create({'name': 'Low Generator', 'is_generator': True})
        cls.transporter = cls.env['res.partner'].create({'name': 'Low Transporter', 'is_transporter': True})
        cls.facility = cls.env['wm.disposal.facility'].create({'name': 'Low Plant', 'facility_type': 'landfill'})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Low Typed Waste', 'code': 'LOWTW'})
        cls.Dashboard = cls.env['wm.compliance.dashboard']
        cls.Custody = cls.env['wm.compliance.custody']

    def _manifest(self, lines=None, **vals):
        return self.env['wm.compliance.manifest'].create(dict({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'line_ids': [(0, 0, line) for line in (lines if lines is not None else [
                {'waste_category_id': self.category.id, 'quantity': 100.0}])],
        }, **vals))

    def _dispose(self, manifest):
        manifest.action_submit()
        manifest.action_collect()
        manifest.action_dispose()

    # ---- L-01 ---------------------------------------------------------------
    def test_certificate_quantity_is_real_total(self):
        """The certificate carries the real total, never a placeholder 1.0;
        a zero-quantity manifest cannot be disposed/certified at all."""
        manifest = self._manifest(lines=[{'waste_category_id': self.category.id, 'quantity': 0.0}])
        with self.assertRaises(UserError):
            self._dispose(manifest)
        cert = self.env['wm.compliance.certificate'].search([('manifest_id', '=', manifest.id)])
        self.assertFalse(cert)

        manifest = self._manifest(lines=[{'waste_category_id': self.category.id, 'quantity': 42.5}])
        self._dispose(manifest)
        cert = self.env['wm.compliance.certificate'].search([('manifest_id', '=', manifest.id)])
        self.assertEqual(cert.quantity, 42.5)

    # ---- L-02 ---------------------------------------------------------------
    def test_dashboard_keeps_all_time_transit_quantity(self):
        """The all-time in-transit quantity is not overwritten by the period value."""
        today = fields.Date.context_today(self.env['wm.compliance.manifest'])
        base = self.Dashboard.get_dashboard_data('today')
        self._manifest(
            lines=[{'waste_category_id': self.category.id, 'quantity': 70.0}],
            manifest_date=today - datetime.timedelta(days=60), state='collected')
        data = self.Dashboard.get_dashboard_data('today')
        self.assertAlmostEqual(data['active_transit_qty'], base['active_transit_qty'] + 70.0)
        # The period value only covers manifests dated in the timeframe
        self.assertAlmostEqual(data['manifest_transit_qty'], base['manifest_transit_qty'])

    # ---- L-03 ---------------------------------------------------------------
    def test_missing_custody_milestone_alert(self):
        """A manifest lacking the custody milestone of its state is flagged."""
        base = self.Dashboard.get_dashboard_data('month')['pending_custody_count']
        manifest = self._manifest(state='collected')
        # Only the generation milestone: the collection one is missing
        self.Custody.create({'manifest_id': manifest.id, 'action': 'generated'})
        data = self.Dashboard.get_dashboard_data('month')
        self.assertEqual(data['pending_custody_count'], base + 1)
        self.assertIn(manifest.id, [m['id'] for m in data['urgent_manifests']])
        # Unrelated custody steps do not satisfy the milestone
        self.Custody.create({'manifest_id': manifest.id, 'action': 'in_transit'})
        self.assertEqual(self.Dashboard.get_dashboard_data('month')['pending_custody_count'], base + 1)
        self.Custody.create({'manifest_id': manifest.id, 'action': 'collected'})
        self.assertEqual(self.Dashboard.get_dashboard_data('month')['pending_custody_count'], base)

        # A disposed manifest without a disposal entry is flagged as well
        disposed = self._manifest(state='disposed')
        self.assertEqual(self.Dashboard.get_dashboard_data('month')['pending_custody_count'], base + 1)
        self.Custody.create({'manifest_id': disposed.id, 'action': 'disposed'})
        self.assertEqual(self.Dashboard.get_dashboard_data('month')['pending_custody_count'], base)

        # The regular workflow always logs its milestones
        regular = self._manifest()
        self._dispose(regular)
        self.assertFalse(self.env['wm.compliance.manifest'].search(
            self.Dashboard._get_missing_custody_domain() + [('id', '=', regular.id)]))

    # ---- L-04 ---------------------------------------------------------------
    def test_deleting_attachment_keeps_document(self):
        """Removing the stored file does not delete the permit record."""
        doc = self.env['wm.compliance.document'].create({
            'name': 'Low Permit',
            'attachment_file': base64.b64encode(b'permit content'),
            'attachment_filename': 'permit.pdf',
            'expiry_date': fields.Date.today() + datetime.timedelta(days=90),
        })
        self.assertTrue(doc.attachment_id)
        doc.attachment_id.unlink()
        self.assertTrue(doc.exists())
        self.assertFalse(doc.attachment_id)
        self.assertFalse(doc.attachment_file)

    # ---- L-06 ---------------------------------------------------------------
    def test_custody_rows_use_manifest_company(self):
        """Custody rows and certificates follow the manifest's company."""
        company_b = self.env['res.company'].create({'name': 'Low Company B'})
        self.assertNotEqual(self.env.company, company_b)
        manifest = self._manifest(company_id=company_b.id)
        self._dispose(manifest)
        self.assertEqual(len(manifest.custody_ids), 3)
        self.assertEqual(manifest.custody_ids.company_id, company_b)
        cert = self.env['wm.compliance.certificate'].search([('manifest_id', '=', manifest.id)])
        self.assertEqual(cert.company_id, company_b)
        # Manually logged custody rows default to the manifest company too
        draft = self._manifest(company_id=company_b.id)
        row = self.Custody.create({'manifest_id': draft.id, 'action': 'generated'})
        self.assertEqual(row.company_id, company_b)

    # ---- L-16 ---------------------------------------------------------------
    def test_certificate_number_from_sequence(self):
        """Certificates without a number are numbered from their sequence."""
        sequence = self.env.ref('wm_compliance.seq_wm_compliance_certificate')
        self.assertEqual(sequence.code, 'wm.compliance.certificate')
        cert = self.env['wm.compliance.certificate'].create({
            'name': 'Low Manual Certificate',
            'facility_id': self.facility.id,
        })
        self.assertTrue(cert.certificate_no.startswith('COD/'))
        explicit = self.env['wm.compliance.certificate'].create({
            'name': 'Low Explicit Certificate',
            'facility_id': self.facility.id,
            'certificate_no': 'EXT-001',
        })
        self.assertEqual(explicit.certificate_no, 'EXT-001')
        # Auto-issued certificates use the same sequence
        manifest = self._manifest()
        self._dispose(manifest)
        auto = self.env['wm.compliance.certificate'].search([('manifest_id', '=', manifest.id)])
        self.assertTrue(auto.certificate_no.startswith('COD/'))

    def test_workflow_buttons_hidden_for_ops_manager(self):
        """Read-only operations managers do not get the workflow buttons."""
        ops = new_test_user(self.env, login='low_ops_mgr', groups='base.group_user,wm_base.group_wm_ops_manager')
        officer = new_test_user(self.env, login='low_officer', groups='base.group_user,wm_base.group_wm_compliance_officer')
        buttons = {
            'wm.compliance.manifest': ['action_submit', 'action_collect', 'action_dispose', 'action_export_and_notify'],
            'wm.compliance.certificate': ['action_issue'],
        }
        for model, names in buttons.items():
            ops_arch = self.env[model].with_user(ops).get_views([(False, 'form')])['views']['form']['arch']
            officer_arch = self.env[model].with_user(officer).get_views([(False, 'form')])['views']['form']['arch']
            for name in names:
                self.assertNotIn('name="%s"' % name, ops_arch)
                self.assertIn('name="%s"' % name, officer_arch)
