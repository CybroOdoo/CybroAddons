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
import json
import logging
import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from odoo.addons.eagle_doc_connector.models.eagle_api import EagleDocAPI

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    """Adds Eagle Doc document upload, status tracking, and feedback actions to invoices."""

    _inherit = 'account.move'

    eagle_doc_task_id = fields.Char(string="Eagle Doc Task ID", copy=False)
    eagle_doc_sub_business_id = fields.Char(string="Eagle Doc Sub-Business ID", copy=False)
    eagle_doc_document_id = fields.Char(string="Eagle Doc Document ID", copy=False)
    eagle_doc_status = fields.Selection([
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ], string="Eagle Doc Status", copy=False)
    eagle_doc_raw_extraction = fields.Text(
        string="Eagle Doc Raw Extraction",
        copy=False,
        help="The last raw extraction JSON returned by Eagle Doc for this "
             "document. Used to pre-fill the vendor/product correction "
             "feedback forms with the original extracted values.",
    )
    is_eagle_doc_total_mismatch = fields.Boolean(
        string="Eagle Doc Total Mismatch",
        copy=False,
        help="True if Eagle Doc's extracted document total did not match "
             "Odoo's computed total (amount_total) within tolerance, the "
             "last time extraction was applied. Cleared automatically the "
             "next time the totals reconcile.",
    )
    eagle_doc_total_mismatch_message = fields.Char(
        string="Eagle Doc Total Mismatch Message",
        copy=False,
    )

    @api.model
    def action_scan_via_eagle_doc(self, filename, file_data, move_type='in_invoice'):
        """Scan a document by creating an invoice/bill, attaching the file, and uploading to Eagle Doc."""
        if not self.env.user.has_group('account.group_account_user'):
            raise AccessError(_("Only accountants can upload documents to Eagle Doc."))
        api_key = self.env['ir.config_parameter'].sudo().get_param('eagle_doc.api_key')
        if not api_key:
            raise UserError(_("Please configure the Eagle Doc API Key in Settings first."))
        allowed_extensions = ('.pdf', '.png', '.jpg', '.jpeg')
        if not filename or not filename.lower().endswith(allowed_extensions):
            raise UserError(_("Unsupported file type. Please upload a PDF, PNG, or JPG/JPEG file."))
        move = self.create({
            'move_type': move_type,
        })
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': file_data,
            'res_model': 'account.move',
            'res_id': move.id,
        })
        try:
            api_client = EagleDocAPI(self.env)
            sub_business_id = api_client.get_or_create_default_sub_business()
            doc_type = "OUTGOING_INVOICE" if move_type in ('out_invoice', 'out_refund') else "INCOMING_INVOICE"
            response = api_client.upload_invoice(
                sub_business_id=sub_business_id, attachment=attachment, doc_type=doc_type
            )
            task_id = response.get('taskId')
            status = response.get('status', 'PROCESSING')
            move.write({
                'eagle_doc_task_id': task_id,
                'eagle_doc_sub_business_id': sub_business_id,
                'eagle_doc_status': 'processing',
            })
            move.message_post(body=_(
                "Uploaded to Eagle Doc. Task ID: %s, Status: %s"
            ) % (task_id, status))
            max_retries = 10
            delay = 1.5
            for retry_index in range(max_retries):
                time.sleep(delay)
                try:
                    status_response = api_client.get_invoice_status(sub_business_id, task_id)
                    status = status_response.get('status')
                    if status == 'PROCESSED':
                        document_id = status_response.get('documentId')
                        move.write({
                            'eagle_doc_document_id': document_id,
                            'eagle_doc_status': 'processed',
                        })
                        document_data = api_client.get_processed_document(sub_business_id, document_id)
                        move._apply_eagle_doc_extraction(document_data, original_attachment=attachment)
                        move.message_post(body=_(
                            "Eagle Doc processing complete. Document ID: %s"
                        ) % document_id)
                        break
                    elif status == 'FAILED':
                        move.write({'eagle_doc_status': 'failed'})
                        move.message_post(body=_(
                            "Eagle Doc processing failed for task %s."
                        ) % task_id)
                        break
                except Exception as poll_exception:
                    _logger.warning("Eagle Doc polling retry %s failed: %s", retry_index, str(poll_exception))
        except Exception as error:
            move.message_post(body=_("Failed to upload to Eagle Doc: %s") % str(error))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'views': [[False, "form"]],
            'res_id': move.id,
            'target': 'current',
        }

    def action_post(self):
        """Validate Eagle Doc total mismatch before posting the invoice."""
        for move in self:
            if move.eagle_doc_document_id and move.eagle_doc_raw_extraction:
                try:
                    document_data = json.loads(move.eagle_doc_raw_extraction)
                    general = document_data.get('general') or {}
                    total_node = general.get('TotalPrice')
                    total_raw = (
                        total_node.get('value')
                        if isinstance(total_node, dict) else total_node
                    )
                    move._eagle_doc_check_total_mismatch(total_raw)
                except Exception as error:
                    _logger.warning(
                        "Eagle Doc: could not re-check total mismatch for "
                        "move %s before posting: %s", move.id, str(error),
                    )
        return super().action_post()

    def action_eagle_doc_submit_vendor_feedback(self, new_vendor_name, new_vendor_account,
                                                 new_vendor_city=None, new_vendor_street=None):
        """Submit vendor matching correction feedback to Eagle Doc."""
        self.ensure_one()
        if not self.eagle_doc_sub_business_id:
            raise UserError(_("This document has no linked Eagle Doc sub-business."))
        general = self._eagle_doc_raw_general()
        old_vendor_name = self._eagle_doc_raw_value(general, 'CustomerName')
        old_vendor_account = (
            self._eagle_doc_raw_value(general, 'BK_CustomerAccountNumber')
            or self._eagle_doc_raw_value(general, 'BK_ShopAccountNumber')
        )
        old_vendor_city = self._eagle_doc_raw_value(general, 'CustomerCity')
        old_vendor_street = self._eagle_doc_raw_value(general, 'CustomerStreet')
        payload = {
            "newVendorName": new_vendor_name,
            "newVendorAccount": new_vendor_account,
        }
        if new_vendor_city:
            payload["newVendorCity"] = new_vendor_city
        if new_vendor_street:
            payload["newVendorStreet"] = new_vendor_street
        if old_vendor_name:
            payload["oldVendorName"] = old_vendor_name
        if old_vendor_account:
            payload["oldVendorAccount"] = old_vendor_account
        if old_vendor_city:
            payload["oldVendorCity"] = old_vendor_city
        if old_vendor_street:
            payload["oldVendorStreet"] = old_vendor_street
        api_client = EagleDocAPI(self.env)
        feedback_result = api_client.submit_vendor_feedback(self.eagle_doc_sub_business_id, payload)
        self.message_post(body=_(
            "Eagle Doc: vendor feedback submitted (%s) — vendor account: %s"
        ) % (feedback_result.get('outcome'), feedback_result.get('accountNumber')))
        return feedback_result

    def action_eagle_doc_submit_product_feedback(self, new_vendor_name, new_bk_account_number,
                                                  new_product_name=None, new_tax_code=None,
                                                  product_name=None):
        """Submit product bookkeeping account and tax feedback to Eagle Doc."""
        self.ensure_one()
        if not self.eagle_doc_sub_business_id:
            raise UserError(_("This document has no linked Eagle Doc sub-business."))
        general = self._eagle_doc_raw_general()
        old_vendor_name = self._eagle_doc_raw_value(general, 'CustomerName')
        old_bk_account = ''
        old_tax_code = ''
        old_product_name = product_name or ''
        if not old_product_name and self.eagle_doc_raw_extraction:
            try:
                document_data = json.loads(self.eagle_doc_raw_extraction)
            except (ValueError, TypeError):
                document_data = {}
            product_items = document_data.get('productItems') or []
            if product_items:
                first_item = product_items[0]
                old_product_name = self._eagle_doc_raw_value(first_item, 'ProductName')
                old_bk_account = self._eagle_doc_raw_value(first_item, 'BK_Account')
                old_tax_code = self._eagle_doc_raw_value(first_item, 'BK_TaxKey')
        if not old_bk_account:
            old_bk_account = self._eagle_doc_raw_value(general, 'BK_Account')
        if not old_tax_code:
            old_tax_code = self._eagle_doc_raw_value(general, 'BK_TaxKey')
        payload = {
            "vendorName": old_vendor_name,
            "productName": old_product_name,
            "bkAccountNumber": old_bk_account,
            "taxCode": old_tax_code,
            "newVendorName": new_vendor_name,
            "newProductName": new_product_name or old_product_name,
            "newBKAccountNumber": new_bk_account_number,
            "newTaxCode": new_tax_code or old_tax_code,
            "docType": "OUTGOING_INVOICE" if self._eagle_doc_is_sale_move() else "INCOMING_INVOICE",
        }
        api_client = EagleDocAPI(self.env)
        feedback_result = api_client.submit_product_feedback(self.eagle_doc_sub_business_id, payload)
        self.message_post(body=_(
            "Eagle Doc: product/account feedback submitted (%s) — account: %s, tax code: %s"
        ) % (feedback_result.get('outcome'), feedback_result.get('accountNumber'), feedback_result.get('taxCode')))
        return feedback_result

    def _apply_eagle_doc_extraction(self, document_data, original_attachment=None):
        """Apply Eagle Doc extraction results to the invoice."""
        self.ensure_one()
        general = document_data.get('general') or {}
        self.eagle_doc_raw_extraction = json.dumps(document_data)

        def gval(*keys):
            """Extract the first truthy value from general for any of the given keys."""
            for key in keys:
                node = general.get(key)
                if isinstance(node, dict):
                    val = node.get('value')
                    if val not in (None, '', []):
                        return val
                elif node not in (None, '', []):
                    return node
            return None

        partner_name = gval('CustomerName')
        invoice_number = gval('InvoiceNumber', 'InvoiceNo', 'BillNumber')
        order_number = gval('OrderNumber', 'SalesOrderNumber', 'PurchaseOrderNumber', 'PONumber')
        invoice_date = gval('InvoiceDate', 'BillDate', 'DocumentDate')
        due_date = gval('InvoiceDueDate', 'DueDate', 'PaymentDueDate')
        currency_code = gval('Currency', 'CurrencyCode')
        vals = {}
        if partner_name:
            partner_vals = {
                'vat': gval('CustomerVAT', 'VATNumber', 'TaxNumber'),
                'street': gval('CustomerStreet'),
                'city': gval('CustomerCity'),
                'zip': gval('CustomerZip'),
                'state_name': gval('CustomerState'),
                'country_code_or_name': gval('CustomerCountry'),
            }
            partner = self._eagle_doc_find_or_create_partner(partner_name, partner_vals)
            if partner and partner != self.partner_id:
                vals['partner_id'] = partner.id
        if self._eagle_doc_is_sale_move():
            if order_number:
                vals['ref'] = str(order_number).strip()
        elif invoice_number:
            vals['ref'] = str(invoice_number).strip()
        if order_number:
            vals['invoice_origin'] = str(order_number).strip()
        if invoice_date:
            try:
                vals['invoice_date'] = self._eagle_doc_parse_date(invoice_date)
            except Exception:
                _logger.warning("Eagle Doc: could not parse invoice_date '%s'", invoice_date)
        if due_date:
            try:
                vals['invoice_date_due'] = self._eagle_doc_parse_date(due_date)
            except Exception:
                _logger.warning("Eagle Doc: could not parse due_date '%s'", due_date)
        if currency_code:
            currency = self.env['res.currency'].search(
                [('name', '=', str(currency_code).strip().upper())], limit=1
            )
            if currency:
                vals['currency_id'] = currency.id
            else:
                _logger.warning(
                    "Eagle Doc: currency '%s' not found in Odoo — left unchanged.", currency_code
                )
                self.message_post(body=_(
                    "Eagle Doc returned currency '%s' which was not found in Odoo. "
                    "Currency left unchanged."
                ) % currency_code)
        if vals:
            self.write(vals)
        line_items = document_data.get('productItems') or document_data.get('lineItems') or []
        top_level_taxes = document_data.get('taxes') or []
        data_issues = ((document_data.get('bookkeeping') or {}).get('dataIssues')) or []
        if line_items and self.state == 'draft':
            self._eagle_doc_apply_lines(
                line_items, top_level_taxes=top_level_taxes, data_issues=data_issues,
            )
            self._eagle_doc_check_total_mismatch(gval('TotalPrice'))
        if original_attachment and original_attachment.res_id != self.id:
            try:
                original_attachment.write({
                    'res_model': 'account.move',
                    'res_id': self.id,
                })
            except Exception as error:
                _logger.warning("Eagle Doc: could not re-link attachment: %s", str(error))

        bookkeeping_entries = (document_data.get('bookkeeping') or {}).get('entries') or []
        if bookkeeping_entries:
            lines = []
            for entry in bookkeeping_entries:
                lines.append(_(
                    "Account: %s | Counter: %s | Tax: %s | Amount: %s"
                ) % (
                    entry.get('accountNumber', '-'),
                    entry.get('counterAccountNumber', '-'),
                    entry.get('taxCode', '-'),
                    entry.get('amount', '-'),
                ))
            self.message_post(
                body=_("Eagle Doc suggested bookkeeping entries:\n%s") % "\n".join(lines)
            )

        applied = []
        if vals.get('partner_id'):
            applied.append(_("Customer") if self._eagle_doc_is_sale_move() else _("Vendor"))
        if vals.get('ref'):
            applied.append(_("Customer Reference") if self._eagle_doc_is_sale_move() else _("Vendor Reference"))
        if vals.get('invoice_origin'):
            applied.append(_("Source Document"))
        if vals.get('invoice_date'):
            applied.append(_("Invoice Date"))
        if vals.get('invoice_date_due'):
            applied.append(_("Due Date"))
        if vals.get('currency_id'):
            applied.append(_("Currency"))
        if line_items:
            applied.append(_("%d line(s)") % len(line_items))

        if applied:
            self.message_post(body=_(
                "Eagle Doc auto-filled: %s."
            ) % ", ".join(applied))

    def _eagle_doc_find_or_create_partner(self, partner_name, partner_vals=None):
        """Find or create a partner based on name and VAT."""
        partner_name = (partner_name or '').strip()
        if not partner_name:
            return False

        partner_vals = partner_vals or {}
        vat = (partner_vals.get('vat') or '').strip()
        vat_clean = self._eagle_doc_clean_vat(vat) if vat else ''

        is_sale = self._eagle_doc_is_sale_move()
        rank_field = 'customer_rank' if is_sale else 'supplier_rank'
        label = _('Customer') if is_sale else _('Vendor')

        partner = False

        if vat_clean:
            all_vat_candidates = self.env['res.partner'].search([('vat', '!=', False)])
            matches = all_vat_candidates.filtered(
                lambda partner_candidate: self._eagle_doc_clean_vat(partner_candidate.vat) == vat_clean
            )
            if matches:
                ranked = matches.filtered(lambda partner_candidate: partner_candidate[rank_field] > 0)
                partner = ranked[:1] or matches[:1]

        if not partner:
            partner = self.env['res.partner'].search([
                ('name', '=ilike', partner_name),
                (rank_field, '>', 0),
            ], limit=1)
        if not partner:
            partner = self.env['res.partner'].search([
                ('name', '=ilike', partner_name),
            ], limit=1)

        if not partner and not self.company_id.is_eagle_doc_auto_create_partner:
            _logger.info(
                "Eagle Doc: %s '%s' not found in Odoo and auto-create is disabled "
                "for company '%s' — left unset.",
                label, partner_name, self.company_id.name,
            )
            self.message_post(body=_(
                "Eagle Doc: %s '%s' was not found in Odoo. Auto-creation of "
                "customers/vendors is disabled for this company — please "
                "select or create the correct one manually."
            ) % (label, partner_name))
            return False

        if not partner:
            create_vals = {
                'name': partner_name,
                rank_field: 1,
                'company_type': 'company',
            }
            if vat:
                create_vals['vat'] = vat
            if partner_vals.get('street'):
                create_vals['street'] = partner_vals['street']
            if partner_vals.get('city'):
                create_vals['city'] = partner_vals['city']
            if partner_vals.get('zip'):
                create_vals['zip'] = partner_vals['zip']

            country_raw = (partner_vals.get('country_code_or_name') or '').strip()
            country = False
            if country_raw:
                country = self.env['res.country'].search([
                    '|', ('code', '=ilike', country_raw), ('name', '=ilike', country_raw),
                ], limit=1)
                if country:
                    create_vals['country_id'] = country.id
                else:
                    _logger.warning(
                        "Eagle Doc: country '%s' not recognised — left unset on new %s '%s'.",
                        country_raw, label, partner_name,
                    )

            state_raw = (partner_vals.get('state_name') or '').strip()
            if state_raw:
                state_domain = [('name', '=ilike', state_raw)]
                if country:
                    state_domain.append(('country_id', '=', country.id))
                state = self.env['res.country.state'].search(state_domain, limit=1)
                if state:
                    create_vals['state_id'] = state.id

            partner = self.env['res.partner'].create(create_vals)
            _logger.info(
                "Eagle Doc: created new %s contact '%s' (id=%s, vat=%s)",
                label, partner_name, partner.id, vat or '-',
            )
            self.message_post(body=_(
                "Eagle Doc: %s '%s' was not found in Odoo and has been created automatically."
            ) % (label, partner_name))

        return partner

    def _eagle_doc_apply_lines(self, line_items, top_level_taxes=None, data_issues=None):
        """Create invoice lines from Eagle Doc extracted items and taxes."""
        self.ensure_one()
        if not line_items:
            return

        tax_use = 'sale' if self._eagle_doc_is_sale_move() else 'purchase'

        brackets = []
        for tax_entry in (top_level_taxes or []):
            bracket_rate = self._eagle_doc_parse_tax_rate(
                self._eagle_doc_unwrap(tax_entry.get('TaxPercentage'))
            )
            bracket_net = self._eagle_doc_safe_float(
                self._eagle_doc_unwrap(tax_entry.get('TaxNetAmount')), default=None,
            )
            if bracket_rate is not None and bracket_net is not None:
                brackets.append((bracket_net, bracket_rate))


        def item_val(line_item, *keys):
            """Return the first unwrapped, truthy value found in *line_item* for any key."""
            for key in keys:
                val = self._eagle_doc_unwrap(line_item.get(key))
                if val not in (None, '', [], {}):
                    return val
            return None

        def find_bracket_rate(net_amount, tolerance=0.02):
            """Return the TaxPercentage of the bracket whose TaxNetAmount is
            within *tolerance* of *net_amount*, or None if no bracket matches.
            """
            if net_amount is None:
                return None
            for bracket_net, bracket_rate in brackets:
                if abs(bracket_net - net_amount) <= tolerance:
                    return bracket_rate
            return None

        line_commands = [(5, 0, 0)]
        unmatched_products = []
        trusted_lines = []
        auto_resolved_lines = []
        review_lines = []

        for line_item in line_items:
            description = (
                item_val(line_item, 'ProductName', 'description', 'name',
                         'itemDescription', 'product_name')
                or _('Imported line')
            )
            description = str(description).strip() or _('Imported line')

            quantity = self._eagle_doc_safe_float(
                item_val(line_item, 'ProductQuantity', 'quantity', 'qty', 'Quantity'),
                default=1.0,
            )

            unit_price = self._eagle_doc_safe_float(
                item_val(line_item, 'ProductUnitPrice', 'unitPrice', 'price',
                         'UnitPrice', 'unit_price'),
                default=0.0,
            )
            line_net_total = self._eagle_doc_safe_float(
                item_val(line_item, 'TaxNetAmount', 'netAmount', 'net_amount'),
                default=unit_price * quantity
            )
            raw_rate = self._eagle_doc_parse_tax_rate(item_val(line_item, 'TaxPercentage'))
            line_tax = False
            if raw_rate is not None:
                line_tax = self._eagle_doc_find_tax(raw_rate)
                if line_tax:
                    trusted_lines.append((description, raw_rate))
            elif len(brackets) == 1:
                bracket_rate = brackets[0][1]
                line_tax = self._eagle_doc_find_tax(bracket_rate)
                if line_tax:
                    auto_resolved_lines.append((description, raw_rate, bracket_rate))
                else:
                    review_lines.append(description)
            else:
                bracket_rate = find_bracket_rate(line_net_total)
                if bracket_rate is not None:
                    line_tax = self._eagle_doc_find_tax(bracket_rate)
                    if line_tax:
                        auto_resolved_lines.append((description, raw_rate, bracket_rate))
                if not line_tax:
                    review_lines.append(description)

            product_code = item_val(line_item, 'ProductId', 'productId', 'sku', 'SKU', 'default_code')
            product = self._eagle_doc_find_or_create_product(
                description,
                product_code=product_code,
                unit_price=unit_price,
            )
            if not product:
                unmatched_products.append(description)

            discount = item_val(line_item, 'DiscountPerc', 'discountPerc')

            line_vals = {
                'name': description,
                'quantity': quantity,
                'price_unit': unit_price,
                'discount' : discount,
                'tax_ids': [(6, 0, [line_tax.id])] if line_tax else [(5, 0, 0)],
            }
            if product:
                line_vals['product_id'] = product.id

            line_commands.append((0, 0, line_vals))

        if len(line_commands) > 1:
            self.invoice_line_ids = line_commands

        if unmatched_products and not self.company_id.is_eagle_doc_auto_create_product:
            self.message_post(body=_(
                "Eagle Doc: %d line(s) had no matching product in Odoo and "
                "were kept as free text (auto-creation of products is "
                "disabled for this company): %s"
            ) % (len(unmatched_products), ", ".join(unmatched_products)))

        message_parts = []
        if auto_resolved_lines:
            details = ", ".join(
                _("%s (%s%% -> %s%%)") % (
                    name, ("%g" % old_rate if old_rate is not None else "?"), "%g" % new_rate
                )
                for name, old_rate, new_rate in auto_resolved_lines
            )
            message_parts.append(_(
                "%d line(s) had an unreliable per-line tax extraction "
                "(flagged by Eagle Doc) and were auto-resolved by matching "
                "against the document's tax brackets - please verify: %s"
            ) % (len(auto_resolved_lines), details))
        if review_lines:
            message_parts.append(_(
                "%d line(s) could not be matched to any tax bracket and "
                "were left with no tax - please assign manually before "
                "confirming: %s"
            ) % (len(review_lines), ", ".join(review_lines)))
        if message_parts:
            self.message_post(body="\n".join(message_parts))

    def _eagle_doc_check_total_mismatch(self, total_price_raw):
        """Compare extracted total with Odoo total and flag any mismatch."""
        self.ensure_one()
        total_price = self._eagle_doc_safe_float(total_price_raw, default=None)

        vals = {
            'is_eagle_doc_total_mismatch': False,
            'eagle_doc_total_mismatch_message': False,
        }
        if total_price is not None:
            self.invalidate_recordset(['amount_total'])
            odoo_total = self.amount_total
            tolerance = max(self.currency_id.rounding * 2, 0.02)
            if abs(total_price - odoo_total) > tolerance:
                message = _(
                    "Eagle Doc extracted a total of %.2f %s, but Odoo's "
                    "computed total is %.2f %s. There is a mismatch between "
                    "the source document and this invoice — please review "
                    "the lines, taxes, and discounts manually before "
                    "confirming."
                ) % (total_price, self.currency_id.name, odoo_total, self.currency_id.name)
                vals['is_eagle_doc_total_mismatch'] = True
                vals['eagle_doc_total_mismatch_message'] = message
                self.message_post(body=message)

        self.write(vals)

    def _eagle_doc_find_or_create_product(self, product_name, product_code=None, unit_price=0.0):
        """Find or create a product based on name or code."""
        product_name = (product_name or '').strip()
        if not product_name:
            return False

        product_code = (product_code or '').strip()
        product = False

        if product_code:
            product = self.env['product.product'].search([
                ('default_code', '=', product_code),
            ], limit=1)

        if not product:
            product = self.env['product.product'].search([
                ('name', '=ilike', product_name),
            ], limit=1)

        if product:
            return product

        if not self.company_id.is_eagle_doc_auto_create_product:
            return False

        category = self._eagle_doc_get_auto_product_category()
        create_vals = {
            'name': product_name,
            'type': 'consu',
            'categ_id': category.id,
            'list_price': unit_price or 0.0,
            'standard_price': unit_price or 0.0,
        }
        if product_code:
            create_vals['default_code'] = product_code

        product = self.env['product.product'].create(create_vals)
        _logger.info(
            "Eagle Doc: created new product '%s' (id=%s, code=%s)",
            product_name, product.id, product_code or '-',
        )
        self.message_post(body=_(
            "Eagle Doc: product '%s' was not found in Odoo and has been "
            "created automatically (category: %s) — please verify price "
            "and accounting details."
        ) % (product_name, category.name))
        return product

    def _eagle_doc_get_auto_product_category(self):
        """Get or create the default category for auto-created products."""
        category = self.env['product.category'].search([
            ('name', '=', 'Eagle Doc Auto-Created'),
        ], limit=1)
        if not category:
            category = self.env['product.category'].create({
                'name': 'Eagle Doc Auto-Created',
            })
        return category

    def _eagle_doc_parse_tax_rate(self, raw):
        """Parse a raw tax rate value into a float percentage."""
        if raw is None:
            return None
        try:
            clean_rate_str = str(raw).replace('%', '').replace(',', '.').strip()
            rate = float(clean_rate_str)
            if 0 < rate < 1:
                rate = round(rate * 100, 4)
            return rate
        except Exception:
            _logger.warning("Eagle Doc: could not parse tax rate '%s'", raw)
            return None

    def _eagle_doc_is_sale_move(self):
        """Check if the move is a sales invoice or refund."""
        self.ensure_one()
        return self.move_type in ('out_invoice', 'out_refund')

    def _eagle_doc_find_tax(self, rate):
        """Find an existing tax record matching the given rate and type."""
        if rate is None:
            return False

        tax_use = 'sale' if self._eagle_doc_is_sale_move() else 'purchase'

        tax = self.env['account.tax'].search([
            ('amount', '=', rate),
            ('amount_type', '=', 'percent'),
            ('type_tax_use', '=', tax_use),
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
        ], limit=1)

        if not tax:
            tax = self.env['account.tax'].with_context(active_test=False).search([
                ('amount', '=', rate),
                ('amount_type', '=', 'percent'),
                ('type_tax_use', '=', tax_use),
                ('company_id', '=', self.company_id.id),
            ], limit=1)

        if not tax and self.company_id.is_eagle_doc_auto_create_tax:
            tax = self._eagle_doc_create_tax(rate, tax_use)

        if not tax:
            _logger.warning(
                "Eagle Doc: no %s tax found for %g%% in company '%s' (id=%s). "
                "Please create it in Accounting -> Configuration -> Taxes.",
                tax_use, rate, self.company_id.name, self.company_id.id,
            )
            self.message_post(body=_(
                "Eagle Doc: extracted a %g%% %s tax, but no matching tax "
                "exists in Odoo for this company and auto-creation is "
                "disabled or not configured. Tax was left blank on the "
                "affected line(s) — please review before confirming."
            ) % (rate, tax_use))

        return tax or False

    def _eagle_doc_create_tax(self, rate, tax_use):
        """Create a new tax record using company placeholder accounts."""
        account = (
            self.company_id.eagle_doc_auto_tax_account_sale_id
            if tax_use == 'sale'
            else self.company_id.eagle_doc_auto_tax_account_purchase_id
        )
        if not account:
            self.message_post(body=_(
                "Eagle Doc: would auto-create a %g%% %s tax, but no "
                "placeholder tax account is configured in Settings > "
                "Eagle Doc Connector for this direction. Please configure "
                "one, or create the tax manually."
            ) % (rate, tax_use))
            return False

        tax_group = self._eagle_doc_get_or_create_tax_group(rate)

        tax = self.env['account.tax'].create({
            'name': _("%g%% (%s) [Eagle Doc]") % (rate, tax_use),
            'amount': rate,
            'amount_type': 'percent',
            'type_tax_use': tax_use,
            'company_id': self.company_id.id,
            'tax_group_id': tax_group.id,
            'invoice_repartition_line_ids': [
                (0, 0, {'repartition_type': 'base'}),
                (0, 0, {'repartition_type': 'tax', 'account_id': account.id}),
            ],
            'refund_repartition_line_ids': [
                (0, 0, {'repartition_type': 'base'}),
                (0, 0, {'repartition_type': 'tax', 'account_id': account.id}),
            ],
        })
        _logger.info(
            "Eagle Doc: auto-created %s tax '%s' (id=%s) for company '%s'",
            tax_use, tax.name, tax.id, self.company_id.name,
        )
        self.message_post(body=_(
            "Eagle Doc: auto-created a %g%% %s tax ('%s') using the "
            "configured placeholder account — please verify the GL "
            "account mapping before relying on this for reporting."
        ) % (rate, tax_use, tax.name))
        return tax

    def _eagle_doc_get_or_create_tax_group(self, rate):
        """Get or create a tax group for the given rate."""
        group_name = _("%g%%") % rate
        group = self.env['account.tax.group'].search([
            ('name', '=', group_name),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        if not group:
            group = self.env['account.tax.group'].create({
                'name': group_name,
                'company_id': self.company_id.id,
            })
            _logger.info(
                "Eagle Doc: auto-created tax group '%s' (id=%s) for company '%s'",
                group_name, group.id, self.company_id.name,
            )
        return group

    @staticmethod
    def _eagle_doc_clean_vat(vat):
        """Normalize a VAT number for comparison."""
        if not vat:
            return ''
        return (
            str(vat).upper()
            .replace(' ', '')
            .replace('-', '')
            .replace('.', '')
            .strip()
        )

    @staticmethod
    def _eagle_doc_unwrap(field_val):
        """Unwrap a value from Eagle Doc's dict structure if needed."""
        if isinstance(field_val, dict):
            return field_val.get('value')
        return field_val

    @staticmethod
    def _eagle_doc_safe_float(val, default=0.0):
        """Safely convert a string value to float."""
        if val is None:
            return default
        try:
            cleaned = (
                str(val)
                .replace(',', '.')
                .replace('\xa0', '')
                .strip()
            )
            for symbol in ('€', '$', '£', '¥', '₹', 'EUR', 'USD', 'GBP'):
                cleaned = cleaned.replace(symbol, '')
            cleaned = cleaned.strip()
            return float(cleaned) if cleaned else default
        except Exception:
            return default

    @staticmethod
    def _eagle_doc_parse_date(raw):
        """Parse a date string in common formats to 'YYYY-MM-DD'.

        Handles ISO (2024-01-15), European (15.01.2024 / 15/01/2024),
        and US (01/15/2024) notations.  Raises ValueError on failure so
        the caller can log and skip gracefully.
        """
        from datetime import datetime

        raw = str(raw).strip()
        if not raw:
            raise ValueError("Empty date string")

        if ',' in raw:
            raw = raw.split(',', 1)[1].strip()

        formats = [
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
            '%Y%m%d',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt).date().isoformat()
            except ValueError:
                continue
        raise ValueError(f"Unrecognised date format: {raw!r}")

    def _eagle_doc_raw_general(self):
        """Get the 'general' block from raw extraction."""
        if not self.eagle_doc_raw_extraction:
            return {}
        try:
            document_data = json.loads(self.eagle_doc_raw_extraction)
        except (ValueError, TypeError):
            return {}
        return document_data.get('general') or {}

    @staticmethod
    def _eagle_doc_raw_value(general, key):
        """Extract the plain value from a raw extraction field."""
        node = general.get(key)
        if isinstance(node, dict):
            return node.get('value') or ''
        return node or ''


    @api.model
    def _cron_process_eagle_doc_uploads(self):
        """Cron job to poll status of pending Eagle Doc uploads in batch."""
        pending_moves = self.search([
            ('eagle_doc_status', '=', 'processing'),
            ('eagle_doc_task_id', '!=', False),
            ('eagle_doc_sub_business_id', '!=', False),
        ])
        if not pending_moves:
            return

        api_client = EagleDocAPI(self.env)

        moves_by_sub_business = {}
        for move in pending_moves:
            moves_by_sub_business.setdefault(move.eagle_doc_sub_business_id, []).append(move)

        BATCH_SIZE = 200

        for sub_business_id, moves in moves_by_sub_business.items():
            move_by_task_id = {m.eagle_doc_task_id: m for m in moves}
            task_ids = list(move_by_task_id.keys())

            for i in range(0, len(task_ids), BATCH_SIZE):
                chunk = task_ids[i:i + BATCH_SIZE]
                try:
                    batch_response = api_client.get_invoice_statuses_batch(sub_business_id, chunk)
                except Exception as error:
                    _logger.error(
                        "Eagle Doc cron: batch status call failed for sub-business %s (%s tasks): %s",
                        sub_business_id, len(chunk), str(error)
                    )
                    self.env.cr.rollback()
                    continue

                if batch_response.get('notFound'):
                    _logger.warning(
                        "Eagle Doc cron: %s task id(s) not found/owned for sub-business %s: %s",
                        len(batch_response['notFound']), sub_business_id, batch_response['notFound']
                    )

                for status_response in batch_response.get('results', []):
                    task_id = status_response.get('taskId')
                    move = move_by_task_id.get(task_id)
                    if not move:
                        continue

                    try:
                        status = status_response.get('status')

                        if status == 'PROCESSED':
                            document_id = status_response.get('documentId')
                            move.write({
                                'eagle_doc_document_id': document_id,
                                'eagle_doc_status': 'processed',
                            })
                            document_data = api_client.get_processed_document(
                                sub_business_id, document_id
                            )
                            move._apply_eagle_doc_extraction(document_data)
                            move.message_post(body=_(
                                "Eagle Doc processing complete. Document ID: %s"
                            ) % document_id)

                        elif status == 'FAILED':
                            move.eagle_doc_status = 'failed'
                            move.message_post(body=_(
                                "Eagle Doc processing failed for task %s."
                            ) % task_id)

                        self.env.cr.commit()

                    except Exception as error:
                        _logger.error(
                            "Eagle Doc cron: error applying result for move %s (task %s): %s",
                            move.id, task_id, str(error)
                        )
                        self.env.cr.rollback()
