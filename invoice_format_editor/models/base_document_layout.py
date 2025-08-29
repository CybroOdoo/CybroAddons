# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, models, fields


class BaseDocumentLayout(models.TransientModel):
    """Inheriting the base document layout model"""
    _inherit = 'base.document.layout'

    base_layout = fields.Selection(
        related='company_id.base_layout',
        readonly=False,
        help="Base layout selection field inside "
             "document layout model")
    document_layout_id = fields.Many2one(
        related='company_id.document_layout_id', readonly=False,
        help="custom document layouts")

    @api.depends('report_layout_id', 'logo', 'font', 'primary_color',
                 'secondary_color', 'report_header', 'report_footer',
                 'base_layout', 'document_layout_id')
    def _compute_preview(self):
        """Compute a qweb based preview to display on the wizard"""
        styles = self._get_asset_style()
        for wizard in self:
            if wizard.report_layout_id:
                preview_css = self._get_css_for_preview(styles, wizard.id)
                ir_ui_view = wizard.env['ir.ui.view']

                # Define helper functions and context variables
                def is_html_empty(value):
                    return not bool(value)

                values = {
                    'company': wizard,
                    'preview_css': preview_css,
                    'is_html_empty': is_html_empty
                }
                try:
                    if wizard.base_layout == 'default':
                        wizard.preview = ir_ui_view._render_template(
                            'web.report_invoice_wizard_preview', values)
                    elif wizard.base_layout == 'normal':
                        wizard.preview = ir_ui_view._render_template(
                            'invoice_format_editor.report_preview_normal', values)
                    elif wizard.base_layout == 'modern':
                        wizard.preview = ir_ui_view._render_template(
                            'invoice_format_editor.report_preview_modern', values)
                    elif wizard.base_layout == 'old':
                        wizard.preview = ir_ui_view._render_template(
                            'invoice_format_editor.report_preview_old', values)
                    else:
                        wizard.preview = False
                except Exception as e:
                    print(f"Error rendering preview: {str(e)}")
                    wizard.preview = False
            else:
                wizard.preview = False

    @api.onchange('paperformat_id')
    def _onchange_paperformat_id(self):
        if self.paperformat_id.id == 3:
            self.base_layout = 'default'
