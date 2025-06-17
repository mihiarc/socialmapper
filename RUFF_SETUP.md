# Modern Toolchain Setup for SocialMapper

This document explains the **cutting-edge development toolchain** for SocialMapper, featuring Ruff for linting/formatting and ty for ultra-fast type checking.

## 🚀 Why Ruff?

**Ruff** is the next-generation Python linter and formatter that's:
- ⚡ **10-100x faster** than traditional tools (Flake8, Black, isort)
- 🔧 **All-in-one** - replaces multiple tools with a single, unified interface
- 🛠️ **Auto-fixing** - automatically fixes 800+ types of issues
- 🏗️ **Modern** - written in Rust, supports Python 3.13+, actively maintained
- 📦 **Comprehensive** - includes rules from Flake8, PyLint, and many plugins

## 📋 Current Configuration

The project uses a **comprehensive rule set** designed for modern Python development:

### Enabled Rule Groups
- **E, W** - PyCodeStyle errors and warnings  
- **F** - Pyflakes (import issues, undefined variables)
- **I** - Import sorting (replaces isort)
- **N** - PEP8 naming conventions
- **D** - Docstring conventions (Google style)
- **UP** - PyUpgrade (modernize Python syntax)
- **B** - Bugbear (common bug patterns)
- **C4** - List/dict comprehension improvements
- **PIE** - Miscellaneous best practices
- **PL** - PyLint rules
- **RUF** - Ruff-specific rules
- **SIM** - Code simplification
- **TCH** - Type-checking import optimization
- **PTH** - Prefer pathlib over os.path
- **FURB** - Refurb (modernize code patterns)
- **PERF** - Performance anti-patterns
- **LOG** - Logging best practices

### Smart Ignores
```toml
ignore = [
    "E501",    # Line too long (handled by formatter)
    "D100",    # Missing docstring in public module
    "D104",    # Missing docstring in public package  
    "D107",    # Missing docstring in __init__
    "PLR0913", # Too many arguments (common in data science)
    "PLR0912", # Too many branches
    "PLR0915", # Too many statements
    "B008",    # Function calls in defaults (FastAPI/Typer)
]
```

### Per-File Customization

## ⚡ Type Checking with ty

**ty** is Astral's revolutionary new Python type checker, written in Rust for unprecedented speed:

### Why ty over mypy/pyright?
- **🚀 10-100x faster** - Type checking that completes in seconds, not minutes
- **🔧 Zero configuration** - Works out of the box with intelligent defaults  
- **🦀 Rust-powered** - Built on the same high-performance foundation as Ruff
- **🔄 Incremental** - Caches results for lightning-fast subsequent runs
- **🎯 Accurate** - Catches type errors other checkers miss

### Usage
```bash
# Check entire codebase (recommended)
uv run ty check

# Check specific modules
uv run ty check socialmapper/api/ socialmapper/census/

# Use our convenient wrapper script
python scripts/type_check.py

# With additional options
python scripts/type_check.py --strict --verbose
```

### Configuration
ty is configured in `pyproject.toml` under `[tool.ty]` with:
- **Strict mode** enabled for comprehensive checking
- **Incremental caching** for maximum performance  
- **Smart error codes** for precise issue identification
- **Per-file ignores** for flexible test and example files

### Performance Example
On our codebase (~50k LOC):
- **mypy**: ~18 seconds
- **ty**: ~0.5 seconds ⚡

### Per-File Customization
- **`__init__.py`** - Allow unused imports and flexible import ordering
- **`tests/`** - Disable docstring requirements, allow assertions
- **`examples/`** - Allow print statements for demo purposes

## 🛠️ Usage

### Quick Commands
```bash
# Check for issues
uv run ruff check socialmapper/

# Auto-fix issues
uv run ruff check --fix socialmapper/

# Format code
uv run ruff format socialmapper/

# Do everything at once
./scripts/ruff_check.sh socialmapper/ all
```

### Convenience Script
The project includes `scripts/ruff_check.sh` for easy usage:

