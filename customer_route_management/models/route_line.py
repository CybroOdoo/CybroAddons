# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or
#    sell copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import models, fields


class RouteLines(models.Model):
    """This class creates a model 'route.line' and adds fields"""
    _name = 'route.line'
    _description = 'Route Line'
    _rec_name = 'route'
    _order = 'sequence'

    sequence = fields.Integer(default=10)
    route = fields.Char(string='Routes', help="Route of corresponding"
                                              " route line.")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', default=lambda self: self.env.company)
    delivery_route_link = fields.Many2one('delivery.route',
                                          help="Delivery route of "
                                               "corresponding delivery.")
    cust_tree = fields.One2many('res.partner',
                                'locations',
                                string='Customers', help="Customer who has "
                                                         "selected "
                                                         "corresponding "
                                                         "route line"
                                                         " line seen under "
                                                         "route line.")
