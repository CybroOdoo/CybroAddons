# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ajith V (<https://www.cybrosys.com>)
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
###############################################################################
from odoo import fields, models


class PosSession(models.Model):
    """To add analytic tags in pos session"""
    _inherit = 'pos.session'

    pos_analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Pos Analytic Tag',
        help="Pos Analytic account in"
             " pos session",
        readonly=True)

    def _create_account_move(self):
        """Call the parent class method using super() and creates
                 account move line"""
        res = super(PosSession, self)._create_account_move()
        analytic_account = self.env['res.config.settings'].sudo().get_values()[
            'pos_analytic_account_id']
        self.pos_analytic_account_id = analytic_account
        analytic_tag = self.env['account.analytic.tag'].search([
            ('name', '=', self.pos_analytic_account_id.name)
        ], limit=1)
        if not analytic_tag:
            analytic_tag = self.env['account.analytic.tag'].create({
                'name': self.pos_analytic_account_id.name,
            })
        account_move_lines = self.env['account.move.line'].search(
            [('move_id.ref', '=', self.name)])
        account_move_lines.write({
            'analytic_tag_ids': [(6, 0, [analytic_tag.id])]})
        return res
