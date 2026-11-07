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
from odoo import api, models


class ProductStockDetails(models.AbstractModel):
    """Creates report.all_in_one_inventory_kit.report_product_stock_template"""
    _name = 'report.all_in_one_inventory_kit.report_product_stock_template'

    @api.model
    def _get_report_values(self, docids, data):
        """Method for getting report values."""
        docs = self.env.context.get('active_ids')
        if docs is None:
            docs = docids
        active_model = self.env.context.get('active_model')
        if active_model == 'product.template':
            docs = self.env['product.template'].search([('id', 'in', docs)])
        else:
            docs = self.env['product.product'].search([('id', 'in', docs)])
            active_model = 'product.product'
        return {
            'data': docs,
            'doc_ids': docs.ids,
            'doc_model': active_model,
            'docs': docs,
            'res_company': self.env.company,
        }