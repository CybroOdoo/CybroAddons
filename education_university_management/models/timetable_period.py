# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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


class TimetablePeriod(models.Model):
    """Manages the period details """
    _name = 'timetable.period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Timetable Period'

    name = fields.Char(string="Name", required=True, help="Enter Period Name")
    time_from = fields.Float(string='From', required=True,
                             help="Start and End time of Period.")
    time_to = fields.Float(string='To', required=True,
                           help="Start and End time of Period.")
    company_id = fields.Many2one(
        'res.company', string='Company', help="Current company",
        default=lambda self: self.env.company)
