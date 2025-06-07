# 🎨 Rich Migration Guide for SocialMapper

This guide covers the migration of SocialMapper to use the [Rich library](https://github.com/Textualize/rich) for beautiful terminal output, progress bars, and enhanced user experience.

## 🚀 Benefits of Rich Integration

### Before Rich
```
=== Starting SocialMapper ===
Processing POIs...
100%|██████████| 50/50 [00:30<00:00,  1.67it/s]
Generating isochrones...
Completed in 45.2 seconds
```

### After Rich
```
┏━━━━━━━━━━━━━━━━ 🏘️ SocialMapper ━━━━━━━━━━━━━━━━┓
┃        End-to-end tool for mapping         ┃
┃              community resources           ┃
┗━━━━━━━━━━━━━━━━━━━━━━ v0.5.0 ━━━━━━━━━━━━━━━━━━━━━━┛

🗺️ Processing points of interest ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 50/50 100% 0:00:25 1.8/s

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                     🎉 Analysis Complete                                       ┃
┃ ✅ SocialMapper completed successfully in 45.2 seconds                                        ┃
┃ Results available in: output/                                                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## 🛠️ Migration Components

### 1. Rich Progress System (`socialmapper/ui/rich_progress.py`)

**Features:**
- ✨ Beautiful progress bars with spinners and time estimates
- 📊 Real-time performance metrics (throughput, memory usage)
- 🎯 Stage-based tracking for the entire SocialMapper pipeline
- 🎨 Colored output with emojis for different processing stages
- 📱 Context-aware (works in both CLI and Streamlit)

**Usage:**
```python
from socialmapper.ui.rich_progress import track_stage, ProcessingStage

# Track a complete stage
with track_stage(ProcessingStage.POI_PROCESSING, total_items=100) as tracker:
    for i in range(100):
        # Do work
        tracker.update_progress(advance=1, substage="poi_query")

# Or use convenience functions
with track_poi_processing(total_pois=50) as tracker:
    # Process POIs
    pass
```

### 2. Rich Console Module (`socialmapper/ui/rich_console.py`)

**Features:**
- 🏷️ Consistent branding with beautiful banners
- ✅ Success/error/warning/info panels with appropriate colors
- 📊 Formatted tables for data display
- ⏳ Status spinners for long operations
- 📄 Syntax-highlighted JSON output
- 🎭 Rich tracebacks for better error debugging

**Usage:**
```python
from socialmapper.ui.rich_console import (
    print_banner, print_success, print_error, status_spinner,
    print_poi_summary_table, console
)

# Print a beautiful banner
print_banner("Analysis Complete", "Community mapping finished successfully", "v0.5.0")

# Show status spinner
with status_spinner("Downloading road networks..."):
    # Long running operation
    pass

# Display data tables
print_poi_summary_table(poi_list)
```

### 3. Enhanced CLI Experience

The CLI now features:
- 🎨 Beautiful banner on startup
- 📊 Formatted tables for census variables and dry-run information
- ✅ Success/error panels instead of plain text
- 📈 Performance summary tables
- 🗂️ File generation summaries

### 4. Better Error Handling

Rich provides:
- 🐛 **Rich Tracebacks**: Better error formatting with local variables
- 🎯 **Contextual Errors**: Error panels with clear titles and styling
- 📍 **Source Highlighting**: Syntax-highlighted code in tracebacks

## 📚 Migration Examples

### Before: Plain Print Statements
```python
print("Starting POI processing...")
print(f"Found {len(pois)} POIs")
print("Processing complete!")
```

### After: Rich Console
```python
from socialmapper.ui.rich_console import print_info, print_success

print_info(f"Starting to process {len(pois):,} points of interest", "POI Processing")
print_poi_summary_table(pois)  # Beautiful table
print_success("POI processing completed successfully!")
```

### Before: Basic Progress
```python
from tqdm import tqdm

for item in tqdm(items, desc="Processing"):
    process_item(item)
```

### After: Rich Progress
```python
from socialmapper.ui.rich_progress import track_stage, ProcessingStage

with track_stage(ProcessingStage.POI_PROCESSING, len(items)) as tracker:
    for item in items:
        process_item(item)
        tracker.update_progress(advance=1, substage="poi_validation")
```

## 🎯 Key Migration Points

### 1. Replace Print Statements

**Old Way:**
```python
print("Error: Something went wrong")
print("Success: Operation completed")
print("Warning: Check your input")
```

**New Way:**
```python
from socialmapper.ui.rich_console import print_error, print_success, print_warning

print_error("Something went wrong")
print_success("Operation completed")  
print_warning("Check your input")
```

### 2. Replace Progress Bars

**Old Way:**
```python
from tqdm import tqdm
progress_bar = tqdm(total=100, desc="Processing")
# Update manually
progress_bar.update(1)
progress_bar.close()
```

**New Way:**
```python
from socialmapper.ui.rich_progress import track_stage, ProcessingStage

with track_stage(ProcessingStage.SETUP, total_items=100) as tracker:
    tracker.update_progress(advance=1, substage="initialization")
```

### 3. Replace Data Display

**Old Way:**
```python
print(f"POI: {poi['name']} at {poi['lat']}, {poi['lon']}")
for poi in pois:
    print(f"  - {poi['name']}")
```

**New Way:**
```python
from socialmapper.ui.rich_console import print_poi_summary_table

print_poi_summary_table(pois)  # Automatic beautiful table
```

## 🚀 Advanced Features

### 1. Custom Tables
```python
from socialmapper.ui.rich_console import create_data_table, console

table = create_data_table(
    title="Custom Data",
    columns=[
        {"name": "Name", "style": "cyan"},
        {"name": "Value", "style": "green", "justify": "right"}
    ],
    rows=[["Item 1", "100"], ["Item 2", "200"]]
)
console.print(table)
```

### 2. Status Spinners
```python
from socialmapper.ui.rich_console import status_spinner

with status_spinner("Downloading large dataset...", spinner="dots"):
    time.sleep(5)  # Long operation
```

### 3. Performance Monitoring
```python
from socialmapper.ui.rich_console import print_performance_summary

metrics = {
    "processing_time": 45.2,
    "items_count": 1000,
    "memory_usage_mb": 256.7,
    "throughput_per_second": 22.1
}
print_performance_summary(metrics)
```

## 🔧 Configuration

### Environment Variables
```bash
# Control Rich output
export TERM=xterm-256color  # Enable full color support
export COLUMNS=120          # Set terminal width
export LINES=40            # Set terminal height
```

### Python Configuration
```python
from rich.console import Console

# Create custom console
console = Console(
    color_system="auto",    # Auto-detect color support
    width=120,              # Custom width
    force_terminal=True     # Force terminal mode
)
```

## 🧪 Testing Rich Integration

### Manual Testing
```bash
# Test CLI with Rich output
socialmapper --list-variables  # Should show beautiful table

# Test with dry run
socialmapper --poi --geocode-area "Test" --poi-type "amenity" --poi-name "library" --dry-run

# Test error handling (intentional error)
socialmapper --poi --geocode-area "NonexistentPlace" --poi-type "invalid" --poi-name "invalid"
```

### Programmatic Testing
```python
# Test Rich components
from socialmapper.ui.rich_console import print_banner, print_success
from socialmapper.ui.rich_progress import get_rich_tracker

# Test banner
print_banner("Test Title", "Test subtitle")

# Test progress
tracker = get_rich_tracker()
with tracker.status("Testing..."):
    time.sleep(2)

print_success("Rich integration test completed!")
```

## 📦 Backwards Compatibility

Rich integration maintains backwards compatibility:

1. **Streamlit Mode**: Automatically detects Streamlit and uses `st.write()` fallbacks
2. **No-Color Terminals**: Gracefully degrades to plain text
3. **API Consistency**: All existing function signatures remain the same
4. **Optional Features**: Rich features are optional and don't break existing code

## 🎨 Customization

### Custom Themes
```python
from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow", 
    "error": "bold red",
    "success": "bold green"
})

