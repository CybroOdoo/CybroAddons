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
from odoo import fields, http
from odoo.http import request
from odoo.tools.translate import _

class PharmaVendorPortal(http.Controller):
    """Controller for handling public vendor access to qualification questionnaires."""

    def _render_questionnaire(self, qualification, access_token, error=None):
        """Render the questionnaire and, when needed, a submission error."""
        return request.render('pharma_vendor_qualification.portal_vendor_questionnaire', {
            'qualification': qualification,
            'access_token': access_token,
            'error': error,
        })

    def _check_access(self, qualification_id, access_token):
        """Validates the qualification record and token securely."""
        if not qualification_id or not access_token:
            return None
        # Must use sudo() to bypass record rules for the public user, relying strictly on the token
        qual_sudo = request.env['pharma.vendor.qualification'].sudo().browse(qualification_id)
        if not qual_sudo.exists() or qual_sudo.access_token != access_token:
            return None
        return qual_sudo

    @http.route(['/pharma/vendor/questionnaire/<int:qualification_id>'], type='http', auth="public", website=True)
    def vendor_questionnaire(self, qualification_id, access_token=None, **kwargs):
        """Renders the vendor qualification questionnaire form for external access."""
        qual_sudo = self._check_access(qualification_id, access_token)
        if not qual_sudo:
            return request.render('http_routing.403')

        return self._render_questionnaire(qual_sudo, access_token)

    @http.route(['/pharma/vendor/questionnaire/<int:qualification_id>/submit'], type='http', auth="public",
                        methods=['POST'], website=True, csrf=False)
    def vendor_questionnaire_submit(self, qualification_id, access_token=None, **post):
        """Handle vendor questionnaire submission and advance the workflow."""
        qual_sudo = self._check_access(qualification_id, access_token)
        if not qual_sudo:
            return request.render('http_routing.403')

        file_answer_values = {}
        for response in qual_sudo.response_ids.filtered(
                lambda response: response.answer_type == 'file'):
            uploaded_file = request.httprequest.files.get(f'answer_file_{response.id}')
            if not uploaded_file or not uploaded_file.filename:
                return self._render_questionnaire(
                    qual_sudo,
                    access_token,
                    _("A file is required for: %s", response.question_text),
                )

            content = uploaded_file.read()
            if not content:
                return self._render_questionnaire(
                    qual_sudo,
                    access_token,
                    _("A file is required for: %s", response.question_text),
                )
            file_answer_values[response.id] = {
                'answer_file': base64.b64encode(content),
                'answer_file_filename': uploaded_file.filename,
            }

        # Process the submitted responses
        for response in qual_sudo.response_ids:
            answer_type = response.question_id.answer_type
            if answer_type == 'yes_no':
                val = post.get(f'answer_yes_no_{response.id}')
                if val in ['True', 'False', 'yes', 'no']:
                    response.answer_yes_no = 'yes' if val in ('True', 'yes') else 'no'
            elif answer_type == 'text':
                val = post.get(f'answer_text_{response.id}')
                if val is not None:
                    response.answer_text = val
            elif answer_type == 'number':
                val = post.get(f'answer_number_{response.id}')
                if val:
                    try:
                        response.answer_number = float(val)
                    except ValueError:
                        pass # Ignore invalid numbers
            elif answer_type == 'file':
                response.write(file_answer_values[response.id])

        # Set submission date
        qual_sudo.submission_date = fields.Datetime.now()

        # Log action in chatter
        qual_sudo.message_post(body=_("Vendor has submitted the qualification questionnaire via the portal."))

        # Advance the workflow status if it was in 'questionnaire_sent'
        if qual_sudo.status == 'questionnaire_sent':
            qual_sudo.status = 'documents_received'

        # Send Notification to QA
        if qual_sudo.create_uid and qual_sudo.create_uid.email:
            template = request.env.ref('pharma_vendor_qualification.email_template_vendor_submission_notification',
                                       raise_if_not_found=False)
            if template:
                template.sudo().send_mail(qual_sudo.id, force_send=True)

        return request.render('pharma_vendor_qualification.portal_vendor_questionnaire_success', {
            'qualification': qual_sudo
        })
