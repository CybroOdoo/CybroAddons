# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMembershipCard(TransactionCase):
    """Test suite for membership.card.line model, paperformat, and report."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Card Test Partner',
            'phone': '+1 555-0199',
            'email': 'card_test@example.com',
        })

        cls.service_product = cls.env['product.template'].create({
            'name': 'Premium Membership Plan',
            'type': 'service',
        })

        cls.consu_product = cls.env['product.template'].create({
            'name': 'Physical Merchandise',
            'type': 'consu',
        })

    def test_create_valid_membership_card_line(self):
        """Test successful creation of a membership card line."""
        today = fields.Date.context_today(self.partner)
        line = self.env['membership.card.line'].create({
            'partner_id': self.partner.id,
            'membership_id': self.service_product.id,
            'date_from': today,
            'date_to': today + timedelta(days=365),
        })
        self.assertTrue(line.id)
        self.assertEqual(line.partner_id, self.partner)
        self.assertEqual(line.membership_id, self.service_product)
        self.assertEqual(line.date_from, today)
        self.assertEqual(line.date_to, today + timedelta(days=365))

    def test_constrain_service_product_type(self):
        """Test that membership_id must be a service product."""
        today = fields.Date.context_today(self.partner)
        with self.assertRaises(ValidationError) as error:
            self.env['membership.card.line'].create({
                'partner_id': self.partner.id,
                'membership_id': self.consu_product.id,
                'date_from': today,
                'date_to': today + timedelta(days=30),
            })
        self.assertIn(
            "must be a service product",
            str(error.exception),
        )

    def test_constrain_dates_valid(self):
        """Test that date_to cannot be earlier than date_from."""
        today = fields.Date.context_today(self.partner)
        with self.assertRaises(ValidationError) as error:
            self.env['membership.card.line'].create({
                'partner_id': self.partner.id,
                'membership_id': self.service_product.id,
                'date_from': today,
                'date_to': today - timedelta(days=5),
            })
        self.assertIn(
            "cannot be earlier than Start Date",
            str(error.exception),
        )

    def test_line_ordering(self):
        """Test that membership card lines are ordered by date_from desc."""
        today = fields.Date.context_today(self.partner)
        line_old = self.env['membership.card.line'].create({
            'partner_id': self.partner.id,
            'membership_id': self.service_product.id,
            'date_from': today - timedelta(days=50),
            'date_to': today - timedelta(days=20),
        })
        line_new = self.env['membership.card.line'].create({
            'partner_id': self.partner.id,
            'membership_id': self.service_product.id,
            'date_from': today,
            'date_to': today + timedelta(days=30),
        })
        lines = self.partner.member_lines
        self.assertEqual(lines[0], line_new)
        self.assertEqual(lines[1], line_old)

    def test_partner_cascade_deletion(self):
        """Test deleting partner cascades to its membership card lines."""
        partner = self.env['res.partner'].create({'name': 'Temp Partner'})
        today = fields.Date.context_today(partner)
        line = self.env['membership.card.line'].create({
            'partner_id': partner.id,
            'membership_id': self.service_product.id,
            'date_from': today,
            'date_to': today + timedelta(days=30),
        })
        line_id = line.id
        partner.unlink()
        self.assertFalse(
            self.env['membership.card.line'].browse(line_id).exists(),
        )

    def test_access_rights_internal_user(self):
        """Test CRUD permissions for standard internal user."""
        test_user = self.env['res.users'].create({
            'name': 'Test Internal User',
            'login': 'test_internal_user',
            'email': 'user@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        today = fields.Date.context_today(self.partner)
        line = self.env['membership.card.line'].with_user(test_user).create({
            'partner_id': self.partner.id,
            'membership_id': self.service_product.id,
            'date_from': today,
            'date_to': today + timedelta(days=30),
        })
        self.assertTrue(line.id)
        # Read
        read_data = line.with_user(test_user).read(['membership_id'])
        self.assertEqual(
            read_data[0]['membership_id'][0],
            self.service_product.id,
        )
        # Write
        new_date_to = today + timedelta(days=60)
        line.with_user(test_user).write({'date_to': new_date_to})
        self.assertEqual(line.date_to, new_date_to)
        # Unlink
        line_id = line.id
        line.with_user(test_user).unlink()
        self.assertFalse(
            self.env['membership.card.line'].browse(line_id).exists(),
        )

    def test_paperformat_configuration(self):
        """Test custom paper format record properties."""
        paperformat = self.env.ref(
            'membership_card_odoo.paperformat_card',
        )
        self.assertTrue(paperformat)
        self.assertEqual(paperformat.page_height, 95)
        self.assertEqual(paperformat.page_width, 60)
        self.assertEqual(paperformat.orientation, 'Landscape')
        self.assertEqual(paperformat.header_spacing, 0)
        self.assertFalse(paperformat.default)

    def test_report_qweb_pdf_rendering(self):
        """Test PDF report generation action renders successfully."""
        report = self.env.ref(
            'membership_card_odoo.action_membership_card',
        )
        self.assertTrue(report)
        data = {
            'name': 'Test Member',
            'image': '',
            'phone': '123456789',
            'function': 'Developer',
            'free_member': True,
            'membership_product': [],
            'start_date': '',
            'end_date': '',
            'company_name': self.env.company.name,
            'company_address': self.env.company.street or '',
            'city': self.env.company.city or '',
            'country': self.env.company.country_id.name or '',
            'state': self.env.company.state_id.name or '',
            'company_email': self.env.company.email or '',
            'company_phone': self.env.company.phone or '',
            'website': self.env.company.website or '',
        }
        pdf_content, content_type = report._render_qweb_pdf(
            report.id,
            res_ids=None,
            data=data,
        )
        self.assertIn(content_type, ('pdf', 'html'))
        self.assertTrue(len(pdf_content) > 0)