console = Console(theme=custom_theme)
```

### Custom Progress Styles
```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

custom_progress = Progress(
    SpinnerColumn("dots2"),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    # Add custom columns
)
```

## 🐛 Troubleshooting

### Common Issues

1. **Colors not showing**: Ensure terminal supports ANSI colors
   ```bash
   echo $TERM  # Should show color-capable terminal
   ```

2. **Progress bars not displaying**: Check terminal width
   ```python
   from rich.console import Console
   console = Console()
   print(console.size)  # Should show width > 40
   ```

3. **Import errors**: Ensure Rich is installed
   ```bash
   pip install rich>=13.0.0
   ```

### Debug Mode
```python
from rich.console import Console

console = Console(stderr=True)  # Debug output to stderr
console.print("Debug info", style="dim")
```

## 🎯 Next Steps

After migration:

1. **Update Documentation**: Update all docs to show Rich output examples
2. **Add Tests**: Create tests for Rich components  
3. **Performance Tuning**: Monitor Rich overhead in production
4. **User Feedback**: Gather feedback on new UI/UX
5. **Additional Features**: Consider Rich's `Live` displays for real-time updates

## 📖 Resources

- [Rich Documentation](https://rich.readthedocs.io/)
- [Rich GitHub Repository](https://github.com/Textualize/rich)
- [Rich Gallery](https://www.textualize.io/rich/) - Examples of Rich output
- [Textual](https://www.textualize.io/) - Rich's sister project for TUI apps

---

The Rich migration transforms SocialMapper from a functional tool into a **beautiful, professional-grade** command-line application that users will love to use! 🎉 