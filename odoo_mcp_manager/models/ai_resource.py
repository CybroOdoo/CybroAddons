import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AiResource(models.Model):
    """An Odoo model exposed as a readable MCP resource under the odoo:// URI scheme."""

    _name = 'ai.resource'
    _description = 'MCP Exposed Resource'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Display Name', required=True)
    model_name = fields.Char(
        string='Model',
        required=True,
        help='Technical Odoo model name, e.g. res.partner',
    )
    description = fields.Text(
        string='Description',
        help='Shown to MCP clients when they list available resources',
    )
    active = fields.Boolean(default=True)

    uri = fields.Char(string='Resource URI', compute='_compute_uri', store=False)
    record_count = fields.Integer(
        string='Records', compute='_compute_record_count', store=False
    )
    model_exists = fields.Boolean(
        string='Model Available', compute='_compute_model_exists', store=False
    )

    @api.depends('model_name')
    def _compute_uri(self) -> None:
        """Build the odoo:// URI from the model's technical name."""
        for rec in self:
            rec.uri = f'odoo://{rec.model_name}' if rec.model_name else ''

    def _compute_model_exists(self) -> None:
        """Set model_exists to True when the model is installed in this environment."""
        for rec in self:
            rec.model_exists = bool(rec.model_name and rec.model_name in self.env)

    def _compute_record_count(self) -> None:
        """Count records in the linked model; falls back to 0 on any error."""
        for rec in self:
            try:
                rec.record_count = (
                    self.env[rec.model_name].sudo().search_count([])
                    if rec.model_name in self.env
                    else 0
                )
            except Exception:
                _logger.debug(
                    'AiResource: could not count records for model %r', rec.model_name
                )
                rec.record_count = 0

    def mcp_definition(self) -> dict:
        """Return the MCP resource descriptor dict for this record."""
        self.ensure_one()
        return {
            'uri': f'odoo://{self.model_name}',
            'name': self.name,
            'description': self.description or '',
            'mimeType': 'application/json',
        }
