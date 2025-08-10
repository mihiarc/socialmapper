# QueryWizard Component Specification
## Project 1.2 - Visual Configuration Interface Core Component

**Date**: August 10, 2025  
**Component Type**: Container/Orchestrator  
**Priority**: Critical Path - Core user experience  
**Integration**: React + TypeScript + Ant Design + Redux Toolkit

---

## Component Overview

The QueryWizard is the primary interface that transforms complex CLI parameters into an intuitive 4-step visual workflow. It orchestrates the complete analysis configuration experience from location selection through parameter validation and submission.

### Success Criteria
- **<5 minute completion time** from start to analysis launch
- **80%+ completion rate** for users who start the wizard
- **<3 validation errors** per session on average
- **90%+ user confidence** in their parameter selections

---

## Component Interface

### TypeScript Interface

```typescript
interface QueryWizardProps {
  // Initial state and configuration
  initialStep?: number;
  initialData?: Partial<AnalysisConfiguration>;
  persistProgress?: boolean;
  showExitWarning?: boolean;
  
  // Event handlers
  onComplete: (config: AnalysisConfiguration) => Promise<void>;
  onCancel?: () => void;
  onStepChange?: (step: number, data: Partial<AnalysisConfiguration>) => void;
  onValidationError?: (step: number, errors: ValidationError[]) => void;
  
  // Customization
  allowStepJump?: boolean;
  showAdvancedOptions?: boolean;
  customSteps?: WizardStep[];
  
  // Integration props
  className?: string;
  style?: React.CSSProperties;
}

interface AnalysisConfiguration {
  // Step 1: Location
  location: LocationValue;
  
  // Step 2: POI Selection  
  poiCategories: string[];
  customPOIs?: CustomPOI[];
  
  // Step 3: Travel Parameters
  travelTime: number;
  travelMode: TravelMode;
  travelOptions?: AdvancedTravelOptions;
  
  // Step 4: Demographics & Export
  demographicVariables: string[];
  exportFormats: ExportFormat[];
  includeIsochrones: boolean;
  includeDemographics: boolean;
  
  // Metadata
  analysisName?: string;
  description?: string;
  tags?: string[];
}

interface WizardStep {
  id: string;
  title: string;
  description: string;
  component: React.ComponentType<StepComponentProps>;
  validation: ValidationSchema;
  optional?: boolean;
  estimatedTime?: string;
}

interface ValidationError {
  field: string;
  message: string;
  severity: 'error' | 'warning';
  suggestion?: string;
}
```

---

## Step-by-Step Design Specification

### Step 1: Location Selection
**Goal**: Clear, confident location selection with area understanding

#### Component Structure
```typescript
interface LocationStepProps extends StepComponentProps {
  value: LocationValue | null;
  onChange: (location: LocationValue) => void;
  showPopularLocations?: boolean;
  recentLocations?: LocationValue[];
}
```

#### Visual Layout
```
┌─────────────────────────────────────────────┐
│ Step 1 of 4: Where would you like to analyze? │
│ Most accessibility studies focus on a city     │
│ or neighborhood area.                          │
├─────────────────────────────────────────────┤
│ [Search: "Enter city, address, or ZIP code"] │
│                                               │
│ Popular Locations:                            │
│ [Denver, CO] [Austin, TX] [Portland, OR]      │
│                                               │
│ ┌─── Interactive Map (400px height) ───────┐ │
│ │  • Click to select location              │ │
│ │  • Search results highlighted           │ │
│ │  • Selected area outlined               │ │
│ │  • Zoom controls accessible             │ │
│ └─────────────────────────────────────────┘ │
│                                               │
│ Selected: Denver, Colorado                    │
│ Analysis area: ~180 sq miles                  │
│ Estimated population: ~2.8M people           │
│                                               │
│ ✓ Good data availability                      │
│                                               │
│ [< Back]                    [Continue >]      │
└─────────────────────────────────────────────┘
```

#### Validation Rules
- **Location Required**: Must select valid location
- **Area Size**: Warn if >500 sq miles (processing time)
- **Data Availability**: Check census and POI data coverage
- **Population**: Confirm reasonable population for analysis

