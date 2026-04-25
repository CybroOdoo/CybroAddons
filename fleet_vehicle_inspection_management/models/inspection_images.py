# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreerag PM(<https://www.cybrosys.com>)
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


class InspectionImages(models.Model):
    """Model to add inspection images"""
    _name = 'inspection.images'
    _description = 'Inspection Images'

    name = fields.Char(string='Image Name', help='Image name', required=True)
    image = fields.Binary(string='Image', help='Inspection Image',
                          required=True)
    inspection_id = fields.Many2one('inspection.request',
                                    help='Vehicle inspection',
                                    string='Vehicle inspection')
    service_log_id = fields.Many2one('vehicle.service.log',
                                     help='Service log',
                                     string='Service log')
