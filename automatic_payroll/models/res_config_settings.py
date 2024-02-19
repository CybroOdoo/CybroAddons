# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    generate_payslip = fields.Boolean(string="Generate Payslip",
                                      config_parameter="automatic_payroll.generate_payslip",
                                      help="Automatic generation of payslip "
                                           "batches and payslips (Monthly)")
    option = fields.Selection(
        [('first', 'Month First'), ('specific', 'Specific date'),
         ('end', 'Month End'), ], string='Option', default='first',
        config_parameter="automatic_payroll.option",
        help='Option to select the date to generate payslips')
    generate_day = fields.Integer(string="Day", default=1,
                                  config_parameter="automatic_payroll.generate_day",
                                  help="payslip generated day in a month")
