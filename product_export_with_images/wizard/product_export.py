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
from odoo import fields, models


class ExportWizard(models.TransientModel):
    """ This class contains the functions to get selected product ids and
    redirect to excel download URL. """

    _name = "product.export"
    _description = "Export Products and Make an Excel Download URL."

    name = fields.Char(help="Name of the record")
    product_tmp_ids = fields.Many2many(
        "product.template", string="Products",
        help="Products for exporting")
    product_ids = fields.Many2many(
        "product.product", string="Products Variants",
        help="Product variants for exporting")

    def action_export_products(self):
        """ Select the active product/ product template ids. Return URL action
        to download excel report. """
        active_products = self.env.context.get("active_ids", [])
        active_model = self.env.context.get("active_model")
        export_wizard = False
        if active_model == "product.template":
            export_wizard = self.env["product.export"].create(
                {"product_tmp_ids": [(6, 0, active_products)]}
            )
        elif active_model == "product.product":
            export_wizard = self.env["product.export"].create(
                {"product_ids": [(6, 0, active_products)]}
            )
        if export_wizard:
            return {
                "type": "ir.actions.act_url",
                "url": "/products_download/excel_report/%s" % export_wizard.id,
                "target": "new",
            }

    def get_product_lines(self):
        """ Returns the product details like name, default code, category,
        image etc. """
        rec_list = []
        active_records = []
        if self.product_ids:
            active_records = self.product_ids
        elif self.product_tmp_ids:
            active_records = self.product_tmp_ids
        for rec in active_records:
            vals = {
                "name": rec.name,
                "internal_reference": rec.default_code,
                "category": rec.categ_id.display_name if rec.categ_id else "",
                "currency": self.env.company.currency_id.symbol or "",
                "cost": rec.standard_price,
                "sales_price": rec.list_price,
                "image": rec.image_1920 or rec.image_128,
            }
            rec_list.append(vals)
        return rec_list
