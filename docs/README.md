# SocialMapper Documentation

This directory contains the source files for SocialMapper's documentation, built with [MkDocs](https://www.mkdocs.org/) and the [Material theme](https://squidfunk.github.io/mkdocs-material/).

## 📚 Documentation Structure

```
docs/
├── index.md                  # Homepage
├── getting-started/         # Installation and quick start guides
├── ADDRESS_GEOCODING.md     # Geocoding feature documentation
├── ARCHITECTURE.md          # System architecture overview
├── OSMNX_FEATURES.md        # OSMnx integration guide
└── assets/                  # CSS and JavaScript files
```

## 🚀 Local Development

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Install documentation dependencies:
```bash
pip install -r docs/requirements.txt
```

2. Serve documentation locally:
```bash
mkdocs serve
```

3. View at http://localhost:8000

### Building

Build static site:
```bash
mkdocs build
```

Output will be in the `site/` directory.

## 🤖 Automated Deployment

Documentation is automatically deployed to GitHub Pages when changes are pushed to the `main` branch.

### GitHub Actions Workflow

The `.github/workflows/docs.yml` workflow:
1. Triggers on pushes to `main` that modify docs
2. Builds the documentation with MkDocs
3. Deploys to GitHub Pages

### Enabling GitHub Pages

1. Go to Settings → Pages in your GitHub repository
2. Under "Source", select "GitHub Actions"
3. Save the settings

The documentation will be available at:
```
https://[username].github.io/socialmapper/
```

## 📝 Writing Documentation

### Adding New Pages

1. Create a new `.md` file in the appropriate directory
2. Add to navigation in `mkdocs.yml`:
```yaml
nav:
  - Section Name:
    - Page Title: path/to/file.md
```

### Markdown Features

The Material theme supports extended markdown:
- Admonitions: `!!! note "Title"`
- Code blocks with syntax highlighting
- Tables
- Task lists
- Tabbed content

See [Material for MkDocs documentation](https://squidfunk.github.io/mkdocs-material/reference/) for all features.

## 🧪 Testing

Before pushing changes:

1. Build locally to check for errors:
```bash
mkdocs build --strict
```

2. Check all links:
```bash
mkdocs build --strict --verbose
```

3. Preview the site:
```bash
mkdocs serve
```

## 🔧 Troubleshooting

### Common Issues

**Build fails with "not found" errors**
- Ensure all files referenced in `mkdocs.yml` exist
- Check for typos in file paths

**GitHub Pages not updating**
- Check Actions tab for workflow status
- Ensure GitHub Pages is enabled in repository settings
- Clear browser cache

**Local server not starting**
- Check if port 8000 is already in use
- Try a different port: `mkdocs serve -a localhost:8001`

## 📚 Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)