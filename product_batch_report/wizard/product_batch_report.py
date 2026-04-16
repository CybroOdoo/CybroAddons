# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from datetime import datetime, timedelta
from odoo import fields, models, _
from odoo.exceptions import UserError


class ProductBatchReport(models.TransientModel):
    """Model to create product batch report"""
    _name = 'product.batch.report'
    _description = 'Product Batch Report'

    tracking_wise = fields.Selection([
        ('tracking_wise', 'Lot/Serial Wise'),
        ('product_wise', 'Product Wise'), ],
        string='Tracking', default="tracking_wise", required=True,
        help="Tracking wise")
    product_ids = fields.Many2many('product.product', string='Product',
                                   help="Add products")
    expiry_days = fields.Integer(string='Within', help="Expire within...")
    expiry_type = fields.Selection([
        ('expired', 'Expired'),
        ('expire', 'Going to Expire'), ],
        string='Tracking Type', required=True, help="Type of expire")

    def generate_pdf_report(self):
        expiration_config = self.env['res.config.settings'].search([], order='id desc', limit=1).mapped(
            'module_product_expiry')
        if not expiration_config:
            raise UserError(_('Please enable Expiration Settings to get the Report.'))

        if self.expiry_days and self.expiry_days < 0:
            raise UserError(_('Please Enter a Non Negative Number.'))

        today = datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')
        batch_data = self.env['stock.lot']
        if self.tracking_wise == 'product_wise' and self.product_ids:
            product_ids = self.product_ids.ids
            batch_data = batch_data.search([('product_id', 'in', product_ids),('product_id.qty_available', '>', 0)])
        else:
            batch_data = batch_data.search([('product_id.qty_available', '>', 0)])

        if self.expiry_type == 'expired':
            batch_data = batch_data.filtered(lambda l: str(l.expiration_date) <= today)
        else:
            batch_data = batch_data.filtered(lambda l: str(l.expiration_date) >= today)
        values = []
        date_within = ''
        if self.expiry_days:
            if self.expiry_type == 'expired':
                date_within = datetime.strftime(datetime.today() - timedelta(days=int(self.expiry_days)),
                                                '%Y-%m-%d %H:%M:%S')
                batch_data = batch_data.filtered(lambda l: str(date_within) <= str(l.expiration_date) <= str(today))
            else:
                date_within = datetime.strftime(datetime.today() + timedelta(days=int(self.expiry_days)),
                                                '%Y-%m-%d %H:%M:%S')
                batch_data = batch_data.filtered(lambda l: str(date_within) >= str(l.expiration_date) >= str(today))

        batch_data = batch_data.filtered(lambda l: l.expiration_date)

        for line in batch_data:
            expiry_date_str = str(line.expiration_date)

            # Attempt to parse the date with and without microseconds
            if '.' in expiry_date_str:
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d %H:%M:%S.%f")
            else:
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d %H:%M:%S")
            expiry_days = (expiry_date - datetime.strptime(today, "%Y-%m-%d %H:%M:%S")).days

            values.append({
                'lot_name': line.name,
                'product': line.product_id.name,
                'expiry_date': expiry_date_str,
                'expiry_days': f"{abs(expiry_days)} Days"
            })
        heading = [{'name': line.id if self.tracking_wise == 'tracking_wise' else line.product_id.name} for line in
                   batch_data]
        heading = [dict(t) for t in {tuple(d.items()) for d in heading}]

        data_dict = {
            'values': values,
            'heading': heading,
            'view_type': self.tracking_wise,
            'expiry_type': self.expiry_type,
            'today': today.split(' ')[0],
            'date_within': date_within.split(' ')[0] if date_within else '',
            'expiry_days': self.expiry_days,
        }
        return self.env.ref('product_batch_report.product_batch_report_action_report').report_action(self,
                                                                                                     data=data_dict)