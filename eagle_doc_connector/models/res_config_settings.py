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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Adds Eagle Doc connection settings and a usage-check shortcut."""

    _inherit = 'res.config.settings'

    eagle_doc_api_key = fields.Char(
        string='Eagle Doc API Key',
        config_parameter='eagle_doc.api_key',
        help='API Key for connecting to Eagle Doc API.'
    )
    eagle_doc_base_url = fields.Char(
        string='Eagle Doc Base URL',
        config_parameter='eagle_doc.base_url',
        help='Base URL for Eagle Doc API endpoint.'
    )

    is_eagle_doc_auto_create_partner = fields.Boolean(
        related='company_id.is_eagle_doc_auto_create_partner',
        string='Auto-create Customer/Vendor',
        readonly=False,
    )
    is_eagle_doc_auto_create_product = fields.Boolean(
        related='company_id.is_eagle_doc_auto_create_product',
        string='Auto-create Product',
        readonly=False,
    )
    is_eagle_doc_auto_create_tax = fields.Boolean(
        related='company_id.is_eagle_doc_auto_create_tax',
        string='Auto-create Tax',
        readonly=False,
    )
    eagle_doc_auto_tax_account_sale_id = fields.Many2one(
        related='company_id.eagle_doc_auto_tax_account_sale_id',
        string='Placeholder Tax Account (Sales)',
        readonly=False,
    )
    eagle_doc_auto_tax_account_purchase_id = fields.Many2one(
        related='company_id.eagle_doc_auto_tax_account_purchase_id',
        string='Placeholder Tax Account (Purchases)',
        readonly=False,
    )

    def action_eagle_doc_check_usage(self):
        """Open the Eagle Doc usage wizard with current month usage."""
        return self.env['eagle.doc.usage.wizard']._open_usage_wizard()


