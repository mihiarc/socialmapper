# Enhanced Design System
## Project 1.2 - SocialMapper Visual Configuration Interface

**Date**: August 10, 2025  
**Design Phase**: Week 7-8  
**Foundation**: Ant Design v5.14.0 + Custom Spatial Analysis Components

---

## Design System Principles

### 1. Accessible by Default
- **WCAG 2.1 AA Compliance**: All components meet accessibility standards
- **Color Contrast**: Minimum 4.5:1 for normal text, 3:1 for large text
- **Keyboard Navigation**: Full functionality available via keyboard
- **Screen Reader Support**: Semantic HTML with proper ARIA labels

### 2. Progressive Disclosure
- **Complexity Management**: Advanced features available but not prominent
- **Contextual Guidance**: Help and examples embedded where needed
- **Smart Defaults**: Sensible starting values reduce cognitive load
- **Expert Shortcuts**: Power users can bypass guidance when desired

### 3. Visual Intelligence
- **Spatial First**: Leverage geographic intuition over abstract concepts
- **Immediate Feedback**: Visual confirmation of all user selections
- **Data Visualization**: Clear, honest representation of analysis results
- **Professional Output**: Results suitable for academic and policy use

---

## Color System

### Primary Palette
Based on accessibility requirements and data visualization best practices:

```css
/* Primary Brand Colors - Accessible blue scale */
--primary-50: #e6f4ff;   /* Light backgrounds, subtle highlights */
--primary-100: #bae0ff;  /* Secondary backgrounds */
--primary-200: #91caff;  /* Inactive states */
--primary-300: #69b1ff;  /* Secondary actions */
--primary-400: #4096ff;  /* Primary actions */
--primary-500: #1677ff;  /* Main brand color (Ant Design primary) */
--primary-600: #0958d9;  /* Hover states */
--primary-700: #003eb3;  /* Pressed states */
--primary-800: #002c8c;  /* High contrast text */
--primary-900: #001d66;  /* Darkest contrast */

/* Semantic Colors - Accessible and color-blind friendly */
--success-main: #52c41a;     /* Success states, positive metrics */
--success-light: #b7eb8f;    /* Success backgrounds */
--warning-main: #fa8c16;     /* Warnings, attention needed */
--warning-light: #ffd591;    /* Warning backgrounds */
--error-main: #ff4d4f;       /* Errors, inaccessible areas */
--error-light: #ffccc7;      /* Error backgrounds */
--info-main: #1677ff;        /* Information, neutral states */
--info-light: #d6e4ff;       /* Information backgrounds */
```

### Spatial Analysis Colors
Color palette specifically designed for geographic visualization:

```css
/* Travel Time Zones - Sequential, accessible color ramp */
--travel-zone-1: #2166ac;    /* 0-5 minutes (darkest blue) */
--travel-zone-2: #4393c3;    /* 5-10 minutes */  
--travel-zone-3: #92c5de;    /* 10-15 minutes */
--travel-zone-4: #d1e5f0;    /* 15-30 minutes */
--travel-zone-5: #f7f7f7;    /* 30+ minutes (light gray) */

/* POI Category Colors - Distinct, accessible hues */
--poi-healthcare: #d32f2f;   /* Red - universal healthcare color */
--poi-education: #7b1fa2;    /* Purple - education/culture */
--poi-food: #f57c00;         /* Orange - food security */
--poi-recreation: #388e3c;   /* Green - parks and recreation */
--poi-transport: #1976d2;    /* Blue - transportation */
--poi-services: #5d4037;     /* Brown - government services */

/* Demographic Data Colors - ColorBrewer inspired, accessible */
--demo-high: #253494;        /* High values (dark blue) */
--demo-med-high: #2c7fb8;    /* Medium-high values */
--demo-medium: #41b6c4;      /* Medium values */
--demo-med-low: #a1dab4;     /* Medium-low values */
--demo-low: #ffffcc;         /* Low values (light yellow) */
--demo-no-data: #969696;     /* No data available (gray) */
```

### Gray Scale
Neutral colors for backgrounds, text, and UI elements:

```css
--gray-50: #fafafa;      /* Lightest background */
--gray-100: #f5f5f5;     /* Light background (current app background) */
--gray-200: #f0f0f0;     /* Card backgrounds */
--gray-300: #d9d9d9;     /* Borders, dividers */
--gray-400: #bfbfbf;     /* Disabled elements */
--gray-500: #8c8c8c;     /* Secondary text */
--gray-600: #595959;     /* Primary text */
--gray-700: #434343;     /* Headings */
--gray-800: #262626;     /* High contrast text */
--gray-900: #141414;     /* Maximum contrast */
```

