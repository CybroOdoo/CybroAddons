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
from datetime import date

from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestPersonalOrganiser(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_a = new_test_user(cls.env, login='po_user_a', groups='base.group_user')
        cls.user_b = new_test_user(cls.env, login='po_user_b', groups='base.group_user')
        cls.Task = cls.env['personal.organiser']
        cls.Note = cls.env['note.maker']

    def _task(self, user, title='Call supplier', day='2026-11-03'):
        return self.Task.with_user(user).create({'task_title': title, 'date': day})

    def test_create_links_allday_event(self):
        task = self._task(self.user_a)
        event = task.calendar_event_id
        self.assertTrue(event)
        self.assertEqual((event.name, event.allday, event.start_date, event.user_id),
                         ('Call supplier', True, date(2026, 11, 3), self.user_a))
        self.assertEqual(task.user_id, self.user_a)

    def test_write_updates_same_event(self):
        task = self._task(self.user_a)
        event = task.calendar_event_id
        task.with_user(self.user_a).write({'task_title': 'Call carrier', 'date': '2026-11-16'})
        self.assertEqual(task.calendar_event_id, event)
        self.assertEqual((event.name, event.start_date), ('Call carrier', date(2026, 11, 16)))

    def test_write_without_event_creates_one(self):
        task = self._task(self.user_a)
        task.calendar_event_id.unlink()
        self.assertFalse(task.calendar_event_id)
        task.write({'date': '2026-11-20'})
        self.assertEqual(task.calendar_event_id.start_date, date(2026, 11, 20))

    def test_unrelated_write_keeps_event(self):
        task = self._task(self.user_a)
        event = task.calendar_event_id
        task.write({'user_id': self.user_a.id})
        self.assertEqual(task.calendar_event_id, event)

    def test_unlink_removes_only_own_event(self):
        task = self._task(self.user_a)
        own_event = task.calendar_event_id
        # Another event with the same title must survive the task's deletion.
        other = self.env['calendar.event'].with_user(self.user_a).create({
            'name': 'Call supplier', 'allday': True,
            'start_date': '2026-11-03', 'stop_date': '2026-11-03',
        })
        task.with_user(self.user_a).unlink()
        self.assertFalse(own_event.exists())
        self.assertTrue(other.exists())

    def test_unlink_after_event_removed(self):
        task = self._task(self.user_a)
        task.calendar_event_id.unlink()
        task.unlink()
        self.assertFalse(task.exists())

    def test_tasks_and_notes_are_private(self):
        task = self._task(self.user_a)
        note = self.Note.with_user(self.user_a).create({'note_title': 'Team sync', 'note': 'Agenda'})
        self.assertEqual(note.user_id, self.user_a)
        self.assertFalse(self.Task.with_user(self.user_b).search([('id', '=', task.id)]))
        self.assertFalse(self.Note.with_user(self.user_b).search([('id', '=', note.id)]))
        self.assertEqual(self.Task.with_user(self.user_a).search([('id', '=', task.id)]), task)
        self.assertEqual(self.Note.with_user(self.user_a).search([('id', '=', note.id)]), note)
