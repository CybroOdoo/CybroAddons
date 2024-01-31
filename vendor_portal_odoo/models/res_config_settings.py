# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Class used to add field to res.config.settings"""
    _inherit = 'res.config.settings'

    rfq_done_based_on = fields.Selection([
        ('based_on_price', 'Minimum Quoted Price'),
        ('based_on_delivery_time', 'Minimum Delivery time')
    ], string="Set RFQs Based on", default='based_on_price',
        help="Rfq done conditions")
    quote_submission_msg = fields.Char(
        string="Quote Submission",
        config_parameter="vendor_portal_odoo.quote_submission_msg",
        help="Status message to display if a quote was submitted")
    quote_accept_msg = fields.Char(
        string="Quote Acceptance",
        config_parameter="vendor_portal_odoo.quote_accept_msg",
        help="Status message to display if a quote was accepted")
    quote_not_accept_msg = fields.Char(
        string="Quote not Accepted",
        config_parameter="vendor_portal_odoo.quote_not_accept_msg",
        help="Status message to display if a quote was not accepted")
    quote_cancel_msg = fields.Char(
        string="Quote Cancelled",
        config_parameter="vendor_portal_odoo.quote_cancel_msg",
        help="Status message to display if a quote was cancelled")
    quote_to_po_msg = fields.Char(
        string="PO created for the RFQ",
        config_parameter="vendor_portal_odoo.quote_to_po_msg",
        help="Status message to display if a quote was converted to PO")
