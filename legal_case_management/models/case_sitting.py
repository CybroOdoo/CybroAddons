# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(odoo@cybrosys.com)
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
from odoo import fields, models


class CaseSitting(models.Model):
    """Create case sitting"""
    _name = 'case.sitting'
    _description = 'Case Sitting"'

    date = fields.Date(string='Date', help='Date of case sitting')
    details = fields.Text(string='Details', help='Details of sittings')
    contact = fields.Char(string='Contact', help="Name of contact person")
    done = fields.Boolean(string='Done', help="Is the sitting is completed or "
                                              "not")
    case_id = fields.Many2one('case.registration', string='Connecting Field',
                              help="case related to the sitting")
