# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models, api, _
from datetime import datetime


class MealsTypes(models.Model):
    _name = "meal.types"
    _description = "Meals Types"

    type_id = fields.Many2one("meal.types", "Types")
    product_categ_id = fields.Many2one('product.category', "Product Category", delegate=True, copy=False,
                                       ondelete="cascade")

    @api.model
    def create(self, vals):
        vals.update({'is_meals_categ': True})
        return super(MealsTypes, self).create(vals)

    def write(self, vals):
        if "type_id" in vals:
            categ = self.env["meal.type"].browse(vals['meal'])
            vals.update({"categ_id": categ.product_categ_id.id})
        return super(MealsTypes, self).write(vals)

    def unlink(self):
        rec = self.env["product.category"].sudo().browse(self.product_categ_id.id)
        rec.unlink()
        return super(MealsTypes, self).unlink()


