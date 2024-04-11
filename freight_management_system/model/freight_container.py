# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class FreightContainer(models.Model):
    """Model for creating the containers for freight"""
    _name = 'freight.container'
    _description = 'Freight Container'

    name = fields.Char(string='Name', required=True,
                       help='Name of the container')
    code = fields.Char(string='Code', help='Code for the container')
    size = fields.Float(string='Size', required=True,
                        help='Size of the container')
    size_uom_id = fields.Many2one('uom.uom', string='Size UOM',
                                  help='The unit of measure of selected size')
    weight = fields.Float(string='Weight', required=True,
                          help='The weight capacity of container')
    weight_uom_id = fields.Many2one('uom.uom', string='Weight UOM',
                                    help='The unit of measure of selected'
                                         'weight')
    volume = fields.Float(string='Volume', required=True,
                          help='Volume of the container')
    volume_uom_id = fields.Many2one('uom.uom', string='Volume UOM',
                                    help='The unit of measure of the volume')
    active = fields.Boolean(string='Active', default=True,
                            help='Make it active or inactive')
    state = fields.Selection([('available', 'Available'),
                              ('reserve', 'Reserve')], default='available',
                             help='Select the state')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
