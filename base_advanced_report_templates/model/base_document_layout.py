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
from odoo import api, fields, models


class BaseDocumentLayout(models.TransientModel):
    """Inherited base document layout for selecting layouts"""
    _inherit = 'base.document.layout'

    sale_document_layout_id = fields.Many2one(string="Sale Template",
                                              related='company_id.sale_document_layout_id',
                                              help="selected layout for sale")
    purchase_document_layout_id = fields.Many2one(string="Purchase Template",
                                                  related='company_id.purchase_document_layout_id',
                                                  help="Selected layout for purchase")
    account_document_layout_id = fields.Many2one(string="Account Template",
                                                 related='company_id.account_document_layout_id',
                                                 help="Selected layout for Invoice")
    stock_document_layout_id = fields.Many2one(string="Delivery Template",
                                               related='company_id.stock_document_layout_id',
                                               help="selected document for Delivery")

    @api.depends('report_layout_id', 'logo', 'font', 'primary_color',
                 'secondary_color', 'report_header', 'report_footer',
                 'sale_document_layout_id',
                 'stock_document_layout_id', 'account_document_layout_id',
                 'purchase_document_layout_id')
    def _compute_preview(self):
        """Compute a qweb based preview to display on the wizard"""
        styles = self._get_asset_style()

        layout_mapping = {
            'sale': {
                'modern': 'report_saleorder_modern_document',
                'traditional': 'report_saleorder_traditional_document',
                'standard': 'report_saleorder_standard_document',
                'attractive': 'report_saleorder_attractive_document',
            },
            'purchase': {
                'modern': 'report_purchaseorder_modern_document',
                'traditional': 'report_purchaseorder_traditional_document',
                'standard': 'report_purchaseorder_standard_document',
                'attractive': 'report_purchaseorder_attractive_document',
            },
            'account': {
                'modern': 'report_account_modern_document',
                'traditional': 'report_account_traditional_document',
                'standard': 'report_account_standard_document',
                'attractive': 'report_account_attractive_document',
            },
            'stock': {
                'modern': 'report_stock_modern_document',
                'traditional': 'report_stock_traditional_document',
                'standard': 'report_stock_standard_document',
                'attractive': 'report_stock_attractive_document',
            },
        }
        ir_ui_view = self.env['ir.ui.view']
        for wizard in self:
            for doc_type, layouts in layout_mapping.items():
                layout_id = getattr(wizard, f"{doc_type}_document_layout_id")
                if layout_id and layout_id in layouts:
                    preview_css = self._get_css_for_preview(styles, wizard.id)
                    template_name = layouts[layout_id]
                    template = f'base_advanced_report_templates.{template_name}'
                    wizard.preview = ir_ui_view._render_template(template, {
                        'company': wizard, 'preview_css': preview_css})
                    break  # Once a valid layout is found, exit the loop
            else:
                wizard.preview = False  # If no valid layout is found
            if not wizard.report_layout_id:
                wizard.preview = False
