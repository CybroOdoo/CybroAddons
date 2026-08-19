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
from odoo import fields,models


class AccountMove(models.Model):
    """Inherit the account_move to add some fields to connect with each Invoice in module"""
    _inherit = 'account.move'
    _description = 'Account Move'

    medical_bill_invoice_id = fields.Many2one(
        comodel_name="case.appointments",
        string="Medical Invoice ID",
        help="Reference to the medical bill invoice associated with a case appointment. "
             "This field links the invoice to the corresponding medical case."
    )
    grooming_bill_invoice_id = fields.Many2one(
        comodel_name="animal.grooming",
        string="Grooming Invoice ID",
        help="Reference to the grooming bill invoice associated with animal grooming services. "
             "This field links the invoice to the corresponding grooming service."
    )
    training_bill_invoice_id = fields.Many2one(
        comodel_name="animal.training",
        string="Training Invoice ID",
        help="Reference to the training bill invoice associated with animal training services. "
             "This field links the invoice to the corresponding training service."
    )
    maintenance_bill_invoice_id = fields.Many2one(
        comodel_name="res.maintenance",
        string="Maintenance Invoice ID",
        help="Reference to the maintenance bill invoice associated with resource maintenance. "
             "This field links the invoice to the corresponding maintenance service."
    )
    medical_test_bill_invoice_id = fields.Many2one(
        comodel_name="medical.report",
        string="Medical Test Invoice ID",
        help="Reference to the medical test bill invoice associated with medical reports. "
             "This field links the invoice to the corresponding medical test or report."
    )
