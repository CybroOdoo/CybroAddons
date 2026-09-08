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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WmSignatureRequestWizard(models.TransientModel):
    """Wizard to configure signers and dispatch digital signature request invitations."""
    _name = 'wm.signature.request.wizard'
    _description = 'Signature Request Wizard'

    template_id = fields.Many2one('wm.signature.template', string='Template', required=True)
    res_model = fields.Char(string='Resource Model', required=True)
    res_id = fields.Integer(string='Resource ID', required=True)
    signer_ids = fields.One2many('wm.signature.request.wizard.signer', 'wizard_id', string='Signers')

    @api.onchange('template_id')
    def _onchange_template_id(self):
        """
        Populate the signer list and document preview from the selected
        signature template when the template field changes, reducing manual
        configuration in the request wizard.
        """
        if not self.template_id:
            self.signer_ids = [(5, 0, 0)]
            return

        signer_vals = []
        # Prepopulate partners if record is a collection order
        record = self.env[self.res_model].browse(self.res_id) if self.res_model and self.res_id and self.res_model in self.env else None

        for role in self.template_id.role_ids:
            partner = self.env['res.partner']
            if record and record._name == 'wm.collection.order':
                role_name_lower = (role.name or '').lower()
                if 'customer' in role_name_lower or 'client' in role_name_lower:
                    partner = record.partner_id
                elif 'driver' in role_name_lower or 'operator' in role_name_lower:
                    partner = record.driver_id

            signer_vals.append((0, 0, {
                'role_id': role.id,
                'partner_id': partner.id or False,
                'email': partner.email or '',
            }))

        self.signer_ids = [(5, 0, 0)] + signer_vals

    def action_confirm(self):
        """
        Validate that all required signers and the document template are
        selected, then create the wm.signature.request record and dispatch the
        signing invitation emails.
        """
        self.ensure_one()
        if not self.signer_ids:
            raise UserError(_("You must configure at least one signer."))

        for line in self.signer_ids:
            if not line.partner_id:
                raise UserError(_("Please select a partner for role: %s") % line.role_id.name)
            if not line.email:
                raise UserError(_("Email is required for signer: %s") % line.partner_id.name)

        # Create the Signature Request
        request = self.env['wm.signature.request'].create({
            'template_id': self.template_id.id,
            'reference_doc': f"{self.res_model},{self.res_id}",
            'signer_ids': [(0, 0, {
                'partner_id': line.partner_id.id,
                'role_id': line.role_id.id,
                'email': line.email,
            }) for line in self.signer_ids],
        })

        # Send the request
        request.action_send()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Signature Request Sent'),
                'message': _('The signature request %s has been created and sent.') % request.name,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }


class WmSignatureRequestWizardSigner(models.TransientModel):
    """Signer participant line in the digital signature request invitation wizard."""
    _name = 'wm.signature.request.wizard.signer'
    _description = 'Signature Request Wizard Signer'

    wizard_id = fields.Many2one('wm.signature.request.wizard', string='Wizard', ondelete='cascade')
    role_id = fields.Many2one('wm.signature.role', string='Role', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    email = fields.Char(string='Email')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Auto-populate the signer's email address from the selected partner
        contact record when the partner field changes in the signature request wizard.
        """
        if self.partner_id:
            self.email = self.partner_id.email