#### Smart Features
- **Autocomplete**: Address and place name suggestions
- **Recent Locations**: Personal history of analyzed locations  
- **Popular Choices**: Commonly analyzed cities by other users
- **Area Preview**: Visual bounding box with size estimates

### Step 2: Analysis Type & POI Selection
**Goal**: Visual understanding of what will be analyzed

#### Component Structure
```typescript
interface POIStepProps extends StepComponentProps {
  selectedCategories: string[];
  customPOIs: CustomPOI[];
  location: LocationValue;
  onCategoriesChange: (categories: string[]) => void;
  onCustomPOIsChange: (pois: CustomPOI[]) => void;
  showCustomUpload?: boolean;
}
```

#### Visual Layout
```
┌─────────────────────────────────────────────┐
│ Step 2 of 4: What would you like to analyze? │
│ Choose the types of places people need to     │
│ access in Denver, Colorado.                   │
├─────────────────────────────────────────────┤
│                                               │
│ Popular Categories:                           │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│ │   🏥    │ │   🏫    │ │   🛒    │          │
│ │Healthcare│ │Education │ │ Groceries│         │
│ │23 found │ │67 found │ │89 found │          │
│ │[Selected]│ │         │ │         │          │
│ └─────────┘ └─────────┘ └─────────┘          │
│                                               │
│ All Categories:                               │
│ ┌── Healthcare ──────────────────────────┐   │
│ │ ☑️ Hospitals (23)  ☑️ Clinics (156)   │   │
│ │ ☑️ Urgent Care (45) □ Pharmacies (234) │   │
│ └─────────────────────────────────────────┘   │
│                                               │
│ ┌── Education & Culture ─────────────────┐   │
│ │ □ Schools K-12 (234)  □ Libraries (67) │   │
│ │ □ Universities (12)   □ Museums (34)   │   │
│ └─────────────────────────────────────────┘   │
│                                               │
│ [Upload Custom Locations] [Preview on Map]   │
│                                               │
│ Selected: Healthcare facilities               │
│ Total POIs: 224 locations                     │
│                                               │
│ [< Back]                    [Continue >]      │
└─────────────────────────────────────────────┘
```

#### Category Organization
```typescript
const poiCategories = {
  healthcare: {
    name: 'Healthcare Access',
    icon: '🏥',
    color: '#d32f2f',
    subcategories: [
      { id: 'hospital', name: 'Hospitals', osmTag: 'amenity=hospital' },
      { id: 'clinic', name: 'Clinics', osmTag: 'amenity=clinic' },
      { id: 'urgent_care', name: 'Urgent Care', osmTag: 'healthcare=urgentcare' },
      { id: 'pharmacy', name: 'Pharmacies', osmTag: 'amenity=pharmacy' }
    ]
  },
  education: {
    name: 'Education & Culture',
    icon: '🏫', 
    color: '#7b1fa2',
    subcategories: [
      { id: 'school', name: 'Schools K-12', osmTag: 'amenity=school' },
      { id: 'university', name: 'Universities', osmTag: 'amenity=university' },
      { id: 'library', name: 'Libraries', osmTag: 'amenity=library' },
      { id: 'museum', name: 'Museums', osmTag: 'tourism=museum' }
    ]
  },
  // ... other categories
};
```

#### Advanced Features
- **Multi-Category**: Select multiple POI types for comprehensive analysis
- **Custom Upload**: CSV/Excel file upload with validation
- **Map Preview**: Show selected POI locations on map
- **Count Estimates**: Real-time POI count updates based on location

### Step 3: Travel Parameters Configuration
**Goal**: Intuitive travel settings with visual impact understanding

#### Component Structure
```typescript
interface TravelStepProps extends StepComponentProps {
  travelTime: number;
  travelMode: TravelMode;
  advancedOptions: AdvancedTravelOptions;
  location: LocationValue;
  onTravelTimeChange: (minutes: number) => void;
  onTravelModeChange: (mode: TravelMode) => void;
  onAdvancedOptionsChange: (options: AdvancedTravelOptions) => void;
  showAdvancedOptions?: boolean;
}
```

