# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import xlrd
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ImportProductPricelist(models.TransientModel):
    """For handling importing of product pricelist"""
    _name = 'import.product.pricelist'
    _description = 'Importing of product pricelist'

    name = fields.Char(string="Name", help="Name",
                       default="Import Product Pricelist")
    file_type = fields.Selection([('csv', 'CSV File'),
                                  ('xlsx', 'XLSX File')], default='csv',
                                 string='Import File Type',
                                 help="File types of importing")
    import_product_by = fields.Selection([
        ('name', 'Name'), ('default_code', 'Internal Reference'),
        ('barcode', 'Barcode')], string="Import Product By", required=True,
        help="Import products by using internal reference or barcode")
    product_pricelist_setting = fields.Selection(
        [('basic', 'Multiple prices per product'),
         ('advanced', 'Advanced price rules (discounts, formulas)')],
        string='Pricelists Method', default='basic',
        help="Pricelist method type")
    compute_price = fields.Selection(
        [('fixed', 'Fixed Price'), ('percentage', 'Discount'),
         ('formula', 'Formula')], string='Computation', default='fixed',
        help="Computation type of pricelist")
    applied_on = fields.Selection([('3_global', 'All Products'),
                                   ('2_product_category', 'Product Category'),
                                   ('1_product', 'Product'),
                                   ('0_product_variant', 'Product Variant')],
                                  string='Apply On', default='3_global',
                                  help="Apply which category products")
    base = fields.Selection(
        [('list_price', 'Sales Price'), ('standard_price', 'Cost'),
         ('pricelist', 'Other Pricelist')], string="Based on",
        help="Selection based on", default='list_price', required=True)
    country_group_ids = fields.Many2many('res.country.group',
                                         string='Country Groups',
                                         help="Country groups for applying "
                                              "pricelist")
    company_id = fields.Many2one('res.company',
                                 string="company", help="Company of the pricelist")
    file_upload = fields.Binary(string='File Upload',
                                help="It helps to upload file")

    def action_product_pricelist_import(self):
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
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise ValidationError(
                    """File not Valid.\n\nPlease check the """
                    """type and format of the file and try again!""")
            headers = sheet.row_values(0)
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)
                data += [{k: v for k, v in zip(headers, row)}]
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
                if item.get('Name'):
                    vals['name'] = item['Name']
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
                price_list = product_pricelist.search([('name', '=',
                                                        item['Name'])])
                if not price_list:
                    price_list = product_pricelist.create(vals)
                    created += 1
                elif len(price_list) > 1:
                    error_msg += row_not_import_msg + (
                            "\n\tMultiple Pricelist with "
                            "name \"%s\" exists."
                            % item['Name'])
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
                        variant_value_ids += [pro_temp_attr_val_id]
                    if variant_value_ids:
                        product_var = product_product.search(
                            [('product_template_variant_value_ids', '=',
                              variant_value_ids)])
                        return product_var

                # Multiple prices per product
                if self.product_pricelist_setting == 'basic':
                    if self.import_product_by == 'name':
                        if item.get('Product'):
                            pro_tmpl = product_template.search(
                                [('name', '=', item['Product'])])
                            if not pro_tmpl:
                                pro_tmpl = product_template.create({
                                    'name': (item['Product']).title()
                                })
                                info_msg += ("\n\tNew Product (%s) created!"
                                             "(row: %d)"
                                             % ((item['Product']).title(),
                                                row))
                            elif len(pro_tmpl) > 1:
                                error_msg += row_not_import_msg + (
                                        "\n\tMultiple Product records with "
                                        "name \"%s\" exists.(row: %d)"
                                        % (item['Product'], row))
                                continue
                            vals_list['product_tmpl_id'] = pro_tmpl.id
                        else:
                            error_msg += row_not_import_msg + (
                                "\n\tProduct name missing in file!")
                            continue
                    if self.import_product_by == 'default_code':
                        if item.get('Internal Reference'):
                            pro_pro = product_product.search(
                                [('default_code', '=', item[
                                    'Internal Reference'])])
                            if not pro_pro:
                                error_msg += row_not_import_msg + (
                                        "\n\tProduct with Internal Reference %s"
                                        " not found!"
                                        % item['Internal Reference'])
                                continue
                            elif len(pro_pro) > 1:
                                error_msg += row_not_import_msg + (
                                        "\n\tMultiple Products with "
                                        "Internal Reference \"%s\" exists."
                                        % item['Internal Reference'])
                                continue
                            pro_tmpl = pro_pro.product_tmpl_id
                            vals_list['product_tmpl_id'] = pro_tmpl.id
                        else:
                            error_msg += row_not_import_msg + (
                                "\n\tInternal Reference missing in file!")
                            continue
                    if self.import_product_by == 'barcode':
                        if item.get('Barcode'):
                            pro_pro = product_product.search(
                                [('barcode', '=', item['Barcode'])])
                            if not pro_pro:
                                error_msg += row_not_import_msg + (
                                        "\n\tProduct with barcode %s not found!"
                                        % item['Barcode'])
                                continue
                            elif len(pro_pro) > 1:
                                error_msg += row_not_import_msg + (
                                        "\n\tMultiple Product records with "
                                        "same Barcode \"%s\" exists."
                                        % item['Barcode'])
                                continue
                            pro_tmpl = pro_pro.product_tmpl_id
                            vals_list['product_tmpl_id'] = pro_tmpl.id
                        else:
                            error_msg += row_not_import_msg + (
                                "\n\tBarcode missing in file!")
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
                    vals_list['compute_price'] = self.compute_price
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
                            vals_list['percent_price'] = item['Discount']
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
                                    "\n\t\"Other Pricelist\" missing in file!")
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
                                "\n\tProduct Category missing in file!")
                            continue
                    if self.applied_on == '1_product':
                        if self.import_product_by == 'name':
                            if item.get('Product'):
                                pro_tmpl = product_template.search(
                                    [('name', '=', item['Product'])])
                                if not pro_tmpl:
                                    pro_tmpl = product_template.create({
                                        'name': item['Product']
                                    })
                                    info_msg += (
                                            "\n\tNew Product (%s) created!"
                                            "(row: %d)"
                                            % (item['Product'], row))
                                elif len(pro_tmpl) > 1:
                                    error_msg += row_not_import_msg + (
                                            "\n\tMultiple Product records with "
                                            "name \"%s\" exists.(row: %d)"
                                            % (item['Product'], row))
                                    continue
                                vals_list['product_tmpl_id'] = pro_tmpl.id
                            else:
                                error_msg += row_not_import_msg + (
                                    "\n\tProduct name missing in file!")
                                continue
                        if self.import_product_by == 'default_code':
                            if item.get('Internal Reference'):
                                pro_pro = product_product.search(
                                    [('default_code', '=',
                                      item['Internal Reference'])])
                                if not pro_pro:
                                    error_msg += row_not_import_msg + (
                                            "\n\tProduct with Internal "
                                            "Reference %s not found!"
                                            % item['Internal Reference'])
                                    continue
                                if len(pro_pro) > 1:
                                    error_msg += row_not_import_msg + (
                                            "\n\tMultiple Product records with "
                                            "Internal Reference \"%s\" exists."
                                            % item['Internal Reference'])
                                    continue
                                pro_tmpl = pro_pro.product_tmpl_id
                                vals_list['product_tmpl_id'] = pro_tmpl.id
                            else:
                                error_msg += row_not_import_msg + (
                                    "\n\tInternal Reference missing!")
                                continue
                        if self.import_product_by == 'barcode':
                            if item.get('Barcode'):
                                pro_pro = product_product.search(
                                    [('barcode', '=', item['Barcode'])])
                                if not pro_pro:
                                    error_msg += row_not_import_msg + (
                                            "\n\tProduct with Barcode %s not "
                                            "found!"
                                            % item['Barcode'])
                                    continue
                                if len(pro_pro) > 1:
                                    error_msg += row_not_import_msg + (
                                            "\n\tMultiple Product records with "
                                            "same Barcode \"%s\" exists."
                                            % item['Barcode'])
                                    continue
                                pro_tmpl = pro_pro.product_tmpl_id
                                vals_list['product_tmpl_id'] = pro_tmpl.id
                            else:
                                error_msg += row_not_import_msg + (
                                    "\n\tBarcode missing!")
                                continue
                    if self.applied_on == '0_product_variant':
                        if item.get('Product'):
                            product_variant = product_product.search(
                                [('name', '=', item['Product'])])
                            if not product_variant:
                                error_msg += row_not_import_msg + (
                                    "\n\tProduct not found!")
                                continue
                            elif len(product_variant) > 1:
                                pro_tmpl_id = product_variant.mapped(
                                    'product_tmpl_id')
                                if len(pro_tmpl_id) > 1:
                                    error_msg += row_not_import_msg + (
                                            "\n\tMultiple Product records are "
                                            "linked with the product variant "
                                            "\"%s\""
                                            ". (row: %d)" % (
                                                item['Product'], row))
                                    continue
                                if item.get('Variant Values'):
                                    variant = variant_search(
                                        item['Variant Values'], pro_tmpl_id)
                                    if variant:
                                        vals_list['product_id'] = variant.id
                                else:
                                    error_msg += row_not_import_msg + (
                                        "\n\tVariant Values missing in "
                                        "file!")
                                    continue
                            else:
                                vals_list['product_id'] = product_variant.id
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
