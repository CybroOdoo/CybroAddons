#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Unit tests for crm_check_approve_limiter module."""
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'crm_check_approve_limiter')
class TestCrmCheckApproveLimiter(TransactionCase):
    """Test suite for CRM checklist and approval limiter features."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Security groups
        cls.group_manager = cls.env.ref(
            'crm_check_approve_limiter.crm_check_approve_manager',
        )
        cls.group_internal = cls.env.ref('base.group_user')
        cls.group_sale_user = cls.env.ref(
            'sales_team.group_sale_salesman_all_leads',
        )
        cls.group_special_approval = cls.env['res.groups'].create({
            'name': 'Checklist Special Approver',
        })

        # Test users
        cls.user_salesman = cls.env['res.users'].create({
            'name': 'Test Salesman',
            'login': 'test_salesman',
            'email': 'salesman@cybrosys.com',
            'group_ids': [(6, 0, [
                cls.group_internal.id,
                cls.group_sale_user.id,
            ])],
        })
        cls.user_approver = cls.env['res.users'].create({
            'name': 'Test Approver',
            'login': 'test_approver',
            'email': 'approver@cybrosys.com',
            'group_ids': [(6, 0, [
                cls.group_internal.id,
                cls.group_sale_user.id,
                cls.group_special_approval.id,
            ])],
        })
        cls.user_checklist_manager = cls.env['res.users'].create({
            'name': 'Test Checklist Manager',
            'login': 'test_checklist_mgr',
            'email': 'mgr@cybrosys.com',
            'group_ids': [(6, 0, [
                cls.group_internal.id,
                cls.group_sale_user.id,
                cls.group_manager.id,
            ])],
        })

        # Sales team
        cls.sales_team = cls.env['crm.team'].create({
            'name': 'Alpha Sales Team',
        })

        # CRM Stages
        cls.stage_new = cls.env['crm.stage'].create({
            'name': 'Initial Assessment',
            'sequence': 1,
            'is_pre_checking': False,
        })
        cls.stage_qualified = cls.env['crm.stage'].create({
            'name': 'Qualified Discovery',
            'sequence': 2,
            'is_pre_checking': False,
            'is_disable_regress': True,
        })
        cls.stage_won = cls.env['crm.stage'].create({
            'name': 'Deal Closed',
            'sequence': 3,
            'is_pre_checking': True,
        })

        # Checklist Items for stage_new
        cls.item_general = cls.env['stage.check.list'].create({
            'check_task': 'Collect Customer Needs',
            'stage_id': cls.stage_new.id,
            'is_stage_recover': True,
        })
        cls.item_team_specific = cls.env['stage.check.list'].create({
            'check_task': 'Verify Technical Compatibility',
            'stage_id': cls.stage_new.id,
            'sales_team_id': cls.sales_team.id,
            'is_stage_recover': False,
        })
        cls.item_restricted = cls.env['stage.check.list'].create({
            'check_task': 'Financial Background Check',
            'stage_id': cls.stage_new.id,
            'approve_groups_ids': [(6, 0, [cls.group_special_approval.id])],
            'is_stage_recover': True,
        })

    def setUp(self):
        super().setUp()
        self.lead = self.env['crm.lead'].create({
            'name': 'Big Enterprise Solution',
            'stage_id': self.stage_new.id,
            'team_id': self.sales_team.id,
            'user_id': self.user_salesman.id,
        })


    def test_01_checklist_progress_computation(self):
        """Test progress percentage computation with 0%, partial, and 100%."""
        lead = self.lead
        self.assertEqual(lead.checklist_progress, 0.0)

        # Complete one item
        lead.with_user(self.user_salesman).write({
            'check_list_ids': [(4, self.item_general.id)],
        })
        # 1 out of 3 items complete => ~33.33%
        self.assertAlmostEqual(lead.checklist_progress, 33.33, places=1)

        # Complete all 3 items (using approver user for restricted item)
        lead.with_user(self.user_salesman).write({
            'check_list_ids': [(4, self.item_team_specific.id)],
        })
        lead.with_user(self.user_approver).write({
            'check_list_ids': [(4, self.item_restricted.id)],
        })
        self.assertEqual(lead.checklist_progress, 100.0)

    def test_02_stage_advancement_validation(self):
        """Test advancing stage is blocked when checklist is incomplete."""
        lead = self.lead
        # Incomplete checklist advancement should fail for normal salesman
        with self.assertRaises(ValidationError):
            lead.with_user(self.user_salesman).write({
                'stage_id': self.stage_qualified.id,
            })

        # Complete all checklist items
        lead.with_user(self.user_salesman).write({
            'check_list_ids': [(4, self.item_general.id)],
        })
        lead.with_user(self.user_salesman).write({
            'check_list_ids': [(4, self.item_team_specific.id)],
        })
        lead.with_user(self.user_approver).write({
            'check_list_ids': [(4, self.item_restricted.id)],
        })
        self.assertEqual(lead.checklist_progress, 100.0)

        # Stage advancement now succeeds
        lead.with_user(self.user_salesman).write({
            'stage_id': self.stage_qualified.id,
        })
        self.assertEqual(lead.stage_id, self.stage_qualified)

    def test_03_manager_override(self):
        """Test checklist manager advances stage despite incomplete items."""
        lead = self.lead
        self.assertNotEqual(lead.checklist_progress, 100.0)
        lead.with_user(self.user_checklist_manager).write({
            'stage_id': self.stage_qualified.id,
        })
        self.assertEqual(lead.stage_id, self.stage_qualified)

    def test_04_pre_checking_stage_bypass(self):
        """Test that is_pre_checking=True bypasses 100% checklist."""
        stage_auto = self.env['crm.stage'].create({
            'name': 'Pre-checked Stage',
            'sequence': 1,
            'is_pre_checking': True,
        })
        self.env['stage.check.list'].create({
            'check_task': 'Optional Task',
            'stage_id': stage_auto.id,
        })
        lead_auto = self.env['crm.lead'].create({
            'name': 'Auto Lead',
            'stage_id': stage_auto.id,
        })
        # Advance without completing checklist
        lead_auto.with_user(self.user_salesman).write({
            'stage_id': self.stage_qualified.id,
        })
        self.assertEqual(lead_auto.stage_id, self.stage_qualified)

    def test_05_permission_validation_and_history(self):
        """Test group permissions on item completion and history log."""
        lead = self.lead
        # Normal salesman without special group cannot complete restricted item
        with self.assertRaises(ValidationError):
            lead.with_user(self.user_salesman).write({
                'check_list_ids': [(4, self.item_restricted.id)],
            })

        # Approver with required group can complete restricted item
        lead.with_user(self.user_approver).write({
            'check_list_ids': [(4, self.item_restricted.id)],
        })
        self.assertIn(self.item_restricted, lead.check_list_ids)

        # Check history record created
        history_complete = self.env['crm.lead.check.history'].search([
            ('lead_id', '=', lead.id),
            ('check_item_id', '=', self.item_restricted.id),
            ('list_action', '=', 'complete'),
        ])
        self.assertTrue(history_complete)
        self.assertEqual(history_complete.user_id, self.user_approver)

        # Approver removes the item
        lead.with_user(self.user_approver).write({
            'check_list_ids': [(3, self.item_restricted.id)],
        })
        self.assertNotIn(self.item_restricted, lead.check_list_ids)

        history_uncomplete = self.env['crm.lead.check.history'].search([
            ('lead_id', '=', lead.id),
            ('check_item_id', '=', self.item_restricted.id),
            ('list_action', '=', 'not_complete'),
        ])
        self.assertTrue(history_uncomplete)

    def test_06_stage_recover_and_onchange(self):
        """Test stage recovery of items and UI onchange validation behavior."""
        lead = self.lead
        # Complete recoverable item
        lead.with_user(self.user_salesman).write({
            'check_list_ids': [(4, self.item_general.id)],
        })

        # Simulate UI onchange stage change forward using new()
        lead_draft_fwd = lead.with_user(self.user_salesman).new({
            'stage_id': self.stage_qualified.id,
        }, origin=lead)
        with self.assertRaises(ValidationError):
            lead_draft_fwd._onchange_stage_id()

        # Advance lead to stage_won first using manager
        lead.with_user(self.user_checklist_manager).write({
            'stage_id': self.stage_won.id,
        })
        # Regressing to stage_qualified has is_disable_regress=True
        lead_draft_regress = lead.with_user(self.user_salesman).new({
            'stage_id': self.stage_qualified.id,
        }, origin=lead)
        with self.assertRaises(ValidationError):
            lead_draft_regress._onchange_stage_id()

        # Regressing to stage_new recovers the recoverable item
        lead_draft_recover = lead.with_user(self.user_salesman).new({
            'stage_id': self.stage_new.id,
        }, origin=lead)
        lead_draft_recover._onchange_stage_id()
        recovered_item_ids = [
            getattr(i.id, 'origin', i.id)
            for i in lead_draft_recover.check_list_ids
        ]
        self.assertIn(self.item_general.id, recovered_item_ids)

    def test_07_bulk_write_no_singleton(self):
        """Test bulk write operations on multiple leads without singleton errors."""
        lead2 = self.env['crm.lead'].create({
            'name': 'Second Enterprise Solution',
            'stage_id': self.stage_new.id,
            'team_id': self.sales_team.id,
            'user_id': self.user_salesman.id,
        })
        leads = self.lead | lead2

        # Bulk write check_list_ids
        leads.with_user(self.user_salesman).write({
            'check_list_ids': [(4, self.item_general.id)],
        })
        self.assertIn(self.item_general, self.lead.check_list_ids)
        self.assertIn(self.item_general, lead2.check_list_ids)

        # Bulk write stage_id using manager
        leads.with_user(self.user_checklist_manager).write({
            'stage_id': self.stage_won.id,
        })
        self.assertEqual(self.lead.stage_id, self.stage_won)
        self.assertEqual(lead2.stage_id, self.stage_won)

    def test_08_recover_history_isolation(self):
        """Test that stage recovery only restores items completed on this lead."""
        lead_a = self.env['crm.lead'].create({
            'name': 'Lead A',
            'stage_id': self.stage_new.id,
            'team_id': self.sales_team.id,
        })
        lead_b = self.env['crm.lead'].create({
            'name': 'Lead B',
            'stage_id': self.stage_won.id,
            'team_id': self.sales_team.id,
        })

        # Complete recoverable item on lead_a only
        lead_a.with_user(self.user_salesman).write({
            'check_list_ids': [(4, self.item_general.id)],
        })

        # Lead B moves to stage_new via write: should NOT recover item_general
        lead_b.with_user(self.user_checklist_manager).write({
            'stage_id': self.stage_new.id,
        })
        self.assertNotIn(
            self.item_general,
            lead_b.check_list_ids,
            "Lead B must not recover checklist items completed on Lead A",
        )

        # Lead B moves to stage_new via onchange: should NOT recover item_general
        lead_b_draft = lead_b.with_user(self.user_salesman).new({
            'stage_id': self.stage_new.id,
        }, origin=lead_b)
        lead_b_draft._onchange_stage_id()
        recovered_ids = [
            getattr(i.id, 'origin', i.id) for i in lead_b_draft.check_list_ids
        ]
        self.assertNotIn(
            self.item_general.id,
            recovered_ids,
            "Lead B onchange must not recover items completed on Lead A",
        )

