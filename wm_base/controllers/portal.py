#############################################################################
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import json
import logging
import urllib.parse

from markupsafe import Markup

from odoo import fields, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)


def _json_for_script(value):
    """
    Serialize ``value`` for inlining in a <script> block. Plain json.dumps
    leaves "</script>" and "<!--" intact, so a signer-entered value could
    close the script tag and inject markup; escape the HTML-significant
    characters (valid JSON/JS string escapes).
    """
    return Markup(
        json.dumps(value)
        .replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    )


def _safe_int_str(value):
    """Return the value as a digit string, or '' (ids are only ever integers)."""
    value = str(value or '').strip()
    return value if value.isdigit() else ''


def _format_weight(weight):
    """Return the weight as 'N kg', or N/A when it was never recorded."""
    return f"{weight} kg" if weight else request.env._('N/A')


def _safe_back_url(url):
    """Only same-site backend paths are accepted as a 'back' target: anything
    else (absolute URLs, //host, javascript:, backslashes, control chars) is
    dropped, which prevents open redirects and script injection."""
    url = (url or '').strip()
    if (url == '/web' or url.startswith('/web#') or url.startswith('/web?')
            or url.startswith('/odoo')) and not any(c in url for c in '\\\r\n\t"\'<>'):
        return url
    return ''


