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


class FreightService(models.Model):
    """For Creating services available for freight"""
    _name = 'freight.service'
    _description = 'Freight Service'

    name = fields.Char(string='Name', required=True, help='Name of service')
    sale_price = fields.Float(string='Sale Price', required=True,
                              help='Sale price of the service')
    line_ids = fields.One2many('freight.service.line', 'service_id',
                               string='Service Lines',
                               help="Service lines corresponding to a service")
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)


class FreightServiceLine(models.Model):
    _name = 'freight.service.line'
    _description = 'Freight Service Line'

    partner_id = fields.Many2one('res.partner', string="Vendor",
                                 help='Partner corresponding to the service')
    sale = fields.Float(string='Sale Price',
                        help='Mention the price for the service')
    service_id = fields.Many2one('freight.service', string='Service',
                                 help='Relation from freight service')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
