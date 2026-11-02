# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RepairReport(models.TransientModel):
    """Wizard to print the machine repair report."""
    _name = 'repair.report'
    _description = 'Repair Report'

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 readonly=True,
                                 help="Company of the logged-in user.")
    from_date = fields.Date(string="Date From",
                            help="Start date of the report.")
    to_date = fields.Date(string="Date To", help="End date of the report.")

    @api.constrains('from_date', 'to_date')
    def _check_date_order(self):
        """Ensure that 'to_date' is not earlier than 'from_date'.

        :raises ValidationError: if 'to_date' is earlier than 'from_date'.
        """
        for record in self:
            if (record.from_date and record.to_date
                    and record.to_date < record.from_date):
                raise ValidationError(self.env._(
                    "Date To cannot be earlier than Date From."))

    def action_repair_report(self):
        """Print the repair report for the selected period."""
        data = {
            'company_id': self.company_id.id,
            'from_date': self.from_date,
            'to_date': self.to_date
        }
        domain = []
        if self.from_date:
            domain.append(('repair_req_date', '>=', self.from_date))
        if self.to_date:
            domain.append(('repair_req_date', '<=', self.to_date))
        if self.env['machine.repair'].search_count(domain, limit=1):
            return self.env.ref(
                'base_machine_repair_management.action_repair_report'
            ).report_action(self, data=data)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': self.env._(
                    "There are no repair requests for the selected period."),
                'type': 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
