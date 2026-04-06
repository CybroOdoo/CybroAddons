# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreerag PM (odoo@cybrosys.com)
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
#############################################################################
"""Module Containing CRM lead and CheckList History Models"""
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    """class for checklist history models"""
    _inherit = "crm.lead"

    check_list_ids = fields.Many2many('stage.check.list',
                                      domain="['&',"
                                             " ('stage_id', '=', stage_id),"
                                             "'|',('sales_team_id','=',"
                                             "team_id),"
                                             "('sales_team_id', '=', False)]",
                                      string="Checklist", tracking=True,
                                      help="Many2many field representing a"
                                           " checklist associated with stage.")
    check_stage_ids = fields.One2many(
        related="stage_id.stage_check_list_lines_ids",
        help="One2many field related to the "
             "stage's check list lines.")

    @api.depends('check_list_ids')
    def checklist_progress(self):
        """Method for Computing CheckList progress value based on selected
        checklist items """
        for rec in self:
            total_len = rec.env['stage.check.list']. \
                search_count(['&', ('stage_id', '=', rec.stage_id.id), '|',
                              ('sales_team_id', '=', rec.team_id.id),
                              ('sales_team_id', '=', False)])
            if total_len != 0:
                check_list_len = len(rec.check_list_ids.filtered(
                    lambda r: r.sales_team_id == rec.team_id or not
                    r.sales_team_id))
                rec.checklist_progress = (check_list_len * 100) / total_len
            else:
                rec.checklist_progress = 0

    checklist_progress = fields.Float(compute=checklist_progress,
                                      string='Progress',
                                      default=0.0)
    check_list_history_ids = fields.One2many('crm.lead.check.history',
                                             'lead_id',
                                             string="History", readonly=True)


    def write(self, vals_set):
        """
        Override write for stage progression/regression validation
        and checklist completion permission control.
        """
        # STAGE CHANGE VALIDATION
        if 'stage_id' in vals_set:
            new_stage = self.env['crm.stage'].browse(vals_set['stage_id'])
            if (
                    new_stage
                    and self.stage_id.sequence < new_stage.sequence
                    and not self.stage_id.is_pre_checking
                    and self.stage_id.stage_check_list_lines_ids
                    and int(self.checklist_progress) != 100
                    and not self.env.user.has_group(
                'crm_check_approve_limiter.crm_check_approve_manager'
            )
            ):
                raise ValidationError(
                    "You cannot move this case forward until all the "
                    "check list items are completed for this stage."
                )

            # Reset checklist and recover items if required
            self.check_list_ids = False
            for item in self.stage_id.stage_check_list_lines_ids:
                if item.is_stage_recover:
                    history = self.check_list_history_ids.search(
                        [('check_item_id', '=', item.id)],
                        order='id desc',
                        limit=1
                    )
                    if history and history.list_action == 'complete':
                        self.check_list_ids |= item

        # CHECKLIST PERMISSION VALIDATION
        if 'check_list_ids' in vals_set:
            group_check = self.env.user.has_group(
                'crm_check_approve_limiter.crm_check_approve_manager'
            )
            user_groups = self.env.user.group_ids

            complete_ids = []
            notcomplete_ids = []

            for operation in vals_set['check_list_ids']:
                if operation[0] == 4:  # Add
                    complete_ids.append(operation[1])
                elif operation[0] == 3:  # Remove
                    notcomplete_ids.append(operation[1])

            new_complete_ids = self.env['stage.check.list'].browse(complete_ids)
            new_notcomplete_ids = self.env['stage.check.list'].browse(
                notcomplete_ids)

            self._validate_groups(new_complete_ids, group_check, user_groups)
            self._validate_groups(new_notcomplete_ids, group_check, user_groups)

            # -----------------------------------------------------
            # CHECKLIST HISTORY CREATION
            # -----------------------------------------------------
            if 'stage_id' not in vals_set:
                history_model = self.env['crm.lead.check.history'].sudo()

                for c_item in new_complete_ids:
                    history_model.create([{
                        'lead_id': self.id,
                        'check_item_id': c_item.id,
                        'list_action': 'complete',
                        'change_date': datetime.now(),
                        'user_id': self.env.user.id,
                        'stage_id': self.stage_id.id,
                    }])

                for c_item in new_notcomplete_ids:
                    history_model.create([{
                        'lead_id': self.id,
                        'check_item_id': c_item.id,
                        'list_action': 'not_complete',
                        'change_date': datetime.now(),
                        'user_id': self.env.user.id,
                        'stage_id': self.stage_id.id,
                    }])

        return super().write(vals_set)

    def _validate_groups(self, check_items, group_check, user_groups):
        """
            Validate user permission for completing or reverting checklist items
            based on required approval groups or manager override.
            """
        for ch_lst in check_items:
            if (
                    ch_lst.approve_groups_ids
                    and not (ch_lst.approve_groups_ids & user_groups)
                    and not group_check
            ):
                grp_string = '\n'.join(
                    ch_lst.approve_groups_ids.mapped('full_name')
                )
                raise ValidationError(

                        "Only the below specified group members "
                        "can complete this task:\n%s"% grp_string
                )

    @api.onchange('stage_id')
    def _onchange_state_id(self):
        """It performs validation checks and updates the 'check_list_ids'
        field. """
        old_stage_id = self._origin.stage_id
        if old_stage_id.sequence < self.stage_id.sequence \
                and not old_stage_id.is_pre_checking \
                and old_stage_id.stage_check_list_lines_ids \
                and int(self.checklist_progress) != 100 and not self.env.user. \
                has_group('crm_check_approve_limiter.'
                          'crm_check_approve_manager'):
            raise ValidationError("You cannot move this case forward until "
                                    "all the check list items are done for"
                                    " this stage.")
        if old_stage_id.sequence > self.stage_id.sequence \
                and self.stage_id.is_disable_regress and not self.env.user. \
                has_group('crm_check_approve_limiter.'
                          'crm_check_approve_manager'):
            raise ValidationError("Regression to the selected stage is "
                                    "blocked. "
                                    "Please contact Administrators for "
                                    "required permission")
        self.check_list_ids = False
        for item in self.stage_id.stage_check_list_lines_ids:
            if item.is_stage_recover:
                history = self.check_list_history_ids.search([(
                    'check_item_id', '=', item.id)], order='id desc',
                    limit=1) or False
                if history and history.list_action == 'complete' and item \
                        not in self.check_list_ids:
                    self.check_list_ids += item
