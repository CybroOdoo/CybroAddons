# Odoo Vibe Coding Assistant

**Chat with AI to generate downloadable Odoo 19 modules.**

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__


---

## Quick Start

### 1 — Install the module

```bash
odoo-bin -i vibe_coding_assistant -d your_database
```

### 2 — Get a free API key

The default provider is **Google Gemini** on the free tier.

1. Visit [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API key**
3. Copy the key (starts with `AIza…`)

### 3 — Configure your provider

1. Open **Vibe Coding → My AI Settings**
2. Click **New**
3. Select **Google Gemini**, leave the model as `gemini-2.0-flash`
4. Paste your API key
5. Toggle **Active** on → Save

### 4 — Generate a module

1. Open **Vibe Coding → Chat**
2. Click **+ New** and type your request, for example:

   > *Create a module for brand management in product*

3. The assistant generates the module (typically 10–30 seconds)
4. Click **View Files** to browse the generated code
5. Click **Download Module** to save the ZIP

### 5 — Install the generated module

```bash
unzip product_brand.zip -d /path/to/addons/
odoo-bin -i product_brand -d your_database
```

---

## Supported Providers

| Provider        | Free tier | Default model              | Key URL                                       |
|-----------------|-----------|----------------------------|-----------------------------------------------|
| Google Gemini   | ✅ Yes     | `gemini-2.0-flash`         | https://aistudio.google.com/apikey            |
| Anthropic Claude | ❌ No     | `claude-sonnet-4-5-20250929` | https://console.anthropic.com               |
| OpenAI          | ❌ No      | `gpt-4o-mini`              | https://platform.openai.com/api-keys          |

All API keys are stored per-user and never shared across accounts.

---

## What Gets Generated

The AI produces a full Odoo 19 addon following all conventions:

| File                              | Description                              |
|-----------------------------------|------------------------------------------|
| `__manifest__.py`                 | Module metadata and dependency list      |
| `__init__.py`                     | Python package init                      |
| `models/*.py`                     | ORM models with fields, compute methods  |
| `views/*.xml`                     | List, form, search views (`<list>` not `<tree>`) |
| `security/ir.model.access.csv`   | Access control rules                     |
| `data/*.xml`                      | Seed data / automations (when requested) |
| `report/*.xml`                    | QWeb reports (when requested)            |
| `wizards/*.py` + `*.xml`          | TransientModel wizards (when requested)  |

Every generated module is validated before download:
- Manifest key presence and version format
- Python syntax check (all `.py` files)
- XML well-formedness (all `.xml` files)
- `models/__init__.py` imports each model file
- `security/ir.model.access.csv` present when models exist

---

## Tips for Better Results

| Goal                              | Prompt example                                                   |
|-----------------------------------|------------------------------------------------------------------|
| Simple CRUD module                | *Create a module to manage customer complaints*                  |
| Module extending an existing one  | *Add a "Brand" field to product.template with a new brand model* |
| Module with a report              | *Create a stock valuation report module*                         |
| Module with automation            | *Create a module that auto-emails the customer 3 days after delivery* |

---

## Security

- API keys are stored in `ai.provider.user.config` and protected by Odoo record rules — each user can only read their own keys.
- API keys are never logged.
- Generated modules are also per-user via record rules.
- The download endpoint re-checks ownership before streaming bytes.

---

## Troubleshooting

**"The AI returned an invalid response"**
The model occasionally drifts from the JSON format. Rephrase the request
and try again. Adding more specifics (e.g., *"with a Many2one to res.partner"*)
often helps.

**Validation errors on the module card**
Click **View Files**, review the error banner at the top of the file tree,
then download and fix the flagged files manually. Common issues: missing
`security/ir.model.access.csv`, XML syntax errors in views.

**Timeout / slow response**
Gemini free-tier requests can take 20–40 seconds for complex modules.
The typing indicator shows while the AI is working.
