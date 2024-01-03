# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anagha S (odoo@cybrosys.com)
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
from ast import literal_eval
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit configuration settings."""
    _inherit = 'res.config.settings'

    generate_work_report = fields.Boolean(string="Generate work report",
                                          help="Generate work report on "
                                               "creating timesheet.",
                                          config_parameter='work_report_from_timesheet.generate_work_report')
    report_method = fields.Selection(
        [('task_report', 'Task Report'), ('daily_report', 'Daily Report')],
        default='task_report', string="Report method",
        config_parameter="work_report_from_timesheet.report_method",
        help='Task Report: Send task report on creating timesheet.\nDaily '
             'Report: Send daily work report of each employee at end '
             'of the day.')
    employee_id = fields.Many2one('hr.employee', string="Email to",
                                  help='Select employee to whom work report '
                                       'to be send.',
                                  config_parameter='work_report_from_timesheet.employee_id')
    employee_ids = fields.Many2many(comodel_name='hr.employee',
                                    string="Email CC",
                                    help='Select employee for cc of email.')

    def set_values(self):
        """Inherit the set_values() method of class ResConfigSettings
         to save values."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('work_report_from_timesheet.employee_ids',
                         self.employee_ids.ids)
        return super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        """Inherit the get_values() method of class ResConfigSettings
         to get the values and update settings."""
        res = super(ResConfigSettings, self).get_values()
        email_cc = self.env['ir.config_parameter'].sudo().get_param(
            'work_report_from_timesheet.employee_ids')
        res.update(
            employee_ids=[
                (6, 0, literal_eval(email_cc))] if email_cc else False)
        return res
