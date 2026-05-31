from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AiModel(models.Model):
    """A specific AI model belonging to a provider, classified by its primary capability."""

    _name = 'ai.model'
    _description = 'AI Model'
    _order = 'provider_id, name'

    name = fields.Char(required=True, help='Internal name of the model (e.g. gpt-4o)')
    provider_id = fields.Many2one(
        'ai.provider', string='Provider', required=True, ondelete='cascade'
    )
    service = fields.Selection(related='provider_id.service', store=True)
    model_use = fields.Selection([
        ('chat', 'Chat Completion'),
        ('embedding', 'Text Embedding'),
        ('multimodal', 'Multimodal / Vision'),
    ], required=True, default='chat', help='Primary capability of the model')
    default = fields.Boolean(
        string='Default for Use',
        default=False,
        help='Use this as the default model for this provider and use case.',
    )
    active = fields.Boolean(default=True)
    setup_guide = fields.Html(compute='_compute_setup_guide', string='Configuration Guide')

    _SETUP_GUIDES = {
        ('openai', 'chat'): """
            <div class="o_field_html">
                <h3>OpenAI — Chat Completion Model</h3>
                <p>Chat completion models generate conversational responses and power the MCP tools and <code>ask_ai</code> / <code>analyze_records</code> tools.</p>
                <h4>Recommended Models</h4>
                <ul>
                    <li><code>gpt-4o</code> — Best overall: multimodal, fast, 128k context. Use for complex reasoning and tool use.</li>
                    <li><code>gpt-4o-mini</code> — Cost-efficient, fast. Ideal for high-volume simple tasks.</li>
                    <li><code>gpt-4-turbo</code> — High intelligence, large context, suited for document analysis.</li>
                    <li><code>gpt-3.5-turbo</code> — Budget option. Less capable but very cheap.</li>
                </ul>
                <h4>Configuration Tips</h4>
                <ul>
                    <li>Set <strong>Default for Use</strong> to make this model the automatic choice for chat tasks on this provider.</li>
                    <li>Model names must match exactly — use IDs from <strong>platform.openai.com/docs/models</strong>.</li>
                    <li>For structured outputs or function calling, use <code>gpt-4o</code> or <code>gpt-4-turbo</code>.</li>
                </ul>
            </div>
        """,
        ('openai', 'embedding'): """
            <div class="o_field_html">
                <h3>OpenAI — Text Embedding Model</h3>
                <p>Embedding models convert text into numeric vectors used for semantic search, similarity matching, and RAG (Retrieval-Augmented Generation).</p>
                <h4>Recommended Models</h4>
                <ul>
                    <li><code>text-embedding-3-small</code> — 1536 dimensions, low cost, fast. Best for most use cases.</li>
                    <li><code>text-embedding-3-large</code> — 3072 dimensions, higher accuracy at a higher cost.</li>
                    <li><code>text-embedding-ada-002</code> — Legacy model, still supported but superseded by v3.</li>
                </ul>
                <h4>Configuration Tips</h4>
                <ul>
                    <li>Set this as the default <strong>Embedding</strong> model so AI resources use it for vector indexing.</li>
                    <li>The embedding dimension must match whatever vector store you pair it with.</li>
                </ul>
            </div>
        """,
        ('openai', 'multimodal'): """
            <div class="o_field_html">
                <h3>OpenAI — Multimodal / Vision Model</h3>
                <p>Multimodal models can process both text and images in a single prompt — useful for document scanning, image analysis, and OCR-like tasks.</p>
                <h4>Recommended Models</h4>
                <ul>
                    <li><code>gpt-4o</code> — Native vision support, fast image understanding.</li>
                    <li><code>gpt-4-turbo</code> — Strong vision capabilities with a large context window.</li>
                </ul>
                <h4>Configuration Tips</h4>
                <ul>
                    <li>Pass image URLs or base64-encoded images in the <code>content</code> array of the message.</li>
                    <li>Not all OpenAI models support vision — only use <code>gpt-4o</code> or <code>gpt-4-turbo</code> for image tasks.</li>
                </ul>
            </div>
        """,
        ('anthropic', 'chat'): """
            <div class="o_field_html">
                <h3>Anthropic — Chat Completion Model</h3>
                <p>Claude models excel at nuanced reasoning, long-context understanding, coding, and safe instruction following.</p>
                <h4>Recommended Models</h4>
                <ul>
                    <li><code>claude-opus-4-7</code> — Most capable Claude model. Best for complex multi-step reasoning.</li>
                    <li><code>claude-sonnet-4-6</code> — Balanced speed and intelligence. Recommended default.</li>
                    <li><code>claude-haiku-4-5-20251001</code> — Fastest and most compact. Use for high-throughput simpler tasks.</li>
                </ul>
                <h4>Configuration Tips</h4>
                <ul>
                    <li>Use the exact model ID from <strong>docs.anthropic.com/en/docs/about-claude/models</strong>.</li>
                    <li>Claude has a 200k token context window on Opus and Sonnet — ideal for analyzing large Odoo datasets.</li>
                    <li>Claude does not support embedding — use <strong>Chat Completion</strong> use type only.</li>
                </ul>
            </div>
        """,
        ('anthropic', 'multimodal'): """
            <div class="o_field_html">
                <h3>Anthropic — Multimodal / Vision Model</h3>
                <p>Claude Sonnet and Opus support image understanding alongside text, enabling document analysis and visual reasoning.</p>
                <h4>Recommended Models</h4>
                <ul>
                    <li><code>claude-sonnet-4-6</code> — Strong vision capabilities, recommended for image + text tasks.</li>
                    <li><code>claude-opus-4-7</code> — Highest accuracy for complex visual reasoning.</li>
                </ul>
                <h4>Configuration Tips</h4>
                <ul>
                    <li>Pass images as base64 or via URL in the <code>content</code> blocks of the message.</li>
                    <li>Supported image formats: JPEG, PNG, GIF, WebP.</li>
                </ul>
            </div>
        """,
        ('ollama', 'chat'): """
            <div class="o_field_html">
                <h3>Ollama — Chat Completion Model</h3>
                <p>Ollama runs open-source models locally. The model name here must exactly match the name shown by <code>ollama list</code>.</p>
                <h4>Popular Models to Pull</h4>
                <ul>
                    <li><code>llama3</code> — Meta Llama 3 8B. Strong general reasoning, fully open weights.</li>
                    <li><code>llama3:70b</code> — Larger Llama 3, requires significant VRAM (≥48 GB).</li>
                    <li><code>mistral</code> — Mistral 7B. Fast, efficient, good instruction following.</li>
                    <li><code>gemma3</code> — Google Gemma 3. Compact and capable.</li>
                    <li><code>phi4</code> — Microsoft Phi-4. Excellent for reasoning tasks at small size.</li>
                    <li><code>qwen2.5</code> — Alibaba Qwen 2.5. Strong multilingual performance.</li>
                </ul>
                <h4>How to Pull a Model</h4>
                <p>Run in terminal: <code>ollama pull llama3</code><br/>Then click <strong>Fetch Models</strong> on the provider to import it here automatically.</p>
                <h4>Configuration Tips</h4>
                <ul>
                    <li>Use quantized variants (e.g. <code>llama3:8b-instruct-q4_K_M</code>) to reduce memory usage.</li>
                    <li>Ensure the Ollama service is running before making requests: <code>ollama serve</code>.</li>
                </ul>
            </div>
        """,
        ('ollama', 'embedding'): """
            <div class="o_field_html">
                <h3>Ollama — Text Embedding Model</h3>
                <p>Ollama supports embedding models for local semantic search and RAG pipelines — no internet required.</p>
                <h4>Recommended Models</h4>
                <ul>
                    <li><code>nomic-embed-text</code> — 768 dimensions. Best general-purpose local embedding model.</li>
                    <li><code>mxbai-embed-large</code> — 1024 dimensions. High accuracy, larger footprint.</li>
                    <li><code>all-minilm</code> — 384 dimensions. Very small and fast, suited for simple similarity tasks.</li>
                </ul>
                <h4>How to Pull</h4>
                <p><code>ollama pull nomic-embed-text</code></p>
            </div>
        """,
        ('ollama', 'multimodal'): """
            <div class="o_field_html">
                <h3>Ollama — Multimodal / Vision Model</h3>
                <p>Some Ollama models support image inputs alongside text for local vision tasks.</p>
                <h4>Recommended Models</h4>
                <ul>
                    <li><code>llava</code> — LLaVA 7B/13B. Pioneer open-source vision-language model.</li>
                    <li><code>llava:34b</code> — Larger LLaVA for higher accuracy (requires ~24 GB VRAM).</li>
                    <li><code>moondream</code> — Very small (1.8B) vision model, extremely fast on CPU.</li>
                    <li><code>bakllava</code> — Mistral-based vision model, strong OCR and diagram understanding.</li>
                </ul>
                <h4>How to Pull</h4>
                <p><code>ollama pull llava</code></p>
            </div>
        """,
        ('custom', 'chat'): """
            <div class="o_field_html">
                <h3>Custom Provider — Chat Completion Model</h3>
                <p>Enter the model identifier exactly as expected by your custom OpenAI-compatible endpoint.</p>
                <h4>Common Examples</h4>
                <ul>
                    <li><strong>LM Studio:</strong> Use the model file name shown in the LM Studio UI (e.g. <code>lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF</code>).</li>
                    <li><strong>Groq:</strong> <code>llama-3.3-70b-versatile</code>, <code>mixtral-8x7b-32768</code>, <code>gemma2-9b-it</code>.</li>
                    <li><strong>Together AI:</strong> <code>meta-llama/Llama-3-70b-chat-hf</code>, <code>mistralai/Mixtral-8x7B-Instruct-v0.1</code>.</li>
                    <li><strong>Azure OpenAI:</strong> Use the <em>deployment name</em> you created in Azure, not the base model name.</li>
                    <li><strong>vLLM:</strong> The model name passed with <code>--model</code> at server start.</li>
                </ul>
                <h4>Configuration Tips</h4>
                <ul>
                    <li>Check your provider's documentation for the exact model ID format.</li>
                    <li>If <strong>Fetch Models</strong> does not work, add the model name manually.</li>
                </ul>
            </div>
        """,
        ('custom', 'embedding'): """
            <div class="o_field_html">
                <h3>Custom Provider — Text Embedding Model</h3>
                <p>Enter the embedding model ID supported by your OpenAI-compatible endpoint.</p>
                <h4>Common Examples</h4>
                <ul>
                    <li><strong>Groq:</strong> Check Groq docs — embedding support may vary.</li>
                    <li><strong>Together AI:</strong> <code>togethercomputer/m2-bert-80M-8k-retrieval</code>.</li>
                    <li><strong>vLLM:</strong> Any HuggingFace embedding model served with <code>--model</code>.</li>
                </ul>
            </div>
        """,
        ('custom', 'multimodal'): """
            <div class="o_field_html">
                <h3>Custom Provider — Multimodal / Vision Model</h3>
                <p>If your custom endpoint supports vision, enter the model ID and send image content in the standard OpenAI format.</p>
                <h4>Common Examples</h4>
                <ul>
                    <li><strong>Together AI:</strong> <code>meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo</code>.</li>
                    <li><strong>vLLM:</strong> <code>llava-hf/llava-1.5-7b-hf</code> (served locally with vision support).</li>
                </ul>
            </div>
        """,
        ('google', 'chat'): """
            <div class="o_field_html">
                <h3>Google Gemini — Chat Completion Model</h3>
                <p>Gemini models are fetched automatically via the API. The model name here must match the short ID (e.g. <code>gemini-2.5-flash</code>, not <code>models/gemini-2.5-flash</code>).</p>
                <h4>Recommended Models</h4>
                <ul>
                    <li><code>gemini-2.5-flash</code> — Fast, 1M context, best cost-efficiency.</li>
                    <li><code>gemini-2.5-pro</code> — Most capable, complex reasoning.</li>
                    <li><code>gemini-2.0-flash</code> — Low latency, high throughput.</li>
                </ul>
            </div>
        """,
        ('google', 'embedding'): """
            <div class="o_field_html">
                <h3>Google Gemini — Text Embedding Model</h3>
                <ul>
                    <li><code>text-embedding-004</code> — Google's latest embedding model.</li>
                    <li><code>embedding-001</code> — Legacy embedding model.</li>
                </ul>
            </div>
        """,
        ('google', 'multimodal'): """
            <div class="o_field_html">
                <h3>Google Gemini — Multimodal / Vision Model</h3>
                <p>All Gemini 2.x models natively support image input alongside text.</p>
                <ul>
                    <li><code>gemini-2.0-flash</code> — Fastest vision model.</li>
                    <li><code>gemini-2.5-pro</code> — Highest accuracy for visual tasks.</li>
                </ul>
            </div>
        """,
    }

    _sql_constraints = [
        ('name_provider_unique', 'unique(name, provider_id)', 'Model name must be unique per provider!'),
    ]

    @api.constrains('default', 'provider_id', 'model_use', 'active')
    def _check_unique_default(self) -> None:
        """Ensure only one active default model exists per provider and use case."""
        for record in self:
            if record.default and record.active:
                other_defaults = self.search([
                    ('id', '!=', record.id),
                    ('provider_id', '=', record.provider_id.id),
                    ('model_use', '=', record.model_use),
                    ('default', '=', True),
                    ('active', '=', True),
                ])
                if other_defaults:
                    raise ValidationError(
                        _('Only one active default model is allowed per provider and use case (%s).')
                        % record.model_use
                    )

    @api.depends('service', 'model_use')
    def _compute_setup_guide(self) -> None:
        """Populate the HTML setup guide based on service + model_use combination."""
        for rec in self:
            rec.setup_guide = self._SETUP_GUIDES.get(
                (rec.service, rec.model_use),
                '<p>Select a provider and use type to see the configuration guide.</p>',
            )

    def chat(self, messages: list, **kwargs) -> str:
        """Delegate a chat completion request to the owning provider using this model's name."""
        self.ensure_one()
        return self.provider_id.chat(messages, model=self.name, **kwargs)

    def embedding(self, text: str, **kwargs) -> list:
        """Delegate an embedding request to the owning provider using this model's name."""
        self.ensure_one()
        return self.provider_id.embedding(text, model=self.name, **kwargs)
