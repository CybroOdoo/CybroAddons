# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models
from odoo.exceptions import ValidationError


class PosAnalysis(models.TransientModel):
    """
    Wizard for configuring POS analysis reports.
    """
    _name = 'pos.analysis'
    _description = 'Wizard for configuring report'

    from_date = fields.Date(
        string='From date',
        help='Start date to filter the records')
    to_date = fields.Date(string='To Date',
                          help='End date to filter the records')
    pos_session_id = fields.Many2one('pos.session',
                                     string='POS Session',
                                     help='List of pos session to generate '
                                          'report')
    partner_id = fields.Many2one('res.partner',
                                 string='Customer',
                                 help='List of partner name to generate '
                                      'report')

    def action_print_pdf(self):
        """Method to Print the report"""
        if self.from_date > self.to_date:
            raise ValidationError('Start Date must be less than End Date')
        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'pos_session_id': self.pos_session_id.id,
            'partner_id': self.partner_id.id,
        }
        return self.env.ref(
            'pos_analysis_report.action_report_pos_analysis').report_action(
            self, data=data)
