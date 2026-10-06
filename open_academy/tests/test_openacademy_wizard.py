# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestOpenAcademyWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestOpenAcademyWizard, cls).setUpClass()
        # Create course and sessions
        cls.course = cls.env['openacademy.course'].create({
            'name': 'Odoo Development',
        })
        cls.session_1 = cls.env['openacademy.session'].create({
            'name': 'Session 1',
            'course_id': cls.course.id,
        })
        cls.session_2 = cls.env['openacademy.session'].create({
            'name': 'Session 2',
            'course_id': cls.course.id,
        })

        # Create attendees
        cls.attendee_1 = cls.env['res.partner'].create({
            'name': 'John Attendee',
        })
        cls.attendee_2 = cls.env['res.partner'].create({
            'name': 'Mary Attendee',
        })

    def test_wizard_attendee_registration(self):
        """ Test that registering attendees via wizard subscribes them to selected sessions """
        # Verify initial state of sessions is empty of these attendees
        self.assertNotIn(self.attendee_1, self.session_1.attendee_ids)
        self.assertNotIn(self.attendee_2, self.session_1.attendee_ids)
        self.assertNotIn(self.attendee_1, self.session_2.attendee_ids)
        self.assertNotIn(self.attendee_2, self.session_2.attendee_ids)

        # Create wizard with active_ids context to simulate action
        wizard = self.env['openacademy.wizard'].with_context(
            active_ids=[self.session_1.id, self.session_2.id]
        ).create({
            'attendee_ids': [(6, 0, [self.attendee_1.id, self.attendee_2.id])],
        })

        # Subscribe attendees to sessions
        res = wizard.subscribe()
        self.assertEqual(res, {})

        # Verify that both attendees were subscribed to both sessions
        self.assertIn(self.attendee_1, self.session_1.attendee_ids)
        self.assertIn(self.attendee_2, self.session_1.attendee_ids)
        self.assertIn(self.attendee_1, self.session_2.attendee_ids)
        self.assertIn(self.attendee_2, self.session_2.attendee_ids)
