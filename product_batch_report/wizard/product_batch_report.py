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
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ProductBatchReport(models.TransientModel):
    """Wizard that prints the lot and serial number expiry report."""

    _name = 'product.batch.report'
    _description = 'Lot/Serial Number Expiry Report'

    tracking_wise = fields.Selection(
        [('tracking_wise', 'Lot/Serial Wise'),
         ('product_wise', 'Product Wise')],
        string='Tracking', default='tracking_wise', required=True,
        help="Choose whether the report lists lots and serial numbers one "
             "by one or grouped under their products.")
    product_ids = fields.Many2many(
        'product.product', string='Products',
        help="Products to include in the report. Leave empty to include "
             "all products.")
    expiry_days = fields.Integer(
        string='Within',
        help="Number of days, counted from today, that the report covers. "
             "Leave it at zero to cover every date.")
    expiry_type = fields.Selection(
        [('expired', 'Expired'),
         ('expire', 'Going to Expire')],
        string='Tracking Type', default='expire', required=True,
        help="Choose whether the report lists lots that have already "
             "expired or lots that are going to expire.")

    @api.constrains('expiry_days')
    def _check_expiry_days(self):
        """Refuse a negative number of days."""
        for wizard in self:
            if wizard.expiry_days < 0:
                raise ValidationError(
                    self.env._("Please enter a non-negative number of days."))

    def _get_date_range(self):
        """Return the (start, end) datetimes covered by the report."""
        now = fields.Datetime.now()
        days = timedelta(days=self.expiry_days)
        if self.expiry_type == 'expired':
            return (now - days if self.expiry_days else False), now
        return now, (now + days if self.expiry_days else False)

    def _get_lot_domain(self, date_from, date_to):
        """Return the domain that selects the lots to print."""
        domain = [
            ('expiration_date', '!=', False),
            ('product_qty', '>', 0),
        ]
        if date_from:
            domain.append(('expiration_date', '>=', date_from))
        if date_to:
            domain.append(('expiration_date', '<=', date_to))
        if self.tracking_wise == 'product_wise' and self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        return domain

    def _format_date(self, value):
        """Return a datetime as a string in the user's time zone."""
        local = fields.Datetime.context_timestamp(self, value)
        return local.strftime('%Y-%m-%d %H:%M:%S')

    def _prepare_report_data(self):
        """Build the values passed to the report template."""
        date_from, date_to = self._get_date_range()
        lots = self.env['stock.lot'].search(
            self._get_lot_domain(date_from, date_to),
            order='product_id, expiration_date')
        now = fields.Datetime.now()
        values = [{
            'lot_name': lot.name,
            'product': lot.product_id.display_name,
            'expiry_date': self._format_date(lot.expiration_date),
            'expiry_days': self.env._(
                "%(days)s Days", days=abs(lot.expiration_date - now).days),
        } for lot in lots]
        if self.tracking_wise == 'product_wise':
            heading = list(dict.fromkeys(line['product'] for line in values))
        else:
            heading = []

        def to_day(value):
            return self._format_date(value).split(' ')[0] if value else ''

        return {
            'values': values,
            'heading': heading,
            'view_type': self.tracking_wise,
            'expiry_type': self.expiry_type,
            'date_from': to_day(date_from),
            'date_to': to_day(date_to),
            'expiry_days': self.expiry_days,
        }

    def generate_pdf_report(self):
        """Return the PDF report action for the selected filters."""
        self.ensure_one()
        data = self._prepare_report_data()
        if not data['values']:
            raise UserError(
                self.env._("No lot or serial number matches the filters."))
        return self.env.ref(
            'product_batch_report.product_batch_report_action_report',
        ).report_action(self, data=data)