#### Visual Layout
```
┌─────────────────────────────────────────────┐
│ Step 3 of 4: How should people travel?       │
│ Configure realistic travel settings for your │
│ accessibility analysis.                       │
├─────────────────────────────────────────────┤
│                                               │
│ Travel Time: 15 minutes                       │
│ [====●================] 5 ──────────── 60    │
│ Reaches ~180,000 people in Denver            │
│                                               │
│ Travel Mode:                                  │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐│
│ │   🚶   │ │   🚲   │ │   🚗   │ │  🚌   ││
│ │Walking  │ │ Cycling │ │Driving  │ │Transit││
│ │3 mph avg│ │10 mph   │ │25 mph   │ │Varies ││
│ │[Selected]│ │         │ │         │ │       ││
│ └─────────┘ └─────────┘ └─────────┘ └───────┘│
│                                               │
│ ┌─── Live Preview Map ───────────────────┐   │
│ │  • Shows reachable area in blue        │   │
│ │  • POI locations as pins               │   │
│ │  • Updates as you adjust settings      │   │
│ │  • Toggle layers: isochrones, POIs     │   │
│ └─────────────────────────────────────────┘   │
│                                               │
│ ▼ Advanced Options                            │
│ □ Consider traffic conditions                 │
│ □ Wheelchair accessible routes only           │
│ Time of day: [Morning Rush ▼]                │
│                                               │
│ Impact Summary:                               │
│ • 15-minute walk reaches 67% of healthcare    │
│ • Average of 3.2 hospitals within range      │
│ • 89% of residents have access               │
│                                               │
│ [< Back]                    [Continue >]      │
└─────────────────────────────────────────────┘
```

#### Travel Mode Specifications
```typescript
const travelModes = {
  walk: {
    id: 'walk',
    name: 'Walking',
    icon: '🚶',
    description: 'Pedestrian access via sidewalks',
    averageSpeed: 3, // mph
    maxRecommendedTime: 30,
    accessibilityNotes: 'Considers sidewalk availability'
  },
  bike: {
    id: 'bike', 
    name: 'Cycling',
    icon: '🚲',
    description: 'Bicycle routes and bike lanes',
    averageSpeed: 10,
    maxRecommendedTime: 45,
    accessibilityNotes: 'Uses bike-friendly routes'
  },
  drive: {
    id: 'drive',
    name: 'Driving', 
    icon: '🚗',
    description: 'Car-based access via roads',
    averageSpeed: 25,
    maxRecommendedTime: 60,
    accessibilityNotes: 'Considers traffic and parking'
  },
  transit: {
    id: 'transit',
    name: 'Public Transit',
    icon: '🚌', 
    description: 'Bus, train, and transit routes',
    averageSpeed: 'varies',
    maxRecommendedTime: 60,
    accessibilityNotes: 'Schedule-dependent, includes walking to stops'
  }
};
```

#### Smart Validations
- **Realistic Combinations**: Warn about 60-minute walking (unrealistic)
- **Mode Appropriateness**: Suggest driving for longer distances
- **Population Impact**: Show how parameter changes affect coverage
- **Data Availability**: Confirm routing data exists for selected mode

### Step 4: Demographics & Export Configuration
**Goal**: Professional output configuration with plain-language options

#### Component Structure
```typescript
interface DemographicsStepProps extends StepComponentProps {
  selectedVariables: string[];
  exportFormats: ExportFormat[];
  includeIsochrones: boolean;
  includeDemographics: boolean;
  analysisName?: string;
  onVariablesChange: (variables: string[]) => void;
  onExportFormatsChange: (formats: ExportFormat[]) => void;
  onIncludeOptionsChange: (isochrones: boolean, demographics: boolean) => void;
  onAnalysisNameChange?: (name: string) => void;
}
```

