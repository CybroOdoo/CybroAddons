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
from .import_utils import get_file_content, read_csv_data, read_xlsx_data
from odoo.exceptions import ValidationError
from odoo import fields, models


class ImportProductPricelist(models.TransientModel):
    """ Model for import product pricelist """
    _name = 'import.product.pricelist'
    _description = 'Product Pricelist Import'

    file_type = fields.Selection(selection=[('csv', 'CSV File'), ('xlsx',
                                                                  'XLSX File')],
                                 string='Import File Type', default='csv',
                                 help="Type of the file to import")
    import_product_by = fields.Selection(selection=[
        ('name', 'Name'), ('default_code', 'Internal Reference'),
        ('barcode', 'Barcode')], required=True, string="Match Products By",
        default='name',
        help="Product field used to match the products in the file")
    product_pricelist_setting = fields.Selection(
        selection=[('basic', 'Multiple prices per product'),
                   ('advanced', 'Advanced price rules (discounts, formulas)')],
        string='Pricelist Method', default='basic',
        help="Pricelist method")
    compute_price = fields.Selection(
        selection=[('fixed', 'Fixed Price'),
                   ('percentage', 'Discount'),
                   ('formula', 'Formula')],
        string='Computation', default='fixed', help="How the price is computed")
    applied_on = fields.Selection(
        selection=[('3_global', 'All Products'),
                   ('2_product_category', 'Product Category'),
                   ('1_product', 'Product'),
                   ('0_product_variant', 'Product Variant')],
        string='Apply On', help="Products the pricelist rule applies to",
        default='3_global')
    base = fields.Selection(selection=[
        ('list_price', 'Sales Price'),
        ('standard_price', 'Cost'),
        ('pricelist', 'Other Pricelist')], string="Based on", help="Price the rule is based on",
        default='list_price', required=True)
    country_group_ids = fields.Many2many(comodel_name='res.country.group',
                                         string='Country Groups',
                                         help="Country groups")
    company_id = fields.Many2one(comodel_name='res.company', help="Company")
    file_upload = fields.Binary(help="File to import")

    def action_import_product_pricelist(self):
        """Creating pricelist record using uploaded xl/csv files"""
        ir_config_parameter = self.env['ir.config_parameter']
        product_template = self.env['product.template']
        product_product = self.env['product.product']
        product_pricelist = self.env['product.pricelist']
        product_category = self.env['product.category']
        product_attribute = self.env['product.attribute']
        product_attribute_value = self.env['product.attribute.value']
        product_template_attribute_value = self.env[
            'product.template.attribute.value']
        if self.product_pricelist_setting == 'basic':
            ir_config_parameter.set_str('product.product_pricelist_setting',
                                         'basic')
        elif self.product_pricelist_setting == 'advanced':
            ir_config_parameter.set_str('product.product_pricelist_setting',
                                         'advanced')
        items = []
        if self.file_type == 'csv':
            try:
                items = read_csv_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format "
                               "of the file, and try again!"))
        if self.file_type == 'xlsx':
            try:
                items = read_xlsx_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the "
                               "type and format of the file and try again!"))
        row = 0
        imported = 0
        created = 0
        error_msg = ""
        info_msg = ""
        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = self.env._("\nRow %(rn)s not imported.", rn=row)
                import_error_msg = ""
                missing_fields_msg = ""
                fields_msg = self.env._("\n\tMissing required field(s):")
                pricelist_name = (
                        item.get('Name') or
                        item.get('Pricelist') or
                        item.get('Pricelist Name') or
                        item.get('Pricelist Rules')
                )
                pricelist_name = str(pricelist_name).strip() if pricelist_name else False

                if pricelist_name:
                    vals['name'] = pricelist_name
                else:
                    if missing_fields_msg:
                        missing_fields_msg += self.env._("\n\t\t\"Name\" ")
                    else:
                        missing_fields_msg += (
                                row_not_import_msg + fields_msg +
                                self.env._("\n\t\t\"Name\""))
                if self.company_id:
                    vals['company_id'] = self.company_id.id
                if self.country_group_ids:
                    vals['country_group_ids'] = self.country_group_ids.ids
                import_error_msg += missing_fields_msg
                if import_error_msg:
                    error_msg += import_error_msg
                    continue
                price_list = product_pricelist.search([('name', '=',
                                                        pricelist_name)])
                if not price_list:
                    price_list = product_pricelist.create(vals)
                    created += 1
                elif len(price_list) > 1:
                    error_msg += row_not_import_msg + (
                            self.env._("\n\tMultiple pricelists with "
                            "name \"%s\" exist.", pricelist_name))
                    continue
                else:
                    if vals.get('company_id'):
                        price_list.company_id = vals['company_id']
                        info_msg += (self.env._("\n\tCompany value updated from row %d", row))
                    if vals.get('country_group_ids'):
                        price_list.country_group_ids = vals[
                            'country_group_ids']
                        info_msg += (self.env._("\n\tCountry Groups updated from row %d", row))
                vals_list = {}

                def variant_search(var_vals, pro_tmpl):
                    """returns product_product record matching the
                    variant values"""
                    if not (var_vals and pro_tmpl):
                        return False
                    variant_values = var_vals.split(',')
                    variant_value_ids = []
                    for var in variant_values:
                        k_v = var.partition(":")
                        attr = k_v[0].strip()
                        attr_val = k_v[2].strip()
                        var_attr_ids = product_attribute.search(
                            [('name', '=', attr)]).ids
                        var_attr_val_ids = product_attribute_value.search(
                            [('name', '=', attr_val),
                             ('attribute_id', 'in', var_attr_ids)]).ids
                        pro_temp_attr_val_id = (
                            product_template_attribute_value.search([
                                ('product_attribute_value_id', 'in',
                                 var_attr_val_ids), ('product_tmpl_id', '=',
                                                     pro_tmpl.id)]).id)
                        if not pro_temp_attr_val_id:
                            return product_product
                        variant_value_ids += [pro_temp_attr_val_id]
                    return pro_tmpl.product_variant_ids.filtered(
                        lambda v: set(v.product_template_variant_value_ids.ids)
                        == set(variant_value_ids))

                # Multiple prices per product
                if self.product_pricelist_setting == 'basic':
                    if self.import_product_by == 'name':
                        product_name = item.get('Product')
                        if product_name:
                            pro_tmpl = product_template.search(
                                [('name', '=', product_name)])
                            if not pro_tmpl:
                                pro_tmpl = product_template.create({
                                    'name': (product_name).title()
                                })
                                info_msg += (self.env._("\n\tNew Product (%(value1)s) created! (row: %(row)d)", value1=(product_name).title(), row=row))
                            elif len(pro_tmpl) > 1:
                                error_msg += row_not_import_msg + (
                                        self.env._("\n\tMultiple products with name \"%(product_name)s\" exist. (row: %(row)d)", product_name=product_name, row=row))
                                continue
                            vals_list['product_tmpl_id'] = pro_tmpl.id
                        else:
                            error_msg += row_not_import_msg + (
                                self.env._("\n\tProduct name missing in file!"))
                            continue
                    if self.import_product_by == 'default_code':
                        if item.get('Internal Reference'):
                            pro_pro = product_product.search(
                                [('default_code', '=', item[
                                    'Internal Reference'])])
                            if not pro_pro:
                                error_msg += row_not_import_msg + (
                                        self.env._("\n\tProduct with Internal Reference %s"
                                        " not found!", item['Internal Reference']))
                                continue
                            elif len(pro_pro) > 1:
                                error_msg += row_not_import_msg + (
                                        self.env._("\n\tMultiple Products with "
                                        "Internal Reference \"%s\" exist.", item['Internal Reference']))
                                continue
                            pro_tmpl = pro_pro.product_tmpl_id
                            vals_list['product_tmpl_id'] = pro_tmpl.id
                        else:
                            error_msg += row_not_import_msg + (
                                self.env._("\n\tInternal Reference missing in file!"))
                            continue
                    if self.import_product_by == 'barcode':
                        if item.get('Barcode'):
                            pro_pro = product_product.search(
                                [('barcode', '=', item['Barcode'])])
                            if not pro_pro:
                                error_msg += row_not_import_msg + (
                                        self.env._("\n\tProduct with barcode %s not found!", item['Barcode']))
                                continue
                            elif len(pro_pro) > 1:
                                error_msg += row_not_import_msg + (
                                        self.env._("\n\tMultiple products with "
                                        "the same Barcode \"%s\" exist.", item['Barcode']))
                                continue
                            pro_tmpl = pro_pro.product_tmpl_id
                            vals_list['product_tmpl_id'] = pro_tmpl.id
                        else:
                            error_msg += row_not_import_msg + (
                                self.env._("\n\tBarcode missing in file!"))
                            continue
                    if item.get('Variant Values') and pro_tmpl:
                        variant = variant_search(item['Variant Values'],
                                                 pro_tmpl)
                        if variant:
                            vals_list['product_id'] = variant.id
                    if item.get('Fixed Price'):
                        vals_list['fixed_price'] = item['Fixed Price']
                # Advanced price rules
                if self.product_pricelist_setting == 'advanced':
                    # Odoo merged the percentage and formula modes into 'discount'
                    vals_list['compute_price'] = (
                        'fixed' if self.compute_price == 'fixed' else 'discount')
                    vals_list['base'] = self.base
                    vals_list['applied_on'] = self.applied_on

                    def parent_category(category):
                        """return the parent category"""
                        if category:
                            parent_categ = category.rpartition('/')[0]
                            if parent_categ:
                                parent = product_category.search(
                                    [('complete_name', '=', parent_categ)])
                                if parent:
                                    p_id = parent.id
                                else:
                                    grand_parent_id = parent_category(
                                        parent_categ)
                                    parent = product_category.create({
                                        'name': parent_categ.rpartition('/')[
                                            2],
                                        'parent_id': grand_parent_id
                                    })
                                    p_id = parent.id
                                return p_id

                    # Price computation
                    if self.compute_price == 'fixed':
                        if item.get('Fixed Price'):
                            vals_list['fixed_price'] = item['Fixed Price']
                    elif self.compute_price == 'percentage':
                        if item.get('Discount%'):
                            vals_list['price_discount'] = item['Discount%']
                    elif self.compute_price == 'formula':
                        if item.get('Discount%'):
                            vals_list['price_discount'] = item['Discount%']
                        if item.get('Extra Fee'):
                            vals_list['price_surcharge'] = item['Extra Fee']
                        if item.get('Rounding Method'):
                            vals_list['price_round'] = item['Rounding Method']
                        if item.get('Min. Margin'):
                            vals_list['price_min_margin'] = item['Min. Margin']
                        if item.get('Max. Margin'):
                            vals_list['price_max_margin'] = item['Max. Margin']
                        if self.base == 'pricelist':
                            if item.get('Other Pricelist'):
                                other_pricelist = product_pricelist.search(
                                    [('name', '=', item['Other Pricelist'])],
                                    limit=1)
                                if other_pricelist:
                                    vals_list['base_pricelist_id'] = (
                                        other_pricelist.id)
                            else:
                                error_msg += row_not_import_msg + (
                                    self.env._("\n\t\"Other Pricelist\" missing in file!"))
                                continue
                    if self.applied_on == '2_product_category':
                        if item.get('Product Category'):
                            item_category = (item['Product Category']).replace(
                                " ", "").replace("/", " / ").title()
                            item_categ_name = item_category.rpartition('/')[2]
                            categ = product_category.search(
                                [('complete_name', '=', item_category)],
                                limit=1)
                            if not categ:
                                categ = product_category.create({
                                    'name': item_categ_name,
                                    'parent_id': parent_category(item_category)
                                })
                            vals_list['categ_id'] = categ.id
                        else:
                            error_msg += row_not_import_msg + (
                                self.env._("\n\tProduct Category missing in file!"))
                            continue
                    if self.applied_on == '1_product':
                        if self.import_product_by == 'name':
                            product_name = item.get('Product')
                            if product_name:
                                pro_tmpl = product_template.search(
                                    [('name', '=', product_name)])
                                if not pro_tmpl:
                                    pro_tmpl = product_template.create({
                                        'name': product_name
                                    })
                                    info_msg += (
                                            self.env._("\n\tNew Product (%(product_name)s) created! (row: %(row)d)", product_name=product_name, row=row))
                                elif len(pro_tmpl) > 1:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\tMultiple products with name \"%(product_name)s\" exist. (row: %(row)d)", product_name=product_name, row=row))
                                    continue
                                vals_list['product_tmpl_id'] = pro_tmpl.id
                            else:
                                error_msg += row_not_import_msg + (
                                    self.env._("\n\tProduct name missing in file!"))
                                continue
                        if self.import_product_by == 'default_code':
                            if item.get('Internal Reference'):
                                pro_pro = product_product.search(
                                    [('default_code', '=',
                                      item['Internal Reference'])])
                                if not pro_pro:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\tProduct with Internal "
                                            "Reference %s not found!", item['Internal Reference']))
                                    continue
                                if len(pro_pro) > 1:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\tMultiple products with "
                                            "Internal Reference \"%s\" exist.", item['Internal Reference']))
                                    continue
                                pro_tmpl = pro_pro.product_tmpl_id
                                vals_list['product_tmpl_id'] = pro_tmpl.id
                            else:
                                error_msg += row_not_import_msg + (
                                    self.env._("\n\tInternal Reference missing!"))
                                continue
                        if self.import_product_by == 'barcode':
                            if item.get('Barcode'):
                                pro_pro = product_product.search(
                                    [('barcode', '=', item['Barcode'])])
                                if not pro_pro:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\tProduct with Barcode %s not "
                                            "found!", item['Barcode']))
                                    continue
                                if len(pro_pro) > 1:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\tMultiple products with "
                                            "the same Barcode \"%s\" exist.", item['Barcode']))
                                    continue
                                pro_tmpl = pro_pro.product_tmpl_id
                                vals_list['product_tmpl_id'] = pro_tmpl.id
                            else:
                                error_msg += row_not_import_msg + (
                                    self.env._("\n\tBarcode missing!"))
                                continue
                    if (self.applied_on == '0_product_variant'
                            and self.import_product_by != 'name'):
                        # Internal Reference and Barcode are variant-level
                        # fields, so they identify the variant directly
                        column = ('Internal Reference'
                                  if self.import_product_by == 'default_code'
                                  else 'Barcode')
                        value = item.get(column)
                        if not value:
                            error_msg += row_not_import_msg + (
                                self.env._("\n\t%s missing in file!", column))
                            continue
                        product_variant = product_product.search(
                            [(self.import_product_by, '=', value)])
                        if not product_variant:
                            error_msg += row_not_import_msg + (
                                self.env._("\n\tProduct with %(column)s \"%(value)s\" not found!", column=column, value=value))
                            continue
                        if len(product_variant) > 1:
                            error_msg += row_not_import_msg + (
                                self.env._("\n\tMultiple products with %(column)s \"%(value)s\" exist.", column=column, value=value))
                            continue
                        vals_list['product_id'] = product_variant.id
                    elif self.applied_on == '0_product_variant':
                        product_name = item.get('Product')
                        if product_name:
                            product_variant = product_product.search(
                                [('name', '=', product_name)])
                            if not product_variant:
                                error_msg += row_not_import_msg + (
                                    self.env._("\n\tProduct not found!"))
                                continue
                            elif len(product_variant) > 1:
                                pro_tmpl_id = product_variant.mapped(
                                    'product_tmpl_id')
                                if len(pro_tmpl_id) > 1:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\tMultiple Product records are linked with the product variant \"%(product_name)s\". (row: %(row)d)", product_name=product_name, row=row))
                                    continue
                                if item.get('Variant Values'):
                                    variant = variant_search(
                                        item['Variant Values'], pro_tmpl_id)
                                    if not variant:
                                        error_msg += row_not_import_msg + (
                                            self.env._("\n\tNo variant of \"%(product_name)s\" matches the Variant Values \"%(values)s\". (row: %(row)d)", product_name=product_name, values=item['Variant Values'], row=row))
                                        continue
                                    vals_list['product_id'] = variant.id
                                else:
                                    error_msg += row_not_import_msg + (
                                        self.env._("\n\tVariant Values missing in "
                                        "file!"))
                                    continue
                            else:
                                vals_list['product_id'] = product_variant.id
                        else:
                            error_msg += row_not_import_msg + (
                                self.env._("\n\tProduct name missing in file!"))
                            continue
                if item.get('Minimum Quantity'):
                    vals_list['min_quantity'] = item['Minimum Quantity']
                if item.get('Start_date'):
                    vals_list['date_start'] = item['Start_date']
                if item.get('End_date'):
                    vals_list['date_end'] = item['End_date']
                price_list.write({
                    'item_ids': [(0, 0, vals_list)]
                })
                imported += 1
            if error_msg:
                error_msg = self.env._("\n\nWarning!!!") + error_msg
                error_message = self.env['import.message'].create(
                    {'message': error_msg})
                return {
                    'name': self.env._('Done!'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'import.message',
                    'res_id': error_message.id,
                    'target': 'new',
                }
            if info_msg:
                info_msg = self.env._("\n\nNotes:") + info_msg
            msg = ((self.env._("Imported %d records.", imported)) + info_msg)
            message = self.env['import.message'].create(
                {'message': msg})
            if message:
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': msg,
                        'type': 'rainbow_man',
                    }
                }
