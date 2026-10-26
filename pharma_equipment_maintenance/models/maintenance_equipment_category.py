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

from .maintenance_equipment import EQUIPMENT_CLASSES


class MaintenanceEquipmentCategory(models.Model):
    """GMP classification of the equipment in the category.

    The class and the sterile flag are not set per equipment: the category
    decides them, so all equipment of a kind is held to the same rules.
    """
    _inherit = 'maintenance.equipment.category'

    gmp_critical = fields.Boolean(
        string='GMP Critical',
        help='Default GMP Critical flag of new equipment in this category.',
    )
    equipment_class = fields.Selection(
        selection=EQUIPMENT_CLASSES,
        help='Class of the equipment in this category: testing instruments '
             'are calibrated and can also be cleaned between uses, manufacturing '
             'equipment is cleaned between products, utility systems are '
             'monitored.',
    )
    pharma_sterile = fields.Boolean(
        string='Sterile Equipment',
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='Manufacturing equipment in this category is sterilised after '
             'cleaning and must be sterile for a sterile product.',
    )
