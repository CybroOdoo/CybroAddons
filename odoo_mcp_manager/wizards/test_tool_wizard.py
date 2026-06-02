import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from .. import utils

_TYPE_DEFAULTS = {
    'string': '',
    'integer': 0,
    'number': 0.0,
    'boolean': False,
    'array': [],
    'object': {},
}


class AiTestToolWizard(models.TransientModel):
    """
    Wizard for interactively testing an AI tool from the Odoo UI.

    Pre-fills a JSON parameter template from the tool's input schema and
    executes the tool inside a savepoint so the result can be inspected
    without committing any side-effects.
    """

    _name = 'ai.test.tool.wizard'
    _description = 'Test AI Tool Wizard'

    tool_id = fields.Many2one('ai.tool', string='Tool', required=True)
    requires_model = fields.Boolean(compute='_compute_requires_model')
    model_id = fields.Many2one(
        'ir.model',
        string='Odoo Model',
        domain=[('transient', '=', False)],
        help="Select an installed Odoo model. The technical name will be injected as the 'model' parameter.",
    )
    params_json = fields.Text(string='Parameters (JSON)', default='{}')
    result = fields.Text(string='Execution Result', readonly=True)

    @api.depends('tool_id')
    def _compute_requires_model(self) -> None:
        """Detect whether the selected tool expects a 'model' parameter."""
        for rec in self:
            rec.requires_model = False
            if not (rec.tool_id and rec.tool_id.input_schema):
                continue
            try:
                schema = json.loads(rec.tool_id.input_schema)
                required = schema.get('required', [])
                props = schema.get('properties', {})
                rec.requires_model = 'model' in required or 'model' in props
            except json.JSONDecodeError:
                pass

    @api.onchange('model_id')
    def _onchange_model_id(self) -> None:
        """Inject the selected model's technical name into the params JSON."""
        if not self.model_id:
            return
        try:
            params = json.loads(self.params_json or '{}')
        except json.JSONDecodeError:
            params = {}
        params['model'] = self.model_id.model
        self.params_json = json.dumps(params, indent=4)

    @api.model
    def default_get(self, field_names: list) -> dict:
        """Pre-populate the tool and build a parameter template from its schema."""
        res = super().default_get(field_names)
        tool_id = self._context.get('default_tool_id') or self._context.get('active_id')
        if tool_id:
            res['tool_id'] = tool_id
            tool = self.env['ai.tool'].browse(tool_id)
            res['params_json'] = self._build_param_template(tool)
        return res

    def _build_param_template(self, tool) -> str:
        """Build a clean JSON template dict from the tool's input schema."""
        if not tool.input_schema:
            return '{}'
        try:
            schema = json.loads(tool.input_schema)
            props = schema.get('properties', {})
            required = schema.get('required', [])
            template = {}
            for key in required:
                if key in props:
                    template[key] = _TYPE_DEFAULTS.get(props[key].get('type', 'string'), '')
            for key, prop in props.items():
                if key not in template:
                    template[key] = prop.get(
                        'default', _TYPE_DEFAULTS.get(prop.get('type', 'string'), '')
                    )
            return json.dumps(template, indent=4)
        except json.JSONDecodeError:
            return '{}'

    def action_execute(self) -> dict:
        """Execute the tool inside a savepoint and store the result for display."""
        self.ensure_one()
        try:
            params = json.loads(self.params_json)
        except json.JSONDecodeError as e:
            raise UserError(_('Invalid JSON parameters: %s') % str(e))

        try:
            with self.env.cr.savepoint():
                res = self.tool_id.execute(params)
            self.result = utils.dumps(res) if isinstance(res, (dict, list)) else str(res)
        except Exception as e:
            self.result = _('Error: Tool Execution Failed: %s') % str(e)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.test.tool.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
