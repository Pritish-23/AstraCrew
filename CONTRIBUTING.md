# Contributing to AstraCrew

Thank you for your interest in contributing to AstraCrew! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites
- Python 3.11 or higher
- Git
- Virtual environment tool (venv or uv)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/Pritish-23/AstraCrew.git
cd AstraCrew

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY if needed
```

## Project Structure

```
AstraCrew/
├── schemas/          # Pydantic data contracts
├── target/           # Three target surfaces (MOCK, RAG, AGENTIC)
├── probes/           # Attack probe implementations
├── evaluation/       # Dual-gate evaluation system
├── tools/            # CrewAI tool wrappers
├── remediation/      # Prompt patching and middleware generation
├── reports/          # PDF report generation
├── tests/            # Test suite
├── config/           # CrewAI agent/task configurations
├── orchestrator.py   # Main orchestration logic
├── crew.py           # CrewAI team assembly
├── main.py           # CLI interface
└── app.py            # Streamlit dashboard
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_phase1.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Linting and Formatting

```bash
# Run linter
ruff check .

# Auto-fix issues
ruff check . --fix

# Check specific files
ruff check probes/ evaluation/
```

### Running the Application

```bash
# Deterministic mode (no API key needed)
python main.py --mode deterministic --export-pdf reports/audit.pdf

# With live LLM
python main.py --mode deterministic --live --model gpt-4o-mini

# CrewAI agentic mode (requires API key)
python main.py --mode crew

# Launch dashboard
streamlit run app.py
```

## Adding New Probes

To add a new attack probe:

1. Choose the appropriate module:
   - `probes/injection_probes.py` - Direct prompt injection attacks
   - `probes/obfuscation_probes.py` - Encoding/obfuscation bypasses
   - `probes/persona_probes.py` - Cognitive/social engineering
   - `probes/rag_probes.py` - RAG-specific attacks
   - `probes/agentic_probes.py` - Tool-calling exploits

2. Create a new probe class:

```python
from probes.base_probe import BaseProbe, ProbeRegistry

@ProbeRegistry.register
class MyNewProbe(BaseProbe):
    def __init__(self):
        super().__init__(
            probe_id="PRB-XXX",  # Sequential ID
            name="Descriptive Name",
            owasp_category="OWASP-LLM0X-Category",
            severity="HIGH",  # CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL
            description="What this probe tests",
            applicable_targets=["MOCK"],  # or ["RAG"], ["AGENTIC"], or ["MOCK", "RAG", "AGENTIC"]
        )
    
    def build_payload(self, context: Dict[str, Any]) -> str:
        # Generate attack payload using context variables
        canary = context.get("canary_token", "CANARY_ASTRA_8829F")
        return f"Your attack payload here: {canary}"
```

3. Add tests in `tests/test_phase2.py` or create a new test file

4. Update README.md with the new probe in the OWASP coverage table

## Adding New Targets

To add a new target surface:

1. Create a new file in `target/` (e.g., `target/my_target.py`)

2. Implement the target interface:

```python
class MyTarget:
    def __init__(self, canary_token: str = "CANARY", use_live_llm: bool = False, model_name: str = "gpt-4o-mini"):
        self.canary_token = canary_token
        self.use_live_llm = use_live_llm
        self.model_name = model_name
        # Initialize your target
    
    def process_query(self, user_query: str) -> str:
        # Handle the query and return response
        pass
```

3. Update `tools/target_client.py` to include the new target

4. Add corresponding tests

## Code Style Guidelines

- Use type hints for all function parameters and return values
- Follow PEP 8 style guide
- Maximum line length: 110 characters (as configured in pyproject.toml)
- Use docstrings for all classes and public methods
- Keep functions focused and single-purpose

## Testing Guidelines

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names (test_<what>_<when>_<then>)
- Mock external API calls when possible
- Mark tests requiring API keys with `@pytest.mark.skipif`

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### PR Requirements

- All tests must pass
- Code must pass linting (`ruff check .`)
- Include tests for new features
- Update documentation as needed
- Describe changes clearly in PR description

## Security

If you discover a security vulnerability, please email pritish@example.com instead of opening a public issue.

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Documentation improvements
- General questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
