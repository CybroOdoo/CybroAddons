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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import json
import os
import tempfile
import datetime
import requests

from odoo import _, api, models, fields
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup


class ImportViaOcr(models.TransientModel):
    """
    Wizard: Upload a PDF/image → call fynix.ai OCR API → preview response →
    create a draft record (Invoice, Vendor Bill, Purchase Order, Sale Order)
    with all fields pre-filled.
    """
    _name = 'import.via.ocr'
    _description = 'Import Document via OCR AI'

    file_upload = fields.Binary(
        string='Upload File',
        help='PDF, PNG, JPG, or JPEG document to send to the OCR AI '
             'service. Maximum file size is 2 MB.',
    )
    file_upload_name = fields.Char(
        string='File Name',
        help='Original name of the uploaded file, used to detect its '
             'format and to label the attachment stored on the created record.',
    )
    ocr_response_received = fields.Boolean(
        help='Set to True once a response has been received from the OCR '
             'AI service for the uploaded file.',
    )
    response_text = fields.Text(
        string='AI Response (JSON)',
        help='Raw JSON data extracted from the document by the OCR AI '
             'service. Used to populate the fields of the record created '
             'by this wizard.',
    )
    file_previews = fields.Html(
        string='File Preview',
        help='HTML preview of the uploaded document, if generated.',
    )
    status = fields.Boolean(
        string='API Status',
        help='Indicates whether the OCR AI service processed the request '
             'successfully.',
    )

    used_token = fields.Integer(
        string='Tokens Used (This Request)',
        readonly=True,
        help='Number of OCR AI tokens consumed by processing this document.',
    )
    total_purchase_token = fields.Integer(
        string='Total Purchased Tokens',
        readonly=True,
        help='Total number of tokens purchased on your fynix.ai account.',
    )
    total_used_token = fields.Integer(
        string='Total Used Tokens',
        readonly=True,
        help='Total number of tokens consumed so far on your fynix.ai account.',
    )
    total_available_token = fields.Integer(
        string='Total Available Tokens',
        readonly=True,
        help='Number of tokens remaining on your fynix.ai account.',
    )

    ocr_config_id = fields.Many2one(
        comodel_name='odoo.ocr.ai.config',
        string='OCR AI Configuration',
        help='The active OCR AI Configuration used to map extracted data '
             'to fields on the target model.',
    )
    ocr_attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        readonly=True,
        string='Uploaded Attachment',
        help='Attachment record created for the uploaded file, later '
             'linked to the record generated from the OCR data.',
    )
    mime_type = fields.Char(
        compute='_compute_mime_type',
        string='MIME Type',
        help='MIME type of the uploaded file, used to choose the correct '
             'preview widget (PDF viewer or image).',
    )
    move_type = fields.Char(
        help='Technical field carrying the target invoice type '
             '(e.g. in_invoice, out_invoice) when creating an account.move '
             'record from this wizard.',
    )
    @api.constrains('file_upload')
    def _check_file_format(self):
        """Validate the uploaded file format."""
        allowed = ['pdf', 'png', 'jpg', 'jpeg']
        for rec in self:
            if rec.file_upload:
                ext = (rec.file_upload_name or '').rsplit('.', 1)[-1].lower()
                if ext not in allowed:
                    raise ValidationError(
                        _('Only PDF, PNG, JPG, and JPEG files are supported.')
                    )

    @api.onchange('file_upload')
    def _onchange_file_upload(self):
        """Reset the OCR response when a new file is uploaded."""
        if self.file_upload:
            self.response_text = False
            self.ocr_response_received = False

    @api.depends('file_upload', 'file_upload_name')
    def _compute_mime_type(self):
        """Compute the MIME type of the uploaded file."""
        mapping = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
        }
        for rec in self:
            if rec.file_upload and rec.file_upload_name:
                ext = rec.file_upload_name.rsplit('.', 1)[-1].lower()
                rec.mime_type = mapping.get(ext, False)
            else:
                rec.mime_type = False

    def _get_date_format(self):
        """Return the date format for the current company or user."""
        lang = self.env['res.lang'].search([('code', '=', self.env.lang)], limit=1)
        if lang:
            return lang.date_format
        config = self.env['odoo.ocr.api.config'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        return config.date_format if config else '%d-%m-%Y'

    def _get_api_credentials(self):
        """Retrieve the OCR API credentials."""
        config = self.env['odoo.ocr.api.config'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        if not config:
            raise UserError(_(
                'No OCR API configuration found for your company.\n'
                'Go to Settings → OCR AI Integration → API Configuration '
                'and add your fynix.ai token.'
            ))
        return config.server_url, config.api_key

    def _get_base_url(self):
        """
        Use ir.config_parameter to get the Odoo base URL.
        http.request is NOT available inside model/wizard methods.
        """
        return self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', default='http://localhost:8069')

    def _build_entities_structure(self, config_lines):
        """Build the OCR entity structure from field mappings."""
        user_lang = self.env['res.lang'].search(
            [('code', '=', self.env.user.lang)], limit=1)
        simple_type_map = {
            'char': 'string',
            'text': 'string',
            'float': 'float',
            'monetary': 'float',
            'integer': 'integer',
            'date': user_lang.date_format if user_lang else '%d-%m-%Y',
            'datetime': user_lang.date_format if user_lang else '%d-%m-%Y',
            'many2one': 'string',
            'many2many': 'string',
        }
        entities = {}
        for line in config_lines:
            if not line.title or not line.ocr_field_id:
                continue
            ftype = line.ocr_field_id.ttype
            if ftype in ['many2one', 'one2many'] and line.ocr_ir_field_ids:
                nested = {
                    f.name: simple_type_map.get(f.ttype)
                    for f in line.ocr_ir_field_ids
                    if simple_type_map.get(f.ttype)
                }
                entities[line.title] = nested if ftype == 'many2one' else [nested]
            else:
                mapped = simple_type_map.get(ftype)
                if mapped:
                    entities[line.title] = mapped
        return entities

    def action_send_to_ocr(self):
        """Upload the document to the OCR service and process the response."""
        if not self.file_upload:
            raise UserError(_('Please upload a PDF or image file first.'))

        active_model = self.env.context.get('active_model', 'account.move')
        config = self.ocr_config_id or self.env['odoo.ocr.ai.config'].search([
            ('model_id.model', '=', active_model),
            ('active', '=', True),
        ], limit=1)
        if not config:
            raise UserError(_(
                'No active OCR AI configuration found for model "%s".\n'
                'Go to Settings → OCR AI Integration → Model Configuration.'
            ) % active_model)
        self.ocr_config_id = config

        file_bytes = base64.b64decode(self.file_upload)
        if len(file_bytes) / 1024 / 1024 > 2:
            raise UserError(_('File must be 2 MB or smaller.'))

        tmp_path = os.path.join(
            tempfile.gettempdir(), self.file_upload_name or 'ocr_upload')
        with open(tmp_path, 'wb') as fh:
            fh.write(file_bytes)

        # Create attachment without pre-deleting any existing ones
        attachment = self.env['ir.attachment'].sudo().create({
            'name': self.file_upload_name,
            'mimetype': self.mime_type or 'application/pdf',
            'datas': self.file_upload,
            'description': self.file_upload_name,
        })

        server_url, auth_token = self._get_api_credentials()
        entities = self._build_entities_structure(config.model_ids.sorted('sequence'))

        payload = {
            'entities': json.dumps(entities),
            'auth_token': auth_token,
            'client_url': self._get_base_url(),
        }

        try:
            with open(tmp_path, 'rb') as fp:
                response = requests.post(
                    server_url,
                    files={'file': fp},
                    data=payload,
                    timeout=60,
                )
            response.raise_for_status()
            res_json = response.json()
        except requests.exceptions.RequestException as exc:
            try:
                msg = response.json().get('message', str(exc))
            except Exception:
                msg = str(exc)
            raise UserError(_('OCR API request failed: %s') % msg)
        except Exception as exc:
            raise UserError(_('Unexpected error during OCR processing: %s') % str(exc))

        self.ocr_response_received = True
        self.ocr_attachment_id = attachment.id
        self.status = res_json.get('status', False)

        usage = res_json.get('response', {}).get('request_usage', {})
        self.used_token = usage.get('Tokens Used', 0)
        self.total_purchase_token = usage.get('Total Purchase Token', 0)
        self.total_used_token = usage.get('Total Used Token', 0)
        self.total_available_token = usage.get('Total Available Token', 0)

        res_json.pop('status', None)
        res_json.pop('status_code', None)
        res_json.get('response', {}).pop('request_usage', None)
        self.response_text = json.dumps(res_json, indent=4)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Import via OCR'),
            'res_model': 'import.via.ocr',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_ocr_attachment_id': attachment.id,
                'default_move_type': self.env.context.get('default_move_type'),
            },
        }

    def action_create_record(self):
        """
        Parse the OCR JSON, map all fields, and create the record directly
        via ORM. This is the only reliable way to write one2many lines
        (invoice_line_ids, order_line) — Odoo ignores one2many fields
        passed as context 'default_' keys.
        """
        try:
            response_dict = json.loads(self.response_text or '{}')
        except json.JSONDecodeError as exc:
            raise UserError(_('Could not parse OCR response JSON: %s') % str(exc))

        if not response_dict.get('status', True):
            raise UserError(response_dict.get('message', _('OCR API returned an error.')))

        ocr_data = response_dict.get('response', {})
        config = self.env['odoo.ocr.ai.config'].browse(self.ocr_config_id.id)
        if not config:
            raise UserError(_('OCR AI configuration not found.'))

        date_fmt = self._get_date_format()
        model_name = config.model_id.model

        SUPPORTED_TTYPES = [
            'char', 'date', 'datetime', 'integer',
            'monetary', 'many2one', 'one2many', 'float', 'text', 'many2many',
        ]

        vals = {
            'is_created_ocr': True,
            'ocr_attachment_id': self.ocr_attachment_id.id,
            'ocr_response_text': json.dumps(ocr_data),
        }

        if model_name == 'account.move':
            move_type = (
                self.env.context.get('default_move_type')
                or self.move_type
                or 'in_invoice'
            )
            vals['move_type'] = move_type

        if model_name == 'stock.picking' and 'picking_type_id' not in vals:
            ctx = self.env.context

            restricted_pt_id = ctx.get('restricted_picking_type_id')
            if restricted_pt_id:
                vals['picking_type_id'] = restricted_pt_id
            else:
                picking_type_code = (
                    ctx.get('default_picking_type_code')
                    or ctx.get('restricted_picking_type_code')
                    or 'incoming'
                )
                pt = self.env['stock.picking.type'].sudo().search([
                    ('code', '=', picking_type_code),
                    ('company_id', '=', self.env.company.id),
                ], limit=1)
                if pt:
                    vals['picking_type_id'] = pt.id

        for line in config.model_ids:
            if not line.title or line.ocr_field_id.ttype not in SUPPORTED_TTYPES:
                continue

            raw_value = ocr_data.get(line.title, '')
            if isinstance(raw_value, dict) and 'display_name' in raw_value:
                raw_value = raw_value['display_name']

            value = self._map_field_value(line, raw_value, date_fmt, config)

            if value is not False and value is not None:
                vals[line.ocr_field_id.name] = value

        new_record = self.env[model_name].sudo().create(vals)

        # ── Post chatter message for traceability ────────────────────────────
        # Only models that inherit mail.thread have a chatter.
        # All supported models (account.move, purchase.order, sale.order,
        # stock.picking) do inherit mail.thread, so this is always safe.
        self._post_ocr_chatter_message(new_record)

        return {
            'type': 'ir.actions.act_window',
            'res_model': model_name,
            'view_mode': 'form',
            'res_id': new_record.id,
            'target': 'current',
        }

    def _post_ocr_chatter_message(self, record):
        """
        Post a traceability message in the chatter of the newly created record.
        Shows: uploaded filename, date/time, user who triggered OCR,
        and a clickable link to the original attachment.
        """
        if not hasattr(record, 'message_post'):
            return

        attachment = self.ocr_attachment_id
        filename = attachment.name if attachment else _('Unknown file')
        user = self.env.user
        now = fields.Datetime.now().strftime('%d/%m/%Y %H:%M')

        # Build attachment link if we have one
        if attachment:
            attachment_link = (
                f'<a href="/web/content/{attachment.id}?download=true">'
                f'{filename}</a>'
            )
        else:
            attachment_link = filename

        body = Markup(
            'Created via OCR'
            'Document: %(link)s'
            'Uploaded by: %(user)s'
            'Date: %(date)s'
        ) % {
            'link': Markup(attachment_link),
            'user': user.name,
            'date': now,
        }

        # Post as the actual user (not sudo) so the chatter shows their name
        record.sudo(False).with_user(user).message_post(
            body=body,
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

    def _map_field_value(self, line, raw_value, date_fmt, config):
        """Map an OCR value to the corresponding Odoo field value."""
        ttype = line.ocr_field_id.ttype

        if ttype in ('char', 'text'):
            return (raw_value or '').strip()

        elif ttype in ('date', 'datetime'):
            return self._parse_date(raw_value, date_fmt)

        elif ttype == 'integer':
            try:
                return int(raw_value) if str(raw_value).lstrip('-').isdigit() else 0
            except (ValueError, TypeError):
                return 0

        elif ttype == 'float':
            try:
                cleaned = str(raw_value).replace(',', '').strip()
                return float(cleaned) if cleaned else 0.0
            except (ValueError, TypeError):
                return 0.0

        elif ttype == 'monetary':
            try:
                cleaned = str(raw_value).replace(',', '').replace('$', '').strip()
                return float(cleaned) if cleaned else 0.0
            except (ValueError, TypeError):
                return 0.0

        elif ttype == 'many2one':
            return self._resolve_many2one(line, raw_value, config)

        elif ttype == 'one2many':
            return self._resolve_one2many(line, raw_value, config)

        elif ttype == 'many2many':
            return self._resolve_many2many(line, raw_value)

        return raw_value

    def _parse_date(self, value, date_fmt):
        """Convert a date string into an Odoo-compatible date."""
        if not value:
            return False
        for fmt in [date_fmt, '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                return datetime.datetime.strptime(str(value), fmt).date()
            except (ValueError, TypeError):
                continue
        return False

    def _resolve_many2one(self, line, value, config):
        """Resolve a many2one field value."""
        relation = line.ocr_field_id.relation

        if relation == 'res.currency':
            rec = self.env['res.currency'].sudo().search(
                [('name', '=', value), ('active', '=', True)], limit=1)
            return rec.id if rec else self.env.company.currency_id.id

        if relation == 'res.partner' and isinstance(value, dict):
            return self._resolve_partner(value, line, config)

        if isinstance(value, dict):
            search_name = value.get('name') or value.get('display_name', '')
        else:
            search_name = value or ''

        rec = self.env[relation].sudo().search(
            [('name', '=', search_name)], limit=1)
        if not rec and line.create_if_not_found and search_name:
            rec = self.env[relation].sudo().create({'name': search_name})
        return rec.id if rec else False

    def _resolve_partner(self, value, line, config):
        """Resolve or create a partner from OCR data."""
        Partner = self.env['res.partner'].sudo()
        company_domain = ('company_id', 'in', [self.env.company.id, False])

        for domain_field, dict_key in [
            ('email', 'email'),
            ('phone', 'phone'),
            ('name', 'name'),
        ]:
            v = value.get(dict_key)
            if v:
                rec = Partner.search([(domain_field, '=', v), company_domain], limit=1)
                if rec:
                    return rec.id

        if not line.create_if_not_found:
            return False

        country_id = False
        state_id = False
        country_name = (value.get('country_id') or '').strip().lower()
        state_name = (value.get('state_id') or '').strip().lower()

        if country_name:
            country = self.env['res.country'].sudo().search([]).filtered(
                lambda c: c.code.lower() == country_name or c.name.lower() == country_name
            )[:1]
            country_id = country.id if country else False

        if state_name and country_id:
            state = self.env['res.country.state'].sudo().search(
                [('country_id', '=', country_id)]
            ).filtered(
                lambda s: s.code.lower() == state_name or s.name.lower() == state_name
            )[:1]
            state_id = state.id if state else False

        partner_fields = self.env['res.partner']._fields.keys()
        contact_data = {k: v for k, v in value.items() if k in partner_fields and v}
        contact_data.update({
            'company_id': self.env.company.id,
            'country_id': country_id,
            'state_id': state_id,
        })
        return Partner.create(contact_data).id

    def _resolve_many2many(self, line, value):
        """
        Supports: a single string, a list of strings, or a list of dicts with 'name'.
        Returns [(6, 0, [ids])] or False.
        """
        relation = line.ocr_field_id.relation
        if not relation or not value:
            return False

        if isinstance(value, str):
            value = [value]
        elif not isinstance(value, list):
            return False

        ids = []
        Model = self.env[relation].sudo()
        for item in value:
            name = item.get('name', '') if isinstance(item, dict) else str(item)
            if not name:
                continue
            rec = Model.search([('name', '=', name)], limit=1)
            if rec:
                ids.append(rec.id)

        return [(6, 0, ids)] if ids else False

    def _resolve_one2many(self, line, value, config):
        """Resolve one2many field values from OCR data."""
        if not isinstance(value, list):
            return False

        relation = line.ocr_field_id.relation
        related_model = self.env[relation]
        related_fields = related_model.fields_get()
        create_products = config.create_products_if_not_found

        result = []
        for item in value:
            mapped = {k: v for k, v in item.items()
                      if k in related_fields and v is not None}

            if 'display_name' in item and item['display_name']:
                if not mapped.get('name'):
                    mapped['name'] = item['display_name']
            mapped.pop('display_name', None)

            product = None
            if 'product_id' in mapped:
                product = self._find_product(
                    mapped.get('product_id'), mapped.get('name') or '', create_products)
                mapped['product_id'] = product.id if product else False
            elif mapped.get('name'):
                product = self._find_product(None, mapped['name'], create_products)
                if product:
                    mapped['product_id'] = product.id

            if 'product_uom' in mapped:
                uom = self.env['uom.uom'].sudo().search(
                    [('name', '=', mapped['product_uom'])], limit=1)
                mapped['product_uom'] = uom.id if uom else False

            for tax_field in ('tax_ids', 'taxes_id', 'tax_id'):
                if tax_field in mapped and tax_field in related_fields:
                    tax_ids = self._resolve_taxes(mapped[tax_field], relation)
                    mapped[tax_field] = [(6, 0, tax_ids)] if tax_ids else False
                    break

            if mapped:
                result.append((0, 0, mapped))

        return result or False

    def _resolve_taxes(self, raw_taxes, line_model):
        """
        Resolve tax names or percentage values to account.tax IDs.
        raw_taxes can be: '15%', 15, [{'name': 'Tax 15%'}], ['15%']
        """
        Tax = self.env['account.tax'].sudo()
        ids = []

        if isinstance(raw_taxes, (str, int, float)):
            raw_taxes = [raw_taxes]
        elif not isinstance(raw_taxes, list):
            return ids

        type_domain = []
        if 'purchase' in line_model:
            type_domain = [('type_tax_use', 'in', ['purchase', 'all'])]
        elif 'sale' in line_model:
            type_domain = [('type_tax_use', 'in', ['sale', 'all'])]

        for item in raw_taxes:
            name = item.get('name', '') if isinstance(item, dict) else str(item)
            if not name:
                continue
            tax = Tax.search([('name', '=', name)] + type_domain, limit=1)
            if not tax:
                try:
                    amount = float(str(name).replace('%', '').strip())
                    tax = Tax.search(
                        [('amount', '=', amount)] + type_domain, limit=1)
                except ValueError:
                    pass
            if tax:
                ids.append(tax.id)
        return ids

    def _find_product(self, code_or_name, display_name, create_if_missing):
        """Find or create a product from OCR data."""
        Product = self.env['product.product'].sudo()
        company_domain = ('company_id', 'in', [self.env.company.id, False])

        if code_or_name:
            p = Product.search([
                ('default_code', '=', code_or_name),
                ('default_code', '!=', False),
                company_domain,
            ], limit=1)
            if p:
                return p
            p = Product.search([
                ('barcode', '=', code_or_name),
                ('barcode', '!=', False),
                company_domain,
            ], limit=1)
            if p:
                return p

        name = display_name or code_or_name or ''
        if name:
            p = Product.search([('name', '=', name), company_domain], limit=1)
            if p:
                return p

        if create_if_missing and name:
            product_vals = {
                'name': name,
                'default_code': code_or_name or False,
                'company_id': self.env.company.id,
            }
            # is_storable exists in Odoo 17+/19; fall back to detailed_type for older
            if 'is_storable' in self.env['product.product']._fields:
                product_vals['is_storable'] = True
            else:
                product_vals['detailed_type'] = 'product'
            return Product.create(product_vals)

        return Product.browse()