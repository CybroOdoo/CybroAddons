# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
class TestPivotConditionalFormatting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPivotConditionalFormatting, cls).setUpClass()

        # Odoo 19 specific partner constraints
        # cls.env['ir.default'].set('res.partner', 'autopost_bills', 'never')
        
        # Get a model to test with
        cls.model_partner = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        
        # Create a pivot view for the model to fully test relations
        cls.view_partner_pivot = cls.env['ir.ui.view'].create({
            'name': 'Test Partner Pivot',
            'type': 'pivot',
            'model': 'res.partner',
            'arch': '<pivot string="Partners"><field name="name" type="row"/></pivot>'
        })

    def test_01_pivot_conditional_settings_domain(self):
        """Test the compute method for view_id_domain in pivot conditional settings."""


        setting = self.env['pivot.conditional.settings'].create({
            'model_id': self.model_partner.id,
        })


        expected_domain = [
            ('model', '=', 'res.partner'),
            ('type', '=', 'pivot')
        ]

        self.assertEqual(
            setting.view_id_domain,
            expected_domain,
            "The computed view domain should strictly filter by the selected model and pivot type."
        )

    def test_02_conditional_rules_creation(self):
        """Test the creation and relations of conditional rules."""

        setting = self.env['pivot.conditional.settings'].create({
            'model_id': self.model_partner.id,
            'view_id': self.view_partner_pivot.id,
        })


        rule = self.env['conditional.rules'].create({
            'conditional_id': setting.id,
            'rule': 'greater_than',
            'value': 100.0,
            'color': '#ff0000',
            'text_color': '#ffffff'
        })

        # Check defaults and related fields
        self.assertEqual(
            rule.company_id,
            self.env.company,
            "The default company should be the active environment company."
        )

        self.assertEqual(
            rule.model_id,
            self.model_partner,
            "The related model_id should be properly fetched from settings."
        )

        self.assertEqual(
            rule.view_id,
            self.view_partner_pivot,
            "The related view_id should be properly fetched from settings."
        )

    def test_03_conditional_rules_in_between(self):
        """Test creating an 'in_between' rule with two values."""

        setting = self.env['pivot.conditional.settings'].create({
            'model_id': self.model_partner.id,
            'view_id': self.view_partner_pivot.id,
        })


        rule = self.env['conditional.rules'].create({
            'conditional_id': setting.id,
            'rule': 'in_between',
            'value': 50.0,
            'second_value': 100.0,
            'color': '#00ff00',
            'text_color': '#000000'
        })


        self.assertEqual(rule.rule, 'in_between')
        self.assertEqual(rule.value, 50.0)
        self.assertEqual(rule.second_value, 100.0)