class WmSignaturePortal(http.Controller):
    """Controller handling digital signature portal pages, signing workflows, and document viewing."""

    @staticmethod
    def _is_signature_manager():
        user = request.env.user
        return user.has_group('wm_base.group_signature_manager') or user.has_group('base.group_system')

    @staticmethod
    def _is_signature_user():
        # auth='user' also lets portal users in: require the internal role
        return request.env.user.has_group('wm_base.group_signature_user')

    @http.route('/wm_signature/sign/<string:token>', type='http', auth='public', website=True)
    def signature_portal(self, token, **kwargs):
        """
        Serve the portal-facing signature capture page for an active signature
        request, validating the access token and rendering the document with
        signature field overlays.
        """
        signer = request.env['wm.signature.request.signer'].sudo().search([('access_token', '=', token)], limit=1)
        if not signer:
            return request.not_found()

        # If signer already signed, redirect to thank you page
        if signer.state == 'signed':
            return request.redirect('/wm_signature/sign/thankyou?name=%s' % signer.partner_id.name)

        req = signer.request_id
        # Links of draft or cancelled (e.g. superseded) requests are dead
        if req.state != 'sent':
            return request.not_found()

        ref_doc_name = ""
        ref_doc_details = []
        if req.reference_doc:
            ref_doc_name = req.reference_doc.display_name
            # If it's a collection order, we can display some waste details
            if req.reference_doc._name == 'wm.collection.order':
                order = req.reference_doc
                categories = []
                materials = []
                if hasattr(order, 'product_ids') and order.product_ids:
                    materials = order.product_ids.mapped('name')
                    cats = order.product_ids.mapped('wm_waste_category_id').filtered(lambda c: c.name)
                    if cats:
                        categories = cats.mapped('name')
                if not categories and hasattr(order, 'collection_point_id') and order.collection_point_id and order.collection_point_id.category_ids:
                    categories = order.collection_point_id.category_ids.mapped('name')
                if not categories and hasattr(order, 'category_ids') and order.category_ids:
                    categories = order.category_ids.mapped('name')

                category_str = ", ".join(categories) if categories else request.env._('N/A')
                material_str = ", ".join(materials) if materials else request.env._('N/A')

                ref_doc_details = [
                    (request.env._('Collection Order'), order.name),
                    (request.env._('Customer'), order.partner_id.name or request.env._('N/A')),
                    (request.env._('Waste Category'), category_str),
                    (request.env._('Waste Material'), material_str),
                    (request.env._('Container Type'), order.container_id.name if hasattr(order, 'container_id') and order.container_id else request.env._('N/A')),
                    (request.env._('Est. Weight'), _format_weight(getattr(order, 'estimated_weight', False))),
                    (request.env._('Confirmed Weight'), _format_weight(getattr(order, 'confirmed_weight', False))),
                ]

            elif req.reference_doc._name in ('wm.partner.contract', 'partner.contract'):
                contract = req.reference_doc
                site_name = request.env._('N/A')
                if hasattr(contract, 'collection_point_id') and contract.collection_point_id:
                    site_name = contract.collection_point_id.name
                elif hasattr(contract, 'site_id') and contract.site_id:
                    site_name = contract.site_id.name
                ref_doc_details = [
                    (request.env._('Contract'), contract.name),
                    (request.env._('Customer'), contract.partner_id.name or request.env._('N/A')),
                    (request.env._('Site'), site_name),
                    (request.env._('From Date'), contract.from_date.strftime('%Y-%m-%d') if contract.from_date else request.env._('N/A')),
                    (request.env._('To Date'), contract.to_date.strftime('%Y-%m-%d') if contract.to_date else request.env._('N/A')),
                    (request.env._('Frequency'), dict(contract._fields['frequency'].selection).get(contract.frequency, contract.frequency) if contract.frequency else request.env._('N/A')),
                ]
            elif req.reference_doc._name == 'wm.batch.inspection':
                inspection = req.reference_doc
                ref_doc_details = [
                    (request.env._('Inspection'), inspection.name),
                    (request.env._('Inspector'), inspection.inspector_id.name or request.env._('N/A')),
                    (request.env._('Date'), inspection.inspection_date.strftime('%Y-%m-%d %H:%M') if inspection.inspection_date else request.env._('N/A')),
                    (request.env._('Status'), dict(inspection._fields['state'].selection).get(inspection.state, inspection.state).upper()),
                ]

        # Get existing items on template
        template_items = []
        if req.reference_doc and req.reference_doc._name in ('wm.partner.contract', 'partner.contract'):
            # Position signature box at bottom left directly over the Client Signature line
            role_id = signer.role_id.id if signer and signer.role_id else (req.template_id.role_ids[:1].id or 1)
            item_id = req.template_id.item_ids[:1].id if req.template_id.item_ids else 999901
            template_items = [{
                'id': item_id,
                'page': 1,
                'x': 8.0,
                'y': 76.0,
                'width': 38.0,
                'height': 10.0,
                'type': 'signature',
                'role_id': role_id,
            }]
        else:
            for item in req.template_id.item_ids:
                template_items.append({
                    'id': item.id,
                    'page': item.page,
                    'x': item.x,
                    'y': item.y,
                    'width': item.width,
                    'height': item.height,
                    'type': item.type,
                    'role_id': item.role_id.id,
                })

        # Get filled values
        filled_values = {}
        for val in req.item_value_ids:
            filled_values[val.item_id.id] = {
                'value': val.value,
                'signature_image': (val.signature_image and val.signature_image.decode('utf-8')) or '',
                'signer_name': val.signer_id.partner_id.name,
            }

        # Get active signer roles in the request
        active_role_ids = req.signer_ids.mapped('role_id').ids

        values = {
            'signer': signer,
            'sig_request': req,
            'ref_doc_name': ref_doc_name,
            'ref_doc_details': ref_doc_details,
            'template_items': json.dumps(template_items),
            'filled_values': json.dumps(filled_values),
            'active_role_ids': json.dumps(active_role_ids),
        }
        return request.render('wm_base.signature_portal_page_template', values)

    # Item id the portal page uses for its fallback signature box when the
    # template has no designed items (see signature_portal / portal JS)
    SYNTHETIC_ITEM_ID = 999901

    @staticmethod
    def _get_signer_allowed_items(signer):
        """
        Template items this signer may fill, mirroring the portal page:
        items of the signer's role, items without a role or whose role has no
        signer on the request, every item when only one role signs, and for
        contracts the single signature box shown to the signer.
        """
        req = signer.request_id.sudo()
        items = req.template_id.item_ids
        active_roles = req.signer_ids.mapped('role_id')
        if len(active_roles) <= 1:
            allowed = items
        else:
            allowed = items.filtered(
                lambda i: not i.role_id or i.role_id == signer.role_id or i.role_id not in active_roles)
        if req.reference_doc and req.reference_doc._name in ('wm.partner.contract', 'partner.contract'):
            allowed |= items[:1]
        return allowed

    @http.route('/wm_signature/sign/submit', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def signature_submit(self, token, filled_fields, **kwargs):
        """
        Accept the POST submission from the portal signature page, validate the
        signature data and access token, then persist the captured signature to
        the request record.
        """
        signer = request.env['wm.signature.request.signer'].sudo().search([('access_token', '=', token)], limit=1)
        if not signer:
            return {'success': False, 'error': request.env._('Invalid access token')}

        if signer.state == 'signed':
            return {'success': False, 'error': request.env._('Already signed')}
        if signer.request_id.state != 'sent':
            return {'success': False, 'error': request.env._('This signature request is no longer open for signing')}

        req = signer.request_id
        template = req.template_id
        Item = request.env['wm.signature.item'].sudo()
        template_items = template.item_ids.sudo()
        allowed_items = self._get_signer_allowed_items(signer)
        if not isinstance(filled_fields, list) or not filled_fields:
            return {'success': False, 'error': request.env._('No signature data submitted')}

        # Validate the submitted items before writing anything
        parsed_fields = []
        use_synthetic_item = False
        for field in filled_fields:
            if not isinstance(field, dict):
                return {'success': False, 'error': request.env._('Invalid signature data')}
            try:
                item_id = int(field.get('item_id'))
            except (TypeError, ValueError):
                return {'success': False, 'error': request.env._('Invalid signature field')}
            sig_data = field.get('signature') or ''
            base64_data = False
            if sig_data:
                if ',' in sig_data:
                    _, base64_data = sig_data.split(',', 1)
                else:
                    base64_data = sig_data
            if item_id == self.SYNTHETIC_ITEM_ID and not template_items:
                # Portal fallback field for templates without designed items
                use_synthetic_item = True
                item = Item
            else:
                item = allowed_items.filtered(lambda i: i.id == item_id)
                if not item:
                    return {'success': False, 'error': request.env._('Invalid signature field')}
            parsed_fields.append((item, field.get('value', '') or '', base64_data))

        signature_items = allowed_items.filtered(lambda i: i.type == 'signature')
        if use_synthetic_item or signature_items:
            has_signature = any(
                base64_data and (not item or item.type == 'signature')
                for item, _val, base64_data in parsed_fields
            )
            if not has_signature:
                return {'success': False, 'error': request.env._('A signature is required')}

        try:
            # All or nothing: if certificate generation (or anything else) fails,
            # the values and the signed state must not be committed.
            with request.env.cr.savepoint():
                synthetic_item = Item
                for item, val_text, base64_data in parsed_fields:
                    if not item:
                        if not synthetic_item:
                            # At most one signature item, only for an item-less template
                            synthetic_item = Item.create({
                                'template_id': template.id,
                                'page': 1,
                                'x': 10.0,
                                'y': 82.0,
                                'width': 38.0,
                                'height': 12.0,
                                'type': 'signature',
                                'role_id': signer.role_id.id,
                            })
                        item = synthetic_item

                    request.env['wm.signature.request.item.value'].sudo().create({
                        'request_id': req.id,
                        'item_id': item.id,
                        'value': val_text,
                        'signature_image': base64_data,
                        'signer_id': signer.id,
                    })

                # Save signer metadata (signed state, date, IP, user agent)
                signer.sudo().write({
                    'state': 'signed',
                    'signed_date': fields.Datetime.now(),
                    'ip_address': request.httprequest.remote_addr,
                    'user_agent': request.httprequest.headers.get('User-Agent', '')[:256]
                })

                # Check if all other signers completed, triggers certificate build
                signer.request_id.sudo()._check_request_completion()
                query = urllib.parse.urlencode({'name': signer.partner_id.name or '', 'token': token})
                return {'success': True, 'redirect_url': f'/wm_signature/sign/thankyou?{query}'}
        except Exception:
            _logger.exception("Signature submission failed for request %s", signer.request_id.id)
            return {'success': False, 'error': request.env._('The signature could not be saved. Please try again or contact the sender.')}

    @http.route('/wm_signature/sign/thankyou', type='http', auth='public', website=True)
    def signature_thankyou(self, name='', token='', **kwargs):
        """
        Render the post-signing thank-you page after a successful portal
        signature submission, with a back link to the linked document when
        known.
        """
        back_url = '/web'
        back_label = request.env._('Back to Odoo')
        signer = False
        if token:
            signer = request.env['wm.signature.request.signer'].sudo().search([('access_token', '=', token)], limit=1)
            if signer and signer.request_id.reference_doc:
                ref = signer.request_id.reference_doc
                back_url = f"/web#id={ref.id}&model={ref._name}&view_type=form"
                if ref._name in ('wm.partner.contract', 'partner.contract'):
                    back_label = request.env._('Back to Contract')
                elif ref._name == 'wm.collection.order':
                    back_label = request.env._('Back to Collection Order')
                elif ref._name == 'wm.batch.inspection':
                    back_label = request.env._('Back to Inspection')

        return request.render('wm_base.signature_thank_you_page_template', {
            'name': name,
            'back_url': back_url,
            'back_label': back_label,
            'signer': signer if signer and signer.state == 'signed' else False,
        })

    @http.route('/wm_signature/request/pdf/<string:token>', type='http', auth='public')
    def get_request_pdf(self, token, **kwargs):
        """
        Serve the request's PDF for a valid signer access token: the signed
        copy once completed, otherwise the document to sign.
        """
        signer = request.env['wm.signature.request.signer'].sudo().search([('access_token', '=', token)], limit=1)
        if not signer:
            return request.not_found()
        req = signer.request_id.sudo()
        if req.signed_document:
            pdf_data = base64.b64decode(req.signed_document)
        else:
            pdf_data = req._get_document_pdf()
        if not pdf_data:
            return request.not_found()
        return request.make_response(pdf_data, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', 'inline; filename="document.pdf"')
        ])

    @http.route('/wm_signature/template/pdf/<int:template_id>', type='http', auth='user')
    def get_template_pdf(self, template_id, **kwargs):
        """
        Stream the PDF shown in the template designer: the linked inspection or
        order report when given, else the template document, else a report of
        a document using this template.
        """
        template = request.env['wm.signature.template'].browse(template_id)
        if not template.exists():
            return request.not_found()

        pdf_data = False
        filename = template.document_filename or "document.pdf"

        inspection_id = kwargs.get('inspection_id')
        if inspection_id and 'wm.batch.inspection' in request.env:
            insp = request.env['wm.batch.inspection'].browse(int(inspection_id))
            if insp.exists():
                try:
                    pdf_data, _format = request.env['ir.actions.report']._render_qweb_pdf(
                        'wm_collection.action_report_batch_inspection', [insp.id]
                    )
                    filename = f"Inspection_{insp.name}.pdf"
                except Exception as e:
                    _logger.warning("Failed to render inspection PDF report for inspection %s: %s", insp.id, e)

        order_id = kwargs.get('order_id')
        if not pdf_data and order_id and 'wm.collection.order' in request.env:
            order = request.env['wm.collection.order'].browse(int(order_id))
            if order.exists():
                if getattr(order, 'collection_report_pdf', False):
                    pdf_data = base64.b64decode(order.collection_report_pdf)
                    filename = order.collection_report_pdf_filename or f"{order.name}.pdf"
                else:
                    try:
                        pdf_data, _format = request.env['ir.actions.report']._render_qweb_pdf(
                            'wm_collection.collection_order_report', [order.id]
                        )
                        filename = f"Collection_Order_{order.name}.pdf"
                    except Exception as e:
                        _logger.warning("Failed to render collection order PDF report for order %s: %s", order.id, e)

        if not pdf_data and template.document:
            pdf_data = base64.b64decode(template.document)

        # No guessing: another record using this template is unrelated data.
        if not pdf_data:
            return request.not_found()

        return request.make_response(pdf_data, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'inline; filename="{filename}"')
        ])

    @http.route('/wm_signature/template/edit/<int:template_id>', type='http', auth='user', website=True)
    def edit_template(self, template_id, **kwargs):
        """
        Render the signature template visual editor with the existing field
        placements, ensuring a signer role and base PDF exist and removing
        unused duplicate fields.
        """
        if not (request.env.user.has_group('wm_base.group_signature_manager') or request.env.user.has_group('base.group_system')):
            raise AccessError(request.env._("Access Denied: Only signature managers can edit signature templates."))

        template = request.env['wm.signature.template'].browse(template_id)
        if not template.exists():
            return request.not_found()

        # Ensure at least one signer role is set on template
        if not template.role_ids:
            default_role = request.env['wm.signature.role'].search([], limit=1)
            if not default_role:
                default_role = request.env['wm.signature.role'].sudo().create({'name': 'Signatory'})
            template.write({'role_ids': [(4, default_role.id)]})

        # Ensure document binary exists
        if not template.document:
            pdf_binary = template._generate_default_pdf_document()
            if pdf_binary:
                template.write({
                    'document': pdf_binary,
                    'document_filename': f"{template.name or 'Document'}.pdf"
                })

        # Clean up exact duplicate items if any accidental double-drops exist
        seen_items = set()
        duplicates_to_unlink = request.env['wm.signature.item']
        for item in template.item_ids:
            item_key = (item.type, item.role_id.id, item.page, round(item.x, 2), round(item.y, 2))
            if item_key in seen_items:
                duplicates_to_unlink |= item
            else:
                seen_items.add(item_key)
        # Never delete a duplicate that already holds captured signature values.
        used = request.env['wm.signature.request.item.value'].sudo().search(
            [('item_id', 'in', duplicates_to_unlink.ids)]).item_id
        duplicates_to_unlink -= used
        if duplicates_to_unlink:
            duplicates_to_unlink.unlink()

        roles = template.role_ids
        # Load existing fields on this template
        existing_items = []
        for item in template.item_ids:
            existing_items.append({
                'id': item.id,
                'page': item.page,
                'x': item.x,
                'y': item.y,
                'width': item.width,
                'height': item.height,
                'type': item.type,
                'role_id': item.role_id.id,
            })

        inspection_id = _safe_int_str(kwargs.get('inspection_id', ''))
        order_id = _safe_int_str(kwargs.get('order_id', ''))
        back_url = _safe_back_url(kwargs.get('back_url', ''))
        if not back_url or back_url.strip() == '/web':
            if inspection_id:
                back_url = f"/web#id={inspection_id}&model=wm.batch.inspection&view_type=form"
            elif order_id:
                back_url = f"/web#id={order_id}&model=wm.collection.order&view_type=form"
            else:
                back_url = f"/web#id={template.id}&model=wm.signature.template&view_type=form"

        values = {
            'template': template,
            'roles': roles,
            'existing_items': json.dumps(existing_items),
            'order_id': order_id,
            'inspection_id': inspection_id,
            'back_url': back_url,
        }
        return request.render('wm_base.signature_template_editor_page_template', values)

    @http.route('/wm_signature/template/save_fields', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def save_fields(self, template_id, fields_data, **kwargs):
        """
        Persist the updated signature field positions, sizes, and types
        submitted from the template designer UI back to the
        wm.signature.template record.
        """
        if not (request.env.user.has_group('wm_base.group_signature_manager') or request.env.user.has_group('base.group_system')):
            return {'success': False, 'error': request.env._('Access Denied: Only signature managers can save signature fields.')}

        template = request.env['wm.signature.template'].browse(template_id)
        if not template.exists():
            return {'success': False, 'error': request.env._('Template not found')}

        # Update existing items in place so values already captured on signed
        # or in-flight requests keep pointing at their field; only fields the
        # designer removed are deleted, and only when no request used them.
        Item = request.env['wm.signature.item']
        existing = {item.id: item for item in template.item_ids}
        keep = set()
        for field in fields_data:
            vals = {
                'page': field.get('page'),
                'x': field.get('x'),
                'y': field.get('y'),
                'width': field.get('width'),
                'height': field.get('height'),
                'type': field.get('type'),
                'role_id': int(field.get('role_id')),
            }
            field_id = field.get('id')
            item = existing.get(field_id) if isinstance(field_id, int) else None
            if item:
                item.write(vals)
                keep.add(item.id)
            else:
                keep.add(Item.create(dict(vals, template_id=template.id)).id)

        removed = template.item_ids.filtered(lambda i: i.id not in keep)
        if removed and request.env['wm.signature.request.item.value'].sudo().search_count(
                [('item_id', 'in', removed.ids)]):
            return {
                'success': False,
                'error': request.env._(
                    'A removed field already has signed values on existing requests. '
                    'Keep the field, or cancel and delete those requests first.'),
            }
        removed.unlink()
        return {'success': True}

    @http.route('/wm_signature/template/sign_now', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def template_sign_now(self, template_id, order_id=None, inspection_id=None, **kwargs):
        """
        Start an immediate signing session for the current user on this
        template (optionally linked to an order or inspection) and return the
        portal signing URL.
        """
        if not self._is_signature_user():
            return {'success': False, 'error': request.env._('Access Denied: You are not allowed to start a signature.')}
        template = request.env['wm.signature.template'].browse(template_id)
        if not template.exists():
            return {'success': False, 'error': request.env._('Template not found')}

        # Link the request to the explicitly given order/inspection and verify write access
        reference_doc = False
        if inspection_id and 'wm.batch.inspection' in request.env:
            insp = request.env['wm.batch.inspection'].browse(int(inspection_id))
            if not insp.exists():
                return {'success': False, 'error': request.env._('Inspection not found')}
            try:
                insp.check_access('write')
            except AccessError:
                return {'success': False, 'error': request.env._('You are not authorized to sign this inspection.')}
            reference_doc = f"wm.batch.inspection,{insp.id}"

        if not reference_doc and order_id and 'wm.collection.order' in request.env:
            order = request.env['wm.collection.order'].browse(int(order_id))
            if not order.exists():
                return {'success': False, 'error': request.env._('Collection order not found')}
            try:
                order.check_access('write')
            except AccessError:
                return {'success': False, 'error': request.env._('You are not authorized to sign this collection order.')}
            reference_doc = f"wm.collection.order,{order.id}"

        # The target document must be named explicitly (order_id / inspection_id):
        # a template can be shared by many documents, so guessing the first match
        # could attach the signature to the wrong one.

        if not reference_doc and (order_id or inspection_id):
            return {'success': False, 'error': request.env._('Target document not found or inaccessible')}

        role = template.role_ids[:1]
        if not role:
            role = request.env['wm.signature.role'].search([], limit=1)
        if not role:
            role = request.env['wm.signature.role'].sudo().create({'name': 'Signer'})

        # Cancel any previous unsigned requests for this reference doc
        if reference_doc:
            # Only the user's own open requests are superseded; other users'
            # pending requests are left alone unless the user manages signatures.
            domain = [
                ('reference_doc', '=', reference_doc),
                ('state', 'in', ('draft', 'sent')),
            ]
            if not self._is_signature_manager():
                domain.append(('create_uid', '=', request.env.uid))
            for req in request.env['wm.signature.request'].sudo().search(domain):
                req.write({'state': 'cancel'})

        sig_request = request.env['wm.signature.request'].sudo().create({
            'template_id': template.id,
            'reference_doc': reference_doc,
            'signer_ids': [(0, 0, {
                'partner_id': request.env.user.partner_id.id,
                'role_id': role.id,
                'email': request.env.user.partner_id.email or request.env.user.email or '',
            })],
        })

        sig_request.write({'state': 'sent'})
        signer = sig_request.signer_ids[0]
        portal_url = f"/wm_signature/sign/{signer.access_token}"
        return {'success': True, 'redirect_url': portal_url}

    @http.route('/wm_signature/template/create_from_pdf', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def template_create_from_pdf(self, name, document_base64, filename, **kwargs):
        """
        Handle the AJAX upload of a PDF file, create a new
        wm.signature.template record from the uploaded binary, and return the
        new template ID for the designer redirect.
        """
        if not self._is_signature_manager():
            return {'success': False, 'error': request.env._('Access Denied: Only signature managers can create signature templates.')}
        try:
            if not document_base64:
                return {'success': False, 'error': request.env._('No file uploaded')}

            # Clean base64 string if it contains data URI header
            if ',' in document_base64:
                document_base64 = document_base64.split(',', 1)[1]

            template_id = request.env['wm.signature.template'].sudo().create_from_pdf(name, document_base64.encode('utf-8'), filename)
            return {'success': True, 'template_id': template_id}
        except (UserError, ValidationError) as e:
            return {'success': False, 'error': str(e)}
        except Exception:
            _logger.exception("Signature template route failed")
            return {'success': False, 'error': request.env._("An unexpected error occurred. Please contact your administrator.")}

    @http.route('/wm_signature/template/create_sample', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def template_create_sample(self, **kwargs):
        """
        Create a sample signature template from a generated demo PDF via AJAX
        and return its id, so administrators can try the signature workflow
        without uploading a PDF.
        """
        if not self._is_signature_manager():
            return {'success': False, 'error': request.env._('Access Denied: Only signature managers can create signature templates.')}
        try:
            template_id = request.env['wm.signature.template'].sudo().create_sample_template()
            return {'success': True, 'template_id': template_id}
        except (UserError, ValidationError) as e:
            return {'success': False, 'error': str(e)}
        except Exception:
            _logger.exception("Signature template route failed")
            return {'success': False, 'error': request.env._("An unexpected error occurred. Please contact your administrator.")}

    @http.route('/wm_signature/template/send_request', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def template_send_request(self, template_id, signers, **kwargs):
        """
        Process the AJAX call from the template designer to create and dispatch
        a new signature request from the current template to the specified list
        of signers.
        """
        if not self._is_signature_user():
            return {'success': False, 'error': request.env._('Access Denied: You are not allowed to send signature requests.')}
        try:
            template = request.env['wm.signature.template'].browse(template_id)
            if not template.exists():
                return {'success': False, 'error': request.env._('Template not found')}
            template.check_access('read')

            if not signers:
                return {'success': False, 'error': request.env._('No signers provided')}

            signer_vals = []
            for signer_data in signers:
                role_id = int(signer_data.get('role_id'))
                name = signer_data.get('name', '').strip()
                email = signer_data.get('email', '').strip()

                if not name or not email:
                    return {'success': False, 'error': request.env._('Name and Email are required for all signers.')}

                # Find or create partner
                # Exact (normalized) match: '=ilike' would treat '_' and '%' in the
                # address as wildcards and could attach the wrong partner.
                normalized = email_normalize(email)
                partner = request.env['res.partner'].sudo().search(
                    [('email_normalized', '=', normalized)], limit=1) if normalized else request.env['res.partner']
                if not partner:
                    partner = request.env['res.partner'].sudo().create({
                        'name': name,
                        'email': email,
                    })
                else:
                    if partner.name == email and name != email:
                        partner.sudo().write({'name': name})

                signer_vals.append((0, 0, {
                    'partner_id': partner.id,
                    'role_id': role_id,
                    'email': email,
                }))

            sig_request = request.env['wm.signature.request'].sudo().create({
                'template_id': template.id,
                'signer_ids': signer_vals,
            })

            sig_request.action_send()
            return {'success': True}
        except (UserError, ValidationError) as e:
            return {'success': False, 'error': str(e)}
        except Exception:
            _logger.exception("Signature template route failed")
            return {'success': False, 'error': request.env._("An unexpected error occurred. Please contact your administrator.")}
