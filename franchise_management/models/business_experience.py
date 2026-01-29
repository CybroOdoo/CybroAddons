# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<https://www.cybrosys.com>)
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
#############################################################################
"""Business Experience model"""
from odoo import fields, models


class BusinessExperience(models.Model):
    """Business experience inverse model."""
    _name = 'business.experience'
    _description = 'Business Experience'

    experience_name = fields.Char(string='Experience',
                                  help='Business Experience')
    from_date = fields.Date(string='From Date', help='Experience start Date')
    to_date = fields.Date(string='To Date', help='Experience To Date')
    experience_id = fields.Many2one('franchise.dealer',
                                    help='Inverse field for Business'
                                         ' Experience model')
