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
from odoo import fields, models, api


class ServiceCategories(models.Model):
    _name = "service.category"
    _description = "Service Categories"

    service_categ_id = fields.Many2one("service.category", "Types")
    product_categ_id = fields.Many2one('product.category', " Category", delegate=True, copy=False,
                                       ondelete="cascade", )

    def write(self, vals):
        if "service_categ_id" in vals:
            categ = self.env["service.category"].browse(vals['service.category'])
            vals.update({"categ_id": categ.product_categ_id.id})
        return super(ServiceCategories, self).write(vals)

    def unlink(self):
        rec = self.env["product.category"].sudo().browse(self.product_categ_id.id)
        rec.unlink()
        return super(ServiceCategories, self).unlink()


class HotelService(models.Model):
    _name = "hotel.service"
    _description = "Hotel Service"

    product_id = fields.Many2one('product.product', "Services", required=True, delegate=True, ondelete="cascade", )
    category_id = fields.Many2one("service.category", "Category", required=True, ondelete="restrict", )
    manager_id = fields.Many2one("res.users", string='Manager')

    @api.model
    def create(self, vals):
        if "category_id" in vals:
            prod = self.env["service.category"].browse(vals["category_id"])
            vals.update({"categ_id": prod.product_categ_id.id, 'service_ok': True})
        return super(HotelService, self).create(vals)

    def write(self, vals):
        if "category_id" in vals:
            prod = self.env["service.category"].browse(vals["category_id"])
            vals.update({"categ_id": prod.product_categ_id.id,'service_ok': True})
        return super(HotelService, self).write(vals)

    def unlink(self):
        rec = self.env["product.product"].sudo().browse(self.product_id.id)
        rec.unlink()
        return super(HotelService, self).unlink()
