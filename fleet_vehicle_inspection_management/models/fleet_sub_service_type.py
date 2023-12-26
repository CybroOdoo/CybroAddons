# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP(odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class FleetSubServiceTypes(models.Model):
    """Model for create service wizard"""
    _name = 'fleet.sub.service.type'
    _description = 'Fleet Sub Service Type'
    _rec_name = 'service_category'

    service_type_id = fields.Many2one('fleet.service.type',
                                      help='Vehicle service type',
                                      string='Vehicle service type')
    service_category = fields.Char(string='Category',
                                   help='Vehicle service category',)

    @api.onchange('service_type_id')
    def _onchange_service_type_id(self):
        """Select service category """
        for rec in self:
            rec.service_category = rec.service_type_id.category
