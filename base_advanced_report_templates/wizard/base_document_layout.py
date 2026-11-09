# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################
"""Transient model extending base document layout."""
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

TEMPLATE_MAP = {
    'sale': {
        'modern': (
            'base_advanced_report_templates.'
            'report_saleorder_modern_document'
        ),
        'traditional': (
            'base_advanced_report_templates.'
            'report_saleorder_traditional_document'
        ),
        'standard': (
            'base_advanced_report_templates.'
            'report_saleorder_standard_document'
        ),
        'attractive': (
            'base_advanced_report_templates.'
            'report_saleorder_attractive_document'
        ),
    },
    'purchase': {
        'modern': (
            'base_advanced_report_templates.'
            'report_purchaseorder_modern_document'
        ),
        'traditional': (
            'base_advanced_report_templates.'
            'report_purchaseorder_traditional_document'
        ),
        'standard': (
            'base_advanced_report_templates.'
            'report_purchaseorder_standard_document'
        ),
        'attractive': (
            'base_advanced_report_templates.'
            'report_purchaseorder_attractive_document'
        ),
    },
    'account': {
        'modern': (
            'base_advanced_report_templates.'
            'report_account_modern_document'
        ),
        'traditional': (
            'base_advanced_report_templates.'
            'report_account_traditional_document'
        ),
        'standard': (
            'base_advanced_report_templates.'
            'report_account_standard_document'
        ),
        'attractive': (
            'base_advanced_report_templates.'
            'report_account_attractive_document'
        ),
    },
    'stock': {
        'modern': (
            'base_advanced_report_templates.'
            'report_stock_modern_document'
        ),
        'traditional': (
            'base_advanced_report_templates.'
            'report_stock_traditional_document'
        ),
        'standard': (
            'base_advanced_report_templates.'
            'report_stock_standard_document'
        ),
        'attractive': (
            'base_advanced_report_templates.'
            'report_stock_attractive_document'
        ),
    },
}


