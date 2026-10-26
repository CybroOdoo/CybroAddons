# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3), Version 3.
#
################################################################################
from xml.etree import ElementTree

from odoo import api, fields, models
from odoo.exceptions import AccessError


class IrUiView(models.Model):
    """Extend views with controlled form-label editing."""

    _inherit = 'ir.ui.view'

    @api.model
    def edit_xml_field_label(self, name, view, old_label, _input_field_name,
                             value, field_name):
        """Update a field label and record the change for authorized users."""
        if not self.env.user.is_edit_field_label:
            raise AccessError("You are not allowed to edit field labels.")

        if value and value[-1] == "\\":
            value = value[:-1]

        views = self.env['ir.ui.view'].search([
            ('model', '=', name), ('type', '=', view),
        ])
        model_name = self.env['ir.model'].search([
            ('model', '=', name),
        ], limit=1).name

        for view_id in views:
            root = ElementTree.fromstring(view_id.arch)
            view_updated = False

            for label in root.iter('label'):
                if label.get('string') != old_label:
                    continue
                if label.get('nolabel'):
                    preceding_div_labels = root.findall(
                        ".//label[@for='%s']" % field_name
                    )
                    for label_tag in preceding_div_labels:
                        label_tag.set('string', value)
                label.set('string', value)
                view_updated = True

            for field in root.iter('field'):
                if field.get('name') != field_name:
                    continue
                if field.get('nolabel'):
                    preceding_div_labels = root.findall(
                        ".//label[@for='%s']" % field_name
                    )
                    for label_tag in preceding_div_labels:
                        label_tag.set('string', value)
                if field.get('string'):
                    field.set('string', value)
                view_updated = True

            if view_updated:
                view_id.sudo().write({
                    'arch': ElementTree.tostring(root, encoding='unicode'),
                })

        field_obj = self.env['ir.model.fields'].search([
            ('model', '=', name), ('name', '=', field_name),
        ], limit=1)
        if not field_obj:
            return False

        field_obj.sudo().write({'field_description': value})
        self.env['label.history'].sudo().create({
            'user_id': self.env.user.id,
            'date': fields.Datetime.now(),
            'model': model_name,
            'old_label': old_label,
            'new_label': value,
        })
        return True
