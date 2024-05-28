# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from collections import defaultdict
from odoo import models, _
from odoo.exceptions import UserError


def _prepare_datas(env, data):
    """
    Change product ids by actual product object to get access to fields in xml
    template we need to pass ids because reports only accepts native python
    types (int, float, strings, ...)
    """
    if data.get('active_model') == 'product.template':
        Product = env['product.template'].with_context(
            display_default_code=False)
    elif data.get('active_model') == 'product.product':
        Product = env['product.product'].with_context(
            display_default_code=False)
    else:
        raise UserError(_('Product model not defined, Please contact your administrator.'))

    total = 0
    quantity_by_product = defaultdict(list)
    for product_qty, qnty in data.get('quantity_by_product').items():
        product = Product.browse(int(product_qty))
        quantity_by_product[product].append((product.barcode, qnty, product.name,
                                             product.categ_id.name,
                                             product.detailed_type,
                                             product.list_price))
        total += qnty
    if data.get('custom_barcodes'):
        # We expect custom barcodes format as: {product: [(barcode, qty_of_barcode)]}
        for product, barcodes_qtys in data.get('custom_barcodes').items():
            quantity_by_product[Product.browse(int(product))] += (barcodes_qtys)
            total += sum(qty for _, qty in barcodes_qtys)
    return {
        'quantity': quantity_by_product,
    }


class ReportProductTemplateLabelDynamic(models.AbstractModel):
    """Product Dynamic Report"""
    _name = 'report.dynamic_product_label_print.report_dynamic'
    _description = 'Product Dynamic Report'

    def _get_report_values(self, docids, data):
        """
        override the method to create custom report with custom values
            :param docids: the recordset/ record from which the report action is
             invoked
            :param data: report data
            :return: data and recordsets to be used in the report template
            """
        return _prepare_datas(self.env, data)
