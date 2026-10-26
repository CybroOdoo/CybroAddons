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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProjectReport(TransactionCase):
    """Test cases for project report rendering in volunteers_donors_management."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.volunteer_type = cls.env['volunteer.type'].create({
            'volunteer_type': 'Field Worker',
            'volunteer_code': 'FW_01',
        })
        cls.volunteer_skill = cls.env['volunteer.skill'].create({
            'volunteer_skill': 'Logistics',
            'volunteer_skill_code': 'LOG_01',
        })
        cls.volunteer = cls.env['res.partner'].create({
            'name': 'Volunteer Bob',
            'email': 'bob@example.com',
            'phone': '+123456789',
            'is_volunteer': True,
            'volunteer_type_id': cls.volunteer_type.id,
            'volunteer_skill_ids': [Command.link(cls.volunteer_skill.id)],
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Emergency Response Project',
            'project_partner_ids': [Command.link(cls.volunteer.id)],
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Setup Camp',
            'project_id': cls.project.id,
            'allocated_hours': 10.0,
        })

    def test_project_report_rendering(self):
        """Verify project report generates successfully with volunteers and tasks."""
        report = self.env.ref('volunteers_donors_management.project_report_action')
        content, content_type = report._render_qweb_pdf(report, res_ids=self.project.ids)
        self.assertTrue(content)
        self.assertIn(content_type, ('pdf', 'html'))
