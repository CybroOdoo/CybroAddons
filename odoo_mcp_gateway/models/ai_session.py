import uuid

from odoo import models, fields, api


class AiSession(models.Model):
    """Tracks an active MCP protocol session for a single Odoo user."""

    _name = 'ai.session'
    _description = 'AI Session'

    session_id = fields.Char(
        required=True,
        index=True,
        default=lambda self: str(uuid.uuid4()),
    )
    user_id = fields.Many2one(
        'res.users',
        string='Odoo User',
        required=True,
        default=lambda self: self.env.user,
    )
    state = fields.Selection([
        ('not_initialized', 'Not Initialized'),
        ('initializing', 'Initializing'),
        ('initialized', 'Initialized'),
        ('terminated', 'Terminated'),
    ], default='not_initialized', required=True)
    protocol_version = fields.Char(string='MCP Version')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('session_id_unique', 'unique(session_id)', 'Session ID must be unique!'),
    ]

    _VALID_TRANSITIONS = {
        'not_initialized': ['initializing'],
        'initializing': ['initialized'],
        'initialized': ['terminated'],
    }

    def transition_to(self, state: str) -> None:
        """Move the session to *state* if the transition is allowed; silently ignore invalid ones."""
        self.ensure_one()
        if state in self._VALID_TRANSITIONS.get(self.state, []):
            self.state = state

    def terminate(self) -> None:
        """Mark the session inactive and set its state to terminated."""
        self.write({'active': False, 'state': 'terminated'})

    @api.model
    def create_new_session(self, user_id: int) -> 'AiSession':
        """Create and return a new session record for the given Odoo user ID."""
        return self.create({
            'user_id': user_id,
            'state': 'not_initialized',
        })
