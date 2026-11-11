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
import json
from datetime import datetime, time

from odoo import models
from odoo.exceptions import ValidationError
from odoo.tools import json_default


class SaleReportMixin(models.AbstractModel):
    """Common helpers of the sale report wizards."""
    _name = 'sale.report.mixin'
    _description = 'Sale Report Mixin'

    def _get_date_domain(self, field_name):
        """Return the domain of the wizard dates. The end date includes that
        whole day, because the order date is a date and time."""
        domain = []
        if self.from_date:
            domain.append((field_name, '>=', self.from_date))
        if self.to_date:
            domain.append((field_name, '<=',
                           datetime.combine(self.to_date, time.max)))
        return domain

    def _raise_no_data(self):
        """Tell the user that nothing matches the selected filters."""
        raise ValidationError(self.env._('No data available for printing.'))

    def _get_report_action(self, xml_id, datas):
        """Return the PDF report action of the wizard."""
        return self.env.ref(xml_id).report_action([], data=datas)

    def _get_xlsx_action(self, datas, report_name):
        """Return the action that downloads the XLSX report."""
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': self._name,
                'options': json.dumps(datas, default=json_default),
                'report_name': report_name,
            },
        }

    def _check_dates(self):
        """Refuse an end date before the start date."""
        for record in self:
            if (record.from_date and record.to_date
                    and record.to_date < record.from_date):
                raise ValidationError(self.env._(
                    'End Date cannot be earlier than Start Date. '
                    'Please correct the date range.'))
