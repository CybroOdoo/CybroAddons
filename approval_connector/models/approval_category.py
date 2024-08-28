# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu K P (<https://www.cybrosys.com>)
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
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'
    """Class inherited for the category associated with approval category
    also add some additional fields"""

    approval_type = fields.Selection(selection_add=[
                    ('purchase', "Create RFQ's"), ('sale', 'Sale'), ],
                        string="Approval Type",
                        ondelete={'sale': 'cascade',},
                        help="Approval type to identify the model")

    @api.constrains('approval_type')
    def _check_approval_type(self):
        for record in self:
            if record.approval_type == 'sale':
                sale_approval_count = self.env[
                    'approval.category'].search_count(
                    [('approval_type', '=', 'sale')]
                )
                if sale_approval_count > 1:
                    raise ValidationError(
                        _("You are not allowed to create more than one sale "
                          "approval type.")
                    )
