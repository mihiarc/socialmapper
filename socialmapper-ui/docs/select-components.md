# Select Component Style Guide

## Overview

The SocialMapper UI includes three select components with enhanced aesthetics and improved user experience:

1. **Select** - Standard dropdown with improved styling
2. **SelectEnhanced** - Advanced dropdown with variants and sizes
3. **MultiSelect** - Multi-selection dropdown with search

## Standard Select Component

The base Select component has been enhanced with:

### Visual Improvements
- **Modern rounded borders** with 2px width for better visibility
- **Smooth transitions** (200ms) on all interactive states
- **Custom chevron icon** replacing browser default
- **Focus ring** with primary color and 20% opacity
- **Dark mode support** with appropriate color adjustments

### States
- **Default**: Clean white background with gray border
- **Hover**: Darker border color for better feedback
- **Focus**: Primary color border with ring effect
- **Disabled**: Reduced opacity with cursor change
- **Error**: Red border with error icon and message

### Usage Example
```tsx
<Select
  label="Choose an option"
  placeholder="Select an option..."
  options={[
    { value: 'opt1', label: 'Option 1' },
    { value: 'opt2', label: 'Option 2' }
  ]}
  value={selectedValue}
  onChange={(e) => setSelectedValue(e.target.value)}
  error={errors.field}
/>
```

## Enhanced Select Component

Provides additional customization options:

### Variants
1. **Default** - Standard bordered style
2. **Filled** - Gray background with no border
3. **Ghost** - Transparent until interaction

### Sizes
- **Small (sm)** - Compact padding for dense UIs
- **Medium (md)** - Standard size (default)
- **Large (lg)** - Increased padding for touch interfaces

### Usage Example
```tsx
<SelectEnhanced
  label="Select Size"
  variant="filled"
  size="lg"
  options={options}
  value={value}
  onChange={(e) => setValue(e.target.value)}
/>
```

## MultiSelect Component

Advanced multi-selection with:

### Features
- **Search functionality** - Filter options by typing
- **Checkbox indicators** - Clear selection state
- **Selection counter** - Shows number of selected items
- **Select all** - Quick action to select everything
- **Clear button** - Remove all selections
- **Smooth animations** - Dropdown appears with fade and zoom

### Usage Example
```tsx
<MultiSelect
  label="Select Points of Interest"
  placeholder="Choose POI types..."
  options={[
    { 
      value: 'amenity:pharmacy', 
      label: 'Pharmacy',
      description: 'Pharmacies and drugstores'
    }
  ]}
  value={selectedPOIs}
  onChange={setSelectedPOIs}
  maxHeight={300}
/>
```

## Styling Details

### Color Palette
- **Primary**: Blue (#3b82f6) - Used for focus states
- **Gray scale**: From 50 to 900 for various states
- **Error**: Red (#ef4444) for validation errors
- **Success**: Green (#10b981) for confirmations

### Spacing
- Consistent padding based on size variant
- 2px borders for better visibility
- 4px focus ring for accessibility

### Typography
- Clear hierarchy with font weights
- Appropriate text sizes for each component size
- Readable contrast ratios

### Animations
- 200ms transitions for smooth interactions
- Fade and zoom effects for dropdowns
- Transform rotation for chevron icons

## Accessibility

All select components include:
- Proper ARIA labels
- Keyboard navigation support
- Focus indicators
- Screen reader compatibility
- Disabled state handling

## Browser Compatibility

- Removes default browser styling with `appearance-none`
- Custom icons work across all modern browsers
- Fallback styling for older browsers
- Consistent rendering across platforms

## Best Practices

1. **Use consistent variants** - Stick to one variant style across similar forms
2. **Provide placeholders** - Help users understand expected input
3. **Show errors clearly** - Use the error prop for validation feedback
4. **Consider mobile** - Use larger sizes for touch interfaces
5. **Group related options** - Use descriptions in MultiSelect for clarity

## Migration Guide

To update existing Select components:

1. The API remains the same - no breaking changes
2. Styling is automatically applied
3. Add `size` or `variant` props for enhanced version
4. Use `MultiSelect` for checkbox-style selections

## Component Demo

View the live component demo at `/components` (when dev tools enabled) to see all variations and states in action.