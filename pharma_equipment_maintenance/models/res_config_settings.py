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


class ResConfigSettings(models.TransientModel):
    """Equipment check settings, shown under the Equipment toggle."""
    _inherit = 'res.config.settings'

    pharma_equipment_check = fields.Selection(
        selection=[
            ('off', 'No Check'),
            ('warn', 'Warn'),
            ('block', 'Block'),
        ],
        string='Equipment Check',
        default='block',
        config_parameter='pharma_equipment.check',
        help='What happens when a manufacturing order is confirmed on unfit '
             'equipment, or a result is entered on an instrument out of '
             'calibration. Block stops it (QA can override a manufacturing '
             'order); Warn lets it through and records the warning.',
    )
    group_pharma_sterile_mfg = fields.Boolean(
        string='Sterile Manufacturing',
        implied_group='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='Sterilisation of equipment and sterile products. Off, no '
             'sterile field, menu or rule appears anywhere.',
    )
