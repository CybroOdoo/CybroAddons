# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nikhil krishnan(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from odoo import models, fields, api


class EntertainmentGames(models.Model):
    _name = 'employee.game.approve'
    _inherit = ['ir.needaction_mixin']
    _order = 'sequence desc'

    name = fields.Char(string='Name', related='employee_id.name')
    approve_datetime = fields.Datetime(string='Datetime', readonly=1)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    user_id = fields.Many2one('res.users', string='User')
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id')
    game_user = fields.Boolean(string='Is Game User')
    state = fields.Selection([
        ('draft', 'Requested'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, default='draft')
    sequence = fields.Integer('Sequence')

    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'draft')]

    def create_employee_game_approve(self, empl_id, user):
        rec = self.search([('employee_id', '=', empl_id)])
        if rec:
            seq = self.env['ir.sequence'].next_by_code('employee.game')
            rec.write({'sequence': seq, 'state': 'draft', 'approve_datetime': datetime.now()})
        else:
            vals = {
                'employee_id': empl_id,
                'user_id': user,
                'approve_datetime': datetime.now(),
                'sequence': self.env['ir.sequence'].next_by_code('employee.game')
            }
            self.create(vals)

    def approve(self):
        group_game_approve = self.env.ref('game_sudoku.odoo_gamer_group', False)
        group_game_approve.write({'users': [(4, self.user_id.id)]})

        group_game_req = self.env.ref('game_sudoku.odoo_gamer_approve_req', False)
        group_game_req.write({'users': [(3, self.user_id.id)]})

        return self.write({'game_user': True, 'state': 'approve'})

    def cancel(self):
        group_game_approve = self.env.ref('game_sudoku.odoo_gamer_group', False)
        group_game_approve.write({'users': [(3, self.user_id.id)]})

        group_game_req = self.env.ref('game_sudoku.odoo_gamer_approve_req', False)
        group_game_req.write({'users': [(4, self.user_id.id)]})

        return self.write({'game_user': False, 'state': 'cancel'})
