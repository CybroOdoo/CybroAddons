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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import binascii
import csv
import io
import tempfile
import openpyxl
from odoo.exceptions import ValidationError
from odoo import fields, models, Command


class ImportProductPricelist(models.TransientModel):
    """ Model for import product pricelist """
    _name = 'import.product.pricelist'
    _description = 'Product Pricelist Import'

    file_type = fields.Selection(selection=[('csv', 'CSV File'), ('xlsx',
                                                                  'XLSX File')],
                                 string='Import File Type', default='csv',
                                 help="file type")
    import_product_by = fields.Selection(selection=[
        ('name', 'Name'), ('default_code', 'Internal Reference'),
        ('barcode', 'Barcode')], required=True, string="Import price list by",
        help="Import product")
    product_pricelist_setting = fields.Selection(
        selection=[('basic', 'Multiple prices per product'),
                   ('advanced', 'Advanced price rules (discounts, formulas)')],
        string='Pricelist Method', default='basic',
        help="pricelist method type")
    compute_price = fields.Selection(
        selection=[('fixed', 'Fixed Price'),
                   ('percentage', 'Discount'),
                   ('formula', 'Formula')],
        string='Computation', default='fixed', help="Computation type")
    applied_on = fields.Selection(
        selection=[('3_global', 'All Products'),
                   ('2_product_category', 'Product Category'),
                   ('1_product', 'Product'),
                   ('0_product_variant', 'Product Variant')],
        string='Apply On', help="Appply on specific category",
        default='3_global')
    base = fields.Selection(selection=[
        ('list_price', 'Sales Price'),
        ('standard_price', 'Cost'),
        ('pricelist', 'Other Pricelist')], string="Based on", help="Base on",
        default='list_price', required=True)
    country_group_ids = fields.Many2many(comodel_name='res.country.group',
                                         string='Country Groups',
                                         help="country groups")
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 help="company")
    file_upload = fields.Binary(string='File Upload',
                                help="It helps to upload file")

    def get_val(self, item, *keys, default=None):
        for key in keys:
            if item.get(key):
                return item.get(key)
        return default

    def variant_search(self, var_vals, pro_tmpl):
        """returns product_product record matching the
        variant values"""
        product_product = self.env['product.product']
        product_attribute = self.env['product.attribute']
        product_attribute_value = self.env['product.attribute.value']
        product_template_attribute_value = self.env['product.template.attribute.value']
        if not (var_vals and pro_tmpl):
            return False
        variant_values = var_vals.split(',')
        variant_value_ids = []
        for var in variant_values:
            k_v = var.partition(":")
            attr = k_v[0].strip()
            attr_val = k_v[2].strip()
            var_attr_ids = product_attribute.search([('name', '=', attr)]).ids
            var_attr_val_ids = product_attribute_value.search(
                [('name', '=', attr_val), ('attribute_id', 'in', var_attr_ids)]).ids
            pro_temp_attr_val_id = (
                product_template_attribute_value.search([
                    ('product_attribute_value_id', 'in', var_attr_val_ids), ('product_tmpl_id', '=', pro_tmpl.id)]).id)
            variant_value_ids += [pro_temp_attr_val_id]
        if variant_value_ids:
            product_var = product_product.search(
                [('product_template_variant_value_ids', '=',
                  variant_value_ids)])
            return product_var
        return self.env['product.product']

    def set_multiple_price_per_product(self, item, vals_list, info_msg, error_msg, row_not_import_msg, row):
        to_continue = False
        product_template = pdt_tmpl = self.env['product.template']
        product_product = self.env['product.product']
        if self.import_product_by == 'name':
            product_name = self.get_val(item, 'Product', 'Pricelist Rules/Product')
            if product_name:
                domain = [('name', '=', product_name)]
                pdt_name = product_name.title()
                pdt_tmpl = product_template.search(domain)
                if not pdt_tmpl:
                    pdt_tmpl = product_template.create({
                        'name': pdt_name
                    })
                    info_msg += ("\n\tNew Product (%s) created!"
                                 "(row: %d)"
                                 % (pdt_name, row))
                elif len(pdt_tmpl) > 1:
                    error_msg += row_not_import_msg + (
                            "\n\tMultiple Product records with "
                            "name \"%s\" exists.(row: %d)"
                            % (product_name, row))
                    to_continue = True
                vals_list['product_tmpl_id'] = pdt_tmpl.id
            else:
                error_msg += row_not_import_msg + (
                    "\n\tProduct name missing in file!")
                to_continue = True
        elif self.import_product_by == 'default_code':
            internal_ref = self.get_val(item, 'Internal Reference', 'Pricelist Rules/Internal Reference')
            if internal_ref:
                domain = [('default_code', '=', internal_ref)]
                pdt = product_product.search(domain)
                if not pdt:
                    error_msg += row_not_import_msg + (
                            "\n\tProduct with Internal Reference %s"
                            " not found!" % internal_ref)
                    to_continue = True
                elif len(pdt) > 1:
                    error_msg += row_not_import_msg + (
                            "\n\tMultiple Products with "
                            "Internal Reference \"%s\" exists."
                            % internal_ref)
                    to_continue = True
                vals_list['product_tmpl_id'] = pdt.product_tmpl_id.id
            else:
                error_msg += row_not_import_msg + (
                    "\n\tInternal Reference missing in file!")
                to_continue = True
        elif self.import_product_by == 'barcode':
            barcode = self.get_val(item, 'Barcode', 'Pricelist Rules/Barcode')
            if barcode:
                domain = [('barcode', '=', barcode)]
                pdt = product_product.search(domain)
                if not pdt:
                    error_msg += row_not_import_msg + (
                            "\n\tProduct with barcode %s not found!"
                            % barcode)
                    to_continue = True
                elif len(pdt) > 1:
                    error_msg += row_not_import_msg + (
                            "\n\tMultiple Product records with "
                            "same Barcode \"%s\" exists."
                            % barcode)
                    to_continue = True
                vals_list['product_tmpl_id'] = pdt.product_tmpl_id.id
            else:
                error_msg += row_not_import_msg + (
                    "\n\tBarcode missing in file!")
                to_continue = True
        variant_vals = self.get_val(item, 'Variant Values', 'Pricelist Rules/Variant Values')
        if variant_vals and pdt_tmpl:
            variant = self.variant_search(variant_vals, pdt_tmpl)
            if variant:
                vals_list['product_id'] = variant.id
        fixed_price = self.get_val(item, 'Fixed Price', 'Pricelist Rules/Fixed Price')
        if fixed_price:
            vals_list['fixed_price'] = fixed_price
        return vals_list, to_continue

    def set_advanced_price_rules(self, item, vals_list, info_msg, error_msg, row_not_import_msg, row):
        vals_list['compute_price'] = self.compute_price
        vals_list['base'] = self.base
        vals_list['applied_on'] = self.applied_on
        product_category = self.env['product.category']
        product_pricelist = self.env['product.pricelist']
        product_template = self.env['product.template']
        product_product = self.env['product.product']
        to_continue = False
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
                        grand_parent_id = parent_category(parent_categ)
                        parent = product_category.create({
                            'name': parent_categ.rpartition('/')[2],
                            'parent_id': grand_parent_id
                        })
                        p_id = parent.id
                    return p_id
            return self.env['product.category']
        # --- Price computation ---
        discount = self.get_val(item, 'Discount%', 'Pricelist Rules/Discount%', 'Disc', 'Pricelist Rules/Disc',
                                'Disc.%', 'Pricelist Rules/Disc.%', 'Discount', 'Pricelist Rules/Discount')
        if self.compute_price == 'fixed':
            fixed_price = self.get_val(item, 'Fixed Price', 'Pricelist Rules/Fixed Price', default=0.0)
            vals_list['fixed_price'] = fixed_price
        elif self.compute_price == 'percentage':
            if discount:
                vals_list['percent_price'] = discount
        elif self.compute_price == 'formula':
            if discount:
                vals_list['price_discount'] = discount
            extra_fee = self.get_val(item, 'Extra Fee', 'Pricelist Rules/Extra Fee')
            if extra_fee:
                vals_list['price_surcharge'] = extra_fee
            rounding = self.get_val(item, 'Rounding Method', 'Pricelist Rules/Rounding Method')
            if rounding:
                vals_list['price_round'] = rounding
            min_margin = self.get_val(item, 'Min. Margin', 'Pricelist Rules/Min. Margin', 'Minimum Margin',
                                      'Pricelist Rules/Minimum Margin', 'Min Marging', 'Pricelist Rules/Min Margin')
            if min_margin:
                vals_list['price_min_margin'] = min_margin
            max_margin = self.get_val(item, 'Max. Margin', 'Pricelist Rules/Max. Margin', 'Max Margin',
                                      'Pricelist Rules/Max Margin', 'Maximum Margin', 'Pricelist Rules/Maximum Margin')
            if max_margin:
                vals_list['price_max_margin'] = max_margin
            if self.base == 'pricelist':
                other_pricelist_name = self.get_val(item, 'Other Pricelist', 'Pricelist Rules/Other Pricelist')
                if other_pricelist_name:
                    other_pricelist = product_pricelist.search(
                        [('name', '=', other_pricelist_name)],
                        limit=1)
                    if other_pricelist:
                        vals_list['base_pricelist_id'] = other_pricelist.id
                else:
                    error_msg += row_not_import_msg + (
                        "\n\t\"Other Pricelist\" missing in file!")
                    to_continue = True
        # --- Applied on category ---
        if self.applied_on == '2_product_category':
            category_name = self.get_val(item, 'Product Category', 'Pricelist Rules/Product Category', 'Category',
                                         'Pricelist Rules/Category')
            if category_name:
                item_category = category_name.replace(" ", "").replace("/", " / ").title()
                item_categ_name = item_category.rpartition('/')[2]

                categ = product_category.search(
                    [('complete_name', '=', item_category)], limit=1)

                if not categ:
                    categ = product_category.create({
                        'name': item_categ_name,
                        'parent_id': parent_category(item_category)
                    })
                vals_list['categ_id'] = categ.id
            else:
                error_msg += row_not_import_msg + (
                    "\n\tProduct Category missing in file!")
                to_continue = True
        # --- Applied on product ---
        if self.applied_on == '1_product':
            product_name = self.get_val(item, 'Product', 'Pricelist Rules/Product')
            if self.import_product_by == 'name':
                if product_name:
                    pro_tmpl = product_template.search(
                        [('name', '=', product_name)])
                    if not pro_tmpl:
                        pro_tmpl = product_template.create({
                            'name': product_name
                        })
                        info_msg += (
                                "\n\tNew Product (%s) created!"
                                "(row: %d)"
                                % (product_name, row))
                    elif len(pro_tmpl) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\tMultiple Product records with "
                                "name \"%s\" exists.(row: %d)"
                                % (product_name, row))
                        to_continue = True
                    vals_list['product_tmpl_id'] = pro_tmpl.id
                else:
                    error_msg += row_not_import_msg + (
                        "\n\tProduct name missing in file!")
                    to_continue = True
            if self.import_product_by == 'default_code':
                internal_ref = self.get_val(item, 'Internal Reference', 'Pricelist Rules/Internal Reference')
                if internal_ref:
                    pdt = product_product.search(
                        [('default_code', '=', internal_ref)])
                    if not pdt:
                        error_msg += row_not_import_msg + (
                                "\n\tProduct with Internal "
                                "Reference %s not found!"
                                % internal_ref)
                        to_continue = True
                    if len(pdt) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\tMultiple Product records with "
                                "Internal Reference \"%s\" exists."
                                % internal_ref)
                        to_continue = True
                    pro_tmpl = pdt.product_tmpl_id
                    vals_list['product_tmpl_id'] = pro_tmpl.id
                else:
                    error_msg += row_not_import_msg + (
                        "\n\tInternal Reference missing!")
                    to_continue = True
            if self.import_product_by == 'barcode':
                barcode = self.get_val(item, 'Barcode', 'Pricelist Rules/Barcode')
                if barcode:
                    pdt = product_product.search(
                        [('barcode', '=', barcode)])
                    if not pdt:
                        error_msg += row_not_import_msg + (
                                "\n\tProduct with Barcode %s not "
                                "found!"
                                % barcode)
                        to_continue = True
                    if len(pdt) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\tMultiple Product records with "
                                "same Barcode \"%s\" exists."
                                % barcode)
                        to_continue = True
                    pro_tmpl = pdt.product_tmpl_id
                    vals_list['product_tmpl_id'] = pro_tmpl.id
                else:
                    error_msg += row_not_import_msg + (
                        "\n\tBarcode missing!")
                    to_continue = True
        # --- Applied on variant ---
        if self.applied_on == '0_product_variant':
            product_name = self.get_val(item, 'Product', 'Pricelist Rules/Product')
            if product_name:
                product_variant = product_product.search(
                    [('name', '=', product_name)])
                if not product_variant:
                    error_msg += row_not_import_msg + (
                        "\n\tProduct not found!")
                    to_continue = True
                elif len(product_variant) > 1:
                    pro_tmpl_id = product_variant.mapped(
                        'product_tmpl_id')
                    if len(pro_tmpl_id) > 1:
                        error_msg += row_not_import_msg + (
                                "\n\tMultiple Product records are "
                                "linked with the product variant "
                                "\"%s\""
                                ". (row: %d)" % (
                                    product_name, row))
                        to_continue = True
                    variant_vals = self.get_val(item, 'Variant Values', 'Pricelist Rules/Variant Values')
                    if variant_vals:
                        variant = self.variant_search(variant_vals, pro_tmpl_id)
                        if variant:
                            vals_list['product_id'] = variant.id
                    else:
                        error_msg += row_not_import_msg + (
                            "\n\tVariant Values missing in "
                            "file!")
                        to_continue = True
                else:
                    vals_list['product_id'] = product_variant.id
        return vals_list, to_continue

    def action_import_product_pricelist(self):
        """Creating pricelist record using uploaded xl/csv files"""
        ir_config_parameter = self.env['ir.config_parameter']
        product_pricelist = self.env['product.pricelist']
        if self.product_pricelist_setting == 'basic':
            ir_config_parameter.set_param('product.product_pricelist_setting',
                                          'basic')
        elif self.product_pricelist_setting == 'advanced':
            ir_config_parameter.set_param('product.product_pricelist_setting',
                                          'advanced')
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file, and try again!")
            items = csv_reader
        if self.file_type == 'xlsx':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
            except:
                raise ValidationError(
                    """File not Valid.\n\nPlease check the """
                    """type and format of the file and try again!""")
            rows = list(sheet.rows)
            headers = [cell.value for cell in rows[0]]
            data = []
            for row in rows[1:]:
                data += [{k: v.value for k, v in zip(headers, row)}]
            items = data
        row = 0
        imported = 0
        created = 0
        error_msg = ""
        info_msg = ""
        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = "\nRow {rn} not imported.".format(rn=row)
                import_error_msg = ""
                missing_fields_msg = ""
                fields_msg = "\n\tMissing required field(s):"

                name = self.get_val(item, 'Name')
                if name:
                    vals['name'] = name
                else:
                    if missing_fields_msg:
                        missing_fields_msg += "\n\t\t\"Name\" "
                    else:
                        missing_fields_msg += (
                                row_not_import_msg + fields_msg +
                                "\n\t\t\"Name\"")
                if self.company_id:
                    vals['company_id'] = self.company_id.id
                if self.country_group_ids:
                    vals['country_group_ids'] = self.country_group_ids.ids
                import_error_msg += missing_fields_msg
                if import_error_msg:
                    error_msg += import_error_msg
                    continue
                price_list = product_pricelist.search([('name', '=', name)])
                if not price_list:
                    price_list = product_pricelist.create(vals)
                    created += 1
                elif len(price_list) > 1:
                    error_msg += row_not_import_msg + (
                            "\n\tMultiple Pricelist with "
                            "name \"%s\" exists."
                            % name)
                    continue
                else:
                    if vals.get('company_id'):
                        price_list.company_id = vals['company_id']
                        info_msg += ("\n\tCompany value updated from row %d"
                                     % row)
                    if vals.get('country_groups_ids'):
                        price_list.country_groups_ids = vals[
                            'country_groups_ids']
                        info_msg += ("\n\tCountry Groups updated from row %d"
                                     % row)
                vals_list = {}
                if self.product_pricelist_setting == 'basic':
                    vals_list, to_continue = self.set_multiple_price_per_product(
                        item, vals_list, info_msg, error_msg,
                        row_not_import_msg, row)
                    if to_continue:
                        continue
                elif self.product_pricelist_setting == 'advanced':
                    vals_list, to_continue = self.set_advanced_price_rules(
                        item, vals_list, info_msg, error_msg,
                        row_not_import_msg, row)
                    if to_continue:
                        continue
                min_qty = self.get_val(item, 'Minimum Quantity')
                if min_qty:
                    vals_list['min_quantity'] = min_qty
                start_date = self.get_val(item, 'Start_date')
                if start_date:
                    vals_list['date_start'] = start_date
                end_date = self.get_val(item, 'End_date')
                if end_date:
                    vals_list['date_end'] = end_date
                price_list.write({
                    'item_ids': [Command.create(vals_list)]
                })
                imported += 1
            if error_msg:
                error_msg = "\n\n⚠⚠⚠Warning!!!⚠⚠⚠" + error_msg
                error_message = self.env['import.message'].create(
                    {'message': error_msg})
                return {
                    'name': 'Done!',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'import.message',
                    'res_id': error_message.id,
                    'target': 'new',
                }
            if info_msg:
                info_msg = "\n\nNotes:" + info_msg
            msg = (("Imported %d records."
                    % imported) + info_msg)
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
        return False
