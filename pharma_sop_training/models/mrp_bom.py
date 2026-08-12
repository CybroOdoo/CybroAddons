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

from odoo import api, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class MrpBom(models.Model):
    """Requires every operation of an approved formula to carry an Effective SOP."""
    _inherit = 'mrp.bom'

    @api.constrains('operation_ids', 'formula_status')
    def _check_operation_sop_effective(self):
        """Ensures each operation of an approved formula uses an Effective SOP."""
        for rec in self:
            if rec.formula_status != 'approved':
                continue
            for op in rec.operation_ids:
                if not op.sop_id or op.sop_id.status != 'effective':
                    raise ValidationError(_(
                        "Cannot approve the formula: Operation '%s' uses an SOP "
                        "that is not currently Effective.") % op.name)
