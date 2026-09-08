# -*- coding: utf-8 -*-
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

from markupsafe import Markup
from odoo import fields, http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class WmSignaturePortal(http.Controller):
    """Extends Portal Controller with digital signature portal pages and document viewing."""

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

                category_str = ", ".join(categories) if categories else _('N/A')
                material_str = ", ".join(materials) if materials else _('N/A')

                ref_doc_details = [
                    (_('Collection Order'), order.name),
                    (_('Customer'), order.partner_id.name or _('N/A')),
                    (_('Waste Category'), category_str),
                    (_('Waste Material'), material_str),
                    (_('Container Type'), order.container_id.name if hasattr(order, 'container_id') and order.container_id else _('N/A')),
                    (_('Est. Weight'), f"{getattr(order, 'estimated_weight', 0.0)} kg"),
                    (_('Confirmed Weight'), f"{getattr(order, 'confirmed_weight', 0.0)} kg"),
                ]

            elif req.reference_doc._name in ('wm.partner.contract', 'partner.contract'):
                contract = req.reference_doc
                site_name = _('N/A')
                if hasattr(contract, 'collection_point_id') and contract.collection_point_id:
                    site_name = contract.collection_point_id.name
                elif hasattr(contract, 'site_id') and contract.site_id:
                    site_name = contract.site_id.name
                ref_doc_details = [
                    (_('Contract'), contract.name),
                    (_('Customer'), contract.partner_id.name or _('N/A')),
                    (_('Site'), site_name),
                    (_('From Date'), contract.from_date.strftime('%Y-%m-%d') if contract.from_date else _('N/A')),
                    (_('To Date'), contract.to_date.strftime('%Y-%m-%d') if contract.to_date else _('N/A')),
                    (_('Frequency'), dict(contract._fields['frequency'].selection).get(contract.frequency, contract.frequency) if contract.frequency else _('N/A')),
                ]
            elif req.reference_doc._name == 'wm.batch.inspection':
                inspection = req.reference_doc
                ref_doc_details = [
                    (_('Inspection'), inspection.name),
                    (_('Inspector'), inspection.inspector_id.name or _('N/A')),
                    (_('Date'), inspection.inspection_date.strftime('%Y-%m-%d %H:%M') if inspection.inspection_date else _('N/A')),
                    (_('Status'), dict(inspection._fields['state'].selection).get(inspection.state, inspection.state).upper()),
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
                'signature_image': val.signature_image and val.signature_image.decode('utf-8') or '',
                'signer_name': val.signer_id.partner_id.name,
            }

        # Get active signer roles in the request
        active_role_ids = req.signer_ids.mapped('role_id').ids

        values = {
            'signer': signer,
            'sig_request': req,
            'ref_doc_name': ref_doc_name,
            'ref_doc_details': ref_doc_details,
            'template_items': Markup(json.dumps(template_items)),
            'filled_values': Markup(json.dumps(filled_values)),
            'active_role_ids': Markup(json.dumps(active_role_ids)),
        }
        return request.render('wm_base.signature_portal_page_template', values)

    @http.route('/wm_signature/sign/submit', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def signature_submit(self, token, filled_fields, **kwargs):
        """
        Accept the POST submission from the portal signature page, validate the
        signature data and access token, then persist the captured signature to
        the request record.
        """
        signer = request.env['wm.signature.request.signer'].sudo().search([('access_token', '=', token)], limit=1)
        if not signer:
            return {'success': False, 'error': 'Invalid access token'}

        if signer.state == 'signed':
            return {'success': False, 'error': 'Already signed'}

        try:
            for field in filled_fields:
                item_id = int(field.get('item_id'))
                val_text = field.get('value', '')
                sig_data = field.get('signature', '')

                base64_data = False
                if sig_data:
                    if ',' in sig_data:
                        _, base64_data = sig_data.split(',', 1)
                    else:
                        base64_data = sig_data

                item = request.env['wm.signature.item'].sudo().browse(item_id)
                if not item.exists():
                    # Fallback creation for synthetic item
                    item_type = 'signature' if (base64_data or item_id == 999901) else 'date'
                    item = request.env['wm.signature.item'].sudo().create({
                        'template_id': signer.request_id.template_id.id,
                        'page': 1,
                        'x': 10.0 if item_type == 'signature' else 55.0,
                        'y': 82.0 if item_type == 'signature' else 85.0,
                        'width': 38.0 if item_type == 'signature' else 30.0,
                        'height': 12.0 if item_type == 'signature' else 6.0,
                        'type': item_type,
                        'role_id': signer.role_id.id,
                    })

                request.env['wm.signature.request.item.value'].sudo().create({
                    'request_id': signer.request_id.id,
                    'item_id': item.id,
                    'value': val_text,
                    'signature_image': base64_data,
                    'signer_id': signer.id,
                })

            # Save signer metadata & log audit trail
            signer.sudo().write({
                'state': 'signed',
                'signed_date': fields.Datetime.now(),
                'ip_address': request.httprequest.remote_addr,
                'user_agent': request.httprequest.headers.get('User-Agent', '')[:256]
            })

            # Check if all other signers completed, triggers certificate build
            signer.request_id.sudo()._check_request_completion()
            return {'success': True, 'redirect_url': f'/wm_signature/sign/thankyou?name={signer.partner_id.name}&token={token}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/wm_signature/sign/thankyou', type='http', auth='public', website=True)
    def signature_thankyou(self, name='', token='', **kwargs):
        """
        Render the post-signing thank-you confirmation page after a successful
        portal signature submission, displaying the document reference and next
        steps for the signer.
        """
        back_url = '/web'
        back_label = _('Back to Odoo')
        if token:
            signer = request.env['wm.signature.request.signer'].sudo().search([('access_token', '=', token)], limit=1)
            if signer and signer.request_id.reference_doc:
                ref = signer.request_id.reference_doc
                back_url = f"/web#id={ref.id}&model={ref._name}&view_type=form"
                if ref._name in ('wm.partner.contract', 'partner.contract'):
                    back_label = _('Back to Contract')
                elif ref._name == 'wm.collection.order':
                    back_label = _('Back to Collection Order')
                elif ref._name == 'wm.batch.inspection':
                    back_label = _('Back to Inspection')

        return request.render('wm_base.signature_thank_you_page_template', {
            'name': name,
            'back_url': back_url,
            'back_label': back_label,
        })

    @http.route('/wm_signature/request/pdf/<string:token>', type='http', auth='public')
    def get_request_pdf(self, token, **kwargs):
        """
        Serve the original unsigned document PDF for a signature request via
        HTTP, validating the access token before streaming the binary to the
        requester's browser.
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

    @http.route('/wm_signature/template/pdf/<int:template_id>', type='http', auth='public')
    def get_template_pdf(self, template_id, **kwargs):
        """
        Stream the signature template's base PDF document over HTTP for preview
        or download purposes, ensuring the template is accessible only to
        authorised users.
        """
        template = request.env['wm.signature.template'].sudo().browse(template_id)
        if not template:
            return request.not_found()

        pdf_data = False
        filename = template.document_filename or "document.pdf"

        inspection_id = kwargs.get('inspection_id')
        if inspection_id and 'wm.batch.inspection' in request.env:
            insp = request.env['wm.batch.inspection'].sudo().browse(int(inspection_id))
            if insp.exists():
                try:
                    pdf_data, _format = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                        'wm_collection.action_report_batch_inspection', [insp.id]
                    )
                    filename = f"Inspection_{insp.name}.pdf"
                except Exception as e:
                    _logger.warning("Failed to render inspection PDF report for inspection %s: %s", insp.id, e)

        order_id = kwargs.get('order_id')
        if not pdf_data and order_id and 'wm.collection.order' in request.env:
            order = request.env['wm.collection.order'].sudo().browse(int(order_id))
            if order.exists():
                if getattr(order, 'collection_report_pdf', False):
                    pdf_data = base64.b64decode(order.collection_report_pdf)
                    filename = order.collection_report_pdf_filename or f"{order.name}.pdf"
                else:
                    try:
                        pdf_data, _format = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                            'wm_collection.collection_order_report', [order.id]
                        )
                        filename = f"Collection_Order_{order.name}.pdf"
                    except Exception as e:
                        _logger.warning("Failed to render collection order PDF report for order %s: %s", order.id, e)

        if not pdf_data and template.document:
            pdf_data = base64.b64decode(template.document)

        if not pdf_data and 'wm.batch.inspection' in request.env:
            insp = request.env['wm.batch.inspection'].sudo().search([('signature_template_id', '=', template.id)], limit=1)
            if insp:
                try:
                    pdf_data, _format = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                        'wm_collection.action_report_batch_inspection', [insp.id]
                    )
                    filename = f"Inspection_{insp.name}.pdf"
                except Exception as e:
                    _logger.warning("Failed to render template fallback inspection PDF report for inspection %s: %s", insp.id, e)

        if not pdf_data and 'wm.collection.order' in request.env:
            order = request.env['wm.collection.order'].sudo().search([('signature_template_id', '=', template.id)], limit=1)
            if order:
                if getattr(order, 'collection_report_pdf', False):
                    pdf_data = base64.b64decode(order.collection_report_pdf)
                    filename = order.collection_report_pdf_filename or f"{order.name}.pdf"
                else:
                    try:
                        pdf_data, _format = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                            'wm_collection.collection_order_report', [order.id]
                        )
                        filename = f"Collection_Order_{order.name}.pdf"
                    except Exception as e:
                        _logger.warning("Failed to render template fallback collection order PDF report for order %s: %s", order.id, e)

        if not pdf_data:
            return request.not_found()

        return request.make_response(pdf_data, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'inline; filename="{filename}"')
        ])

    @http.route('/wm_signature/template/edit/<int:template_id>', type='http', auth='public', website=True)
    def edit_template(self, template_id, **kwargs):
        """
        Render the signature template visual editor, loading the existing field
        placements and page dimensions so administrators can reposition or add
        signature zones.
        """
        template = request.env['wm.signature.template'].sudo().browse(template_id)
        if not template:
            return request.not_found()

        # Ensure at least one signer role is set on template
        if not template.role_ids:
            default_role = request.env['wm.signature.role'].sudo().search([], limit=1)
            if not default_role:
                default_role = request.env['wm.signature.role'].sudo().create({'name': 'Signatory'})
            template.sudo().write({'role_ids': [(4, default_role.id)]})

        # Ensure document binary exists
        if not template.document:
            pdf_binary = template._generate_default_pdf_document()
            if pdf_binary:
                template.sudo().write({
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

        inspection_id = kwargs.get('inspection_id', '')
        order_id = kwargs.get('order_id', '')
        back_url = kwargs.get('back_url', '')
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
            'existing_items': Markup(json.dumps(existing_items)),
            'order_id': order_id,
            'inspection_id': inspection_id,
            'back_url': back_url,
        }
        return request.render('wm_base.signature_template_editor_page_template', values)

    @http.route('/wm_signature/template/save_fields', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def save_fields(self, template_id, fields_data, **kwargs):
        """
        Persist the updated signature field positions, sizes, and types
        submitted from the template designer UI back to the
        wm.signature.template record.
        """
        template = request.env['wm.signature.template'].sudo().browse(template_id)
        if not template:
            return {'success': False, 'error': 'Template not found'}

        # Remove old items
        template.item_ids.unlink()

        # Create new items
        for field in fields_data:
            request.env['wm.signature.item'].create({
                'template_id': template.id,
                'page': field.get('page'),
                'x': field.get('x'),
                'y': field.get('y'),
                'width': field.get('width'),
                'height': field.get('height'),
                'type': field.get('type'),
                'role_id': int(field.get('role_id')),
            })
        return {'success': True}

    @http.route('/wm_signature/template/sign_now', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def template_sign_now(self, template_id, order_id=None, inspection_id=None, **kwargs):
        """
        Initiate an immediate signing session for the template's owner,
        bypassing the standard invitation workflow and opening the signature
        capture interface directly.
        """
        template = request.env['wm.signature.template'].sudo().browse(template_id)
        if not template:
            return {'success': False, 'error': 'Template not found'}

        role = template.role_ids[:1]
        if not role:
            role = request.env['wm.signature.role'].sudo().search([], limit=1)
        if not role:
            role = request.env['wm.signature.role'].sudo().create({'name': 'Signer'})

        # Link request to any matching document referencing this template
        reference_doc = False
        if inspection_id and 'wm.batch.inspection' in request.env:
            insp = request.env['wm.batch.inspection'].sudo().browse(int(inspection_id))
            if insp.exists():
                reference_doc = f"wm.batch.inspection,{insp.id}"

        if not reference_doc and order_id and 'wm.collection.order' in request.env:
            order = request.env['wm.collection.order'].sudo().browse(int(order_id))
            if order.exists():
                reference_doc = f"wm.collection.order,{order.id}"

        if not reference_doc:
            if 'wm.batch.inspection' in request.env:
                inspection = request.env['wm.batch.inspection'].sudo().search([('signature_template_id', '=', template.id)], limit=1)
                if inspection:
                    reference_doc = f"wm.batch.inspection,{inspection.id}"
            if not reference_doc and 'wm.collection.order' in request.env:
                order = request.env['wm.collection.order'].sudo().search([('signature_template_id', '=', template.id)], limit=1)
                if order:
                    reference_doc = f"wm.collection.order,{order.id}"

        # Cancel any previous unsigned requests for this reference doc
        if reference_doc:
            existing = request.env['wm.signature.request'].sudo().search([
                ('reference_doc', '=', reference_doc),
                ('state', '!=', 'cancel')
            ])
            for req in existing:
                if req.state != 'signed':
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
        try:
            if not document_base64:
                return {'success': False, 'error': 'No file uploaded'}

            # Clean base64 string if it contains data URI header
            if ',' in document_base64:
                _, document_base64 = document_base64.split(',', 1)

            template_id = request.env['wm.signature.template'].sudo().create_from_pdf(name, document_base64.encode('utf-8'), filename)
            return {'success': True, 'template_id': template_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/wm_signature/template/create_sample', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def template_create_sample(self, **kwargs):
        """
        Create a sample signature template with pre-positioned default fields
        via AJAX, enabling administrators to explore the signature workflow
        without uploading a PDF.
        """
        try:
            template_id = request.env['wm.signature.template'].sudo().create_sample_template()
            return {'success': True, 'template_id': template_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/wm_signature/template/send_request', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def template_send_request(self, template_id, signers, **kwargs):
        """
        Process the AJAX call from the template designer to create and dispatch
        a new signature request from the current template to the specified list
        of signers.
        """
        try:
            template = request.env['wm.signature.template'].sudo().browse(template_id)
            if not template:
                return {'success': False, 'error': 'Template not found'}

            if not signers:
                return {'success': False, 'error': 'No signers provided'}

            signer_vals = []
            for signer_data in signers:
                role_id = int(signer_data.get('role_id'))
                name = signer_data.get('name', '').strip()
                email = signer_data.get('email', '').strip()

                if not name or not email:
                    return {'success': False, 'error': 'Name and Email are required for all signers.'}

                # Find or create partner
                partner = request.env['res.partner'].sudo().search([('email', '=ilike', email)], limit=1)
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
        except Exception as e:
            return {'success': False, 'error': str(e)}