---

## Typography System

### Font Stack
Building on Ant Design's font stack with spatial analysis considerations:

```css
--font-family-primary: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
                       'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 
                       'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 
                       'Noto Color Emoji';

--font-family-mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, 
                    'Courier New', monospace; /* For coordinates, technical data */
```

### Typography Scale
Accessible, readable hierarchy for complex interfaces:

```css
/* Display Text - Landing page, major headings */
--text-display-large: 3.5rem;    /* 56px - Hero headlines */
--text-display-medium: 2.8rem;   /* 45px - Section headers */
--text-display-small: 2.25rem;   /* 36px - Card titles */

/* Headings - Content hierarchy */
--text-h1: 2rem;          /* 32px - Page titles */
--text-h2: 1.75rem;       /* 28px - Major sections */
--text-h3: 1.5rem;        /* 24px - Subsections */
--text-h4: 1.25rem;       /* 20px - Component titles */
--text-h5: 1.125rem;      /* 18px - Minor headings */

/* Body Text - Primary content */
--text-large: 1.125rem;   /* 18px - Important body text */
--text-base: 1rem;        /* 16px - Standard body text */
--text-small: 0.875rem;   /* 14px - Secondary information */
--text-xs: 0.75rem;       /* 12px - Labels, captions */

/* Line Heights - Optimized for readability */
--line-height-tight: 1.25;   /* Headings */
--line-height-normal: 1.5;   /* Body text */
--line-height-relaxed: 1.75; /* Long-form content */
```

### Font Weights
```css
--font-weight-light: 300;    /* Light emphasis */
--font-weight-normal: 400;   /* Standard text */
--font-weight-medium: 500;   /* Slight emphasis */
--font-weight-semibold: 600; /* Strong emphasis */
--font-weight-bold: 700;     /* Headings, important text */
```

---

## Spacing System

### Base Spacing Unit
Building on Ant Design's 8px base unit with spatial analysis needs:

```css
--space-0: 0;          /* 0px - No space */
--space-1: 0.25rem;    /* 4px - Micro spacing */
--space-2: 0.5rem;     /* 8px - Small spacing (Ant Design base) */
--space-3: 0.75rem;    /* 12px - Medium-small spacing */
--space-4: 1rem;       /* 16px - Standard spacing */
--space-5: 1.25rem;    /* 20px - Medium spacing */
--space-6: 1.5rem;     /* 24px - Large spacing */
--space-8: 2rem;       /* 32px - Extra large spacing */
--space-10: 2.5rem;    /* 40px - Section spacing */
--space-12: 3rem;      /* 48px - Major section spacing */
--space-16: 4rem;      /* 64px - Page-level spacing */
--space-20: 5rem;      /* 80px - Hero section spacing */
```

### Component-Specific Spacing
```css
/* Wizard Steps */
--wizard-step-spacing: var(--space-8);    /* Between wizard steps */
--wizard-content-padding: var(--space-6); /* Step content padding */

/* Map Components */
--map-control-margin: var(--space-4);     /* Map control spacing */
--map-popup-padding: var(--space-4);      /* Map popup internal spacing */

/* Cards and Panels */
--card-padding: var(--space-6);           /* Standard card padding */
--panel-margin: var(--space-4);           /* Between panels */
```

---

## Component Specifications

### Core Spatial Analysis Components

#### 1. LocationSelector Component
**Purpose**: Interactive location selection with map and search

**Design Specifications**:
```typescript
interface LocationSelectorProps {
  value?: LocationValue;
  onChange: (location: LocationValue) => void;
  placeholder?: string;
  showPopularLocations?: boolean;
  bounds?: GeoBounds;
  zoomLevel?: number;
  onAreaEstimate?: (area: number, population: number) => void;
}

interface LocationValue {
  address: string;
  coordinates: [number, number]; // [lng, lat]
  boundingBox: GeoBounds;
  confidence: 'high' | 'medium' | 'low';
  population?: number;
  area?: number;
}
```

**Visual Design**:
- **Map Container**: 400px height, rounded corners (8px border radius)
- **Search Input**: Full width, large touch target (48px height)
- **Popular Locations**: Horizontal scroll chips below search
- **Selection Feedback**: Highlighted bounding box with area info
- **Confidence Indicator**: Color-coded border (green/yellow/red)

