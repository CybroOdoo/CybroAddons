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
from odoo import fields, models


class WmSignatureSignNowWizard(models.TransientModel):
    """Wizard to execute an immediate digital signature capture on a target document."""
    _name = 'wm.signature.sign.now.wizard'
    _description = 'Sign Now Wizard'

    name = fields.Char(string='Document Name', required=True)
    document = fields.Binary(string='Document (PDF)', required=True, attachment=True)
    document_filename = fields.Char(string='Document Filename')

    def action_upload_and_design(self):
        """
        Open the signature template designer with the uploaded PDF pre-loaded,
        allowing the user to position signature and date fields
        before sending the request.
        """
        self.ensure_one()
        # Find or create roles
        roles = self.env['wm.signature.role'].search([])
        if not roles:
            roles = self.env['wm.signature.role'].create({'name': 'Signer'})

        # Create a new template
        template = self.env['wm.signature.template'].create({
            'name': self.name,
            'document': self.document,
            'document_filename': self.document_filename,
            'role_ids': [(6, 0, roles.ids)],
        })

        # Return URL action to redirect to template designer
        return {
            'type': 'ir.actions.act_url',
            'url': f'/wm_signature/template/edit/{template.id}?sign_now=1',
            'target': 'self',
        }
