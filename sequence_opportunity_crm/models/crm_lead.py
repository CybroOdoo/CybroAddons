# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

    opportunity_code = fields.Char(string="Opportunity Sequence Code",
                            help='Unique code for each opportunity',
                            readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        seq = self.env["ir.sequence"]
        for rec in records.filtered(lambda r: not r.opportunity_code):
            rec.opportunity_code = seq.next_by_code("code.opportunity.crm")

        return records

    @api.model
    def _assign_missing_opportunity_codes(self):
        """Assign sequence codes to existing records missing a code."""
        seq = self.env["ir.sequence"]
        leads = (
            self.sudo()
            .with_context(active_test=False)
            .search([("opportunity_code", "=", False)])
        )
        for lead in leads:
            lead.opportunity_code = seq.next_by_code("code.opportunity.crm")
