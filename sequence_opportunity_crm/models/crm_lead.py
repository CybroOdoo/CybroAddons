# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Sabeel B (Contact : odoo@cybrosys.com)
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
from odoo import api, fields, models


class CrmLead(models.Model):
    """
    CRM Lead
    This class extends the base `crm.lead` model to add opportunity functionally
    """
    _inherit = 'crm.lead'
    _description = 'CRM Lead'

    oppo_code = fields.Char(string="Opportunity Sequence Code",
                            help='Unique code for each opportunity',
                            readonly=True)
    sequence_create = fields.Boolean(compute="_compute_sequence_create",
                                     string='Create Sequence',
                                     help='Creates unique code for '
                                          'each opportunity')

    def _compute_sequence_create(self):
        """ This method is used to compute the value of sequence_create field
        """
        for rec in self:
            rec.sequence_create = (
                self.env["ir.config_parameter"].sudo().get_param(
                    "sequence_opportunity_crm.sequence_create"))

    @api.model_create_multi
    def create(self, vals):
        """ This method is used to create sequence for each opportunity """
        oppo = super().create(vals)
        if oppo.sequence_create:
            oppo.oppo_code = (self.env["ir.sequence"].next_by_code
                              ("code.opportunity.crm"))
        return oppo
