import jinja2

from odoo import models, fields, api
from odoo.http import request

_PLATFORM_CONFIGS = {
    'claude_desktop': {
        'config': (
            '{\n'
            '  "mcpServers": {\n'
            '    "odoo-ai-hub": {\n'
            '      "type": "stdio",\n'
            '      "command": "npx",\n'
            '      "args": ["-y", "mcp-remote", "{{ url }}", "--header",'
            ' "Authorization: Bearer {{ key }}"],\n'
            '      "env": {"MCP_TRANSPORT": "streamable-http"}\n'
            '    }\n'
            '  }\n'
            '}'
        ),
        'instruction': (
            'Paste this config into your Claude Desktop config file, then restart Claude Desktop.\n\n'
            '  macOS   →  ~/Library/Application Support/Claude/claude_desktop_config.json\n'
            '  Windows →  %APPDATA%\\Claude\\claude_desktop_config.json\n'
            '  Linux   →  ~/.config/Claude/claude_desktop_config.json\n\n'
            'If the file already has an "mcpServers" key, merge the "odoo-ai-hub" block into it.'
        ),
    },
    'claude_cloud': {
        'config': '{{ url }}?api_key={{ key }}',
        'instruction': (
            'Connect via claude.ai → Settings → Integrations:\n\n'
            '  1. Click "Add custom integration"\n'
            '  2. Paste the MCP Server URL from the box below — the API key is already\n'
            '     embedded in the URL as ?api_key=..., so no separate header is needed.\n'
            '  3. Leave the "Authorization" header field blank.\n'
            '  4. Click Save, then start a new conversation — the Odoo tools will appear.\n\n'
            'Alternative (Authorization header instead of URL param):\n'
            '  • MCP Server URL : {{ url }}\n'
            '  • Header Name    : Authorization\n'
            '  • Header Value   : Bearer {{ key }}'
        ),
    },
    'claude_code': {
        'config': (
            "claude mcp add-json odoo-ai-hub '{\n"
            '  "type": "stdio",\n'
            '  "command": "npx",\n'
            '  "args": ["-y", "mcp-remote", "{{ url }}",\n'
            '           "--header", "Authorization: Bearer {{ key }}"],\n'
            '  "env": {"MCP_TRANSPORT": "streamable-http"}\n'
            "}'"
        ),
        'instruction': (
            'Copy the full command from the box below and paste it into your Linux terminal.\n\n'
            'The command registers the Odoo MCP server with Claude Code CLI.\n'
            'Run it once — no file editing required.\n\n'
            'Requirements:\n'
            '  • Node.js / npx  →  node --version\n'
            '  • Claude Code CLI →  claude --version\n\n'
            'After running, verify the server is registered:\n'
            '  claude mcp list\n\n'
            'Then restart Claude Code to activate the tools.'
        ),
    },
    'codex': {
        'config': (
            '{\n'
            '  "mcpServers": {\n'
            '    "odoo-ai-hub": {\n'
            '      "type": "stdio",\n'
            '      "command": "npx",\n'
            '      "args": ["-y", "mcp-remote", "{{ url }}", "--header",'
            ' "Authorization: Bearer {{ key }}"],\n'
            '      "env": {"MCP_TRANSPORT": "streamable-http"}\n'
            '    }\n'
            '  }\n'
            '}'
        ),
        'instruction': (
            'Add this config to: ~/.codex/config.json\n\n'
            'Requirements:\n'
            '  • Node.js + npx installed\n'
            '  • Codex CLI installed\n\n'
            'Then start Codex — the Odoo AI Hub tools will be listed automatically.'
        ),
    },
}

_PLATFORM_DEFAULT_NAMES = {
    'claude_desktop': 'Claude Desktop',
    'claude_cloud': 'Claude Cloud',
    'claude_code': 'Claude Code CLI',
    'codex': 'OpenAI Codex CLI',
}


class AiGenerateMcpKey(models.TransientModel):
    """Wizard that generates a new MCP API key and renders the platform-specific config snippet."""

    _name = 'ai.generate.mcp.key'
    _description = 'Generate MCP Key Wizard'

    name = fields.Char(string='Key Description', required=True, default='Claude Desktop')
    platform = fields.Selection([
        ('claude_desktop', 'Claude Desktop'),
        ('claude_cloud', 'Claude Cloud (claude.ai)'),
        ('claude_code', 'Claude Code CLI'),
        ('codex', 'OpenAI Codex CLI'),
    ], string='Platform', required=True, default='claude_desktop',
       help='Select the AI platform where this MCP key will be used.')
    key = fields.Char(string='Generated Key', readonly=True)
    mcp_url = fields.Char(string='MCP Server URL', readonly=True)
    claude_config = fields.Text(string='Platform Configuration', readonly=True)
    setup_instruction = fields.Text(string='Setup Instructions', readonly=True)
    state = fields.Selection([
        ('input', 'Enter Description'),
        ('result', 'Key Generated'),
    ], default='input')

    @api.onchange('platform')
    def _onchange_platform(self) -> None:
        """Update the default key name and re-render templates when the platform changes."""
        if not self.platform:
            return
        if self.state == 'result' and self.key and self.mcp_url:
            self._render_templates(self.mcp_url, self.key)
        else:
            self.name = _PLATFORM_DEFAULT_NAMES.get(self.platform, 'My MCP Key')

    def _get_mcp_url(self) -> str:
        """Derive the MCP Server URL from the current HTTP request or system parameter."""
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'http://localhost:8069'
        ).rstrip('/')
        if request and request.httprequest:
            base_url = request.httprequest.host_url.rstrip('/')
        return f'{base_url}/mcp_gateway'

    def _render_templates(self, mcp_url: str, key: str) -> None:
        """Render the platform config snippet and setup instructions using Jinja2."""
        platform_data = _PLATFORM_CONFIGS.get(self.platform or 'claude_desktop')
        if not platform_data:
            return
        self.claude_config = jinja2.Template(platform_data['config']).render(
            url=mcp_url, key=key
        )
        self.setup_instruction = jinja2.Template(platform_data['instruction']).render(
            url=mcp_url, key=key
        )

    def action_generate(self) -> dict:
        """Generate a new API key, render the config snippet, and advance to the result step."""
        self.ensure_one()
        new_key_str = self.env['res.users.apikeys'].sudo()._generate('rpc', self.name, None)
        mcp_url = self._get_mcp_url()
        self._render_templates(mcp_url, new_key_str)
        self.write({'key': new_key_str, 'mcp_url': mcp_url, 'state': 'result'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.generate.mcp.key',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
