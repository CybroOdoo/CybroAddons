# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LegalCourt(models.Model):
    """Creation of legal court"""
    _name = 'legal.court'
    _description = 'legal court'

    name = fields.Char("Name", required=True, help='Name')
    judge_id = fields.Many2one('res.partner',
                               domain="[('is_judge', '=', True),"
                                      "('judge_unavailable', '=',False)]",
                               string='Judge',
                               help='Judges are available in the court')

    @api.onchange('judge_id')
    def _onchange_judge_id(self):
        """get judges"""
        self.judge_id.is_judge = True
        self.judge_id.judge_unavailable = True

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        """ Prevent the deletion of a court if it is used in any cases. """
        cases = self.sudo().env['case.registration'].search_count([
            ('court_id', 'in', self.ids),
            ('state', 'not in', ['draft'])
        ])
        if cases:
            raise UserError(_("You can not delete a court, "
                              "because it is used in case"))
