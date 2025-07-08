# Playwright MCP Server Setup Guide

This guide documents the setup of Microsoft's Playwright MCP (Model Context Protocol) server for automated browser testing and navigation of the SocialMapper Streamlit app.

## What's Installed

1. **Playwright MCP Server**: `@executeautomation/playwright-mcp-server`
   - Location: `/opt/homebrew/lib/node_modules/@executeautomation/playwright-mcp-server/`
   - Main file: `dist/index.js`

2. **Playwright Core**: Local installation for browser automation
   - Chromium browser installed and ready

## Claude Code Configuration

The MCP server is configured in Claude Code via `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "node",
      "args": [
        "/opt/homebrew/lib/node_modules/@executeautomation/playwright-mcp-server/dist/index.js"
      ],
      "env": {
        "BROWSER": "chromium",
        "HEADLESS": "false"
      }
    }
  }
}
```

## Available Playwright Tools (via MCP)

Once Claude Code restarts and connects to the MCP server, you'll have access to these browser automation tools:

### Navigation Tools
- `navigate_to` - Navigate to a specific URL
- `go_back` - Go back in browser history
- `go_forward` - Go forward in browser history
- `reload_page` - Reload the current page

### Interaction Tools
- `click_element` - Click on elements by selector
- `fill_text` - Fill input fields with text
- `press_key` - Send keyboard inputs
- `hover_element` - Hover over elements
- `scroll_page` - Scroll the page

### Information Gathering
- `get_page_content` - Extract page text content
- `take_screenshot` - Capture page screenshots
- `get_element_text` - Get text from specific elements
- `get_page_url` - Get current page URL
- `wait_for_element` - Wait for elements to appear

### Form Interactions
- `select_option` - Select from dropdown menus
- `check_checkbox` - Check/uncheck checkboxes
- `upload_file` - Upload files to file inputs

## Testing the Streamlit App

Your Streamlit app is running at: **http://localhost:8501**

### Common Selectors for SocialMapper UI

```javascript
// Main header
'h1:has-text("SocialMapper Dashboard")'

// Location input (first text input)
'input[type="text"]'

// Run Analysis button
'button:has-text("Run Analysis")'

// Sidebar
'[data-testid="stSidebar"]'

// Form elements
'[data-testid="stForm"]'

// Metrics cards
'[data-testid="metric-container"]'

// Map container (Folium)
'[data-testid="stIFrame"]'
```

## Example Use Cases

1. **Automated Testing**: Test form submissions and validate results
2. **UI Development**: Navigate and interact with different pages
3. **Screenshot Documentation**: Capture app states for documentation
4. **Performance Testing**: Measure page load times and interactions
5. **Accessibility Testing**: Check element visibility and interactions

## Next Steps

1. **Restart Claude Code** to activate the MCP server connection
2. **Test basic navigation**: Ask Claude to navigate to the Streamlit app
3. **Automate form filling**: Have Claude fill out the analysis form
4. **Capture screenshots**: Document different app states
5. **Test workflows**: Automate complete analysis workflows

## Troubleshooting

- **MCP server not connecting**: Check the file path in settings.json
- **Browser not launching**: Ensure Chromium is installed (`npx playwright install chromium`)
- **Headless mode**: Change `"HEADLESS": "true"` in settings.json for background operation
- **Different browser**: Change `"BROWSER"` to "firefox" or "webkit" if needed

## Example Commands for Claude

Once the MCP server is active, you can ask Claude to:

```
"Navigate to the Streamlit app and take a screenshot"
"Fill in 'Raleigh, NC' in the location field and click Run Analysis"
"Check if the analysis results are displayed correctly"
"Navigate through all the different pages in the sidebar"
"Test the travel modes comparison feature"
```

The Playwright MCP server is now ready to help with automated browser interaction and testing of your SocialMapper Streamlit application!