#### Visual Layout
```
┌─────────────────────────────────────────────┐
│ Step 4 of 4: What data should we include?    │
│ Choose demographic data and export options   │
│ for your accessibility analysis.             │
├─────────────────────────────────────────────┤
│                                               │
│ Demographic Variables:                        │
│                                               │
│ Quick Presets:                                │
│ [Basic Demographics] [Economic Analysis]      │
│ [Housing Study] [Age & Mobility] [Custom]    │
│                                               │
│ ┌── Population Characteristics ──────────┐   │
│ │ ☑️ Total Population                    │   │
│ │ ☑️ Age Groups (Under 18, 65+)         │   │
│ │ □ Race and Ethnicity                  │   │
│ │ □ Household Size                      │   │
│ └─────────────────────────────────────────┘   │
│                                               │
│ ┌── Economic Indicators ─────────────────┐   │
│ │ ☑️ Household Income                   │   │
│ │ ☑️ Poverty Status                     │   │
│ │ □ Employment Status                   │   │
│ │ □ Occupation Types                    │   │
│ └─────────────────────────────────────────┘   │
│                                               │
│ Analysis Outputs:                             │
│ ☑️ Include travel time boundaries (isochrones)│
│ ☑️ Include demographic breakdowns             │
│                                               │
│ Export Formats:                               │
│ ☑️ CSV (spreadsheets)  ☑️ PDF (report)       │
│ ☑️ GeoJSON (GIS)       □ Web Map (sharing)   │
│                                               │
│ Analysis Name: "Healthcare Access - Denver"  │
│ [Optional description field]                  │
│                                               │
│ [< Back]              [Start Analysis >]     │
└─────────────────────────────────────────────┘
```

#### Demographic Presets
```typescript
const demographicPresets = {
  basic: {
    name: 'Basic Demographics',
    description: 'Essential population characteristics',
    variables: ['B01003_001E', 'B25003_001E', 'B08303_001E'] // Population, Housing, Commute
  },
  economic: {
    name: 'Economic Analysis', 
    description: 'Income, poverty, and employment data',
    variables: ['B19013_001E', 'B17001_002E', 'B23025_005E'] // Income, Poverty, Unemployment
  },
  housing: {
    name: 'Housing Study',
    description: 'Homeownership, costs, and characteristics', 
    variables: ['B25003_001E', 'B25077_001E', 'B25024_001E'] // Tenure, Value, Units
  },
  ageAndMobility: {
    name: 'Age & Mobility',
    description: 'Age groups and transportation access',
    variables: ['B01001_001E', 'B08301_001E', 'B08141_001E'] // Age, Transport, No Vehicle
  }
};
```

---

## Component Architecture

### State Management
Using Redux Toolkit for complex state management:

```typescript
interface WizardState {
  currentStep: number;
  configuration: Partial<AnalysisConfiguration>;
  validation: {
    [stepId: string]: ValidationResult;
  };
  progress: {
    completedSteps: number[];
    canAdvance: boolean;
    estimatedTimeRemaining: string;
  };
  ui: {
    isLoading: boolean;
    showAdvancedOptions: boolean;
    persistProgress: boolean;
  };
}

// Redux slice
const wizardSlice = createSlice({
  name: 'wizard',
  initialState,
  reducers: {
    setCurrentStep: (state, action) => {
      state.currentStep = action.payload;
    },
    updateConfiguration: (state, action) => {
      state.configuration = { ...state.configuration, ...action.payload };
    },
    setValidation: (state, action) => {
      const { step, validation } = action.payload;
      state.validation[step] = validation;
    },
    toggleAdvancedOptions: (state) => {
      state.ui.showAdvancedOptions = !state.ui.showAdvancedOptions;
    }
  }
});
```

### Progress Persistence
Automatically save progress to localStorage:

```typescript
const useProgressPersistence = (wizardState: WizardState) => {
  useEffect(() => {
    if (wizardState.ui.persistProgress) {
      localStorage.setItem('socialmapper-wizard-progress', JSON.stringify({
        configuration: wizardState.configuration,
        currentStep: wizardState.currentStep,
        timestamp: Date.now()
      }));
    }
  }, [wizardState]);

  const loadSavedProgress = useCallback(() => {
    const saved = localStorage.getItem('socialmapper-wizard-progress');
    if (saved) {
      const data = JSON.parse(saved);
      // Only load if saved within last 24 hours
      if (Date.now() - data.timestamp < 24 * 60 * 60 * 1000) {
        return data;
      }
    }
    return null;
  }, []);

  return { loadSavedProgress };
};
```

---

## Validation System

### Step-by-Step Validation
Each step has comprehensive validation rules:

