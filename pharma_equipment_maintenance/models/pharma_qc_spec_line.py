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


class PharmaQcSpecLine(models.Model):
    """Suggested instrument for a test parameter.

    Only a suggestion: a specification is a controlled document, and naming
    one asset would force a revision each time that unit is replaced.
    """
    _inherit = 'pharma.qc.spec.line'

    default_instrument_id = fields.Many2one(
        comodel_name='maintenance.equipment',
        domain="[('equipment_class', '=', 'testing')]",
        help='Instrument proposed on new results. The analyst may pick any '
             'other calibrated instrument.',
    )
