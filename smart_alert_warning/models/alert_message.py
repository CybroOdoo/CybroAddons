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
import ast
import re
import uuid

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# Domain operators and the Python comparison they map to in the view's
# invisible expression, which the web client evaluates with py.js.
COMPARISON_OPERATORS = {
    '=': '==', '==': '==', '!=': '!=', '<>': '!=',
    '<': '<', '>': '>', '<=': '<=', '>=': '>=',
    'in': 'in', 'not in': 'not in',
}
FIELD_NAME_RE = re.compile(r'^[a-z_][a-z0-9_]*$')


class AlertMessage(models.Model):
    """Alert banner shown on the form view of any model, for the records
    matching a domain and, optionally, only to one group."""
    _name = 'alert.message'
    _description = 'Alert Message'

    name = fields.Char(required=True, help='Name of the alert')
    document_type_id = fields.Many2one(
        'ir.model', required=True,
        ondelete='cascade', help='Select the type of the Document')
    group_id = fields.Many2one(
        'res.groups',
        help='Only show the alert to the users of this group')
    alert_messages = fields.Char(
        string='Alert Message', required=True,
        help='Alert message that will show in the view.')
    type = fields.Selection(
        [('alert-primary', 'Alert Primary'),
         ('alert-secondary', 'Alert Secondary'),
         ('alert-success', 'Alert Success'),
         ('alert-danger', 'Alert Danger'),
         ('alert-warning', 'Alert Warning'),
         ('alert-info', 'Alert Info')],
        required=True, help='Type of alert message')
    model_name = fields.Char(
        related='document_type_id.model',
        help='Technical name of the document type')
    field_filter = fields.Char(
        string='Filter', default='[]',
        help='Show the alert only on the records matching these conditions')
    view_id = fields.Many2one(
        'ir.ui.view', required=True, ondelete='cascade',
        domain="[('model', '=', model_name), ('type', '=', 'form')]",
        help='Form view on which the alert is shown')
    new_view_id = fields.Many2one(
        'ir.ui.view', string='Created View', readonly=True, copy=False,
        ondelete='set null',
        help='View created when the alert is applied, which adds the alert '
             'to the form view')
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done'), ('cancelled', 'Cancelled')],
        default='draft', copy=False,
        help='Only applied alerts, in the Done state, show on the form view')

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        """Clear the view and the filter, which belong to the old model."""
        self.view_id = self.env['ir.ui.view']
        self.field_filter = '[]'

    def action_apply(self):
        """Create the inherited view adding the alert to the form view."""
        for alert in self.filtered(lambda rec: rec.state == 'draft'):
            view = alert._create_alert_view()
            alert.write({'new_view_id': view.id, 'state': 'done'})

    def action_cancel(self):
        """Remove the alert from the form view."""
        self.new_view_id.sudo().unlink()
        self.state = 'cancelled'

    def action_reset_draft(self):
        """Reset the alert to draft so it can be changed and applied again."""
        self.state = 'draft'

    def unlink(self):
        """Remove the views of the applied alerts with them."""
        self.new_view_id.sudo().unlink()
        return super().unlink()

    def _create_alert_view(self):
        """Create the view adding the alert above the sheet of the form view.

        The alert is hidden with an ``invisible`` expression on the records
        that do not match the filter, so it shows and hides live while the
        record is edited. Views are only open to the Settings administrators,
        so it is created as superuser for the alert admins."""
        self.ensure_one()
        attrs = {'role': 'alert', 'class': f'alert {self.type} o_smart_alert'}
        if self.group_id:
            attrs['groups'] = self._get_group_xml_id()
        condition = self._get_filter_expression()
        if condition:
            attrs['invisible'] = f'not ({condition})'
        xpath = etree.Element('xpath', expr='//sheet', position='before')
        alert = etree.SubElement(xpath, 'div', attrs)
        alert.text = self.alert_messages
        try:
            return self.env['ir.ui.view'].sudo().create({
                'name': f'{self.type}.alert.{self.view_id.name}.{self.id}',
                'type': 'form',
                'model': self.model_name,
                'priority': 99,
                'inherit_id': self.view_id.id,
                'mode': 'extension',
                'arch_base': etree.tostring(xpath, encoding='unicode'),
            })
        except ValidationError as error:
            raise UserError(self.env._(
                "The alert can't be added to the view %(view)s: %(error)s",
                view=self.view_id.display_name, error=error)) from error

    def _get_group_xml_id(self):
        """Return the XML id of the group, which the ``groups`` attribute of
        the view needs. Groups created from the interface have none, so one
        is created in ``__export__``, like exporting records does."""
        group = self.group_id
        xml_id = group.get_external_id()[group.id]
        if not xml_id:
            name = f'res_groups_{group.id}_{uuid.uuid4().hex[:8]}'
            self.env['ir.model.data'].sudo().create({
                'module': '__export__', 'name': name,
                'model': group._name, 'res_id': group.id,
            })
            xml_id = f'__export__.{name}'
        return xml_id

    def _get_filter_expression(self):
        """Return the filter as a Python expression for the view, or an
        empty string when there is no filter."""
        try:
            domain = ast.literal_eval(self.field_filter or '[]')
        except (ValueError, SyntaxError) as error:
            raise UserError(self.env._(
                "The filter is not valid. It must use fixed values, not "
                "expressions such as the current date.")) from error
        if not domain:
            return ''
        if not isinstance(domain, (list, tuple)):
            raise UserError(self.env._("The filter is not valid."))
        tokens = list(domain)
        expressions = []
        while tokens:
            expressions.append(self._parse_domain(tokens))
        return ' and '.join(f'({expr})' for expr in expressions) \
            if len(expressions) > 1 else expressions[0]

    def _parse_domain(self, tokens):
        """Consume one term of a prefix-notation domain from ``tokens`` and
        return it as a Python expression."""
        token = tokens.pop(0) if tokens else None
        if token in ('&', '|'):
            left = self._parse_domain(tokens)
            right = self._parse_domain(tokens)
            operator = 'and' if token == '&' else 'or'
            return f'({left}) {operator} ({right})'
        if token == '!':
            return f'not ({self._parse_domain(tokens)})'
        if isinstance(token, (list, tuple)) and len(token) == 3:
            return self._leaf_to_expression(*token)
        raise UserError(self.env._("The filter is not valid."))

    def _leaf_to_expression(self, field_name, operator, value):
        """Return the condition ``(field_name, operator, value)`` as a Python
        expression on the values of the record in the form view."""
        if (field_name, operator, value) in ((1, '=', 1), (0, '=', 1)):
            return 'True' if field_name else 'False'
        field = self.env[self.model_name]._fields.get(field_name) \
            if isinstance(field_name, str) and FIELD_NAME_RE.match(field_name) \
            else None
        if not field:
            raise UserError(self.env._(
                "The filter can only use fields of %(model)s itself, not "
                "\"%(field)s\".", model=self.document_type_id.name,
                field=field_name))
        if field.groups:
            raise UserError(self.env._(
                "The filter can't use %(field)s, which only some users can "
                "read.", field=field.string))
        if isinstance(value, tuple):
            value = list(value)
        if value is False and operator in ('=', '==', '!=', '<>'):
            # "is set" / "is not set", for any field type
            return field_name if operator in ('!=', '<>') else f'not {field_name}'
        if field.type in ('one2many', 'many2many'):
            raise UserError(self.env._(
                "On %(field)s, the filter can only check whether it is set or "
                "not set.", field=field.string))
        if operator in ('in', 'not in') and not isinstance(value, list):
            raise UserError(self.env._("The filter is not valid."))
        if field.type == 'many2one' and not all(
                isinstance(item, int)
                for item in (value if isinstance(value, list) else [value])):
            # The form view only knows the id of the record, not its name
            raise UserError(self.env._(
                "On %(field)s, the filter can only compare with selected "
                "records, not with a name.", field=field.string))
        if operator in COMPARISON_OPERATORS:
            return f'{field_name} {COMPARISON_OPERATORS[operator]} {value!r}'
        if operator in ('like', 'not like', 'ilike', 'not ilike') \
                and field.type in ('char', 'text', 'html', 'selection') \
                and isinstance(value, str):
            text, search = f'({field_name} or "")', repr(value)
            if operator.endswith('ilike'):
                text, search = f'{text}.lower()', repr(value.lower())
            negate = 'not ' if operator.startswith('not') else ''
            return f'{search} {negate}in {text}'
        raise UserError(self.env._(
            "The operator \"%(operator)s\" can't be used in an alert filter.",
            operator=operator))