```typescript
const validationSchemas = {
  location: {
    required: ['location'],
    rules: {
      location: [
        { type: 'required', message: 'Please select a location for analysis' },
        { type: 'custom', 
          validator: (value) => value.area < 500, 
          message: 'Large areas (>500 sq miles) may take longer to process',
          severity: 'warning' 
        },
        { type: 'custom',
          validator: (value) => value.dataAvailable,
          message: 'Limited census data available for this location',
          severity: 'error'
        }
      ]
    }
  },
  poi: {
    required: ['poiCategories'],
    rules: {
      poiCategories: [
        { type: 'minLength', value: 1, message: 'Select at least one POI category' },
        { type: 'custom',
          validator: (categories, state) => {
            const totalPOIs = calculatePOICount(categories, state.location);
            return totalPOIs > 0;
          },
          message: 'No POIs found for selected categories in this area'
        }
      ]
    }
  },
  travel: {
    required: ['travelTime', 'travelMode'],
    rules: {
      travelTime: [
        { type: 'range', min: 5, max: 60, message: 'Travel time must be 5-60 minutes' },
        { type: 'custom',
          validator: (time, state) => {
            if (state.travelMode === 'walk' && time > 30) {
              return { valid: false, severity: 'warning' };
            }
            return { valid: true };
          },
          message: 'Walking times over 30 minutes are uncommon in accessibility studies'
        }
      ]
    }
  }
};
```

### Real-time Validation
Validation occurs as user interacts:

```typescript
const useRealtimeValidation = (step: string, configuration: Partial<AnalysisConfiguration>) => {
  const [validation, setValidation] = useState<ValidationResult>({ valid: true, errors: [] });

  useEffect(() => {
    const schema = validationSchemas[step];
    if (schema) {
      const result = validateStep(schema, configuration);
      setValidation(result);
    }
  }, [step, configuration]);

  return validation;
};
```

---

## Advanced Features

### Smart Defaults
Context-aware default values:

```typescript
const getSmartDefaults = (location: LocationValue, userHistory?: AnalysisConfiguration[]) => {
  const defaults: Partial<AnalysisConfiguration> = {
    travelTime: 15, // Most common in literature
    travelMode: 'walk', // Most equitable analysis
    includeIsochrones: true,
    includeDemographics: true
  };

  // Adjust based on location characteristics
  if (location.populationDensity < 1000) {
    defaults.travelMode = 'drive'; // Rural areas typically car-dependent
    defaults.travelTime = 30;
  }

  // Learn from user history
  if (userHistory && userHistory.length > 0) {
    const mostCommonMode = findMostCommon(userHistory.map(h => h.travelMode));
    const avgTravelTime = average(userHistory.map(h => h.travelTime));
    
    defaults.travelMode = mostCommonMode;
    defaults.travelTime = Math.round(avgTravelTime);
  }

  return defaults;
};
```

### Expert Mode
Streamlined interface for experienced users:

```typescript
const ExpertModeToggle: React.FC = () => {
  const [isExpertMode, setIsExpertMode] = useState(false);
  
  if (isExpertMode) {
    return (
      <ExpertConfigurationPanel 
        onConfigurationComplete={onComplete}
        showGuidance={false}
        allowAdvancedParameters={true}
      />
    );
  }

  return <StandardWizard />;
};
```

### Configuration Templates
Save and reuse analysis configurations:

```typescript
interface ConfigurationTemplate {
  id: string;
  name: string;
  description: string;
  configuration: AnalysisConfiguration;
  tags: string[];
  isPublic: boolean;
  usageCount: number;
  createdBy: string;
  createdAt: string;
}

const useConfigurationTemplates = () => {
  const saveAsTemplate = useCallback((config: AnalysisConfiguration, metadata: TemplateMetadata) => {
    // Save configuration as reusable template
  }, []);

  const loadTemplate = useCallback((templateId: string) => {
    // Load saved template into wizard
  }, []);

  return { saveAsTemplate, loadTemplate };
};
```

---

## Accessibility Implementation

### Keyboard Navigation
Complete keyboard accessibility:

```typescript
const useWizardKeyboardNavigation = (currentStep: number, maxStep: number) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      switch (event.key) {
        case 'ArrowLeft':
          if (event.ctrlKey && currentStep > 0) {
            // Ctrl+Left: Previous step
            dispatch(setCurrentStep(currentStep - 1));
          }
          break;
        case 'ArrowRight':
          if (event.ctrlKey && currentStep < maxStep) {
            // Ctrl+Right: Next step (if valid)
            dispatch(setCurrentStep(currentStep + 1));
          }
          break;
        case 'Escape':
          // Show exit confirmation
          setShowExitConfirmation(true);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentStep, maxStep]);
};
```

