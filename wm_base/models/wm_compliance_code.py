# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class WmComplianceCode(models.Model):
    """Reference table mapping waste streams to their official regulatory compliance and classification codes."""
    _name = 'wm.compliance.code'
    _description = 'Compliance Code'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', help='Provides information about name', required=True)
    manifest_type = fields.Selection([
        ('hazardous', 'Hazardous Waste Manifest'),
        ('non_hazardous', 'Non-Hazardous Waste Manifest'),
        ('medical', 'Medical Waste Manifest'),
    ], string='Manifest Type')
    regulatory_body = fields.Char(string='Regulatory Body', help='Provides information about regulatory body')
