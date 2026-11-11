# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
###############################################################################
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestCalendarChecklist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = new_test_user(cls.env, login='cmc_owner', groups='base.group_user')
        cls.other = new_test_user(cls.env, login='cmc_other', groups='base.group_user')
        cls.slides = cls.env['meeting.checklist'].create({'name': 'Bring slides'})
        cls.room = cls.env['meeting.checklist'].create({'name': 'Book room'})
        cls.template = cls.env['checklist.template'].create({
            'name': 'Board meeting', 'checklist_ids': [(6, 0, (cls.slides | cls.room).ids)]})

    def _event(self, privacy='private'):
        return self.env['calendar.event'].with_user(self.owner).create({
            'name': 'Board meeting',
            'privacy': privacy,
            'start': '2026-11-10 09:00:00',
            'stop': '2026-11-10 10:00:00',
            'partner_ids': [(6, 0, [self.owner.partner_id.id])],
            'checklist_line_ids': [(0, 0, {'checklist_id': self.slides.id}),
                                   (0, 0, {'checklist_id': self.room.id})],
        })

    def _completed_events(self):
        return self.env['calendar.event'].search([('completed_checklist', '=', True)])

    def test_progress_and_completed_filter(self):
        """The stored flag follows the lines without anyone opening the event."""
        event = self._event()
        line_slides, line_room = event.checklist_line_ids
        self.assertEqual(event.checklist_progress, 0)
        line_slides.with_user(self.owner).action_complete()
        self.assertEqual(event.checklist_progress, 50)
        self.assertNotIn(event, self._completed_events())
        line_room.with_user(self.owner).action_complete()
        self.env.invalidate_all()
        self.assertIn(event, self._completed_events())
        self.assertEqual(event.checklist_progress, 100)
        # Reopening a line must clear the flag again.
        line_room.write({'stage': 'new'})
        self.env.invalidate_all()
        self.assertNotIn(event, self._completed_events())

    def test_event_without_lines_is_not_completed(self):
        event = self._event()
        event.checklist_line_ids.unlink()
        self.assertEqual(event.checklist_progress, 0)
        self.assertFalse(event.completed_checklist)

    def test_other_user_can_read_private_event_progress(self):
        """Reading the progress of someone else's event must not try to write
        it (it used to raise AccessError, which broke the calendar list view).
        Calendar masks a private event's fields for other users, so they see 0."""
        event = self._event()
        event.checklist_line_ids.write({'stage': 'completed'})
        self.env.invalidate_all()
        self.assertEqual(event.with_user(self.other).checklist_progress, 0)
        self.env.invalidate_all()
        self.assertEqual(event.with_user(self.owner).checklist_progress, 100)
        self.assertTrue(event.with_user(self.owner).completed_checklist)

    def test_lines_follow_event_write_access(self):
        """A user who cannot edit a private event cannot change its checklist."""
        event = self._event()
        line = event.checklist_line_ids[0]
        Lines = self.env['calendar.checklist.lines'].with_user(self.other)
        with self.assertRaises(AccessError):
            line.with_user(self.other).action_complete()
        with self.assertRaises(AccessError):
            Lines.create({'event_id': event.id, 'checklist_id': self.slides.id})
        with self.assertRaises(AccessError):
            line.with_user(self.other).unlink()
        self.assertEqual(line.stage, 'new')
        self.assertEqual(len(event.checklist_line_ids), 2)
        # The owner keeps full control.
        line.with_user(self.owner).action_cancel()
        self.assertEqual(line.stage, 'canceled')
        line.with_user(self.owner).unlink()
        self.assertEqual(len(event.checklist_line_ids), 1)

    def test_public_event_lines_stay_editable(self):
        """On a public event, which other users may edit, nothing changes."""
        event = self._event(privacy='public')
        line = event.checklist_line_ids[0]
        line.with_user(self.other).action_complete()
        self.assertEqual(line.stage, 'completed')

    def test_line_cannot_be_moved_to_a_locked_event(self):
        own_event = self.env['calendar.event'].with_user(self.other).create({
            'name': 'Mine', 'start': '2026-11-11 09:00:00', 'stop': '2026-11-11 10:00:00',
            'checklist_line_ids': [(0, 0, {'checklist_id': self.slides.id})]})
        private_event = self._event()
        with self.assertRaises(AccessError):
            own_event.checklist_line_ids.with_user(self.other).write({'event_id': private_event.id})

    def test_template_onchange_fills_lines(self):
        event = self.env['calendar.event'].new({'name': 'New meeting'})
        event.checklist_template_ids = self.template
        event._onchange_checklist_template_ids()
        self.assertEqual(event.checklist_line_ids.checklist_id._origin, self.slides | self.room)
        self.assertEqual(set(event.checklist_line_ids.mapped('stage')), {'new'})
