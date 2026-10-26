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


class PharmaValueSource(models.Model):
    """The equipment a registered measurement source belongs to."""
    _inherit = 'pharma.value.source'

    equipment_id = fields.Many2one(
        comodel_name='maintenance.equipment',
        index='btree_not_null',
        ondelete='set null',
        help='Equipment register entry of the device.',
    )


class MrpWorkcenter(models.Model):
    """GMP equipment used at the work centre."""
    _inherit = 'mrp.workcenter'

    pharma_equipment_ids = fields.Many2many(
        comodel_name='maintenance.equipment',
        relation='pharma_equipment_workcenter_rel',
        column1='workcenter_id',
        column2='equipment_id',
        string='GMP Equipment',
        help='Equipment checked when a manufacturing order routed through '
             'this work centre is confirmed.',
    )


class ProductTemplate(models.Model):
    """Marks products made under sterile conditions."""
    _inherit = 'product.template'

    pharma_sterile_product = fields.Boolean(
        string='Sterile Product',
        tracking=True,
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='Batches of this product need clean and sterile equipment.',
    )
