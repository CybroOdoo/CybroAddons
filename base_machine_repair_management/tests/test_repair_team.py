# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
#
#############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestRepairTeam(TransactionCase):
    """Test cases for the RepairTeam (repair.team) and TeamMember (team.member) models."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lead = cls.env['hr.employee'].create({'name': 'Team Lead Alpha'})
        cls.member1 = cls.env['hr.employee'].create({'name': 'Member One'})
        cls.member2 = cls.env['hr.employee'].create({'name': 'Member Two'})
        cls.partner = cls.env['res.partner'].create({'name': 'Repair Team Customer'})

    # ------------------------------------------------------------------
    # 1. RepairTeam — basic CRUD
    # ------------------------------------------------------------------
    def test_01_create_repair_team(self):
        """A repair team can be created with a name and team lead."""
        team = self.env['repair.team'].create({
            'team_name': 'Beta Squad',
            'team_lead_id': self.lead.id,
        })
        self.assertTrue(team.exists())
        self.assertEqual(team.team_name, 'Beta Squad')
        self.assertEqual(team.team_lead_id.id, self.lead.id)

    def test_02_create_team_without_name_raises(self):
        """Creating a team without team_name (required) should raise."""
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            self.env['repair.team'].create({
                'team_lead_id': self.lead.id,
            })

    def test_03_create_team_without_lead_raises(self):
        """Creating a team without team_lead_id (required) should raise."""
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            self.env['repair.team'].create({
                'team_name': 'No Lead Team',
            })

    def test_04_team_rec_name_is_team_name(self):
        """The display name of a repair team should be the team_name."""
        team = self.env['repair.team'].create({
            'team_name': 'Gamma Force',
            'team_lead_id': self.lead.id,
        })
        self.assertEqual(team.display_name, 'Gamma Force')

    # ------------------------------------------------------------------
    # 2. TeamMember
    # ------------------------------------------------------------------
    def test_05_add_member_to_team(self):
        """A team.member record can be added to a repair team."""
        team = self.env['repair.team'].create({
            'team_name': 'Delta Team',
            'team_lead_id': self.lead.id,
        })
        tm = self.env['team.member'].create({
            'inverse_id': team.id,
            'member_id': self.member1.id,
        })
        self.assertEqual(tm.inverse_id.id, team.id)
        self.assertEqual(tm.member_id.id, self.member1.id)

    def test_06_team_member_login_related(self):
        """team.member login field should reflect the employee's work_email."""
        self.member1.work_email = 'member1@example.com'
        team = self.env['repair.team'].create({
            'team_name': 'Epsilon Team',
            'team_lead_id': self.lead.id,
        })
        tm = self.env['team.member'].create({
            'inverse_id': team.id,
            'member_id': self.member1.id,
        })
        self.assertEqual(tm.login, 'member1@example.com')

    def test_07_team_member_required_member_id(self):
        """Creating a team.member without member_id (required) should raise."""
        team = self.env['repair.team'].create({
            'team_name': 'Zeta Team',
            'team_lead_id': self.lead.id,
        })
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            self.env['team.member'].create({
                'inverse_id': team.id,
                # member_id missing — required
            })

    def test_08_multiple_members_in_team(self):
        """Multiple members can belong to the same team."""
        team = self.env['repair.team'].create({
            'team_name': 'Eta Team',
            'team_lead_id': self.lead.id,
        })
        self.env['team.member'].create({
            'inverse_id': team.id,
            'member_id': self.member1.id,
        })
        self.env['team.member'].create({
            'inverse_id': team.id,
            'member_id': self.member2.id,
        })
        count = self.env['team.member'].search_count(
            [('inverse_id', '=', team.id)]
        )
        self.assertEqual(count, 2)

    # ------------------------------------------------------------------
    # 3. Assigning team to repair
    # ------------------------------------------------------------------
    def test_09_assign_team_to_repair_sets_state(self):
        """Assigning a team to a repair changes state to 'assigned'."""
        team = self.env['repair.team'].create({
            'team_name': 'Theta Team',
            'team_lead_id': self.lead.id,
        })
        repair = self.env['machine.repair'].create({
            'name': 'Test Assign Repair',
            'customer_id': self.partner.id,
            'priority': 'high',
            'repair_detail': 'Full overhaul.',
            'repair_team_id': team.id,
        })
        repair.action_assign_teams()
        self.assertEqual(repair.state, 'assigned')
        self.assertTrue(repair.is_team_assigned)

    def test_10_assign_team_populates_repair_work_ids(self):
        """After assignment, the repair should appear in team.repair_work_ids."""
        team = self.env['repair.team'].create({
            'team_name': 'Iota Team',
            'team_lead_id': self.lead.id,
        })
        repair = self.env['machine.repair'].create({
            'name': 'Assign Team Repair',
            'customer_id': self.partner.id,
            'priority': 'normal',
            'repair_detail': 'Check wiring.',
            'repair_team_id': team.id,
        })
        repair.action_assign_teams()
        self.assertIn(repair.id, team.repair_work_ids.ids)

    def test_11_assign_team_without_team_raises_validation(self):
        """action_assign_teams() without a team should raise ValidationError."""
        repair = self.env['machine.repair'].create({
            'name': 'No Team Repair',
            'customer_id': self.partner.id,
            'priority': 'low',
            'repair_detail': 'Needs attention.',
        })
        with self.assertRaises(ValidationError):
            repair.action_assign_teams()

    # ------------------------------------------------------------------
    # 4. repair_work_ids field is readonly
    # ------------------------------------------------------------------
    def test_12_repair_work_ids_readonly_flag(self):
        """repair_work_ids field should be declared as readonly=True."""
        field = self.env['repair.team']._fields['repair_work_ids']
        self.assertTrue(field.readonly,
                        "repair_work_ids should be a readonly field.")