**Accessibility**:
- **Keyboard Navigation**: Tab through search, popular locations, map controls
- **Screen Reader**: Descriptive text for map interactions
- **High Contrast**: Sufficient contrast for selection highlights

#### 2. POICategoryPicker Component
**Purpose**: Visual POI category selection with preview and validation

**Design Specifications**:
```typescript
interface POICategoryPickerProps {
  categories: POICategory[];
  selectedCategories: string[];
  onSelectionChange: (categories: string[]) => void;
  location?: LocationValue;
  showCustomUpload?: boolean;
  maxSelections?: number;
}

interface POICategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  examples: string[];
  count?: number; // POIs found in selected location
  popular: boolean;
}
```

**Visual Design**:
- **Grid Layout**: 2-3 columns on desktop, 1 column on mobile
- **Category Cards**: 200px width, 150px height, hover effects
- **Visual Hierarchy**: Popular categories highlighted
- **Count Indicators**: "23 libraries found" in bottom right
- **Multi-Select UI**: Checkboxes with selected state styling

**Categories Structure**:
```
Healthcare Access 🏥          Education & Culture 🏫
├─ Hospitals                  ├─ Schools (K-12)
├─ Clinics                    ├─ Universities
├─ Urgent Care                ├─ Libraries
└─ Pharmacies                 └─ Museums

Daily Needs 🛒               Transportation 🚌
├─ Grocery Stores             ├─ Bus Stops
├─ Supermarkets               ├─ Train Stations
├─ Pharmacies                 ├─ Bike Share
└─ Banks                      └─ Parking

Recreation 🌳                Public Services 🏛️
├─ Parks                      ├─ Post Offices
├─ Playgrounds                ├─ Government Offices
├─ Sports Facilities          ├─ Police Stations
└─ Community Centers          └─ Fire Stations
```

#### 3. TravelParameterConfig Component
**Purpose**: Intuitive travel time and mode configuration with visual feedback

**Design Specifications**:
```typescript
interface TravelParameterConfigProps {
  travelTime: number;
  travelMode: TravelMode;
  onTravelTimeChange: (minutes: number) => void;
  onTravelModeChange: (mode: TravelMode) => void;
  location?: LocationValue;
  showAdvancedOptions?: boolean;
}

interface TravelMode {
  id: 'walk' | 'bike' | 'drive' | 'transit';
  name: string;
  description: string;
  icon: string;
  maxTime: number;
  avgSpeed: number;
}
```

**Visual Design**:
- **Time Slider**: Large, touch-friendly with distance indicators
- **Mode Selection**: Large button cards with icons and descriptions
- **Visual Preview**: Live map update showing reachable area
- **Impact Estimate**: "Reaches ~85,000 people" below slider
- **Smart Validation**: Warning for unrealistic combinations

**Travel Mode Cards**:
```
🚶 Walking              🚗 Driving
   Pedestrian access       Car-based access
   Max: 30 minutes        Max: 60 minutes
   Avg: 3 mph             Avg: 25 mph
   
🚲 Cycling             🚌 Public Transit
   Bike-friendly routes   Bus/train routes
   Max: 45 minutes        Schedule-dependent
   Avg: 10 mph            Varies by route
```

#### 4. DemographicSelector Component  
**Purpose**: Plain-language demographic variable selection

**Design Specifications**:
```typescript
interface DemographicSelectorProps {
  availableVariables: DemographicVariable[];
  selectedVariables: string[];
  onSelectionChange: (variables: string[]) => void;
  showPresets?: boolean;
  maxSelections?: number;
}

interface DemographicVariable {
  code: string;          // Census variable code
  name: string;          // Plain language name
  category: string;      // Population, Economic, Housing, etc.
  description: string;   // What this measures
  universe: string;      // What population this applies to
  popular: boolean;      // Commonly used variable
}
```

**Visual Design**:
- **Category Tabs**: Group variables by theme
- **Variable Cards**: Name, description, universe information
- **Preset Options**: "Common Analysis Variables" quick selection
- **Selection Limit**: Visual indicator of maximum selections
- **Plain Language**: No raw census codes exposed to users

**Category Organization**:
```
👥 Population Characteristics    💰 Economic Indicators
├─ Total Population             ├─ Household Income
├─ Age Groups (Under 18, 65+)   ├─ Poverty Rates  
├─ Race and Ethnicity           ├─ Employment Status
└─ Household Size               └─ Occupation Types

🏠 Housing Characteristics       🎓 Education & Language
├─ Homeownership Rates          ├─ Educational Attainment
├─ Housing Age                  ├─ School Enrollment
├─ Occupancy Status             ├─ Language Spoken at Home
└─ Housing Costs                └─ English Proficiency
```