class BaseDocumentLayout(models.TransientModel):
    """Extend base.document.layout to incorporate advanced report templates."""
    _inherit = 'base.document.layout'

    sale_document_layout_id = fields.Many2one(
        related='company_id.sale_document_layout_id',
        readonly=False,
        string="Sale Document Layout",
        help="This field specifies the document layout for sales "
             "associated with the company.",
    )
    purchase_document_layout_id = fields.Many2one(
        related='company_id.purchase_document_layout_id',
        readonly=False,
        string="Purchase Document Layout",
        help="This field specifies the document layout for purchases "
             "associated with the company.",
    )
    account_document_layout_id = fields.Many2one(
        related='company_id.account_document_layout_id',
        readonly=False,
        string="Account Document Layout",
        help="This field specifies the document layout for accounting "
             "associated with the company.",
    )
    stock_document_layout_id = fields.Many2one(
        related='company_id.stock_document_layout_id',
        readonly=False,
        string="Stock Document Layout",
        help="This field specifies the document layout for stock "
             "management associated with the company.",
    )
    watermark = fields.Boolean(
        help="This field is used to specify watermark settings "
             "for documents associated with the company.",
    )
    watermark_show = fields.Selection(
        selection=[
            ('logo', 'Company Logo'),
            ('name', 'Company Name'),
        ],
        default='logo',
        help="Select the element to show as a watermark on the documents.",
    )

    def _get_template_for_layout(self, doc_type, layout):
        """Find the template identifier corresponding to the layout theme."""
        style = getattr(layout, 'theme_style', False)
        if not style and hasattr(layout, 'name') and layout.name:
            name_lower = layout.name.lower()
            for key in ('attractive', 'modern', 'standard', 'traditional'):
                if key in name_lower:
                    style = key
                    break
        if not style:
            style = 'traditional'
        return TEMPLATE_MAP.get(doc_type, {}).get(style)

    def _create_mock_record(self, doc_type, company):
        """Build in-memory mock record for fallback preview."""
        partner = company.partner_id or self.env['res.partner'].search([], limit=1)
        product = self.env['product.product'].search([], limit=1)
        vals = {
            'company_id': company.id,
            'partner_id': partner.id if partner else False,
        }
        if doc_type == 'sale':
            vals.update({'name': 'SO0001', 'state': 'draft'})
            if product:
                vals['order_line'] = [
                    (0, 0, {
                        'product_id': product.id,
                        'product_uom_qty': 1.0,
                        'price_unit': 100.0,
                    })
                ]
            return self.env['sale.order'].new(vals)
        if doc_type == 'purchase':
            vals.update({'name': 'PO0001', 'state': 'draft'})
            if product:
                vals['order_line'] = [
                    (0, 0, {
                        'product_id': product.id,
                        'product_qty': 1.0,
                        'price_unit': 100.0,
                    })
                ]
            return self.env['purchase.order'].new(vals)
        if doc_type == 'account':
            vals.update({'name': 'INV0001', 'move_type': 'out_invoice'})
            if product:
                vals['invoice_line_ids'] = [
                    (0, 0, {
                        'product_id': product.id,
                        'quantity': 1.0,
                        'price_unit': 100.0,
                    })
                ]
            return self.env['account.move'].new(vals)
        if doc_type == 'stock':
            picking_type = self.env['stock.picking.type'].search(
                [('company_id', '=', company.id)], limit=1
            )
            vals.update({
                'name': 'WH/OUT/0001',
                'picking_type_id': picking_type.id if picking_type else False,
            })
            return self.env['stock.picking'].new(vals)
        return None

    # pylint: disable=broad-exception-caught
    def _get_sample_record(self, doc_type, layout=None):
        """Retrieve or create a sample document record for preview rendering."""
        _ = layout
        company = self.company_id or self.env.company
        model_map = {
            'sale': 'sale.order',
            'purchase': 'purchase.order',
            'account': 'account.move',
            'stock': 'stock.picking',
        }
        model_name = model_map.get(doc_type)
        if not model_name:
            return None

        # 1. Check active record from context
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model == model_name and active_id:
            record = self.env[model_name].browse(active_id)
            if record.exists():
                return record

        # 2. Search for existing database record
        record = self.env[model_name].search([('company_id', '=', company.id)], limit=1)
        if not record:
            record = self.env[model_name].search([], limit=1)
        if record:
            return record

        # 3. Create fallback in-memory mock record
        try:
            return self._create_mock_record(doc_type, company)
        except Exception as err:
            _logger.warning("Could not generate mock record for %s: %s", doc_type, err)
        return None

    # pylint: disable=protected-access,broad-exception-caught
    def _render_layout_preview(self, wizard, layout_items, styles, preview_css):
        """Attempt rendering template preview for given layout items."""
        for doc_type, layout in layout_items:
            if not layout:
                continue
            template = wizard._get_template_for_layout(doc_type, layout)
            if not template:
                continue
            try:
                record = wizard._get_sample_record(doc_type, layout)
                if record:
                    render_info = wizard._get_render_information(styles)
                    render_info.update({
                        'preview_css': preview_css,
                        'doc': record,
                        'o': record,
                        'docs': record,
                        'lang': (
                            record.partner_id.lang
                            if hasattr(record, 'partner_id') and record.partner_id
                            else (wizard.env.user.lang or 'en_US')
                        ),
                    })
                    wizard.preview = self.env['ir.ui.view']._render_template(
                        template, render_info
                    )
                    return True
            except Exception as err:
                _logger.warning(
                    "Failed preview render for %s (%s): %s",
                    doc_type, template, err
                )
        return False

    # pylint: disable=protected-access,broad-exception-caught
    @api.depends(
        'sale_document_layout_id', 'stock_document_layout_id',
        'account_document_layout_id', 'purchase_document_layout_id',
    )
    def _compute_preview(self):
        """Compute a qweb based preview to display on the wizard."""
        res = super()._compute_preview()
        styles = self._get_asset_style()
        active_doc = {
            'sale.order': 'sale',
            'purchase.order': 'purchase',
            'account.move': 'account',
            'stock.picking': 'stock',
        }.get(self.env.context.get('active_model'))
        for wizard in self:
            if not wizard.report_layout_id:
                continue
            items = [
                ('sale', wizard.sale_document_layout_id),
                ('purchase', wizard.purchase_document_layout_id),
                ('account', wizard.account_document_layout_id),
                ('stock', wizard.stock_document_layout_id),
            ]
            if active_doc:
                items.sort(key=lambda it: 0 if it[0] == active_doc else 1)
            preview_css = wizard._get_css_for_preview(styles, wizard.id)
            self._render_layout_preview(wizard, items, styles, preview_css)
        return res
