"""Machine repair management"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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


class RepairSummary(models.TransientModel):
    """This is used for the repairs for the machines report"""
    _name = 'repair.report.wizards'
    _description = 'Repair Report Wizard'

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 readonly=True, help="Login Company")
    from_date = fields.Date(string="Date From",
                            help="Start date of printing report")
    to_date = fields.Date(string="Date To", help="End date of printing report")

    def action_repair_report(self):
        """This function is used to return the wizard for printing the report"""
        data = {
            'company_id': self.company_id.id,
            'from_date': self.from_date,
            'to_date': self.to_date
        }
        return self.env.ref(
            'base_machine_repair_management.action_repair_report').report_action(
            self, data=data)
