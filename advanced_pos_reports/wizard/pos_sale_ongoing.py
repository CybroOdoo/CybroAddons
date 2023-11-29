# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class PosSaleOngoing(models.TransientModel):
    """Generate wizard for generate ongoing session report"""
    _name = 'pos.sale.ongoing'
    _description = 'Point of Sale Ongoing Session Report'

    session_ids = fields.Many2many('pos.session',
                                   string='POS Ongoing Sessions',
                                   required=True,
                                   help="Currently ongoing sessions",
                                   domain=[('state', '=', 'opened')])

    def action_generate_report(self):
        """Function to generate ongoing session report"""
        data = {'session_ids': self.session_ids.ids}
        return self.env.ref(
            'advanced_pos_reports.pos_ongoing_session_report').report_action(
            [], data=data)