### Enhanced Ant Design Components

#### 1. Wizard Component
Enhanced version of Ant Design Steps with spatial analysis needs:

```typescript
interface SpatialWizardProps {
  steps: WizardStep[];
  currentStep: number;
  onStepChange: (step: number) => void;
  allowStepJump?: boolean;
  showProgress?: boolean;
  persistState?: boolean;
}

interface WizardStep {
  title: string;
  description?: string;
  icon?: ReactNode;
  content: ReactNode;
  validation?: () => boolean;
  optional?: boolean;
}
```

**Enhanced Features**:
- **Progress Persistence**: Save state across browser sessions
- **Step Validation**: Prevent advancement with invalid data
- **Visual Progress**: Enhanced progress indicators with time estimates
- **Mobile Optimization**: Stack steps vertically on small screens

#### 2. Interactive Map Component
Mapbox integration with spatial analysis enhancements:

```typescript
interface SpatialMapProps {
  center?: [number, number];
  zoom?: number;
  height?: string | number;
  onLocationSelect?: (location: LocationValue) => void;
  showControls?: boolean;
  layers?: MapLayer[];
  interactive?: boolean;
  accessibilityLabel?: string;
}
```

**Accessibility Features**:
- **Keyboard Navigation**: Arrow keys pan map, +/- keys zoom
- **Screen Reader**: Descriptive text for map interactions
- **Focus Management**: Clear focus indicators for map controls
- **Alternative Interface**: Text-based location entry always available

#### 3. Results Visualization Components
Specialized components for analysis results display:

```typescript
interface ResultsSummaryProps {
  analysisResults: AnalysisResult;
  showExecutiveSummary?: boolean;
  highlightInsights?: boolean;
  comparisonData?: AnalysisResult[];
}

interface AccessibilityMapProps {
  isochrones: GeoJSON.FeatureCollection;
  pois: POILocation[];
  demographics?: DemographicData;
  onLayerToggle?: (layer: string, visible: boolean) => void;
  colorScheme?: 'default' | 'colorblind' | 'highContrast';
}
```

---

## Iconography System

### Spatial Analysis Icons
Custom icon set designed for accessibility and clarity:

```css
/* Travel Modes */
.icon-walk { /* Walking person icon */ }
.icon-bike { /* Bicycle icon */ }
.icon-drive { /* Car icon */ }
.icon-transit { /* Bus icon */ }

/* POI Categories */
.icon-hospital { /* Hospital cross */ }
.icon-school { /* School building */ }
.icon-library { /* Book icon */ }
.icon-grocery { /* Shopping cart */ }
.icon-park { /* Tree icon */ }
.icon-transit-stop { /* Bus stop sign */ }

/* Interface Actions */
.icon-location { /* Map pin */ }
.icon-time { /* Clock */ }
.icon-people { /* People group */ }
.icon-export { /* Download arrow */ }
.icon-share { /* Share arrow */ }
.icon-help { /* Question mark circle */ }
```

**Design Principles**:
- **Consistent Style**: Outlined icons, 2px stroke weight
- **Accessibility**: Works at minimum 16px size
- **Cultural Sensitivity**: Universal symbols avoid culture-specific references
- **Color Independence**: Recognizable without color information

---

## Responsive Design System

### Breakpoints
Optimized for spatial analysis workflows:

```css
--breakpoint-xs: 480px;   /* Small phones */
--breakpoint-sm: 768px;   /* Large phones, small tablets */
--breakpoint-md: 1024px;  /* Tablets, small laptops */
--breakpoint-lg: 1440px;  /* Desktop, large laptops */
--breakpoint-xl: 1920px;  /* Large desktop, external monitors */
```

### Component Behavior

#### Wizard Steps
- **Mobile (xs-sm)**: Single column, full-width steps
- **Tablet (md)**: Single column with side navigation
- **Desktop (lg+)**: Multi-column layout with step overview

#### Map Components
- **Mobile**: Full-width, 300px minimum height
- **Tablet**: 50/50 split with controls
- **Desktop**: Larger map area with panel overlays

#### Results Dashboard
- **Mobile**: Stacked layout, swipeable sections
- **Tablet**: 2-column grid layout
- **Desktop**: Complex dashboard layout with multiple panels

---

## Accessibility Standards

### WCAG 2.1 AA Compliance Checklist

#### Color and Contrast
- ✅ **4.5:1 contrast** for normal text
- ✅ **3:1 contrast** for large text and UI components
- ✅ **Color independence** - information not conveyed by color alone
- ✅ **Pattern support** for color-blind users

