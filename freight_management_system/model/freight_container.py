# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import fields, models


class FreightContainer(models.Model):
    _name = 'freight.container'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    size = fields.Float('Size', required=True)
    size_uom_id = fields.Many2one('uom.uom', string='Size UOM')
    weight = fields.Float('Weight', required=True)
    weight_uom_id = fields.Many2one('uom.uom', string='Weight UOM')
    volume = fields.Float('Volume', required=True)
    volume_uom_id = fields.Many2one('uom.uom', string='Volume UOM')
    active = fields.Boolean('Active', default=True)
    state = fields.Selection([('available', 'Available'),
                              ('reserve', 'Reserve')], default='available')


class FreightService(models.Model):
    _name = 'freight.service'

    name = fields.Char('Name', required=True)
    sale_price = fields.Float('Sale Price', required=True)
    line_ids = fields.One2many('freight.service.line', 'line_id')


class FreightServiceLine(models.Model):
    _name = 'freight.service.line'

    partner_id = fields.Many2one('res.partner', string="Vendor")
    sale = fields.Float('Sale Price')
    line_id = fields.Many2one('freight.service')
