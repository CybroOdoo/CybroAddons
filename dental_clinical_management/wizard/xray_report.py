# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models


class XRayReport(models.TransientModel):
    """To add the x-ray report of the patients"""
    _name = 'xray.report'
    _description = 'X-Ray Report'

    patient_id = fields.Many2one('res.partner',
                                 string='Patient', required=True,
                                 help="name of the patient")
    report_date = fields.Date(string='Report Date',
                              default=lambda self: fields.Date.context_today(self),
                              required=True,
                              help="date of report adding")
    report_file = fields.Binary(string='Report File', required=True,
                                help="File to upload")
    file_name = fields.Char(string="File Name",
                            help="Name of the file")
    description = fields.Text(string='Description',
                              help="To add the description of the x-ray report")
