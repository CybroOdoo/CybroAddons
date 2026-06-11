# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bashir Muhammed A (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase


class TestMailTemplate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a parent company partner
        cls.parent_partner = cls.env['res.partner'].create({
            'name': 'Test Parent Company',
            'is_company': True,
            'email': 'parent@example.com',
        })

        # Create child contact partners under parent company
        cls.child_partner_1 = cls.env['res.partner'].create({
            'name': 'Test Child Contact 1',
            'parent_id': cls.parent_partner.id,
            'email': 'child1@example.com',
        })
        cls.child_partner_2 = cls.env['res.partner'].create({
            'name': 'Test Child Contact 2',
            'parent_id': cls.parent_partner.id,
            'email': 'child2@example.com',
        })

        # Create a dummy mail template
        cls.template = cls.env['mail.template'].create({
            'name': 'Test Child Contacts Template',
            'model_id': cls.env.ref('base.model_res_partner').id,
        })

    def test_01_generate_template_recipients_adds_children(self):
        """Test that _generate_template_recipients adds child contacts of the commercial partner"""
        # Mock the initial render results as returned by super()
        initial_render_results = {
            self.parent_partner.id: {
                'partner_ids': [self.parent_partner.id],
            }
        }

        res = self.template._generate_template_recipients(
            res_ids=[self.parent_partner.id],
            render_fields=['partner_to'],
            render_results=initial_render_results
        )

        partner_ids = res[self.parent_partner.id]['partner_ids']
        # The parent partner and both child partners should be present
        self.assertIn(self.parent_partner.id, partner_ids)
        self.assertIn(self.child_partner_1.id, partner_ids)
        self.assertIn(self.child_partner_2.id, partner_ids)
        # Verify the size is at least 3
        self.assertEqual(len(partner_ids), 3)

    def test_02_generate_template_recipients_no_results(self):
        """Test that _generate_template_recipients returns empty if no record IDs are passed"""
        res = self.template._generate_template_recipients(
            res_ids=[],
            render_fields=['partner_to'],
            render_results={}
        )
        self.assertEqual(res, {})

    def test_03_generate_template_recipients_no_partner_ids(self):
        """Test that _generate_template_recipients does not crash and works if partner_ids is missing or empty"""
        self.template.use_default_to = False
        self.template.partner_to = False
        res = self.template._generate_template_recipients(
            res_ids=[self.parent_partner.id],
            render_fields=['partner_to']
        )
        partner_ids = res.get(self.parent_partner.id, {}).get('partner_ids', [])
        self.assertEqual(partner_ids, [])
