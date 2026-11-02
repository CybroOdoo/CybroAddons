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
from datetime import timedelta

import psycopg2

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestActivityDashboard(TransactionCase):
    """Test suite covering Activity Dashboard and Tag functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner for Activity',
        })
        cls.activity_type = cls.env['mail.activity.type'].search([], limit=1)
        if not cls.activity_type:
            cls.activity_type = cls.env['mail.activity.type'].create({
                'name': 'Test Call',
                'delay_count': 1,
            })

        cls.tag_urgent = cls.env['activity.tag'].create({
            'name': 'Urgent Tag',
        })
        cls.tag_followup = cls.env['activity.tag'].create({
            'name': 'Follow-up Tag',
            'color': 5,
        })

    def test_activity_tag_creation(self):
        """Test activity tag creation, default color, and constraints."""
        tag = self.env['activity.tag'].create({
            'name': 'Review Tag',
        })
        self.assertTrue(tag.id)
        self.assertTrue(1 <= tag.color <= 11)

        # Unique name constraint
        with mute_logger('odoo.sql_db'), self.assertRaises((ValidationError, psycopg2.IntegrityError)):
            self.env['activity.tag'].create({
                'name': 'Review Tag',
            })

    def test_mail_activity_with_tags(self):
        """Test mail.activity creation with tags."""
        activity = self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id('res.partner'),
            'res_id': self.partner.id,
            'activity_type_id': self.activity_type.id,
            'summary': 'Call partner with tags',
            'date_deadline': self.today + timedelta(days=2),
            'activity_tag_ids': [(6, 0, [self.tag_urgent.id, self.tag_followup.id])],
        })
        self.assertEqual(len(activity.activity_tag_ids), 2)
        self.assertIn(self.tag_urgent, activity.activity_tag_ids)

    def test_activity_state_search(self):
        """Test _search_state for planned, today, overdue, and done states."""
        # 1. Planned activity (future date)
        planned_act = self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id('res.partner'),
            'res_id': self.partner.id,
            'activity_type_id': self.activity_type.id,
            'summary': 'Planned Activity',
            'date_deadline': self.today + timedelta(days=3),
        })

        # 2. Today activity
        today_act = self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id('res.partner'),
            'res_id': self.partner.id,
            'activity_type_id': self.activity_type.id,
            'summary': 'Today Activity',
            'date_deadline': self.today,
        })

        # 3. Overdue activity (past date)
        overdue_act = self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id('res.partner'),
            'res_id': self.partner.id,
            'activity_type_id': self.activity_type.id,
            'summary': 'Overdue Activity',
            'date_deadline': self.today - timedelta(days=3),
        })

        # 4. Search planned (must exclude today and overdue)
        test_scope_ids = (planned_act | today_act | overdue_act).ids
        found_planned = self.env['mail.activity'].search([
            ('id', 'in', test_scope_ids),
            ('state', '=', 'planned'),
        ])
        self.assertEqual(found_planned, planned_act)
        self.assertNotIn(today_act, found_planned)
        self.assertNotIn(overdue_act, found_planned)

        # 5. Search today (must exclude planned and overdue)
        found_today = self.env['mail.activity'].search([
            ('id', 'in', test_scope_ids),
            ('state', '=', 'today'),
        ])
        self.assertEqual(found_today, today_act)
        self.assertNotIn(planned_act, found_today)
        self.assertNotIn(overdue_act, found_today)

        # 6. Search overdue (must exclude planned and today)
        found_overdue = self.env['mail.activity'].search([
            ('id', 'in', test_scope_ids),
            ('state', '=', 'overdue'),
        ])
        self.assertEqual(found_overdue, overdue_act)
        self.assertNotIn(planned_act, found_overdue)
        self.assertNotIn(today_act, found_overdue)

        # 7. Action done & search done
        today_act._action_done()
        self.assertFalse(today_act.active)
        found_done = self.env['mail.activity'].with_context(active_test=False).search([
            ('id', 'in', test_scope_ids),
            ('state', '=', 'done'),
        ])
        self.assertEqual(found_done, today_act)

        # 8. Negative state search (!= done)
        found_not_done = self.env['mail.activity'].search([
            ('id', 'in', [planned_act.id, overdue_act.id]),
            ('state', '!=', 'done'),
        ])
        self.assertEqual(len(found_not_done), 2)

        # 9. Other negative operators and not in
        found_not_today = self.env['mail.activity'].search([
            ('id', 'in', [planned_act.id, overdue_act.id]),
            ('state', '!=', 'today'),
        ])
        self.assertEqual(len(found_not_today), 2)

        found_not_overdue = self.env['mail.activity'].search([
            ('id', 'in', [planned_act.id, overdue_act.id]),
            ('state', '!=', 'overdue'),
        ])
        self.assertEqual(found_not_overdue, planned_act)

        found_not_planned = self.env['mail.activity'].search([
            ('id', 'in', [planned_act.id, overdue_act.id]),
            ('state', '!=', 'planned'),
        ])
        self.assertEqual(found_not_planned, overdue_act)

        # 10. Multi-value 'in' search
        found_multi = self.env['mail.activity'].search([
            ('id', 'in', test_scope_ids),
            ('state', 'in', ['planned', 'overdue']),
        ])
        self.assertEqual(found_multi, planned_act | overdue_act)

        # 11. Multi-value 'not in' search
        found_multi_not = self.env['mail.activity'].search([
            ('id', 'in', test_scope_ids),
            ('state', 'not in', ['planned', 'done']),
        ])
        self.assertEqual(found_multi_not, overdue_act)

        # 12. Direct _search_state tests covering all branches
        self.assertTrue(self.env['mail.activity']._search_state('in', ['planned', 'today', 'overdue', 'done']))
        self.assertTrue(self.env['mail.activity']._search_state('not in', ['planned', 'today', 'overdue', 'done']))
        empty_search = self.env['mail.activity']._search_state('like', 'something')
        self.assertEqual(empty_search, [])

    def test_multi_recordset_action_done(self):
        """Test multi-recordset execution for _action_done."""
        act1 = self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id('res.partner'),
            'res_id': self.partner.id,
            'activity_type_id': self.activity_type.id,
            'summary': 'Batch Act 1',
            'date_deadline': self.today,
        })
        act2 = self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id('res.partner'),
            'res_id': self.partner.id,
            'activity_type_id': self.activity_type.id,
            'summary': 'Batch Act 2',
            'date_deadline': self.today,
        })
        batch = act1 | act2
        batch._action_done()
        self.assertFalse(act1.active)
        self.assertFalse(act2.active)

    def test_get_activity_endpoint(self):
        """Test get_activity method under valid, edge, and invalid inputs."""
        act = self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id('res.partner'),
            'res_id': self.partner.id,
            'activity_type_id': self.activity_type.id,
            'summary': 'Test Get Activity',
            'date_deadline': self.today,
        })

        # Valid ID
        res = self.env['mail.activity'].get_activity(act.id)
        self.assertEqual(res.get('model'), 'res.partner')
        self.assertEqual(res.get('res_id'), self.partner.id)

        # Valid string ID
        res_str = self.env['mail.activity'].get_activity(str(act.id))
        self.assertEqual(res_str.get('model'), 'res.partner')
        self.assertEqual(res_str.get('res_id'), self.partner.id)

        # Invalid/Empty inputs
        self.assertEqual(self.env['mail.activity'].get_activity(False), {})
        self.assertEqual(self.env['mail.activity'].get_activity(None), {})
        self.assertEqual(self.env['mail.activity'].get_activity(''), {})
        self.assertEqual(self.env['mail.activity'].get_activity('invalid_number'), {})
        self.assertEqual(self.env['mail.activity'].get_activity(99999999), {})
