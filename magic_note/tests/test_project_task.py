# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProjectTask(TransactionCase):

    def setUp(self):
        super().setUp()

        # Config parameters
        self.config = self.env['ir.config_parameter'].sudo()

        self.config.set_str(
            'magic_note.note_color_default',
            'green'
        )

        self.config.set_str(
            'magic_note.after_deadline',
            'red'
        )

        self.config.set_str(
            'magic_note.not_in_interval',
            'grey'
        )

        # Create interval
        self.interval = self.env['note.color'].create({
            'name': 'Urgent',
            'color_note': 'orange',
            'start_interval': fields.Date.today(),
            'end_interval': fields.Date.today() + timedelta(days=5),
        })

    def test_compute_inside_interval(self):
        """ Test color assignment inside interval """
        task = self.env['project.task'].create({
            'name': 'Interval Task',
            'date_deadline': fields.Date.today() + timedelta(days=2),
        })
        self.assertEqual(
            task.note_color,
            'orange'
        )

    def test_compute_after_deadline(self):
        """ Test after deadline condition """
        self.env['note.color'].search([]).unlink()

        task = self.env['project.task'].create({
            'name': 'Expired Task',
            'date_deadline': fields.Date.today() - timedelta(days=1),
        })
        self.assertEqual(
            task.note_color,
            'red'
        )

    def test_compute_after_deadline_with_intervals(self):
        """ Test after deadline condition with intervals present """
        task = self.env['project.task'].create({
            'name': 'Expired Task with Interval',
            'date_deadline': fields.Date.today() - timedelta(days=1),
        })
        self.assertEqual(
            task.note_color,
            'red'
        )

    def test_compute_default_color(self):
        """ Test default color condition """
        self.env['note.color'].search([]).unlink()

        task = self.env['project.task'].create({
            'name': 'Default Task',
            'date_deadline': fields.Date.today() + timedelta(days=2),
        })
        self.assertEqual(task.note_color, 'green')

    def test_compute_not_in_interval(self):
        """ Test not inside interval condition """
        task = self.env['project.task'].create({
            'name': 'Outside Interval',
            'date_deadline': fields.Date.today() + timedelta(days=10),
        })
        self.assertEqual(
            task.note_color,
            'grey'
        )

        with self.assertRaises(ValidationError):
            self.env['note.color'].create({
                'name': 'Invalid Interval',
                'color_note': 'red',
                'start_interval': fields.Date.today() + timedelta(days=5),
                'end_interval': fields.Date.today() + timedelta(days=1),
            })
