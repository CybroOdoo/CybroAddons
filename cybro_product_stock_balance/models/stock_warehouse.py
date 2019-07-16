# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Sreejith P(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    location_ids = fields.One2many('stock.location', 'location_id', compute='get_location')

    def get_location(self):
        for this in self:
            obj_warehouse = this.env['stock.warehouse'].browse(this.id).view_location_id
            obj_location = this.env['stock.location'].search([('usage', '=', 'internal')])
            locations_list = []
            if this.code:
                for i in obj_location:
                    if i.complete_name.find(obj_warehouse.complete_name) != -1:
                        locations_list.append(i.id)
                this.location_ids = locations_list