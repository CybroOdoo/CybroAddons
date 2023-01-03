# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    purchase_terms = fields.Text(string="Purchase Terms & Conditions", readonly=False)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_terms = fields.Text(related='company_id.purchase_terms', string=" Purchase Terms & Conditions",
                                 readonly=False)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _default_notes(self):
        return self.env.company.purchase_terms

    notes = fields.Html(string='Terms and Conditions', default=_default_notes)
