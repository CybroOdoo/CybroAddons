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
import datetime

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_compliance')
class TestComplianceMediumFixes(TransactionCase):
    """Regression tests for the wm_compliance medium-severity fixes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.generator = cls.env['res.partner'].create({'name': 'Med Generator', 'is_generator': True})
        cls.transporter = cls.env['res.partner'].create({'name': 'Med Transporter', 'is_transporter': True})
        cls.facility = cls.env['wm.disposal.facility'].create({'name': 'Med Plant', 'facility_type': 'landfill'})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Med Typed Waste', 'code': 'MEDTW'})
        cls.kg = cls.env.ref('uom.product_uom_kgm')
        cls.ton = cls.env.ref('uom.product_uom_ton')
        cls.litre = cls.env.ref('uom.product_uom_litre')

    def _manifest(self, codes=None, lines=None, **vals):
        return self.env['wm.compliance.manifest'].create(dict({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'compliance_code_ids': [(6, 0, codes.ids if codes else [])],
            'line_ids': [(0, 0, line) for line in (lines or [
                {'waste_category_id': self.category.id, 'quantity': 100.0}])],
        }, **vals))

    # ---- M-05 ---------------------------------------------------------------
    def test_typed_rule_applies_without_and_with_matching_type(self):
        code = self.env['wm.compliance.code'].create({'name': 'MED-HAZ', 'manifest_type': 'hazardous'})
        med_code = self.env['wm.compliance.code'].create({'name': 'MED-MED', 'manifest_type': 'medical'})
        rule = self.env['wm.compliance.rule.set'].create({
            'name': 'Med Hazardous Typed Rule',
            'state': 'active',
            'waste_category_id': self.category.id,
            'manifest_type': 'hazardous',
            'required_code_ids': [(6, 0, code.ids)],
        })
        RuleSet = self.env['wm.compliance.rule.set']
        self.assertIn(rule, RuleSet._get_applicable_rules(waste_category=self.category))
        self.assertIn(rule, RuleSet._get_applicable_rules(waste_category=self.category, manifest_type='hazardous'))
        self.assertNotIn(rule, RuleSet._get_applicable_rules(waste_category=self.category, manifest_type='medical'))

        # Untyped manifest: the typed rule is enforced
        manifest = self._manifest()
        with self.assertRaises(UserError):
            manifest.action_submit()
        # A medical manifest is not subject to the hazardous rule
        medical = self._manifest(codes=med_code)
        self.assertEqual(medical._get_manifest_type(), 'medical')
        medical.action_submit()
        self.assertEqual(medical.state, 'submitted')
        # Hazardous manifest with the required code passes
        hazardous = self._manifest(codes=code)
        hazardous.action_submit()
        self.assertEqual(hazardous.state, 'submitted')

    # ---- M-06 / M-07 --------------------------------------------------------
    def test_target_role_company_and_uom(self):
        today = fields.Date.today()
        self._manifest(lines=[
            {'waste_category_id': self.category.id, 'quantity': 1.0, 'uom_id': self.ton.id},
            {'waste_category_id': self.category.id, 'quantity': 500.0, 'uom_id': self.kg.id},
            {'waste_category_id': self.category.id, 'quantity': 7.0, 'uom_id': self.litre.id},
            {'waste_category_id': self.category.id, 'quantity': 3.0},
        ]).action_submit()
        target = self.env['wm.compliance.target'].create({
            'partner_id': self.generator.id,
            'partner_role': 'generator',
            'waste_category_id': self.category.id,
            'period_start': today - datetime.timedelta(days=1),
            'period_end': today + datetime.timedelta(days=1),
            'target_quantity': 1000.0,
        })
        # 1 t + 500 kg converted; litres and no-uom lines kept as-is
        self.assertAlmostEqual(target.achieved_quantity, 1000.0 + 500.0 + 7.0 + 3.0)
        # partner_role is a dependency: changing it recomputes
        target.partner_role = 'transporter'
        self.assertEqual(target.achieved_quantity, 0.0)
        target.partner_role = 'generator'
        # Another company's target does not count this company's manifests
        company_b = self.env['res.company'].create({'name': 'Med Company B'})
        target.company_id = company_b
        self.assertEqual(target.achieved_quantity, 0.0)

    def test_target_not_limited_by_current_user_rules(self):
        today = fields.Date.today()
        self._manifest().action_submit()
        target = self.env['wm.compliance.target'].create({
            'partner_id': self.generator.id,
            'waste_category_id': self.category.id,
            'period_start': today,
            'period_end': today,
            'target_quantity': 100.0,
        })
        self.assertAlmostEqual(target.achieved_quantity, 100.0)
        # Recomputed by a user currently working in another company only
        company_b = self.env['res.company'].create({'name': 'Med Company Other'})
        user = new_test_user(self.env, login='med_target_officer', groups='wm_base.group_wm_compliance_officer',
                             company_id=company_b.id, company_ids=[(6, 0, (company_b | self.env.company).ids)])
        # (target fields are loaded in cache first: only the line search is
        # under test, the user cannot read the target itself in company B)
        target.read(['partner_id', 'partner_role', 'waste_category_id', 'period_start',
                     'period_end', 'target_quantity', 'company_id'])
        user_target = target.with_user(user).with_context(allowed_company_ids=[company_b.id])
        computed = [target._fields[f] for f in ('achieved_quantity', 'compliance_pct', 'state')]
        with user_target.env.protecting(computed, user_target):
            user_target._compute_achieved_quantity()
        self.assertAlmostEqual(target.achieved_quantity, 100.0)

    def test_manifest_total_in_kg(self):
        manifest = self._manifest(lines=[
            {'waste_category_id': self.category.id, 'quantity': 2.0, 'uom_id': self.ton.id},
            {'waste_category_id': self.category.id, 'quantity': 250.0, 'uom_id': self.kg.id},
        ])
        self.assertAlmostEqual(manifest.total_quantity, 2250.0)

    # ---- M-08 ---------------------------------------------------------------
    def _officer(self):
        return new_test_user(self.env, login='med_lock_officer', groups='wm_base.group_wm_compliance_officer')

    def test_submitted_manifest_is_locked(self):
        officer = self._officer()
        manifest = self._manifest().with_user(officer)
        manifest.action_submit()
        line = manifest.line_ids
        with self.assertRaises(UserError):
            line.quantity = 5.0
        with self.assertRaises(UserError):
            line.unlink()
        with self.assertRaises(UserError):
            self.env['wm.compliance.manifest.line'].with_user(officer).create({
                'manifest_id': manifest.id, 'waste_category_id': self.category.id, 'quantity': 1.0})
        with self.assertRaises(UserError):
            manifest.generator_id = self.transporter
        with self.assertRaises(UserError):
            manifest.write({'line_ids': [(0, 0, {'waste_category_id': self.category.id, 'quantity': 1.0})]})
        # Workflow and chatter remain possible
        manifest.message_post(body="note")
        manifest.transport_mode = 'rail'
        manifest.action_collect()
        manifest.action_dispose()
        self.assertEqual(manifest.state, 'disposed')
        self.assertTrue(self.env['wm.compliance.certificate'].search([('manifest_id', '=', manifest.id)]))

    def test_draft_manifest_lines_editable_and_inline_create(self):
        officer = self._officer()
        manifest = self._manifest().with_user(officer)
        manifest.line_ids.quantity = 42.0
        self.assertEqual(manifest.total_quantity, 42.0)
        # Creating directly in a non-draft state with inline lines still works
        submitted = self.env['wm.compliance.manifest'].with_user(officer).create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'state': 'submitted',
            'line_ids': [(0, 0, {'waste_category_id': self.category.id, 'quantity': 3.0})],
        })
        self.assertEqual(len(submitted.line_ids), 1)
        with self.assertRaises(UserError):
            submitted.line_ids.quantity = 8.0
        # Superuser (automation) and the explicit bypass may still correct it
        submitted.sudo().line_ids.quantity = 7.0
        self.assertEqual(submitted.total_quantity, 7.0)
        submitted.line_ids.sudo().with_context(bypass_compliance_lock=True).quantity = 6.0
        self.assertEqual(submitted.total_quantity, 6.0)

    # ---- M-09 ---------------------------------------------------------------
    def test_report_builder_filters(self):
        draft = self._manifest()
        submitted = self._manifest()
        submitted.action_submit()
        Report = self.env['wm.compliance.report']
        today = fields.Date.today()
        wizard = Report.create({'report_type': 'manifest', 'output_format': 'pdf',
                                'date_from': today, 'date_to': today, 'facility_id': self.facility.id})
        ids = wizard.action_generate()['context']['active_ids']
        self.assertIn(submitted.id, ids)
        self.assertNotIn(draft.id, ids)

        Cert = self.env['wm.compliance.certificate']
        common = {'certificate_type': 'disposal', 'facility_id': self.facility.id, 'quantity': 1.0}
        issued = Cert.create(dict(common, name='Med Issued', certificate_no='MED-C1', state='issued', issued_date=today))
        Cert.create(dict(common, name='Med Draft', certificate_no='MED-C2', state='draft'))
        Cert.create(dict(common, name='Med Old', certificate_no='MED-C3', state='issued',
                         issued_date=today - datetime.timedelta(days=400)))
        wizard = Report.create({'report_type': 'certificate', 'output_format': 'pdf',
                                'date_from': today, 'date_to': today, 'facility_id': self.facility.id})
        ids = wizard.action_generate()['context']['active_ids']
        self.assertEqual(ids, issued.ids)

    # ---- V-19 ---------------------------------------------------------------
    def test_multi_certificate_copy(self):
        Cert = self.env['wm.compliance.certificate']
        common = {'certificate_type': 'disposal', 'facility_id': self.facility.id, 'quantity': 1.0}
        certs = Cert.create([dict(common, name='Med Copy A', certificate_no='MED-CA'),
                             dict(common, name='Med Copy B', certificate_no='MED-CB', state='issued')])
        copies = certs.copy()
        self.assertEqual(len(copies), 2)
        self.assertEqual(sorted(copies.mapped('name')), ['Med Copy A (Copy)', 'Med Copy B (Copy)'])
        self.assertEqual(set(copies.mapped('state')), {'draft'})

    # ---- X-11 ---------------------------------------------------------------
    def test_company_rules_on_children(self):
        company_b = self.env['res.company'].create({'name': 'Med Rules Company'})
        manifest = self._manifest()
        manifest.action_submit()
        user = new_test_user(self.env, login='med_rules_officer', groups='wm_base.group_wm_compliance_officer',
                             company_id=company_b.id, company_ids=[(6, 0, company_b.ids)])
        rule_set = self.env['wm.compliance.rule.set'].create({'name': 'Med Company Rule'})
        for records in (manifest.line_ids, manifest.custody_ids, rule_set, manifest.signature_id):
            self.assertTrue(records)
            self.assertFalse(records.with_user(user).search([('id', 'in', records.ids)]),
                             "%s must be company-restricted" % records._name)
        self.assertEqual(manifest.signature_id.company_id, manifest.company_id)

    # ---- X-12 ---------------------------------------------------------------
    def test_dashboard_requires_compliance_group(self):
        Dashboard = self.env['wm.compliance.dashboard']
        plain = new_test_user(self.env, login='med_dash_plain', groups='base.group_user')
        with self.assertRaises(AccessError):
            Dashboard.with_user(plain).get_dashboard_data('month')
        officer = new_test_user(self.env, login='med_dash_officer', groups='wm_base.group_wm_compliance_officer')
        data = Dashboard.with_user(officer).get_dashboard_data('month')
        self.assertTrue(data['can_access_manifest'])
