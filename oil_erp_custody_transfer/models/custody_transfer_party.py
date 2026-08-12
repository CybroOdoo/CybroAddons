# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

from odoo import fields, models

class CustodyTransferParty(models.Model):
    """
    Participants in a custody transfer.

    A single transfer can have multiple parties so the same engine can model
    single-company operations, hybrid flows (company owned, transporter held),
    intercompany transfers and full third-party commercial sales. Roles are
    intentionally additive to the dedicated owner/custodian/operator/carrier
    fields on the transfer.
    """
    _name = "custody.transfer.party"
    _description = "Custody Transfer Party"
    _order = "transfer_id, role, id"

    transfer_id = fields.Many2one(
        "custody.transfer",
        string="Transfer",
        required=True,
        ondelete="cascade",
        help="Custody transfer that this party participates in.",
    )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, help="The company managing this operational record or transaction.")
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True,
        help="Business partner playing this role on the transfer.",
    )
    role = fields.Selection(
        [
            ("seller", "Seller"),
            ("buyer", "Buyer"),
            ("operator", "Operator"),
            ("transporter", "Transporter"),
            ("customer", "Customer"),
            ("witness", "Witness"),
        ],
        string="Role",
        required=True,
        help="Role this partner plays on the transfer.",
    )
    reference = fields.Char(
        string="Reference",
        help="Optional external reference (contract number, dispatch id, etc.).",
    )
    notes = fields.Text(
        string="Notes",
        help="Free-text notes specific to this party's participation.",
    )
