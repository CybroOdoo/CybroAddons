# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, fields, api, _


class HrRewardWarning(models.Model):
    _inherit = 'hr.employee'

    warning_count = fields.Integer(compute='_warning_count', string='# Warnings')
    reward_count = fields.Integer(compute='_reward_count', string='# Rewards')
    ann_count = fields.Integer(compute='_ann_count', string='# Announcements')
    letter_count = fields.Integer(compute='_letter_count', string='# Letters')

    @api.multi
    def _warning_count(self):
        for each in self:
            warning_ids = self.env['hr.reward.warning'].sudo().search([('employee_id', '=', each.id),
                                                                       ('hr_type', '=', 'warning'),
                                                                       ('state', 'in', ('approved', 'done'))])
            each.warning_count = len(warning_ids)

    @api.multi
    def _letter_count(self):
        for each in self:
            letter_ids = self.env['hr.reward.warning'].sudo().search([('employee_id', '=', each.id),
                                                                      ('hr_type', '=', 'letter'),
                                                                      ('state', 'in', ('approved', 'done'))])
            each.letter_count = len(letter_ids)

    @api.multi
    def _reward_count(self):
        for each in self:
            reward_ids = self.env['hr.reward.warning'].sudo().search([('employee_id', '=', each.id),
                                                                      ('hr_type', '=', 'reward'),
                                                                      ('state', 'in', ('approved', 'done'))])
            each.reward_count = len(reward_ids)

    @api.multi
    def _ann_count(self):
        for each in self:
            ann_ids = self.env['hr.reward.warning'].sudo().search([('is_announcement', '=', True),
                                                                   ('state', 'in', ('approved', 'done'))])
            each.ann_count = len(ann_ids)

    @api.multi
    def warning_view(self):
        for each1 in self:
            warning_obj = self.env['hr.reward.warning'].sudo().search([('employee_id', '=', each1.id),
                                                                       ('hr_type', '=', 'warning'),
                                                                       ('state', 'in', ('approved', 'done'))])
            warning_ids = []
            for each in warning_obj:
                warning_ids.append(each.id)
            view_id = self.env.ref('hr_reward_warning.view_hr_reward_warning_form').id
            if warning_ids:
                if len(warning_ids) <= 1:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'hr.reward.warning',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Warnings'),
                        'res_id': warning_ids and warning_ids[0]
                    }
                else:
                    value = {
                        'domain': str([('id', 'in', warning_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'hr.reward.warning',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Warnings'),
                        'res_id': warning_ids
                    }

                return value

    @api.multi
    def letter_view(self):
        for each1 in self:
            letter_obj = self.env['hr.reward.warning'].sudo().search([('employee_id', '=', each1.id),
                                                                      ('hr_type', '=', 'letter'),
                                                                      ('state', 'in', ('approved', 'done'))])
            letter_ids = []
            for each in letter_obj:
                letter_ids.append(each.id)
            view_id = self.env.ref('hr_reward_warning.view_hr_reward_warning_form').id
            if letter_ids:
                if len(letter_ids) <= 1:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'hr.reward.warning',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Letters'),
                        'res_id': letter_ids and letter_ids[0]
                    }
                else:
                    value = {
                        'domain': str([('id', 'in', letter_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'hr.reward.warning',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Letters'),
                        'res_id': letter_ids
                    }

                return value

    @api.multi
    def reward_view(self):
        for each1 in self:
            reward_obj = self.env['hr.reward.warning'].sudo().search([('employee_id', '=', each1.id),
                                                                      ('hr_type', '=', 'reward'),
                                                                      ('state', 'in', ('approved', 'done'))])
            reward_ids = []
            for each in reward_obj:
                reward_ids.append(each.id)
            view_id = self.env.ref('hr_reward_warning.view_hr_reward_warning_form').id
            if reward_ids:
                if len(reward_ids) <= 1:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'hr.reward.warning',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Rewards'),
                        'res_id': reward_ids and reward_ids[0]
                    }
                else:
                    value = {
                        'domain': str([('id', 'in', reward_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'hr.reward.warning',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Rewards'),
                        'res_id': reward_ids
                    }

                return value

    @api.multi
    def announcement_view(self):
        for each1 in self:
            ann_obj = self.env['hr.reward.warning'].sudo().search([('is_announcement', '=', True),
                                                                   ('state', 'in', ('approved', 'done'))])
            ann_ids = []
            for each in ann_obj:
                ann_ids.append(each.id)
            view_id = self.env.ref('hr_reward_warning.view_hr_reward_warning_form').id
            if ann_ids:
                if len(ann_ids) <= 1:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'hr.reward.warning',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Announcements'),
                        'res_id': ann_ids and ann_ids[0]
                    }
                else:
                    value = {
                        'domain': str([('id', 'in', ann_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'hr.reward.warning',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Announcements'),
                        'res_id': ann_ids
                    }

                return value
