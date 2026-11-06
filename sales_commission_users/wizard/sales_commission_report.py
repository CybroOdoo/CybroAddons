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
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SalesCommissionReport(models.TransientModel):
    """Creating sales commission report model."""
    _name = 'sales.commission.report'
    _description = 'Sales Commission Report'

    sales_person_id = fields.Many2one(
        'res.users',
        string='Sales Person',
        help="Salesperson to filter commission records.",
    )
    start_date = fields.Date(
        string='Start Date',
        help="Start date for the report period.",
    )
    end_date = fields.Date(
        string='End Date',
        help="End date for the report period.",
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Ensure start date is not later than end date."""
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError(
                    _("Start Date cannot be greater than End Date.")
                )

    def action_print_report(self):
        """Create a report for sales commission for a salesperson."""
        self.ensure_one()
        data = {
            'sales_person_id': self.sales_person_id.id,
            'sales_person_name': self.sales_person_id.name or False,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        return self.env.ref(
            'sales_commission_users.sales_commission_report_action'
        ).report_action(self, data=data)
