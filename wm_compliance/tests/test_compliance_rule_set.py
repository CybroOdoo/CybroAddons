from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestComplianceRuleSet(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_us = cls.env.ref('base.us')
        cls.state_ca = cls.env.ref('base.state_us_5')  # California

        cls.generator = cls.env['res.partner'].create({
            'name': 'Test Generator Corp',
            'is_generator': True,
            'country_id': cls.country_us.id,
            'state_id': cls.state_ca.id,
        })
        cls.transporter = cls.env['res.partner'].create({
            'name': 'Test Logistics Transporter',
            'is_transporter': True,
        })
        cls.facility = cls.env['wm.disposal.facility'].create({
            'name': 'Green Disposal Plant',
            'facility_type': 'landfill',
        })

        cls.category_haz = cls.env['wm.waste.category'].create({
            'name': 'Chemical Hazardous Waste',
            'code': 'HAZ-CHEM',
        })

        cls.code_epa = cls.env['wm.compliance.code'].create({
            'name': 'EPA-HW-01 - EPA Hazardous Waste Tracking Code',
            'manifest_type': 'hazardous',
            'regulatory_body': 'EPA',
        })

        # Rules
        cls.global_rule = cls.env['wm.compliance.rule.set'].create({
            'name': 'Global Default Rule',
            'state': 'active',
            'sequence': 100,
            'requires_manifest': True,
        })
        cls.ca_haz_rule = cls.env['wm.compliance.rule.set'].create({
            'name': 'California Hazardous Rule',
            'state': 'active',
            'country_id': cls.country_us.id,
            'state_id': cls.state_ca.id,
            'waste_category_id': cls.category_haz.id,
            'required_code_ids': [(6, 0, [cls.code_epa.id])],
            'requires_manifest': True,
            'sequence': 10,
        })

    def test_01_rule_precedence_resolution(self):
        """Test rule resolution specificity ordering."""
        RuleSet = self.env['wm.compliance.rule.set']
        rules = RuleSet._get_applicable_rules(
            waste_category=self.category_haz,
            country=self.country_us,
            state=self.state_ca
        )
        self.assertTrue(rules)
        # California specific rule should be selected first over global default
        self.assertEqual(rules[0], self.ca_haz_rule)

    def test_02_onchange_and_submit_validation(self):
        """Test compliance code auto-suggestion and submit validation on manifest."""
        manifest = self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'line_ids': [(0, 0, {
                'waste_category_id': self.category_haz.id,
                'quantity': 250.0,
            })]
        })

        # Call onchange handler
        manifest._onchange_suggest_compliance_codes()
        self.assertIn(self.code_epa, manifest.compliance_code_ids)

        # Remove mandatory code and attempt to submit -> should raise UserError
        manifest.compliance_code_ids = [(5, 0, 0)]
        with self.assertRaises(UserError):
            manifest.action_submit()

        # Re-add code and submit -> should succeed
        manifest.compliance_code_ids = [(6, 0, [self.code_epa.id])]
        manifest.action_submit()
        self.assertEqual(manifest.state, 'submitted')

    def test_new_rule_set_starts_in_draft_until_activated(self):
        """A new rule set is a Draft (not enforced) until it is activated."""
        rule = self.env['wm.compliance.rule.set'].create({'name': 'Draft By Default'})
        self.assertEqual(rule.state, 'draft')
        self.assertNotIn(rule, self.env['wm.compliance.rule.set']._get_applicable_rules())
        rule.action_activate()
        self.assertEqual(rule.state, 'active')
        self.assertIn(rule, self.env['wm.compliance.rule.set']._get_applicable_rules())
