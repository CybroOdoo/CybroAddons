# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
from odoo import fields, models


class DaycareActivities(models.Model):
    """ Adding fields and functionalities in daycare activities"""
    _name = 'daycare.activities'
    _description = 'Day Care Activities'
    _rec_name = 'activity_type_id'

    activity_type_id = fields.Many2one('activity.type', string='Name',
                                       required=True, help='To add name of'
                                                           ' activity')
    product_id = fields.Many2one('product.template',
                                 string='Product',
                                 domain=[('is_adult_activity', '=', True)],
                                 help='To add product details', required=True)
    notes = fields.Char(string='Notes', help='To add notes')
    time_in = fields.Float(string='Time In', help='To add time in details')
    time_out = fields.Float(string='Time Out', help='To add time out details')
    responsible_id = fields.Many2one('res.users',
                                     string='Responsible By',
                                     help='To add responsible person details')
    res_partner_id = fields.Many2one('res.partner',
                                     string='Partner',
                                     help='Partner Details')