### Screen Reader Support
Comprehensive ARIA implementation:

```typescript
const QueryWizard: React.FC<QueryWizardProps> = (props) => {
  return (
    <div 
      role="application"
      aria-label="Analysis Configuration Wizard"
      aria-describedby="wizard-description"
    >
      <div id="wizard-description" className="sr-only">
        4-step wizard to configure your accessibility analysis. 
        Use arrow keys to navigate between steps.
      </div>
      
      <WizardProgress 
        currentStep={currentStep}
        totalSteps={4}
        aria-label="Configuration progress"
      />
      
      <div 
        role="tabpanel"
        aria-labelledby={`step-${currentStep}-title`}
        aria-describedby={`step-${currentStep}-description`}
      >
        {currentStepComponent}
      </div>
    </div>
  );
};
```

### High Contrast Support
CSS custom properties for accessibility themes:

```css
.query-wizard[data-theme="high-contrast"] {
  --wizard-bg: #000000;
  --wizard-text: #ffffff;
  --wizard-border: #ffff00;
  --wizard-focus: #ff0000;
  --wizard-selected: #00ff00;
}

.query-wizard[data-theme="high-contrast"] .wizard-step {
  border: 2px solid var(--wizard-border);
  background: var(--wizard-bg);
  color: var(--wizard-text);
}

.query-wizard[data-theme="high-contrast"] .wizard-step:focus-within {
  outline: 3px solid var(--wizard-focus);
  outline-offset: 2px;
}
```

---

## Performance Optimization

### Lazy Loading
Load step components on demand:

```typescript
const LocationStep = lazy(() => import('./steps/LocationStep'));
const POIStep = lazy(() => import('./steps/POIStep'));
const TravelStep = lazy(() => import('./steps/TravelStep'));
const DemographicsStep = lazy(() => import('./steps/DemographicsStep'));

const stepComponents = [
  LocationStep,
  POIStep, 
  TravelStep,
  DemographicsStep
];

const CurrentStepComponent = stepComponents[currentStep];

return (
  <Suspense fallback={<StepLoadingSkeleton />}>
    <CurrentStepComponent {...stepProps} />
  </Suspense>
);
```

### Debounced API Calls
Optimize real-time validation and preview updates:

```typescript
const useDebouncedLocationUpdate = (location: LocationValue | null) => {
  const [debouncedLocation, setDebouncedLocation] = useState(location);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedLocation(location);
    }, 500); // 500ms debounce
    
    return () => clearTimeout(timer);
  }, [location]);

  return debouncedLocation;
};

// Use debounced value for API calls
const { data: poiCounts } = usePOICountQuery(debouncedLocation, {
  skip: !debouncedLocation
});
```

### Memoization
Prevent unnecessary re-renders:

```typescript
const WizardStep = memo<WizardStepProps>(({ 
  stepData, 
  validation, 
  onChange 
}) => {
  const memoizedValidation = useMemo(() => 
    validation, 
    [validation.valid, validation.errors]
  );

  const handleChange = useCallback((data: Partial<StepData>) => {
    onChange(data);
  }, [onChange]);

  return (
    <div className="wizard-step">
      {/* Step content */}
    </div>
  );
});
```

---

## Testing Strategy

### Component Testing
Comprehensive test coverage:

