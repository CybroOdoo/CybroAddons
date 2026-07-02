# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
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
from odoo.http import request


class CustomerQrTemplate(models.AbstractModel):
    """Abstract model for generating the customer QR template report."""
    _name = 'report.customer_product_qrcode.customer_qr_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get the report values for generating the customer QR template."""
        context = data.get('context', {})

        active_model = context.get('active_model')
        if active_model == 'res.partner':
            dat = [request.env['res.partner'].browse(context['active_id'])]
        elif active_model == 'product.template':
            dat = [request.env['product.product'].search(
                [('product_tmpl_id', '=', context['active_id'])])]
        else:
            dat = request.env['product.product'].browse(context['active_id'])
        return {
            'data': dat,
        }
