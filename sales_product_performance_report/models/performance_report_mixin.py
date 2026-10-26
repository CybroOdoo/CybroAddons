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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Fields and helpers shared by the product and sales report wizards."""
from datetime import datetime, time
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PerformanceReportMixin(models.AbstractModel):
    """Period and company selection of the performance report wizards."""

    _name = 'performance.report.mixin'
    _description = "Performance Report Mixin"

    start_date = fields.Date(
        help="The start date",
    )
    end_date = fields.Date(
        help="The end date",
    )
    up_to_date_report = fields.Boolean(
        string="Report Up To Date",
        help='Ignore the dates and report on everything until today',
    )
    company_ids = fields.Many2many(
        comodel_name='res.company',
        help='Select companies to filter the report',
    )

    @api.constrains('start_date', 'end_date')
    def _check_date_validation(self):
        """Ensure the end date is not earlier than the start date."""
        for record in self:
            if (record.start_date and record.end_date
                    and record.end_date < record.start_date):
                raise ValidationError(self.env._(
                    "End Date must be greater than or equal to Start Date."))

    def _get_scope_companies(self):
        """Return the companies the report may cover.

        The selection is always intersected with the companies the current
        user belongs to, so a company can never be reached by tampering with
        ``company_ids``. With no (valid) selection, the active companies are
        used.
        """
        self.ensure_one()
        return (
            self.company_ids & self.env.user.company_ids
            or self.env.companies)

    def _get_date_domain(self, field_name):
        """Return the domain restricting ``field_name`` to the period.

        The end date is inclusive: ``field_name`` may be a datetime.
        """
        self.ensure_one()
        domain = []
        if not self.up_to_date_report:
            if self.start_date:
                start_dt = datetime.combine(self.start_date, time.min)
                domain.append((field_name, '>=', start_dt))
            if self.end_date:
                end_dt = datetime.combine(self.end_date, time.max)
                domain.append((field_name, '<=', end_dt))
        return domain
