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
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PartnerRelation(models.Model):
    """Model to manage partner relation mappings."""
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

    relation_email = fields.Char(
        related='relation_contact_id.email',
        string='Email',
    )
    relation_phone = fields.Char(
        related='relation_contact_id.phone',
        string='Phone',
    )
    relation_avatar = fields.Binary(
        related='relation_contact_id.avatar_128',
        string='Avatar',
    )
    relation_name = fields.Char(
        related='relation_contact_id.name',
        string='Related Name',
    )

    _unique_partner_relation = models.Constraint(
        'unique(contact_id, relation_contact_id, relation_type_id)',
        'This relationship already exists.'
    )

    @api.constrains('contact_id', 'relation_contact_id')
    def _check_self_relation(self):
        """Prevent a contact from being related to itself."""
        for rec in self:
            if (rec.contact_id and rec.relation_contact_id
                    and rec.contact_id == rec.relation_contact_id):
                raise ValidationError(
                    self.env._("A contact cannot have a relation with itself."))

    def _find_symmetric_reverse_relation(self):
        """Find corresponding reciprocal relation record(s)."""
        self.ensure_one()
        return self.search([
            ('contact_id', '=', self.relation_contact_id.id),
            ('relation_contact_id', '=', self.contact_id.id),
            ('relation_type_id', '=', self.reverse_relation_type_id.id)
        ], limit=1)

    @api.model_create_multi
    def create(self, vals_list):
        """Create reciprocal relation and prevent recursion."""
        records = super().create(vals_list)
        if self.env.context.get('no_reverse_creation'):
            return records

        reciprocal_vals = []
        for record in records:
            existing_reverse = self.search([
                ('contact_id', '=', record.relation_contact_id.id),
                ('relation_contact_id', '=', record.contact_id.id),
                ('relation_type_id', '=', record.reverse_relation_type_id.id)
            ], limit=1)
            if not existing_reverse:
                reciprocal_vals.append({
                    'contact_id': record.relation_contact_id.id,
                    'relation_contact_id': record.contact_id.id,
                    'relation_type_id': record.reverse_relation_type_id.id,
                    'reverse_relation_type_id': record.relation_type_id.id
                })
        if reciprocal_vals:
            self.with_context(no_reverse_creation=True).create(reciprocal_vals)
        return records

    def write(self, vals):
        """Handle updates and maintain symmetry of reciprocal relations."""
        if self.env.context.get('no_reverse_update'):
            return super().write(vals)

        key_fields = ['contact_id', 'relation_contact_id',
                      'relation_type_id', 'reverse_relation_type_id']

        if any(field in vals for field in key_fields):
            for record in self:
                old_inverse = record._find_symmetric_reverse_relation()
                old_inverse.with_context(no_reverse_unlink=True).unlink()

                super(PartnerRelation, record).write(vals)

                self.with_context(no_reverse_creation=True).create({
                    'contact_id': record.relation_contact_id.id,
                    'relation_contact_id': record.contact_id.id,
                    'relation_type_id': record.reverse_relation_type_id.id,
                    'reverse_relation_type_id': record.relation_type_id.id
                })
            return True
        return super().write(vals)

    def unlink(self):
        """Delete reciprocal relation."""
        if not self.env.context.get('no_reverse_unlink'):
            for record in self:
                reverse_record = record._find_symmetric_reverse_relation()
                reverse_record.with_context(no_reverse_unlink=True).unlink()
        return super().unlink()

    def open_related_contact(self):
        """
        Open the related contact in form view.

        :return: Action to open the linked res.partner record or False.
        :rtype: dict or bool
        """
        record = self[:1]
        if not record and self.env.context.get('active_model') == self._name:
            active_id = self.env.context.get('active_id')
            if active_id:
                record = self.browse(active_id)

        partner_id = record.relation_contact_id.id if record else False
        if not partner_id:
            partner_id = self.env.context.get('default_relation_contact_id')

        if not partner_id:
            return False

        return {
            'name': self.env._('Contact'),
            'view_mode': 'form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'res_id': partner_id,
        }