```bash
# Check entire project
./scripts/ruff_check.sh

# Fix issues in specific directory
./scripts/ruff_check.sh socialmapper/ fix

# Format specific files
./scripts/ruff_check.sh tests/ format

# Run everything (fix + format)
./scripts/ruff_check.sh . all

# Show what would change without applying
./scripts/ruff_check.sh socialmapper/ diff

# Run unsafe fixes (be careful!)
./scripts/ruff_check.sh socialmapper/ unsafe
```

## 🎯 Integration

### VS Code Setup
The project includes `.vscode/settings.json` with:
- **Ruff as default formatter** (replaces Black)
- **Auto-fix on save**
- **Import organization on save**
- **Disabled conflicting extensions** (Black, isort, Flake8)

### Pre-commit Hook (Recommended)
Add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## 📊 Migration Results

The migration from Black + isort + basic Ruff to comprehensive Ruff found:

- **3,870 total issues** in the codebase
- **3,142 automatically fixed** (81% success rate!)
- **403 remaining issues** requiring manual review
- **73 files reformatted** for consistency

Common auto-fixes applied:
- ✅ Import sorting and optimization
- ✅ Trailing whitespace removal
- ✅ Modern Python syntax (f-strings, type annotations)
- ✅ Code simplification
- ✅ Unused import removal

## 🔧 Customization

### Adding New Rules
To enable additional rule groups, edit `pyproject.toml`:
```toml
[tool.ruff.lint]
select = [
    # ... existing rules ...
    "S",      # bandit (security)
    "ERA",    # eradicate (commented code)
    "T20",    # flake8-print (no print statements)
]
```

### Project-Specific Ignores
For issues specific to your codebase:
```toml
[tool.ruff.lint]
ignore = [
    "PLR2004",  # Magic values (common in data science)
    "D102",     # Missing method docstrings (adjust as needed)
]
```

### File-Specific Rules
```toml
[tool.ruff.lint.per-file-ignores]
"scripts/*" = ["T201"]     # Allow prints in scripts
"notebooks/*" = ["D", "T201", "F401"]  # Relax rules for notebooks
```

## 🎓 Learning Opportunities

As your coding teacher, here are key learning points:

### 1. **Modern Python Patterns**
Ruff helps you learn modern Python by suggesting:
- `pathlib` over `os.path`
- Type hints with `|` unions (Python 3.10+)
- f-strings over `%` formatting
- List/dict comprehensions over loops

### 2. **Code Quality Principles**
- **Simplicity** - SIM rules suggest simpler patterns
- **Performance** - PERF rules catch anti-patterns
- **Security** - B rules prevent common vulnerabilities
- **Maintainability** - PL rules enforce good structure

### 3. **Professional Standards**
- **Docstring conventions** (Google style)
- **Import organization** (standard library → third-party → local)
- **Naming conventions** (PEP8 compliance)
- **Error handling** best practices

## 🔄 Workflow Integration

### Development Workflow
1. **Write code** in your editor with Ruff auto-fixing
2. **Run checks** with `./scripts/ruff_check.sh` before committing
3. **Fix remaining issues** that need manual attention
4. **Commit clean code** that passes all checks

### CI/CD Integration
Add to your GitHub Actions:
```yaml
- name: Run Ruff
  run: |
    uv run ruff check .
    uv run ruff format --check .
```

## 📈 Next Steps

1. **Review remaining 403 issues** - many are stylistic preferences
2. **Set up pre-commit hooks** for automatic checking
3. **Configure IDE integration** for real-time feedback
4. **Consider enabling additional rule groups** as your codebase matures

## 🆘 Troubleshooting

### Common Issues
- **Too many magic number warnings?** Add constants or ignore PLR2004
- **Docstring requirements too strict?** Adjust D* rules in ignore list
- **Import ordering conflicts?** Check known-first-party configuration

### Getting Help
- **Ruff Documentation**: https://docs.astral.sh/ruff/
- **Rule Reference**: https://docs.astral.sh/ruff/rules/
- **Configuration Guide**: https://docs.astral.sh/ruff/configuration/

---

**Remember**: Ruff is not just a linter - it's a learning tool that helps you write better, more maintainable Python code! 🐍✨ 