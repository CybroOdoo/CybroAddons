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
"""Wizard for selecting and importing product variant files."""
from odoo import fields, models
from odoo.exceptions import UserError


class ImportVariant(models.TransientModel):
    """Wizard for selecting the imported Files"""
    _name = 'import.product.variant'
    _description = "Import Product Variants"

    import_file = fields.Selection(
        [('csv', 'CSV File'), ('excel', 'Excel File')],
        required=True,
        string="Import File Type",
        help="Select the format of the file to import",
    )
    method = fields.Selection(
        [
            ('create', 'Create Product'),
            ('update', 'Update Product'),
            ('update_product', 'Update Product Variant'),
        ],
        required=True,
        help="Method for importing",
    )
    file = fields.Binary(
        required=True,
        help="The file to upload",
    )
    filename = fields.Char(string="File Name")

    def action_import_product_variant(self):
        """Redirects uploaded file into default Odoo base_import view."""
        self.ensure_one()
        if not self.file:
            raise UserError(self.env._("Please select a file to upload."))

        target_model = (
            'product.template'
            if self.method in ('create', 'update')
            else 'product.product'
        )
        file_name = self.filename or (
            'import_file.csv'
            if self.import_file == 'csv'
            else 'import_file.xlsx'
        )
        file_type = (
            'text/csv'
            if self.import_file == 'csv' or file_name.endswith('.csv')
            else 'application/vnd.openxmlformats-officedocument.'
                 'spreadsheetml.sheet'
        )

        base_import = self.env['base_import.import'].create({
            'res_model': target_model,
            'file': self.file,
            'file_name': file_name,
            'file_type': file_type,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'import',
            'name': self.env._('Import Products'),
            'params': {
                'model': target_model,
                'import_id': base_import.id,
                'file_name': file_name,
                'context': dict(self.env.context, active_model=target_model),
            },
        }
