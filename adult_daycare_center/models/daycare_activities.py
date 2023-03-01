# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import models, fields


class DaycareActivitiesView(models.Model):
    _name = 'daycare.activities'
    _description = 'Day Care Activities'

    name = fields.Many2one('activity.type', string='Name', required=True)
    product_id = fields.Many2one('product.template', string='Product', required=True,
                                 domain=[('is_adult_activity', '=', True)])
    notes = fields.Char(string='Notes')
    time_in = fields.Float(string='Time In')
    time_out = fields.Float(string='Time Out')
    responsible = fields.Many2one('res.users', string='Responsible By')
    res_partner_id = fields.Many2one('res.partner')

