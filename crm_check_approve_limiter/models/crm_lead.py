# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Naveen K (odoo@cybrosys.com)
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

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LeadCheckList(models.Model):
    _inherit = "crm.lead"

    check_list_ids = fields.Many2many('stage.check.list',
                                      domain="['&',"
                                             " ('stage_id', '=', stage_id),"
                                             "'|',('s_team_id','=',team_id),"
                                             "('s_team_id', '=', False)]",
                                      string="Checklist", tracking=True)
    check_stage_ids = fields.One2many(related="stage_id.stage_check_list_lines")

    @api.depends('check_list_ids')
    def checklist_progress(self):
        """Method for Computing CheckList progress value based on selected
        checklist items """
        for rec in self:
            total_len = rec.env['stage.check.list']. \
                search_count(['&', ('stage_id', '=', rec.stage_id.id), '|',
                              ('s_team_id', '=', rec.team_id.id),
                              ('s_team_id', '=', False)])
            if total_len != 0:
                check_list_len = len(rec.check_list_ids.filtered(
                    lambda r: r.s_team_id == rec.team_id or not r.s_team_id))
                rec.checklist_progress = (check_list_len * 100) / total_len
            else:
                rec.checklist_progress = 0

    checklist_progress = fields.Float(compute=checklist_progress,
                                      string='Progress',
                                      default=0.0)

    check_list_history = fields.One2many('crm.lead.check.history', 'lead_id',
                                         string="History", readonly=True)

    def write(self, vals_set):
        """Super the write method for data validation.Here we check
        Progression and regression of stages and based on checklist
        completion stage progression can be blocked from here """
        if 'stage_id' in vals_set.keys():
            new_stage_id = self.env['crm.stage'].browse([vals_set['stage_id']])
            if new_stage_id \
                    and self.stage_id.sequence < new_stage_id.sequence \
                    and not self.stage_id.pre_checking \
                    and self.stage_id.stage_check_list_lines \
                    and int(self.checklist_progress) != 100 \
                    and not self.env.user. \
                    has_group('crm_check_approve_limiter.'
                              'crm_check_approve_manager'):
                raise ValidationError("You cannot move this case forward until "
                                      "all the check list items are done for "
                                      "this "
                                      " stage.")
            self.check_list_ids = False
            for item in self.stage_id.stage_check_list_lines:
                if item.stage_recover:
                    history = self.check_list_history.search([(
                        'check_item', '=', item.id)], order='id desc',
                        limit=1) or False
                    if history and history.list_action == 'complete' \
                            and item not in self.check_list_ids:
                        self.check_list_ids += item
        if 'check_list_ids' in vals_set.keys():
            group_check = self.env.user.\
                has_group('crm_check_approve_limiter.'
                          'crm_check_approve_manager')
            user_groups = self.env.user.groups_id
            new_ids = self.env['stage.check.list']. \
                search([('id', 'in', vals_set['check_list_ids'][-1][-1])])
            old_ids = self.check_list_ids
            check_item = (old_ids - new_ids)
            check_item2 = (new_ids - old_ids)
            for ch_lst in check_item2:
                if ch_lst.approve_groups and not ch_lst. \
                        approve_groups.filtered(lambda f: f in user_groups)\
                        and not group_check:
                    grp_string_t = '\n'.join(map(str, ch_lst.approve_groups.
                                                 mapped('full_name')))
                    raise ValidationError(f'Only the below specified group'
                                          f' members can complete this task'
                                          f' : {grp_string_t}')
            for ch_lst in check_item:
                if ch_lst.approve_groups and not ch_lst. \
                        approve_groups.filtered(lambda f: f in user_groups)\
                        and not group_check:
                    grp_string_t = '\n'.join(map(str, ch_lst.approve_groups.
                                                 mapped('full_name')))
                    raise ValidationError(f'Only the below specified group'
                                          f' members can undo this task'
                                          f' : {grp_string_t}')
            if 'stage_id' not in vals_set.keys() and check_item:
                for c_item in check_item:
                    vals = {
                        'lead_id': self.id,
                        'check_item': c_item.id,
                        'list_action': 'not_complete',
                        'change_date': datetime.now(),
                        'user_id': self.env.user.id,
                        'stage_id': self.stage_id.id
                    }
                    self.env['crm.lead.check.history'].sudo().create(vals)
            elif 'stage_id' not in vals_set.keys() and check_item2:
                for c_item in check_item2:
                    vals = {
                        'lead_id': self.id,
                        'check_item': c_item.id,
                        'list_action': 'complete',
                        'change_date': datetime.now(),
                        'user_id': self.env.user.id,
                        'stage_id': self.stage_id.id
                    }
                    self.env['crm.lead.check.history'].sudo().create(vals)
        res = super().write(vals_set)
        return res

    @api.onchange('stage_id')
    def _onchange_state_id(self):
        old_stage_id = self._origin.stage_id
        if old_stage_id.sequence < self.stage_id.sequence \
                and not old_stage_id.pre_checking \
                and old_stage_id.stage_check_list_lines \
                and int(self.checklist_progress) != 100 and not self.env.user.\
                has_group('crm_check_approve_limiter.'
                          'crm_check_approve_manager'):
            raise ValidationError("You cannot move this case forward until "
                                  "all the check list items are done for this"
                                  " stage.")
        if old_stage_id.sequence > self.stage_id.sequence \
                and self.stage_id.disable_regress and not self.env.user.\
                has_group('crm_check_approve_limiter.'
                          'crm_check_approve_manager'):
            raise ValidationError("Regression to the selected stage is "
                                  "blocked. "
                                  "Please contact Administrators for "
                                  "required permission")
        self.check_list_ids = False
        for item in self.stage_id.stage_check_list_lines:
            if item.stage_recover:
                history = self.check_list_history.search([(
                    'check_item', '=', item.id)], order='id desc',
                    limit=1) or False
                if history and history.list_action == 'complete' \
                        and item not in self.check_list_ids:
                    self.check_list_ids += item


class StageCheckHistory(models.Model):
    _name = "crm.lead.check.history"

    check_item = fields.Many2one('stage.check.list', string="Check Item")
    list_action = fields.Selection([
        ('complete', 'Complete'), ('not_complete', 'Not Complete')],
        required=True, string="Action")
    user_id = fields.Many2one('res.users', string="User")
    change_date = fields.Datetime(string="Date")
    stage_id = fields.Many2one('crm.stage', string="Stage")
    lead_id = fields.Many2one('crm.lead', string="Lead")
