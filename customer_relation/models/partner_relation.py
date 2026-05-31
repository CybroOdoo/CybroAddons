# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreerag PM (<odoo@cybrosys.com>)
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
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PartnerRelation(models.Model):
    _name = 'partner.relation'
    _description = 'Partner Relation Mapping'

    contact_id = fields.Many2one(
        'res.partner',
        string='Primary Contact',
        required=True,
        ondelete='cascade'
    )
    relation_contact_id = fields.Many2one(
        'res.partner',
        string='Related Contact',
        required=True,
        ondelete='cascade'
    )
    relation_type_id = fields.Many2one(
        'relation.type',
        string='Relation Type',
        required=True
    )
    reverse_relation_type_id = fields.Many2one(
        'relation.type',
        string='Reverse Relation Type',
        required=True
    )

    # Display-only related info
    relation_email = fields.Char(
        related='relation_contact_id.email',
        string='Email',
        store=False
    )
    relation_phone = fields.Char(
        related='relation_contact_id.phone',
        string='Phone',
        store=False
    )
    relation_mobile = fields.Char(
        related='relation_contact_id.mobile',
        string='Mobile',
        store=False
    )
    relation_avatar = fields.Binary(
        related='relation_contact_id.avatar_128',
        string='Avatar',
        store=False
    )
    relation_name = fields.Char(
        related='relation_contact_id.name',
        string='Related Name',
        store=False
    )

    _sql_constraints = [
        (
            'unique_partner_relation',
            'unique(contact_id, relation_contact_id, relation_type_id)',
            _('This relationship already exists.')
        ),
    ]

    @api.constrains('contact_id', 'relation_contact_id')
    def _check_self_relation(self):
        """Prevent a contact from being related to itself."""
        for rec in self:
            if rec.contact_id and rec.relation_contact_id and rec.contact_id == rec.relation_contact_id:
                raise ValidationError(
                    _("A contact cannot have a relation with itself."))

    def _find_symmetric_reverse_relation(self):
        """Find the corresponding reciprocal relation record(s) based on current fields."""
        self.ensure_one()
        reverse_type = self.reverse_relation_type_id

        if not reverse_type:
            return self.env['partner.relation']

        # Find the record where the contacts are swapped and the type is the reciprocal type
        return self.search([
            ('contact_id', '=', self.relation_contact_id.id),
            ('relation_contact_id', '=', self.contact_id.id),
            ('relation_type_id', '=', reverse_type.id)
        ], limit=1)

    @api.model
    def create(self, vals):
        """Create reciprocal relation if reverse_type exists and prevents recursion."""
        # Use context to prevent infinite recursion
        if self.env.context.get('no_reverse_creation'):
            return super().create(vals)
        record = super().create(vals)
        reverse_type = record.reverse_relation_type_id
        # If a reverse type is selected by the user
        if reverse_type:
            existing_reverse = self.search([
                ('contact_id', '=', record.relation_contact_id.id),
                ('relation_contact_id', '=', record.contact_id.id),
                ('relation_type_id', '=', reverse_type.id)
            ], limit=1)
            if not existing_reverse:
                # Create the reciprocal relation, ensuring symmetry:
                # 1. The reverse record's relation_type_id is the original's reverse_relation_type_id.
                # 2. The reverse record's reverse_relation_type_id is the original's relation_type_id.
                self.with_context(no_reverse_creation=True).create({
                    'contact_id': record.relation_contact_id.id,
                    'relation_contact_id': record.contact_id.id,
                    'relation_type_id': reverse_type.id,
                    'reverse_relation_type_id': record.relation_type_id.id
                    # Maintain symmetry
                })
        return record

    # OVERRIDE WRITE: To handle updates and maintain symmetry
    def write(self, vals):
        """Handles updates, primarily by deleting and recreating the reciprocal if key fields change."""
        # Use context to prevent infinite recursion
        if self.env.context.get('no_reverse_update'):
            return super().write(vals)

        # Fields that affect the identity or symmetry of the reciprocal record
        key_fields = ['contact_id', 'relation_contact_id',
                      'relation_type_id', 'reverse_relation_type_id']

        if any(field in vals for field in key_fields):
            for record in self:
                # 1. Find and unlink the *old* reciprocal before applying the write
                old_inverse = record._find_symmetric_reverse_relation()
                old_inverse.with_context(no_reverse_unlink=True).unlink()

                # Apply the write operation to the original record
                super(PartnerRelation, record).write(vals)

                # 2. Re-create the *new* reciprocal based on the updated record values
                reverse_type = record.reverse_relation_type_id

                if reverse_type:
                    # Create the new inverse record
                    self.with_context(no_reverse_creation=True).create({
                        'contact_id': record.relation_contact_id.id,
                        'relation_contact_id': record.contact_id.id,
                        'relation_type_id': reverse_type.id,
                        'reverse_relation_type_id': record.relation_type_id.id
                    })
            return True

        return super().write(vals)

    # OVERRIDE UNLINK: To handle deletion and maintain symmetry
    def unlink(self):
        """Delete reciprocal relation."""
        # Use context to prevent infinite recursion
        if not self.env.context.get('no_reverse_unlink'):
            # Find and unlink the reciprocal records
            for record in self:
                reverse_record = record._find_symmetric_reverse_relation()
                # Use context to prevent infinite loop
                reverse_record.with_context(no_reverse_unlink=True).unlink()

        return super().unlink()

    def open_related_contact(self):
        """
            Open the related contact in form view.

            :return: Action to open the linked res.partner record.
            :rtype: dict
            """
        self.ensure_one()
        return {
            'name': _('Contact'),
            'view_mode': 'form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'res_id': self.relation_contact_id.id,
        }
