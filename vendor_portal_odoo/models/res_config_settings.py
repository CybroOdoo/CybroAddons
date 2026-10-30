# -*- coding: utf-8 -*-
#############################################################################
#
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
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Class used to add field to res.config.settings"""
    _inherit = 'res.config.settings'

    rfq_done_based_on = fields.Selection([
        ('based_on_price', 'Minimum Quoted Price'),
        ('based_on_delivery_time', 'Minimum Delivery time')
    ], string="Set RFQs Based on", default='based_on_price', help='RFQ Based On')
    quote_submission_msg = fields.Text("Quote Submission",
                                       help="Status message to display if a quote was submitted")
    quote_accept_msg = fields.Text("Quote Acceptance",
                                   help="Status message to display if a quote was accepted")
    quote_not_accept_msg = fields.Text("Quote not Accepted",
                                       help="Status message to display if a quote was not accepted"
                                       )
    quote_cancel_msg = fields.Text("Quote Cancelled",
                                   help="Status message to display if a quote was cancelled")
    quote_to_po_msg = fields.Text("PO created for the RFQ",
                                  help="Status message to display if a quote was converted to PO")

    def set_values(self):
        """Setting field values"""
        res = super().set_values()
        config_parm = self.env['ir.config_parameter'].sudo()
        config_parm.set_str(
            'vendor_portal_odoo.rfq_done_based_on', self.rfq_done_based_on or 'based_on_price')
        config_parm.set_str(
            'vendor_portal_odoo.quote_submission_msg', self.quote_submission_msg or '')
        config_parm.set_str(
            'vendor_portal_odoo.quote_accept_msg', self.quote_accept_msg or '')
        config_parm.set_str(
            'vendor_portal_odoo.quote_not_accept_msg', self.quote_not_accept_msg or '')
        config_parm.set_str(
            'vendor_portal_odoo.quote_cancel_msg', self.quote_cancel_msg or '')
        config_parm.set_str(
            'vendor_portal_odoo.quote_to_po_msg', self.quote_to_po_msg or '')
        return res

    def get_values(self):
        """Getting field values"""
        res = super().get_values()
        config_parm = self.env['ir.config_parameter'].sudo()
        rfq_based = config_parm.get_str('vendor_portal_odoo.rfq_done_based_on', default='based_on_price')
        res['rfq_done_based_on'] = rfq_based if rfq_based in ('based_on_price', 'based_on_delivery_time') else 'based_on_price'
        res['quote_submission_msg'] = config_parm.get_str('vendor_portal_odoo.quote_submission_msg', default='')
        res['quote_accept_msg'] = config_parm.get_str('vendor_portal_odoo.quote_accept_msg', default='')
        res['quote_not_accept_msg'] = config_parm.get_str('vendor_portal_odoo.quote_not_accept_msg', default='')
        res['quote_cancel_msg'] = config_parm.get_str('vendor_portal_odoo.quote_cancel_msg', default='')
        res['quote_to_po_msg'] = config_parm.get_str('vendor_portal_odoo.quote_to_po_msg', default='')
        return res
