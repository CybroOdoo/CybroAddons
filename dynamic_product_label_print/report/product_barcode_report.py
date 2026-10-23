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
from collections import defaultdict
from odoo import models


def _get_product_field_val(product, fname, env):
    """Retrieve formatted value of a field for the given product."""
    if fname == 'categ_id':
        return product.categ_id.display_name or product.categ_id.name or ''
    elif fname == 'list_price':
        return str(product.list_price) if product.list_price else '0.0'
    elif fname == 'name':
        return product.name or ''
    elif fname == 'type':
        if (hasattr(product, '_fields')
                and 'type' in product._fields
                and hasattr(product._fields['type'],
                            '_description_selection')):
            selection_dict = dict(
                product._fields['type']._description_selection(env)
            )
            return (
                selection_dict.get(product.type)
                or str(product.type or '')
            )
        return str(product.type or '')
    elif hasattr(product, fname):
        val = getattr(product, fname)
        if hasattr(val, 'display_name'):
            return val.display_name or ''
        elif hasattr(val, 'name'):
            return val.name or ''
        return str(val) if val is not False and val is not None else ''
    return ''


def _prepare_datas(env, data):
    """
    Change product ids by actual product object to get access to fields in xml
    template we need to pass ids because reports only accepts native python
    types (int, float, strings, ...)
    """
    active_model = (
        data.get('active_model')
        or env.context.get('active_model')
        or 'product.product'
    )
    if active_model == 'product.template':
        Product = env['product.template'].with_context(
            display_default_code=False
        )
    else:
        Product = env['product.product'].with_context(
            display_default_code=False
        )

    template_id = data.get('layout_wizard')
    template = (
        env['dynamic.template'].browse(template_id)
        if template_id else False
    )
    fields_def = (
        template.dynamic_field_ids
        if (template and template.dynamic_field_ids) else []
    )

    cat_line = {'size': '14', 'color': 'red'}
    price_line = {'size': '16', 'color': 'green'}
    name_line = {'size': '14', 'color': 'blue'}
    field_lines = []

    for fdef in fields_def:
        fname = fdef.fd_name_id.name if fdef.fd_name_id else False
        if not fname:
            continue
        c_val = (fdef.color or '').strip()
        s_val = fdef.size or '14'
        if fname == 'categ_id':
            cat_line = {'size': s_val, 'color': c_val or 'red'}
        elif fname == 'list_price':
            price_line = {'size': s_val, 'color': c_val or 'green'}
        elif fname == 'name':
            name_line = {'size': s_val, 'color': c_val or 'blue'}

        field_lines.append({
            'fname': fname,
            'size': s_val,
            'color': c_val or '#000000',
        })

    quantity_by_product = defaultdict(list)
    for product_qty, qnty in (data.get('quantity_by_product') or {}).items():
        product = Product.browse(int(product_qty))
        barcode_val = (
            product.barcode
            or product.default_code
            or product.name
            or ''
        )

        prod_field_lines = []
        for fl in field_lines:
            val = _get_product_field_val(product, fl['fname'], env)
            prod_field_lines.append({
                'fname': fl['fname'],
                'val': val,
                'size': fl['size'],
                'color': fl['color'],
            })

        categ_name = (
            product.categ_id.display_name
            or product.categ_id.name
            or ''
        )
        quantity_by_product[product].append({
            'barcode': barcode_val,
            'qty': qnty,
            'product_name': product.name or '',
            'categ_name': categ_name,
            'price': str(product.list_price) if product.list_price else '0.0',
            'cat_line': cat_line,
            'price_line': price_line,
            'name_line': name_line,
            'field_lines': prod_field_lines,
        })

    if data.get('custom_barcodes'):
        for product, barcodes_qtys in data.get('custom_barcodes').items():
            for b_code, qty_val in barcodes_qtys:
                p_rec = Product.browse(int(product))
                prod_field_lines = []
                for fl in field_lines:
                    val = _get_product_field_val(p_rec, fl['fname'], env)
                    prod_field_lines.append({
                        'fname': fl['fname'],
                        'val': val,
                        'size': fl['size'],
                        'color': fl['color'],
                    })
                p_categ_name = (
                    p_rec.categ_id.display_name
                    or p_rec.categ_id.name
                    or ''
                )
                quantity_by_product[p_rec].append({
                    'barcode': b_code,
                    'qty': qty_val,
                    'product_name': p_rec.name or '',
                    'categ_name': p_categ_name,
                    'price': (
                        str(p_rec.list_price)
                        if p_rec.list_price else '0.0'
                    ),
                    'cat_line': cat_line,
                    'price_line': price_line,
                    'name_line': name_line,
                    'field_lines': prod_field_lines,
                })

    data.update({
        'quantity': quantity_by_product,
    })
    return data


class ReportProductTemplateLabelDynamic(models.AbstractModel):
    """Product Dynamic Report"""
    _name = 'report.dynamic_product_label_print.report_dynamic'
    _description = 'Product Dynamic Report'

    def _get_report_values(self, docids, data):
        """
        Override the method to create custom report with custom values
            :param docids: the recordset/ record from which the report action is
             invoked
            :param data: report data
            :return: data and recordsets to be used in the report template
        """
        return _prepare_datas(self.env, data)
