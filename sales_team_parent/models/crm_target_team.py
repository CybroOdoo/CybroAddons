# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
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

from odoo import models, fields, api


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    def get_currency(self):
        return self.env.user.company_id.currency_id.id

    team_target = fields.Float(string='Team Target', compute="compute_team_target")
    parent_team = fields.Many2one('crm.team', string='Parent Team', copy=False)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.get_currency())

    @api.one
    def compute_team_target(self):
        total = 0
        childs = self.get_childs(self.id)
        childs += self
        for team in childs:
            for member_id in team.member_ids:
                target = team.env['crm.target'].search([('user_id', '=', member_id.id)])
                if target:
                    for t in target:
                        total += t.target_amount

            team.team_target = total
        return

    def get_childs(self, team_id):
        child_teams = self.search([('parent_team.id', '=', team_id)])
        if child_teams:
            for team in child_teams:
                child_teams += self.get_childs(team.id)
        return child_teams


