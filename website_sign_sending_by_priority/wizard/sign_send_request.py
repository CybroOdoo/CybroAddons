# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
from odoo import Command, models
from odoo.exceptions import ValidationError


class SignSendRequest(models.TransientModel):
    """Inheriting the model and a field"""
    _inherit = 'sign.send.request'

    def create_request(self):
        """Creating the request based on the signers"""
        template_id = self.template_id.id
        signers = [
            {'partner_id': signer.partner_id.id, 'role_id': signer.role_id.id,
             'priority': signer.priority} for signer in self.signer_ids]
        # Check for duplicate priorities
        priority_set = set()
        for signer in signers:
            if signer['priority'] in priority_set:
                raise ValidationError("Duplicate priority found. Please set")
            priority_set.add(signer['priority'])
        # Sort signers based on priority
        signers = sorted(signers, key=lambda x: x['priority'])
        sign_request = self.env['sign.request'].create({
            'template_id': template_id,
            'request_item_ids': [Command.create({
                'partner_id': signer['partner_id'],
                'role_id': signer['role_id'],
                'state': 'sent',
            }) for signer in signers],
            'reference': self.filename,
            'subject': self.subject,
            'message': self.message,
            'message_cc': self.message_cc,
            'attachment_ids': [Command.set(self.attachment_ids.ids)],
        })
        sign_request.message_subscribe(partner_ids=self.follower_ids.ids)
        return sign_request

    def send_request(self):
        """Sending the request to the corresponding signers based on
        the priority """
        request = self.create_request()
        signers = [
            {'partner_id': signer.partner_id.id, 'role_id': signer.role_id.id,
             'priority': signer.priority} for signer in self.signer_ids]
        for item in request.request_item_ids:
            for each in signers:
                if each['partner_id'] == item.partner_id.id and each['priority'] == 1:
                    request.send_signature_accesses()
                    item.is_mail_sent = True
        current_signer = self.signer_ids.filtered(
            lambda s: s.partner_id == self.env.user.partner_id)
        if current_signer.priority == 1:
            if self.activity_id:
                self._activity_done()
                return {'type': 'ir.actions.act_window_close'}
            return request.go_to_document()
        else:
            return request.go_to_document()