```typescript
describe('QueryWizard', () => {
  describe('Step Navigation', () => {
    it('should advance to next step when current step is valid', async () => {
      const onStepChange = jest.fn();
      render(<QueryWizard onStepChange={onStepChange} />);
      
      // Complete location step
      await userEvent.type(screen.getByRole('searchbox'), 'Denver, CO');
      await userEvent.click(screen.getByRole('button', { name: /continue/i }));
      
      expect(onStepChange).toHaveBeenCalledWith(1, expect.any(Object));
    });

    it('should prevent advancement when step is invalid', async () => {
      render(<QueryWizard />);
      
      // Try to continue without selecting location
      await userEvent.click(screen.getByRole('button', { name: /continue/i }));
      
      expect(screen.getByText(/please select a location/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should support keyboard navigation', async () => {
      render(<QueryWizard />);
      
      // Focus wizard
      const wizard = screen.getByRole('application');
      wizard.focus();
      
      // Test keyboard navigation
      await userEvent.keyboard('{Control>}{ArrowRight}{/Control}');
      
      // Should not advance (step invalid)
      expect(screen.getByText(/step 1 of 4/i)).toBeInTheDocument();
    });

    it('should announce step changes to screen readers', async () => {
      render(<QueryWizard />);
      
      // Complete first step and advance
      await completeLocationStep();
      
      expect(screen.getByRole('status')).toHaveTextContent(/step 2 of 4/i);
    });
  });

  describe('Data Persistence', () => {
    it('should save progress to localStorage', async () => {
      const localStorageSpy = jest.spyOn(Storage.prototype, 'setItem');
      
      render(<QueryWizard persistProgress={true} />);
      
      // Make selections
      await completeLocationStep();
      
      expect(localStorageSpy).toHaveBeenCalledWith(
        'socialmapper-wizard-progress',
        expect.stringContaining('configuration')
      );
    });

    it('should restore progress from localStorage', () => {
      // Mock saved progress
      jest.spyOn(Storage.prototype, 'getItem').mockReturnValue(
        JSON.stringify({
          configuration: { location: mockLocation },
          currentStep: 1,
          timestamp: Date.now()
        })
      );

      render(<QueryWizard />);
      
      expect(screen.getByText(/step 2 of 4/i)).toBeInTheDocument();
    });
  });
});
```

### Integration Testing
Test complete wizard workflows:

```typescript
describe('Complete Analysis Workflow', () => {
  it('should complete full wizard and submit analysis', async () => {
    const onComplete = jest.fn();
    render(<QueryWizard onComplete={onComplete} />);
    
    // Complete all steps
    await completeLocationStep();
    await completePOIStep();
    await completeTravelStep(); 
    await completeDemographicsStep();
    
    // Submit analysis
    await userEvent.click(screen.getByRole('button', { name: /start analysis/i }));
    
    expect(onComplete).toHaveBeenCalledWith({
      location: expect.any(Object),
      poiCategories: expect.any(Array),
      travelTime: expect.any(Number),
      travelMode: expect.any(String),
      demographicVariables: expect.any(Array),
      exportFormats: expect.any(Array),
      includeIsochrones: true,
      includeDemographics: true
    });
  });
});
```

### Accessibility Testing
Automated accessibility validation:

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('QueryWizard Accessibility', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<QueryWizard />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should support screen reader navigation', () => {
    render(<QueryWizard />);
    
    // Verify proper ARIA structure
    expect(screen.getByRole('application')).toHaveAttribute('aria-label');
    expect(screen.getByRole('tabpanel')).toHaveAttribute('aria-labelledby');
  });
});
```

---

## Success Metrics & Analytics

### User Experience Metrics
Track wizard performance:

```typescript
const useWizardAnalytics = () => {
  const trackStepCompletion = (step: number, timeSpent: number) => {
    analytics.track('wizard_step_completed', {
      step,
      timeSpent,
      timestamp: Date.now()
    });
  };

  const trackValidationError = (step: number, error: ValidationError) => {
    analytics.track('wizard_validation_error', {
      step,
      field: error.field,
      message: error.message,
      severity: error.severity
    });
  };

  const trackWizardAbandonment = (step: number, reason?: string) => {
    analytics.track('wizard_abandoned', {
      step,
      reason,
      progress: step / 4
    });
  };

  return { trackStepCompletion, trackValidationError, trackWizardAbandonment };
};
```

### Performance Monitoring
Real-time performance tracking:

```typescript
const usePerformanceMonitoring = () => {
  useEffect(() => {
    // Monitor component render time
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.name.includes('wizard')) {
          analytics.track('wizard_performance', {
            component: entry.name,
            duration: entry.duration,
            startTime: entry.startTime
          });
        }
      });
    });

    observer.observe({ entryTypes: ['measure'] });

    return () => observer.disconnect();
  }, []);
};
```

---

*This QueryWizard component specification provides the foundation for an intuitive, accessible, and efficient analysis configuration experience that transforms complex GIS parameters into a guided visual workflow.*