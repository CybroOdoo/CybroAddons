# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RepairReport(models.TransientModel):
    """This is used for the repairs for the machines report"""
    _name = 'repair.report'
    _description = 'Repair Report'

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 readonly=True, help="Login Company")
    from_date = fields.Date(string="Date From",
                            help="Start date of printing report")
    to_date = fields.Date(string="Date To", help="End date of printing report")

    @api.constrains('from_date', 'to_date')
    def _check_date_order(self):
        """Ensures that 'to_date' is later than 'from_date'.
        Raises:ValidationError: If 'to_date' is less than to 'from_date'."""
        for record in self:
            if record.from_date and record.to_date and record.to_date < record.from_date:
                raise ValidationError(_("To Date must be greater than From Date."))

    def action_repair_report(self):
        """This function is used to return the wizard for printing the report"""
        data = {
            'company_id': self.company_id.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
        }

        domain = []

        if self.from_date and self.to_date:
            domain.append(('repair_req_date', '>=', self.from_date))
            domain.append(('repair_req_date', '<=', self.to_date))
        elif self.from_date and not self.to_date:
            domain.append(('repair_req_date', '>=', self.from_date))
        elif self.to_date and not self.from_date:
            domain.append(('repair_req_date', '<=', self.to_date))

        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))

        vals = self.env['machine.repair'].search(domain, limit=1)

        if not vals:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'There is no repair request for the selected date(s).',
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }

        return self.env.ref(
            'base_machine_repair_management.action_repair_report'
        ).report_action(self, data=data)