#### Keyboard Navigation
- ✅ **Tab order** logical and complete
- ✅ **Focus indicators** visible and clear
- ✅ **Keyboard shortcuts** for common actions
- ✅ **Escape mechanisms** from modal states

#### Screen Reader Support
- ✅ **Semantic HTML** structure
- ✅ **ARIA labels** for complex interactions
- ✅ **Alternative text** for maps and visualizations
- ✅ **Status updates** announced appropriately

#### Motor Accessibility
- ✅ **Touch targets** minimum 44px
- ✅ **Hover alternatives** for touch devices
- ✅ **Timeout extensions** for complex tasks
- ✅ **Error prevention** and clear recovery

---

## Implementation Guidelines

### Component Development Standards

#### 1. TypeScript First
All components must be fully typed with clear interfaces:
```typescript
// Good - Clear, specific types
interface LocationSelectorProps {
  value?: LocationValue;
  onChange: (location: LocationValue) => void;
  bounds?: GeoBounds;
}

// Avoid - Vague or missing types
interface LocationSelectorProps {
  value?: any;
  onChange: (data: any) => void;
  config?: object;
}
```

#### 2. Accessibility by Default
Every component includes accessibility features:
```typescript
const LocationSelector: React.FC<LocationSelectorProps> = ({ 
  value, 
  onChange,
  accessibilityLabel = "Select analysis location"
}) => {
  return (
    <div 
      role="region" 
      aria-label={accessibilityLabel}
      tabIndex={0}
    >
      {/* Component content */}
    </div>
  );
};
```

#### 3. Performance Optimization
- **Lazy Loading**: Components load when needed
- **Memoization**: Expensive calculations cached appropriately
- **Bundle Splitting**: Map components in separate chunks
- **Progressive Enhancement**: Basic functionality works without JavaScript

#### 4. Testing Requirements
- **Unit Tests**: Component logic and state management
- **Accessibility Tests**: Screen reader and keyboard navigation
- **Visual Regression**: Component appearance across breakpoints
- **Integration Tests**: Multi-component workflows

---

## Design Tokens

### CSS Custom Properties
All design values stored as CSS custom properties:

```css
:root {
  /* Colors */
  --color-primary: #1677ff;
  --color-success: #52c41a;
  --color-warning: #fa8c16;
  --color-error: #ff4d4f;
  
  /* Typography */
  --font-size-base: 1rem;
  --line-height-base: 1.5;
  --font-weight-base: 400;
  
  /* Spacing */
  --space-base: 0.5rem;
  --space-large: 2rem;
  
  /* Shadows */
  --shadow-small: 0 2px 8px rgba(0, 0, 0, 0.1);
  --shadow-medium: 0 4px 16px rgba(0, 0, 0, 0.1);
  
  /* Border Radius */
  --radius-small: 4px;
  --radius-medium: 8px;
  --radius-large: 12px;
  
  /* Transitions */
  --transition-fast: 0.15s ease-out;
  --transition-medium: 0.25s ease-out;
  --transition-slow: 0.5s ease-out;
}
```

### JavaScript Token Export
Design tokens available to JavaScript components:

```typescript
export const designTokens = {
  colors: {
    primary: '#1677ff',
    success: '#52c41a',
    // ... other colors
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    // ... other spacing values
  },
  // ... other token categories
} as const;
```

---

## Component Library Documentation

### Storybook Integration
Each component includes comprehensive Storybook documentation:

```typescript
// LocationSelector.stories.tsx
export default {
  title: 'Spatial Analysis/LocationSelector',
  component: LocationSelector,
  parameters: {
    docs: {
      description: {
        component: 'Interactive location selection with map and search capabilities'
      }
    }
  }
};

export const Default = {
  args: {
    placeholder: "Enter city or address",
    showPopularLocations: true
  }
};

export const WithBounds = {
  args: {
    bounds: {
      north: 40.7829,
      south: 40.7489,
      east: -73.9441,
      west: -73.9927
    }
  }
};

export const Accessibility = {
  args: {
    accessibilityLabel: "Select location for accessibility analysis"
  },
  parameters: {
    a11y: {
      config: {
        rules: [
          { id: 'color-contrast', enabled: true },
          { id: 'keyboard', enabled: true }
        ]
      }
    }
  }
};
```

---

*This enhanced design system provides the foundation for creating an intuitive, accessible, and professional spatial analysis interface that serves both technical accuracy and user experience excellence.*