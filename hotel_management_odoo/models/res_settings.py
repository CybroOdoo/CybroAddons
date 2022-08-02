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


class ProductProduct(models.Model):
    _inherit = "product.product"

    service_ok = fields.Boolean("Is Service")
    room_ok = fields.Boolean("Is Room")
    meals_ok = fields.Boolean("Is Room")
    amenity_ok = fields.Boolean(string="Is Amenity")
    type_id = fields.Many2one('room.types')


class ProductProduct(models.Model):
    _inherit = "product.category"

    is_room_categ = fields.Boolean()
    is_meals_categ = fields.Boolean()


class Rooms(models.Model):
    _name = "room.room"
    _description = 'Rooms'

    floor_id = fields.Many2one('hotel.floor', string='Floor')
    type_id = fields.Many2one('room.types', string='Type',required=True)
    product_id = fields.Many2one('product.product', "product_id", required=True, delegate=True, ondelete="cascade")
    amenity_ids = fields.Many2many('hotel.amenity')
    status = fields.Selection([("available", "Available"), ("occupied", "Occupied"), ('book', 'Booked')],
                              default="available")
    manager_id = fields.Many2one('res.users', string='Manager')

    @api.model
    def create(self, vals):
        if "type_id" in vals:
            prod = self.env["room.types"].browse(vals["type_id"])
            vals.update({"categ_id": prod.categ_id.id, 'room_ok': True})
        return super(Rooms, self).create(vals)

    def write(self, vals):
        if "type_id" in vals:
            prod = self.env["room.types"].browse(vals["type_id"])
            vals.update({"categ_id": prod.categ_id.id})
        return super(Rooms, self).write(vals)

    def unlink(self):
        rec = self.env["product.product"].sudo().browse(self.product_id.id)
        rec.unlink()
        return super(Rooms, self).unlink()


class RoomTypes(models.Model):
    _name = "room.types"
    _description = 'Room Types'

    room_type_id = fields.Many2one("room.types", "Types")
    categ_id = fields.Many2one('product.category', "Product Category", delegate=True, copy=False, ondelete="cascade")
    num_person = fields.Integer(string='Number of persons',required=True)

    @api.model
    def create(self, vals):
        vals.update({'is_room_categ': True})
        return super(RoomTypes, self).create(vals)

    def write(self, vals):
        if "room_type_id" in vals:
            categ = self.env["room.types"].browse(vals['room_type_id'])
            vals.update({"categ_id": categ.categ_id.id})
        return super(RoomTypes, self).write(vals)

    def unlink(self):
        rec = self.env["product.category"].sudo().browse(self.categ_id.id)
        rec.unlink()
        return super(RoomTypes, self).unlink()


class Floor(models.Model):
    _name = "hotel.floor"
    _description = "Floor"

    name = fields.Char(string="Name", required=True)
