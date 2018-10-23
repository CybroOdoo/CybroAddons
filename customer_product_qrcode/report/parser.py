# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.http import request


class CustomerBadge(models.AbstractModel):
    _name = 'report.customer_product_qrcode.customer_qr_template'

    @api.model
    def get_report_values(self, docids, data=None):
        if data['type'] == 'cust':
            dat = [request.env['res.partner'].browse(data['data'])]
            print(dat)
        elif data['type'] == 'all':
            dat = [request.env['product.product'].search([('product_tmpl_id', '=', data['data'])])]
        else:
            dat = request.env['product.product'].browse(data['data'])
        return {
            'data': dat,
        }
