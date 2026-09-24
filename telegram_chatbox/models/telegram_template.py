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
import re
from odoo import api, models, fields

class TelegramTemplateVariable(models.Model):
    """Model to define variables used within Telegram templates."""
    _name = 'telegram.template.variable'
    _description = 'Telegram Template Variable'

    template_id = fields.Many2one(
        'telegram.template',
        string="Template",
        ondelete='cascade',
        help="Telegram template to which this variable belongs."
    )

    name = fields.Char(
        string='Variable',
        help="Variable name used in the template, such as 'customer_name'. Do not include curly braces."
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        help="Model from which the variable value will be fetched."
    )

    field_id = fields.Many2one(
        'ir.model.fields',
        string='Field',
        domain="[('model_id', '=', model_id)]",
        required=True,
        ondelete='cascade',
        help="Field whose value will be substituted into the template variable."
    )


class TelegramTemplate(models.Model):
    """Model for Telegram templates."""
    _name = 'telegram.template'
    _description = 'Telegram Template'

    name = fields.Char(
        string='Name',
        help="Name of the Telegram message template."
    )

    message = fields.Text(
        string='Message',
        help="Message content. You can use dynamic variables such as {{customer_name}}."
    )

    header_attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Template Static Header",
        copy=False,
        help="Files that will be sent along with the message whenever this template is used."
    )

    dynamic_variable_ids = fields.One2many(
        'telegram.template.variable',
        'template_id',
        string="Dynamic Variables",
        help="Variables available for dynamic value substitution in the template message."
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        help="Business model associated with this template. Dynamic variables will be fetched from records of this model."
    )

    @api.onchange('message')
    def _onchange_message(self):
        """
        Synchronize dynamic variables with placeholders found in the message.

        This method is triggered whenever the `message` field changes. It
        extracts placeholder variables in the format `{{variable_name}}`
        from the message content and updates the related dynamic variable
        records accordingly."""

        if not self.message:
            self.dynamic_variable_ids = [(5, 0, 0)]
            return

        placeholders = set(re.findall(r"\{\{(\w+)\}\}", self.message))
        
        commands = []
        
        for rec in self.dynamic_variable_ids:
            if rec.name not in placeholders:
                commands.append((2, rec.id, 0))
                
        existing_names = set(self.dynamic_variable_ids.mapped('name'))
        new_names = placeholders - existing_names
        
        for name in new_names:
            commands.append((0, 0, {'name': name}))
            
        if commands:
            self.dynamic_variable_ids = commands

    def render_template(self, message, values=None, record=None):
        """
        Render a Telegram message template by replacing dynamic placeholders
        with actual values.
        This method populates template variables from either the provided
        values dictionary or from fields mapped through dynamic variables on
        the given record. Placeholders in the format `{{variable_name}}` are
        replaced with their corresponding values.
        """
        if values is None:
            values = {}
        
        if record:
            for var in self.dynamic_variable_ids:
                if var.name and var.model_id.model == record._name and var.field_id:
                    field_val = getattr(record, var.field_id.name, "")
                    if hasattr(field_val, 'display_name') and field_val:
                        field_val = field_val.display_name
                    values[var.name] = field_val or ""

        def replace(match):
            """
            Replace a template placeholder with its corresponding value.
            """
            key = match.group(1)
            return str(values.get(key, match.group(0)))  # fallback if missing

        return re.sub(r"\{\{(\w+)\}\}", replace, message)
