# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class PropertyCommission(models.Model):
    """A class for the model property commission to represent
    the commission type for property"""
    _name = 'property.commission'
    _description = 'Property Commission'

    name = fields.Char(string='Commission Name',
                       help="Name of commission plan", required=True)
    commission_type = fields.Selection([('fixed', 'Fixed'),
                                        ('percentage', 'Percentage')],
                                       string='Commission Type', required=True,
                                       help='The type of the commission either '
                                            'fixed or a percentage')
    commission = fields.Float(string='Commission Rate',
                              help="Commission calculating value.")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
