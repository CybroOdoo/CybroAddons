# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, models


class CustomerQrTemplate(models.AbstractModel):
    """Abstract model for generating the customer QR template report."""
    _name = 'report.customer_product_qrcode.customer_qr_template'
    _description = 'Customer and Product QR Code Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get the report values for generating the customer QR template."""
        data = data or {}
        context = data.get('context') or self.env.context or {}
        active_model = context.get('active_model')
        report_type = data.get('type')
        record_id = data.get('data')

        if isinstance(record_id, (list, tuple)):
            target_ids = list(record_id)
        elif record_id:
            target_ids = [record_id]
        else:
            target_ids = docids

        if report_type == 'cust' or active_model == 'res.partner':
            dat = [self.env['res.partner'].browse(target_ids)]
        elif report_type == 'prod' or active_model == 'product.product':
            dat = [self.env['product.product'].browse(target_ids)]
        elif active_model == 'product.template':
            dat = [self.env['product.product'].search(
                [('product_tmpl_id', 'in', target_ids)])]
        else:
            if docids and self.env['res.partner'].browse(docids).exists():
                dat = [self.env['res.partner'].browse(docids)]
            else:
                dat = [self.env['product.product'].browse(target_ids)]
        return {
            'data': dat,
        }
