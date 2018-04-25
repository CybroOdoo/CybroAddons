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


class HrLegal(models.Model):
    _inherit = 'hr.employee'

    legal_count = fields.Integer(compute='_legal_count', string='# Legal Actions')

    @api.multi
    def _legal_count(self):
        for each in self:
            legal_ids = self.env['hr.lawsuit'].search([('employee_id', '=', each.id)])
            each.legal_count = len(legal_ids)

    @api.multi
    def legal_view(self):
        for each1 in self:
            legal_obj = self.env['hr.lawsuit'].sudo().search([('employee_id', '=', each1.id)])
            legal_ids = []
            for each in legal_obj:
                legal_ids.append(each.id)
            view_id = self.env.ref('oh_hr_lawsuit_management.hr_lawsuit_form_view').id
            if legal_ids:
                if len(legal_ids) <= 1:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'hr.lawsuit',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Legal Actions'),
                        'res_id': legal_ids and legal_ids[0]
                    }
                else:
                    value = {
                        'domain': str([('id', 'in', legal_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'hr.lawsuit',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Legal Actions'),
                        'res_id': legal_ids
                    }

                return value


class PartnerLegal(models.Model):
    _inherit = 'res.partner'

    legal_count = fields.Integer(compute='_legal_count', string='# Legal Actions')

    @api.multi
    def _legal_count(self):
        for each in self:
            legal_ids = self.env['hr.lawsuit'].sudo().search(['|', ('customer_id', '=', each.id),
                                                                   ('supplier_id', '=', each.id)])
            each.legal_count = len(legal_ids)

    @api.multi
    def legal_view(self):
        for each1 in self:
            legal_obj = self.env['hr.lawsuit'].sudo().search(['|', ('customer_id', '=', each1.id),
                                                                   ('supplier_id', '=', each1.id)])
            legal_ids = []
            for each in legal_obj:
                legal_ids.append(each.id)
            view_id = self.env.ref('oh_hr_lawsuit_management.hr_lawsuit_form_view').id
            if legal_ids:
                if len(legal_ids) <= 1:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'hr.lawsuit',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Legal Actions'),
                        'res_id': legal_ids and legal_ids[0]
                    }
                else:
                    value = {
                        'domain': str([('id', 'in', legal_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'hr.lawsuit',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Legal Actions'),
                        'res_id': legal_ids
                    }

                return value
