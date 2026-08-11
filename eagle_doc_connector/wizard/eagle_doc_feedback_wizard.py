# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EagleDocFeedbackWizard(models.TransientModel):
    """Wizard to send document correction feedback to Eagle Doc."""

    _name = 'eagle.doc.feedback.wizard'
    _description = 'Send a correction to Eagle Doc'

    move_id = fields.Many2one('account.move', string="Document", required=True)
    feedback_type = fields.Selection([
        ('vendor', 'Vendor / Customer was wrong'),
        ('product_account', 'Bookkeeping Account or Tax Code was wrong'),
    ], string="What would you like to teach Eagle Doc?", required=True, default='vendor')
    new_vendor_name = fields.Char(string="Correct Vendor/Customer Name")
    new_vendor_account = fields.Char(string="Correct Account Number")
    new_vendor_city = fields.Char(string="Correct City")
    new_vendor_street = fields.Char(string="Correct Street")
    product_name = fields.Char(
        string="Product Name",
        help="Leave empty to correct at the vendor level instead of a specific product.",
    )
    new_bk_account_number = fields.Char(string="Correct Bookkeeping Account")
    new_tax_code = fields.Char(string="Correct Tax Code")

    @api.model
    def default_get(self, fields_list):
        """Default the document to the invoice the wizard was opened from."""
        res = super().default_get(fields_list)
        move_id = self.env.context.get('active_id')
        if move_id and 'move_id' in fields_list:
            res['move_id'] = move_id
        return res

    def action_submit(self):
        """Submit the selected correction to Eagle Doc's feedback API."""
        self.ensure_one()
        if not self.move_id.eagle_doc_sub_business_id:
            raise UserError(
                _("This document has no linked Eagle Doc sub-business."))

        if self.feedback_type == 'vendor':
            if not self.new_vendor_name or not self.new_vendor_account:
                raise UserError(
                    _("Please fill in both the correct vendor name and account number."))
            self.move_id.action_eagle_doc_submit_vendor_feedback(
                new_vendor_name=self.new_vendor_name,
                new_vendor_account=self.new_vendor_account,
                new_vendor_city=self.new_vendor_city,
                new_vendor_street=self.new_vendor_street,
            )
        else:
            if not self.new_bk_account_number:
                raise UserError(
                    _("Please fill in the correct bookkeeping account."))
            self.move_id.action_eagle_doc_submit_product_feedback(
                new_vendor_name=self.new_vendor_name or self.move_id.partner_id.name,
                new_bk_account_number=self.new_bk_account_number,
                new_product_name=self.product_name,
                new_tax_code=self.new_tax_code,
                product_name=self.product_name,
            )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Feedback Sent"),
                'message': _(
                    "Your correction was sent to Eagle Doc successfully."),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }