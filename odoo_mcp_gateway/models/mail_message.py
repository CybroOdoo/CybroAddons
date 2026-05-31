import json
import logging

from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    """Extends mail.message with AI conversation role metadata and structured data storage."""

    _inherit = 'mail.message'

    ai_role = fields.Selection([
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('tool', 'Tool'),
        ('system', 'System'),
    ], string='AI Role', index=True, help='Role of this message in an AI conversation')
    body_json = fields.Text(
        string='Structured Data (JSON)',
        help='Stores tool calls or structured results',
    )

    def get_tool_calls(self) -> list:
        """Return the list of tool calls embedded in an assistant message's body_json."""
        if self.ai_role == 'assistant' and self.body_json:
            try:
                return json.loads(self.body_json).get('tool_calls', [])
            except json.JSONDecodeError:
                _logger.debug('MailMessage: body_json is not valid JSON on message %s', self.id)
        return []

    def execute_tool_call(
        self, _tool_call_id: str, tool_name: str, parameters: dict
    ) -> object:
        """
        Execute a named tool and post the result as a child tool message.

        Args:
            _tool_call_id: Identifier for the tool call (reserved for future threading).
            tool_name: Technical name of the ai.tool record to invoke.
            parameters: Input parameters for the tool.

        Returns:
            The raw result returned by the tool.
        """
        tool = self.env['ai.tool'].search([('name', '=', tool_name)], limit=1)
        if not tool:
            result = _('Error: Tool %s not found') % tool_name
        else:
            try:
                result = tool.execute(parameters)
            except Exception as e:
                result = _('Error: %s') % str(e)

        self.env['mail.message'].create({
            'model': self.model,
            'res_id': self.res_id,
            'ai_role': 'tool',
            'body': str(result),
            'parent_id': self.id,
        })
        return result
