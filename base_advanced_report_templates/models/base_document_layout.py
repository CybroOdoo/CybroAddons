# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
    """Extends the functionality of the base.document.layout model in Odoo
    by adding additional fields .

    Methods:
        _compute_preview:
                Compute a qweb based preview to display on the wizards.
    """
    _inherit = 'base.document.layout'

    sale_document_layout_id = fields.Many2one(
        string="Sale Template",
        related='company_id.sale_document_layout_id',
        help='The report layout for sale  in the company.')
    purchase_document_layout_id = fields.Many2one(
        string="Purchase Template",
        related='company_id.purchase_document_layout_id',
        help='The report layout for purchase in the company.')
    account_document_layout_id = fields.Many2one(
        string="Account Template",
        related='company_id.account_document_layout_id',
        help='The report layout for account in the company.')
    stock_document_layout_id = fields.Many2one(
        string="Stock Template",
        related='company_id.stock_document_layout_id',
        help='The report layout for inventory in the company.')
    watermark = fields.Boolean(string='Watermark',
                               help='Enable or disable the watermark on '
                                    'the documents.')
    watermark_show = fields.Selection([
        ('logo', 'Company Logo'),
        ('name', 'Company Name'),
    ], default='logo', string="Watermark Show",
        help="The option to determine what should be displayed as the "
             "watermark on the documents. Select 'Company Logo' to display the "
             "company's logo as the watermark,or select 'Company Name' to "
             "display the company's name as the watermark.")

    @api.depends('report_layout_id', 'logo', 'font', 'primary_color',
                 'secondary_color', 'report_header', 'report_footer',
                 'sale_document_layout_id',
                 'stock_document_layout_id', 'account_document_layout_id',
                 'purchase_document_layout_id')
    def _compute_preview(self):
        """ Compute a qweb based preview to display on the wizards """
        styles = self._get_asset_style()
        for wizard in self:
            if wizard.report_layout_id and wizard.sale_document_layout_id:
                if wizard.sale_document_layout_id == 'modern':
                    preview_css = self._get_css_for_preview(styles,
                                                            wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'base_advanced_report_templates.'
                        'report_saleorder_modern_document',
                        {'company': wizard, 'preview_css': preview_css})
                elif wizard.sale_document_layout_id == 'traditional':
                    preview_css = self._get_css_for_preview(styles,
                                                            wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'base_advanced_report_templates.'
                        'report_saleorder_traditional_document',
                        {'company': wizard, 'preview_css': preview_css, })
                elif wizard.sale_document_layout_id == 'standard':
                    preview_css = self._get_css_for_preview(styles,
                                                            wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'base_advanced_report_templates.'
                        'report_saleorder_standard_document',
                        {'company': wizard, 'preview_css': preview_css, })
                elif wizard.sale_document_layout_id == 'attractive':
                    preview_css = self._get_css_for_preview(styles,
                                                            wizard.id)
                    ir_ui_view = wizard.env['ir.ui.view']
                    wizard.preview = ir_ui_view._render_template(
                        'base_advanced_report_templates.'
                        'report_saleorder_attractive_document',
                        {'company': wizard, 'preview_css': preview_css, })
                else:
                    wizard.preview = False
                if wizard.purchase_document_layout_id:
                    if wizard.purchase_document_layout_id == 'modern':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_purchaseorder_modern_document',
                            {'company': wizard, 'preview_css': preview_css})
                    elif wizard.purchase_document_layout_id == 'traditional':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_purchaseorder_traditional_document',
                            {'company': wizard, 'preview_css': preview_css, })
                    elif wizard.purchase_document_layout_id == 'standard':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_purchaseorder_standard_document',
                            {'company': wizard, 'preview_css': preview_css, })
                    elif wizard.purchase_document_layout_id == 'attractive':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_purchaseorder_attractive_document',
                            {'company': wizard, 'preview_css': preview_css, })
                    else:
                        wizard.preview = False
                if wizard.account_document_layout_id:
                    if wizard.account_document_layout_id == 'modern':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_account_modern_document',
                            {'company': wizard, 'preview_css': preview_css})
                    elif wizard.account_document_layout_id == 'traditional':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_account_traditional_document',
                            {'company': wizard, 'preview_css': preview_css, })
                    elif wizard.account_document_layout_id == 'standard':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_account_standard_document',
                            {'company': wizard, 'preview_css': preview_css, })
                    elif wizard.account_document_layout_id == 'attractive':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_account_attractive_document',
                            {'company': wizard, 'preview_css': preview_css, })
                    else:
                        wizard.preview = False
                if wizard.stock_document_layout_id:
                    if wizard.stock_document_layout_id == 'modern':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_stock_modern_document',
                            {'company': wizard, 'preview_css': preview_css})
                    elif wizard.stock_document_layout_id == 'traditional':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_stock_traditional_document',
                            {'company': wizard, 'preview_css': preview_css, })
                    elif wizard.stock_document_layout_id == 'standard':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_stock_standard_document',
                            {'company': wizard, 'preview_css': preview_css, })
                    elif wizard.stock_document_layout_id == 'attractive':
                        preview_css = self._get_css_for_preview(styles,
                                                                wizard.id)
                        ir_ui_view = wizard.env['ir.ui.view']
                        wizard.preview = ir_ui_view._render_template(
                            'base_advanced_report_templates.'
                            'report_stock_attractive_document',
                            {'company': wizard, 'preview_css': preview_css, })
                    else:
                        wizard.preview = False
            else:
                wizard.preview = False
