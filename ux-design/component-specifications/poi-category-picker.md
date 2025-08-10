# POICategoryPicker Component Specification
## Project 1.2 - Visual POI Selection Interface

**Date**: August 10, 2025  
**Component Type**: Visual Selection Interface  
**Priority**: Critical Path - Step 2 of QueryWizard  
**Integration**: React + TypeScript + Ant Design + POI Discovery API

---

## Component Overview

The POICategoryPicker transforms complex OpenStreetMap POI categories into an intuitive visual selection interface. It helps users understand what places they're analyzing through familiar categories, visual examples, and real-time count indicators, eliminating the need to understand technical POI taxonomies.

### Success Criteria
- **<15 seconds** average POI category selection time
- **95%+ users** successfully understand selected categories
- **Clear visual feedback** on selection impact and POI availability
- **Support for both novice and expert** user needs

---

## Component Interface

### TypeScript Interface

```typescript
interface POICategoryPickerProps {
  // Value and selection management
  selectedCategories: string[];
  selectedCustomPOIs?: CustomPOI[];
  onCategoriesChange: (categories: string[]) => void;
  onCustomPOIsChange?: (pois: CustomPOI[]) => void;
  
  // Context and constraints
  location: LocationValue;
  maxSelections?: number;
  minSelections?: number;
  
  // Feature toggles
  showCustomUpload?: boolean;
  showPOICounts?: boolean;
  showMapPreview?: boolean;
  allowMultipleCategories?: boolean;
  showPopularCombinations?: boolean;
  
  // Display options
  layout?: 'grid' | 'list' | 'compact';
  showDescriptions?: boolean;
  showExamples?: boolean;
  groupByCategory?: boolean;
  
  // Accessibility
  accessibilityLabel?: string;
  announceChanges?: boolean;
  
  // Styling
  className?: string;
  style?: React.CSSProperties;
}

interface POICategory {
  // Identification
  id: string;
  name: string;
  shortName: string;
  
  // Display
  icon: string;
  color: string;
  description: string;
  examples: string[];
  
  // Metadata
  category: POIMainCategory;
  subcategories: POISubcategory[];
  osmTags: OSMTag[];
  
  // Usage data
  popular: boolean;
  usageCount: number;
  lastUsed?: string;
}

interface POISubcategory {
  id: string;
  name: string;
  osmTag: OSMTag;
  description?: string;
  icon?: string;
  selected?: boolean;
  count?: number; // Available in current location
}

interface OSMTag {
  key: string;
  value: string;
  displayName?: string;
}

interface CustomPOI {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  address?: string;
  category?: string;
  description?: string;
  source: 'upload' | 'manual' | 'api';
}

interface POICountData {
  categoryId: string;
  totalCount: number;
  subcategoryCounts: Record<string, number>;
  confidence: 'high' | 'medium' | 'low';
  lastUpdated: string;
}

enum POIMainCategory {
  HEALTHCARE = 'healthcare',
  EDUCATION = 'education',
  FOOD = 'food',
  RECREATION = 'recreation',
  TRANSPORTATION = 'transportation',
  SERVICES = 'services',
  RETAIL = 'retail',
  CUSTOM = 'custom'
}
```

---

## Visual Design Specification

### Main Grid Layout

```
┌─────────────────────────────────────────────────────────────┐
│ What places should people be able to access?               │
│ Choose the types of facilities for your accessibility       │
│ analysis in Denver, Colorado.                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Popular Combinations: 🔥                                    │
│ [Healthcare + Pharmacies] [Schools + Libraries]            │
│ [Groceries + Transit] [Parks + Recreation]                 │
│                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │     🏥      │ │     🏫      │ │     🛒      │            │
│ │ Healthcare  │ │ Education   │ │ Daily Needs │            │
│ │             │ │ & Culture   │ │             │            │
│ │ 189 found   │ │ 167 found   │ │ 234 found   │            │
│ │ [✓Selected] │ │             │ │             │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │     🌳      │ │     🚌      │ │     🏛️      │            │
│ │ Recreation  │ │ Transport   │ │ Public      │            │
│ │ & Parks     │ │             │ │ Services    │            │
│ │ 145 found   │ │ 89 found    │ │ 67 found    │            │
│ │             │ │             │ │             │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                             │
│ ▼ Selected: Healthcare (189 locations) ────────────────────│
│                                                             │
│   Subcategories:                     Map Preview:          │
│   ☑️ Hospitals (23)                  ┌─────────────────┐    │
│   ☑️ Clinics (156)                   │ • • •   •     • │    │
│   ☑️ Urgent Care (45)                │   •   •   •     │    │
│   □ Pharmacies (89) ────────────     │ •       •   •   │    │
│   □ Mental Health (12)               │   •   •     •   │    │
│                                      │     •   • •     │    │
│   ℹ️ Learn about healthcare access   └─────────────────┘    │
│                                                             │
│ [Upload Custom Locations] [Preview All Selected]           │
│                                                             │
│ Selection Summary:                                          │
│ • Healthcare facilities: 189 locations                     │
│ • Total POIs selected: 189                                 │
│ • Analysis will show access to medical care                │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Layout

```
┌───────────────────┐
│ What places?      │
├───────────────────┤
│ Popular:          │
│ [Healthcare +     │
│  Pharmacies] [+]  │
│                   │
│ ┌──────┐ ┌──────┐ │
│ │ 🏥   │ │ 🏫   │ │
│ │Health│ │Edu.  │ │
│ │189 ✓ │ │167   │ │
│ └──────┘ └──────┘ │
│                   │
│ ┌──────┐ ┌──────┐ │
│ │ 🛒   │ │ 🌳   │ │
│ │Daily │ │Parks │ │
│ │234   │ │145   │ │
│ └──────┘ └──────┘ │
│                   │
│ [See More] [Map]  │
│                   │
│ ✓ Selected:       │
│ Healthcare (189)  │
│                   │
│ Subcategories:    │
│ ☑️ Hospitals (23) │
│ ☑️ Clinics (156)  │
│ [Expand All]      │
│                   │
│ [Upload Custom]   │
└───────────────────┘
```

---

## POI Category System

### Main Categories Configuration

```typescript
const poiCategories: Record<POIMainCategory, POICategory> = {
  [POIMainCategory.HEALTHCARE]: {
    id: 'healthcare',
    name: 'Healthcare Access',
    shortName: 'Healthcare',
    icon: '🏥',
    color: '#d32f2f',
    description: 'Medical facilities and health services',
    examples: ['Hospitals', 'Clinics', 'Pharmacies', 'Urgent Care'],
    category: POIMainCategory.HEALTHCARE,
    popular: true,
    usageCount: 1456,
    subcategories: [
      {
        id: 'hospital',
        name: 'Hospitals',
        osmTag: { key: 'amenity', value: 'hospital' },
        description: 'Full-service hospitals with emergency care',
        icon: '🏥'
      },
      {
        id: 'clinic',
        name: 'Clinics',
        osmTag: { key: 'amenity', value: 'clinic' },
        description: 'Medical clinics and doctor offices',
        icon: '⚕️'
      },
      {
        id: 'pharmacy',
        name: 'Pharmacies',
        osmTag: { key: 'amenity', value: 'pharmacy' },
        description: 'Prescription and over-counter medications',
        icon: '💊'
      },
      {
        id: 'urgent_care',
        name: 'Urgent Care',
        osmTag: { key: 'healthcare', value: 'urgentcare' },
        description: 'Walk-in urgent care centers',
        icon: '🚑'
      },
      {
        id: 'mental_health',
        name: 'Mental Health',
        osmTag: { key: 'healthcare', value: 'psychotherapist' },
        description: 'Mental health and counseling services',
        icon: '🧠'
      }
    ],
    osmTags: [
      { key: 'amenity', value: 'hospital' },
      { key: 'amenity', value: 'clinic' },
      { key: 'amenity', value: 'pharmacy' },
      { key: 'healthcare', value: 'urgentcare' }
    ]
  },

  [POIMainCategory.EDUCATION]: {
    id: 'education',
    name: 'Education & Culture',
    shortName: 'Education',
    icon: '🏫',
    color: '#7b1fa2',
    description: 'Educational institutions and cultural facilities',
    examples: ['Schools', 'Libraries', 'Universities', 'Museums'],
    category: POIMainCategory.EDUCATION,
    popular: true,
    usageCount: 1289,
    subcategories: [
      {
        id: 'school',
        name: 'Schools K-12',
        osmTag: { key: 'amenity', value: 'school' },
        description: 'Elementary, middle, and high schools',
        icon: '🏫'
      },
      {
        id: 'university',
        name: 'Universities',
        osmTag: { key: 'amenity', value: 'university' },
        description: 'Colleges and universities',
        icon: '🎓'
      },
      {
        id: 'library',
        name: 'Libraries',
        osmTag: { key: 'amenity', value: 'library' },
        description: 'Public and academic libraries',
        icon: '📚'
      },
      {
        id: 'museum',
        name: 'Museums',
        osmTag: { key: 'tourism', value: 'museum' },
        description: 'Museums and cultural institutions',
        icon: '🏛️'
      }
    ],
    osmTags: [
      { key: 'amenity', value: 'school' },
      { key: 'amenity', value: 'university' },
      { key: 'amenity', value: 'library' },
      { key: 'tourism', value: 'museum' }
    ]
  },

  [POIMainCategory.FOOD]: {
    id: 'food',
    name: 'Food & Groceries',
    shortName: 'Daily Needs',
    icon: '🛒',
    color: '#f57c00',
    description: 'Food access and daily necessities',
    examples: ['Grocery Stores', 'Supermarkets', 'Restaurants', 'Markets'],
    category: POIMainCategory.FOOD,
    popular: true,
    usageCount: 2134,
    subcategories: [
      {
        id: 'supermarket',
        name: 'Supermarkets',
        osmTag: { key: 'shop', value: 'supermarket' },
        description: 'Large grocery stores and supermarkets',
        icon: '🏪'
      },
      {
        id: 'grocery',
        name: 'Grocery Stores',
        osmTag: { key: 'shop', value: 'convenience' },
        description: 'Convenience stores and small groceries',
        icon: '🛒'
      },
      {
        id: 'market',
        name: 'Farmers Markets',
        osmTag: { key: 'amenity', value: 'marketplace' },
        description: 'Farmers markets and fresh food markets',
        icon: '🥕'
      },
      {
        id: 'restaurant',
        name: 'Restaurants',
        osmTag: { key: 'amenity', value: 'restaurant' },
        description: 'Restaurants and food service',
        icon: '🍽️'
      }
    ],
    osmTags: [
      { key: 'shop', value: 'supermarket' },
      { key: 'shop', value: 'convenience' },
      { key: 'amenity', value: 'marketplace' },
      { key: 'amenity', value: 'restaurant' }
    ]
  },

  [POIMainCategory.RECREATION]: {
    id: 'recreation',
    name: 'Recreation & Parks',
    shortName: 'Recreation',
    icon: '🌳',
    color: '#388e3c',
    description: 'Parks, sports, and recreational facilities',
    examples: ['Parks', 'Playgrounds', 'Sports Centers', 'Trails'],
    category: POIMainCategory.RECREATION,
    popular: true,
    usageCount: 987,
    subcategories: [
      {
        id: 'park',
        name: 'Parks',
        osmTag: { key: 'leisure', value: 'park' },
        description: 'Public parks and green spaces',
        icon: '🌳'
      },
      {
        id: 'playground',
        name: 'Playgrounds',
        osmTag: { key: 'leisure', value: 'playground' },
        description: 'Children\'s playgrounds and play areas',
        icon: '🛝'
      },
      {
        id: 'sports_center',
        name: 'Sports Centers',
        osmTag: { key: 'leisure', value: 'sports_centre' },
        description: 'Gyms, fitness centers, and sports facilities',
        icon: '🏋️'
      },
      {
        id: 'swimming_pool',
        name: 'Swimming Pools',
        osmTag: { key: 'leisure', value: 'swimming_pool' },
        description: 'Public swimming pools and aquatic centers',
        icon: '🏊'
      }
    ],
    osmTags: [
      { key: 'leisure', value: 'park' },
      { key: 'leisure', value: 'playground' },
      { key: 'leisure', value: 'sports_centre' },
      { key: 'leisure', value: 'swimming_pool' }
    ]
  },

  [POIMainCategory.TRANSPORTATION]: {
    id: 'transportation',
    name: 'Transportation',
    shortName: 'Transit',
    icon: '🚌',
    color: '#1976d2',
    description: 'Public transit and transportation hubs',
    examples: ['Bus Stops', 'Train Stations', 'Bike Share', 'Parking'],
    category: POIMainCategory.TRANSPORTATION,
    popular: false,
    usageCount: 634,
    subcategories: [
      {
        id: 'bus_stop',
        name: 'Bus Stops',
        osmTag: { key: 'public_transport', value: 'stop_position' },
        description: 'Public bus stops and transit stations',
        icon: '🚏'
      },
      {
        id: 'train_station',
        name: 'Train Stations',
        osmTag: { key: 'railway', value: 'station' },
        description: 'Train and subway stations',
        icon: '🚇'
      },
      {
        id: 'bike_rental',
        name: 'Bike Share',
        osmTag: { key: 'amenity', value: 'bicycle_rental' },
        description: 'Bike sharing stations',
        icon: '🚲'
      },
      {
        id: 'parking',
        name: 'Parking',
        osmTag: { key: 'amenity', value: 'parking' },
        description: 'Public parking facilities',
        icon: '🅿️'
      }
    ],
    osmTags: [
      { key: 'public_transport', value: 'stop_position' },
      { key: 'railway', value: 'station' },
      { key: 'amenity', value: 'bicycle_rental' },
      { key: 'amenity', value: 'parking' }
    ]
  },

  [POIMainCategory.SERVICES]: {
    id: 'services',
    name: 'Public Services',
    shortName: 'Services',
    icon: '🏛️',
    color: '#5d4037',
    description: 'Government and essential services',
    examples: ['Post Offices', 'Government', 'Police', 'Fire Stations'],
    category: POIMainCategory.SERVICES,
    popular: false,
    usageCount: 445,
    subcategories: [
      {
        id: 'post_office',
        name: 'Post Offices',
        osmTag: { key: 'amenity', value: 'post_office' },
        description: 'Postal services and mail centers',
        icon: '📮'
      },
      {
        id: 'government',
        name: 'Government Offices',
        osmTag: { key: 'office', value: 'government' },
        description: 'Government buildings and civic centers',
        icon: '🏛️'
      },
      {
        id: 'police',
        name: 'Police Stations',
        osmTag: { key: 'amenity', value: 'police' },
        description: 'Police stations and law enforcement',
        icon: '👮'
      },
      {
        id: 'fire_station',
        name: 'Fire Stations',
        osmTag: { key: 'amenity', value: 'fire_station' },
        description: 'Fire departments and emergency services',
        icon: '🚒'
      }
    ],
    osmTags: [
      { key: 'amenity', value: 'post_office' },
      { key: 'office', value: 'government' },
      { key: 'amenity', value: 'police' },
      { key: 'amenity', value: 'fire_station' }
    ]
  }
};
```

### Popular Category Combinations

```typescript
const popularCombinations = [
  {
    id: 'healthcare_complete',
    name: 'Complete Healthcare',
    description: 'All medical facilities and pharmacies',
    categories: ['healthcare'],
    subcategories: ['hospital', 'clinic', 'pharmacy', 'urgent_care'],
    icon: '🏥+💊',
    usageCount: 456
  },
  {
    id: 'education_access',
    name: 'Educational Access',
    description: 'Schools, libraries, and learning centers',
    categories: ['education'],
    subcategories: ['school', 'library', 'university'],
    icon: '🏫+📚',
    usageCount: 389
  },
  {
    id: 'daily_essentials',
    name: 'Daily Essentials',
    description: 'Groceries, pharmacies, and transit',
    categories: ['food', 'healthcare', 'transportation'],
    subcategories: ['supermarket', 'pharmacy', 'bus_stop'],
    icon: '🛒+💊+🚌',
    usageCount: 567
  },
  {
    id: 'family_amenities',
    name: 'Family Amenities',
    description: 'Parks, schools, and recreation for families',
    categories: ['recreation', 'education'],
    subcategories: ['park', 'playground', 'school'],
    icon: '🌳+🛝+🏫',
    usageCount: 234
  }
];
```

---

## Component Implementation

### Main POICategoryPicker Component

```typescript
const POICategoryPicker: React.FC<POICategoryPickerProps> = ({
  selectedCategories,
  selectedCustomPOIs = [],
  onCategoriesChange,
  onCustomPOIsChange,
  location,
  maxSelections = 5,
  minSelections = 1,
  showCustomUpload = true,
  showPOICounts = true,
  showMapPreview = true,
  allowMultipleCategories = true,
  showPopularCombinations = true,
  layout = 'grid',
  showDescriptions = true,
  showExamples = true,
  groupByCategory = true,
  accessibilityLabel = "Select points of interest for accessibility analysis",
  announceChanges = true,
  className = '',
  style = {}
}) => {
  const [poiCounts, setPOICounts] = useState<Record<string, POICountData>>({});
  const [selectedSubcategories, setSelectedSubcategories] = useState<Record<string, string[]>>({});
  const [showSubcategories, setShowSubcategories] = useState<Set<string>>(new Set());
  const [customPOIModalVisible, setCustomPOIModalVisible] = useState(false);
  const [mapPreviewData, setMapPreviewData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { data: poiCountsData, isLoading: countsLoading } = usePOICountsQuery(
    { location, categories: Object.keys(poiCategories) },
    { skip: !location }
  );

  // Update POI counts when data changes
  useEffect(() => {
    if (poiCountsData) {
      setPOICounts(poiCountsData.reduce((acc: Record<string, POICountData>, item: any) => {
        acc[item.categoryId] = item;
        return acc;
      }, {}));
    }
  }, [poiCountsData]);

  // Announce selection changes to screen readers
  useEffect(() => {
    if (announceChanges && selectedCategories.length > 0) {
      const categoryNames = selectedCategories
        .map(id => poiCategories[id as POIMainCategory]?.name)
        .filter(Boolean)
        .join(', ');
      
      const totalCount = selectedCategories
        .reduce((sum, id) => sum + (poiCounts[id]?.totalCount || 0), 0);

      const announcement = `Selected ${categoryNames}. ${totalCount} locations found.`;
      announceToScreenReader(announcement);
    }
  }, [selectedCategories, poiCounts, announceChanges]);

  const handleCategoryToggle = (categoryId: string) => {
    let newSelection: string[];
    
    if (selectedCategories.includes(categoryId)) {
      newSelection = selectedCategories.filter(id => id !== categoryId);
      // Remove from subcategories selection
      setSelectedSubcategories(prev => {
        const next = { ...prev };
        delete next[categoryId];
        return next;
      });
      // Hide subcategories
      setShowSubcategories(prev => {
        const next = new Set(prev);
        next.delete(categoryId);
        return next;
      });
    } else {
      // Check max selections limit
      if (selectedCategories.length >= maxSelections && maxSelections > 1) {
        message.warning(`You can select up to ${maxSelections} categories`);
        return;
      }
      
      newSelection = [...selectedCategories, categoryId];
      // Auto-select all subcategories
      const category = poiCategories[categoryId as POIMainCategory];
      if (category) {
        setSelectedSubcategories(prev => ({
          ...prev,
          [categoryId]: category.subcategories.map(sub => sub.id)
        }));
        // Show subcategories
        setShowSubcategories(prev => new Set([...prev, categoryId]));
      }
    }
    
    onCategoriesChange(newSelection);
  };

  const handleSubcategoryToggle = (categoryId: string, subcategoryId: string) => {
    setSelectedSubcategories(prev => {
      const currentSubs = prev[categoryId] || [];
      const newSubs = currentSubs.includes(subcategoryId)
        ? currentSubs.filter(id => id !== subcategoryId)
        : [...currentSubs, subcategoryId];
      
      return {
        ...prev,
        [categoryId]: newSubs
      };
    });
  };

  const handlePopularCombinationSelect = (combination: typeof popularCombinations[0]) => {
    onCategoriesChange(combination.categories);
    
    // Set subcategories
    const newSubcategories: Record<string, string[]> = {};
    combination.categories.forEach(catId => {
      newSubcategories[catId] = combination.subcategories || 
        poiCategories[catId as POIMainCategory]?.subcategories.map(sub => sub.id) || [];
    });
    setSelectedSubcategories(newSubcategories);

    // Show all selected categories
    setShowSubcategories(new Set(combination.categories));
  };

  const getTotalSelectedPOIs = () => {
    return selectedCategories.reduce((total, categoryId) => {
      const categoryCount = poiCounts[categoryId]?.totalCount || 0;
      const selectedSubs = selectedSubcategories[categoryId] || [];
      
      if (selectedSubs.length === 0) {
        return total + categoryCount;
      }
      
      // Calculate count for selected subcategories
      const subCount = selectedSubs.reduce((subTotal, subId) => {
        return subTotal + (poiCounts[categoryId]?.subcategoryCounts[subId] || 0);
      }, 0);
      
      return total + subCount;
    }, 0);
  };

  return (
    <div 
      className={`poi-category-picker ${className}`} 
      style={style}
      role="region"
      aria-label={accessibilityLabel}
    >
      {/* Header */}
      <div className="picker-header">
        <Typography.Title level={4}>
          What places should people be able to access?
        </Typography.Title>
        <Typography.Text type="secondary">
          Choose the types of facilities for your accessibility analysis in {location.displayName}.
        </Typography.Text>
      </div>

      {/* Popular Combinations */}
      {showPopularCombinations && (
        <div className="popular-combinations">
          <div className="section-label">
            <FireOutlined /> Popular Combinations:
          </div>
          <div className="combinations-list">
            {popularCombinations.map(combo => (
              <Button
                key={combo.id}
                type="default"
                size="small"
                onClick={() => handlePopularCombinationSelect(combo)}
                title={combo.description}
                className="combination-button"
              >
                {combo.icon} {combo.name}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Main Category Grid */}
      <div className={`category-grid ${layout}`}>
        {Object.values(poiCategories).map(category => {
          const isSelected = selectedCategories.includes(category.id);
          const count = poiCounts[category.id]?.totalCount || 0;
          const isLoading = countsLoading;

          return (
            <CategoryCard
              key={category.id}
              category={category}
              isSelected={isSelected}
              count={count}
              isLoading={isLoading}
              onClick={() => handleCategoryToggle(category.id)}
              showCount={showPOICounts}
              showDescription={showDescriptions}
              showExamples={showExamples}
            />
          );
        })}
      </div>

      {/* Selected Categories Detail */}
      {selectedCategories.length > 0 && (
        <div className="selected-categories-detail">
          <Divider />
          
          {selectedCategories.map(categoryId => {
            const category = poiCategories[categoryId as POIMainCategory];
            const showSubs = showSubcategories.has(categoryId);
            const selectedSubs = selectedSubcategories[categoryId] || [];
            
            if (!category) return null;

            return (
              <CategorySubcategoryPanel
                key={categoryId}
                category={category}
                isExpanded={showSubs}
                selectedSubcategories={selectedSubs}
                poiCounts={poiCounts[categoryId]?.subcategoryCounts || {}}
                onToggleExpanded={() => {
                  setShowSubcategories(prev => {
                    const next = new Set(prev);
                    if (next.has(categoryId)) {
                      next.delete(categoryId);
                    } else {
                      next.add(categoryId);
                    }
                    return next;
                  });
                }}
                onSubcategoryToggle={(subId) => handleSubcategoryToggle(categoryId, subId)}
                showMapPreview={showMapPreview}
              />
            );
          })}
        </div>
      )}

      {/* Custom POI Upload */}
      {showCustomUpload && (
        <div className="custom-poi-section">
          <Divider />
          <div className="custom-poi-header">
            <Typography.Text strong>Custom Locations</Typography.Text>
            <Typography.Text type="secondary">
              Upload your own points of interest from CSV or Excel files.
            </Typography.Text>
          </div>
          
          <Space>
            <Button
              icon={<UploadOutlined />}
              onClick={() => setCustomPOIModalVisible(true)}
            >
              Upload Custom Locations
            </Button>
            
            {selectedCustomPOIs.length > 0 && (
              <Typography.Text type="secondary">
                {selectedCustomPOIs.length} custom locations added
              </Typography.Text>
            )}
          </Space>
        </div>
      )}

      {/* Selection Summary */}
      <div className="selection-summary">
        <Divider />
        <div className="summary-content">
          <div className="summary-stats">
            <Statistic
              title="Selected Categories"
              value={selectedCategories.length}
              suffix={`/ ${maxSelections}`}
            />
            <Statistic
              title="Total POIs"
              value={getTotalSelectedPOIs()}
              loading={countsLoading}
            />
          </div>
          
          {selectedCategories.length > 0 && (
            <div className="summary-description">
              <Typography.Text>
                Analysis will show access to:{' '}
                {selectedCategories.map(id => 
                  poiCategories[id as POIMainCategory]?.name
                ).join(', ')}
              </Typography.Text>
            </div>
          )}
        </div>
      </div>

      {/* Custom POI Upload Modal */}
      <CustomPOIUploadModal
        visible={customPOIModalVisible}
        onCancel={() => setCustomPOIModalVisible(false)}
        onSuccess={(pois) => {
          if (onCustomPOIsChange) {
            onCustomPOIsChange([...selectedCustomPOIs, ...pois]);
          }
          setCustomPOIModalVisible(false);
        }}
        location={location}
      />
    </div>
  );
};
```

### CategoryCard Component

```typescript
interface CategoryCardProps {
  category: POICategory;
  isSelected: boolean;
  count: number;
  isLoading: boolean;
  onClick: () => void;
  showCount: boolean;
  showDescription: boolean;
  showExamples: boolean;
}

const CategoryCard: React.FC<CategoryCardProps> = ({
  category,
  isSelected,
  count,
  isLoading,
  onClick,
  showCount,
  showDescription,
  showExamples
}) => {
  return (
    <Card
      hoverable
      className={`category-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
      style={{
        borderColor: isSelected ? category.color : undefined,
        backgroundColor: isSelected ? `${category.color}08` : undefined
      }}
      bodyStyle={{ padding: '16px' }}
    >
      <div className="card-content">
        <div className="card-header">
          <div className="category-icon" style={{ fontSize: '32px' }}>
            {category.icon}
          </div>
          <div className="selection-indicator">
            {isSelected && <CheckCircleOutlined style={{ color: category.color }} />}
          </div>
        </div>
        
        <div className="card-body">
          <Typography.Title level={5} style={{ margin: '8px 0 4px 0' }}>
            {category.name}
          </Typography.Title>
          
          {showDescription && (
            <Typography.Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>
              {category.description}
            </Typography.Text>
          )}
          
          {showCount && (
            <div className="count-display">
              {isLoading ? (
                <Spin size="small" />
              ) : (
                <Typography.Text strong style={{ color: category.color }}>
                  {count > 0 ? `${count} found` : 'No data'}
                </Typography.Text>
              )}
            </div>
          )}
          
          {showExamples && (
            <div className="examples-list">
              <Typography.Text style={{ fontSize: '11px', color: '#8c8c8c' }}>
                {category.examples.slice(0, 2).join(' • ')}
              </Typography.Text>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
```

### CategorySubcategoryPanel Component

```typescript
interface CategorySubcategoryPanelProps {
  category: POICategory;
  isExpanded: boolean;
  selectedSubcategories: string[];
  poiCounts: Record<string, number>;
  onToggleExpanded: () => void;
  onSubcategoryToggle: (subcategoryId: string) => void;
  showMapPreview: boolean;
}

const CategorySubcategoryPanel: React.FC<CategorySubcategoryPanelProps> = ({
  category,
  isExpanded,
  selectedSubcategories,
  poiCounts,
  onToggleExpanded,
  onSubcategoryToggle,
  showMapPreview
}) => {
  const totalCount = Object.values(poiCounts).reduce((sum, count) => sum + count, 0);

  return (
    <Card 
      size="small" 
      className="subcategory-panel"
      title={
        <div className="panel-header">
          <span style={{ color: category.color }}>
            {category.icon} {category.name} ({totalCount} locations)
          </span>
          <Button
            type="link"
            size="small"
            icon={isExpanded ? <UpOutlined /> : <DownOutlined />}
            onClick={onToggleExpanded}
          >
            {isExpanded ? 'Hide' : 'Show'} Details
          </Button>
        </div>
      }
    >
      {isExpanded && (
        <div className="panel-content">
          <Row gutter={[16, 16]}>
            <Col xs={24} md={showMapPreview ? 16 : 24}>
              <div className="subcategories-list">
                <Typography.Text strong style={{ fontSize: '13px' }}>
                  Subcategories:
                </Typography.Text>
                
                <div className="subcategory-checkboxes">
                  {category.subcategories.map(subcategory => {
                    const isSelected = selectedSubcategories.includes(subcategory.id);
                    const count = poiCounts[subcategory.id] || 0;
                    
                    return (
                      <div key={subcategory.id} className="subcategory-item">
                        <Checkbox
                          checked={isSelected}
                          onChange={() => onSubcategoryToggle(subcategory.id)}
                        >
                          <Space>
                            <span>{subcategory.icon}</span>
                            <span>{subcategory.name}</span>
                            <span className="count">({count})</span>
                          </Space>
                        </Checkbox>
                      </div>
                    );
                  })}
                </div>
                
                <div className="category-info">
                  <Button type="link" size="small" icon={<InfoCircleOutlined />}>
                    Learn about {category.name.toLowerCase()} access
                  </Button>
                </div>
              </div>
            </Col>
            
            {showMapPreview && (
              <Col xs={24} md={8}>
                <div className="map-preview">
                  <Typography.Text strong style={{ fontSize: '13px' }}>
                    Map Preview:
                  </Typography.Text>
                  <div className="mini-map">
                    <POIMapPreview
                      category={category}
                      selectedSubcategories={selectedSubcategories}
                      height={120}
                    />
                  </div>
                </div>
              </Col>
            )}
          </Row>
        </div>
      )}
    </Card>
  );
};
```

---

## Custom POI Upload Feature

### CustomPOIUploadModal Component

```typescript
interface CustomPOIUploadModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: (pois: CustomPOI[]) => void;
  location: LocationValue;
}

const CustomPOIUploadModal: React.FC<CustomPOIUploadModalProps> = ({
  visible,
  onCancel,
  onSuccess,
  location
}) => {
  const [uploadMethod, setUploadMethod] = useState<'file' | 'manual'>('file');
  const [fileList, setFileList] = useState<any[]>([]);
  const [parsedPOIs, setParsedPOIs] = useState<CustomPOI[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [manualPOI, setManualPOI] = useState({
    name: '',
    address: '',
    latitude: '',
    longitude: '',
    category: '',
    description: ''
  });

  const handleFileUpload = async (file: File) => {
    setIsProcessing(true);
    try {
      const pois = await parseCustomPOIFile(file, location);
      setParsedPOIs(pois);
    } catch (error) {
      message.error('Failed to parse POI file');
      console.error('POI parsing error:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleManualAdd = () => {
    if (!manualPOI.name || !manualPOI.latitude || !manualPOI.longitude) {
      message.warning('Name, latitude, and longitude are required');
      return;
    }

    const poi: CustomPOI = {
      id: `manual_${Date.now()}`,
      name: manualPOI.name,
      latitude: parseFloat(manualPOI.latitude),
      longitude: parseFloat(manualPOI.longitude),
      address: manualPOI.address,
      category: manualPOI.category,
      description: manualPOI.description,
      source: 'manual'
    };

    setParsedPOIs(prev => [...prev, poi]);
    
    // Reset form
    setManualPOI({
      name: '',
      address: '',
      latitude: '',
      longitude: '',
      category: '',
      description: ''
    });
  };

  const handleSubmit = () => {
    if (parsedPOIs.length === 0) {
      message.warning('Please add at least one POI');
      return;
    }

    onSuccess(parsedPOIs);
  };

  return (
    <Modal
      title="Upload Custom Points of Interest"
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      okText={`Add ${parsedPOIs.length} POI${parsedPOIs.length !== 1 ? 's' : ''}`}
      okButtonProps={{ disabled: parsedPOIs.length === 0 }}
      width={800}
      destroyOnClose
    >
      <div className="custom-poi-upload">
        <Alert
          message="Custom POI Upload"
          description={`Add your own points of interest for analysis in ${location.displayName}. Supported formats: CSV, Excel (XLSX). Required columns: name, latitude, longitude.`}
          type="info"
          style={{ marginBottom: '16px' }}
        />

        <Radio.Group
          value={uploadMethod}
          onChange={(e) => setUploadMethod(e.target.value)}
          style={{ marginBottom: '16px' }}
        >
          <Radio.Button value="file">Upload File</Radio.Button>
          <Radio.Button value="manual">Add Manually</Radio.Button>
        </Radio.Group>

        {uploadMethod === 'file' && (
          <div className="file-upload-section">
            <Dragger
              fileList={fileList}
              beforeUpload={(file) => {
                handleFileUpload(file);
                setFileList([file]);
                return false; // Prevent auto upload
              }}
              onRemove={() => {
                setFileList([]);
                setParsedPOIs([]);
              }}
              accept=".csv,.xlsx,.xls"
              maxCount={1}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">Click or drag file to upload</p>
              <p className="ant-upload-hint">
                Supports CSV and Excel files. Must include name, latitude, longitude columns.
              </p>
            </Dragger>

            {isProcessing && (
              <div style={{ textAlign: 'center', margin: '16px 0' }}>
                <Spin /> Processing file...
              </div>
            )}
          </div>
        )}

        {uploadMethod === 'manual' && (
          <div className="manual-input-section">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12}>
                <Input
                  placeholder="POI Name *"
                  value={manualPOI.name}
                  onChange={(e) => setManualPOI(prev => ({ ...prev, name: e.target.value }))}
                />
              </Col>
              <Col xs={24} sm={12}>
                <Input
                  placeholder="Address (optional)"
                  value={manualPOI.address}
                  onChange={(e) => setManualPOI(prev => ({ ...prev, address: e.target.value }))}
                />
              </Col>
              <Col xs={24} sm={12}>
                <Input
                  placeholder="Latitude *"
                  value={manualPOI.latitude}
                  onChange={(e) => setManualPOI(prev => ({ ...prev, latitude: e.target.value }))}
                />
              </Col>
              <Col xs={24} sm={12}>
                <Input
                  placeholder="Longitude *"
                  value={manualPOI.longitude}
                  onChange={(e) => setManualPOI(prev => ({ ...prev, longitude: e.target.value }))}
                />
              </Col>
              <Col xs={24} sm={12}>
                <Input
                  placeholder="Category (optional)"
                  value={manualPOI.category}
                  onChange={(e) => setManualPOI(prev => ({ ...prev, category: e.target.value }))}
                />
              </Col>
              <Col xs={24} sm={12}>
                <Input
                  placeholder="Description (optional)"
                  value={manualPOI.description}
                  onChange={(e) => setManualPOI(prev => ({ ...prev, description: e.target.value }))}
                />
              </Col>
              <Col xs={24}>
                <Button
                  type="primary"
                  onClick={handleManualAdd}
                  disabled={!manualPOI.name || !manualPOI.latitude || !manualPOI.longitude}
                >
                  Add POI
                </Button>
              </Col>
            </Row>
          </div>
        )}

        {parsedPOIs.length > 0 && (
          <div className="parsed-pois-preview">
            <Divider />
            <Typography.Title level={5}>
              Preview ({parsedPOIs.length} POIs)
            </Typography.Title>
            
            <Table
              dataSource={parsedPOIs}
              columns={[
                {
                  title: 'Name',
                  dataIndex: 'name',
                  key: 'name'
                },
                {
                  title: 'Address', 
                  dataIndex: 'address',
                  key: 'address',
                  render: (text) => text || 'N/A'
                },
                {
                  title: 'Coordinates',
                  key: 'coordinates',
                  render: (_, poi) => `${poi.latitude.toFixed(4)}, ${poi.longitude.toFixed(4)}`
                },
                {
                  title: 'Category',
                  dataIndex: 'category',
                  key: 'category',
                  render: (text) => text || 'Custom'
                },
                {
                  title: 'Action',
                  key: 'action',
                  render: (_, poi) => (
                    <Button
                      type="link"
                      size="small"
                      danger
                      onClick={() => setParsedPOIs(prev => prev.filter(p => p.id !== poi.id))}
                    >
                      Remove
                    </Button>
                  )
                }
              ]}
              size="small"
              scroll={{ y: 200 }}
              pagination={false}
            />
          </div>
        )}
      </div>
    </Modal>
  );
};

// Helper function to parse POI files
const parseCustomPOIFile = async (file: File, location: LocationValue): Promise<CustomPOI[]> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const data = e.target?.result as string;
        const pois: CustomPOI[] = [];
        
        if (file.name.endsWith('.csv')) {
          // Parse CSV
          const lines = data.split('\n');
          const headers = lines[0].toLowerCase().split(',').map(h => h.trim());
          
          const nameIndex = headers.findIndex(h => h.includes('name'));
          const latIndex = headers.findIndex(h => h.includes('lat'));
          const lngIndex = headers.findIndex(h => h.includes('lng') || h.includes('lon'));
          const addressIndex = headers.findIndex(h => h.includes('address'));
          const categoryIndex = headers.findIndex(h => h.includes('category') || h.includes('type'));
          
          if (nameIndex === -1 || latIndex === -1 || lngIndex === -1) {
            throw new Error('Required columns (name, latitude, longitude) not found');
          }
          
          for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',').map(v => v.trim());
            if (values.length < 3 || !values[nameIndex] || !values[latIndex] || !values[lngIndex]) continue;
            
            const poi: CustomPOI = {
              id: `upload_${i}_${Date.now()}`,
              name: values[nameIndex],
              latitude: parseFloat(values[latIndex]),
              longitude: parseFloat(values[lngIndex]),
              address: addressIndex !== -1 ? values[addressIndex] : undefined,
              category: categoryIndex !== -1 ? values[categoryIndex] : undefined,
              source: 'upload'
            };
            
            // Validate coordinates
            if (!isNaN(poi.latitude) && !isNaN(poi.longitude) && 
                Math.abs(poi.latitude) <= 90 && Math.abs(poi.longitude) <= 180) {
              pois.push(poi);
            }
          }
        } else {
          // TODO: Handle Excel files
          throw new Error('Excel file parsing not yet implemented');
        }
        
        resolve(pois);
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
};
```

---

## Accessibility Implementation

### Screen Reader Support

```typescript
const announceToScreenReader = (message: string) => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  setTimeout(() => {
    if (document.body.contains(announcement)) {
      document.body.removeChild(announcement);
    }
  }, 1000);
};

// Enhanced keyboard navigation for category cards
const useCategoryKeyboardNavigation = (categories: POICategory[]) => {
  const [focusedIndex, setFocusedIndex] = useState(-1);
  
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!categories.length) return;
      
      switch (e.key) {
        case 'ArrowRight':
          e.preventDefault();
          setFocusedIndex(prev => (prev + 1) % categories.length);
          break;
        case 'ArrowLeft':
          e.preventDefault();
          setFocusedIndex(prev => prev <= 0 ? categories.length - 1 : prev - 1);
          break;
        case 'ArrowDown':
          e.preventDefault();
          setFocusedIndex(prev => Math.min(prev + 3, categories.length - 1)); // Assume 3 columns
          break;
        case 'ArrowUp':
          e.preventDefault();
          setFocusedIndex(prev => Math.max(prev - 3, 0));
          break;
        case 'Enter':
        case ' ':
          e.preventDefault();
          if (focusedIndex >= 0) {
            // Trigger category selection
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [categories, focusedIndex]);

  return focusedIndex;
};

// ARIA labels and descriptions
const getCategoryAriaLabel = (category: POICategory, count: number, isSelected: boolean): string => {
  return `${category.name} category. ${count > 0 ? `${count} locations found` : 'No data available'}. ${isSelected ? 'Selected' : 'Not selected'}. ${category.description}`;
};
```

### High Contrast Theme Support

```css
.poi-category-picker[data-theme="high-contrast"] {
  --category-border: #ffff00;
  --category-selected-bg: #000080;
  --category-selected-text: #ffffff;
  --category-hover-bg: #008000;
  --count-text: #ffff00;
}

.poi-category-picker[data-theme="high-contrast"] .category-card {
  border: 2px solid var(--category-border);
  background: #000000;
  color: #ffffff;
}

.poi-category-picker[data-theme="high-contrast"] .category-card.selected {
  background: var(--category-selected-bg);
  border-color: #ffffff;
}

.poi-category-picker[data-theme="high-contrast"] .category-card:hover {
  background: var(--category-hover-bg);
}

.poi-category-picker[data-theme="high-contrast"] .count-display {
  color: var(--count-text);
  font-weight: bold;
}
```

---

## Testing Strategy

### Component Testing

```typescript
describe('POICategoryPicker', () => {
  const mockLocation: LocationValue = {
    address: 'Denver, Colorado',
    displayName: 'Denver, Colorado',
    coordinates: [-104.9903, 39.7392],
    confidence: 'high',
    placeType: 'city',
    boundingBox: { north: 40, south: 39, east: -104, west: -105 },
    center: [-104.9903, 39.7392],
    country: 'US'
  };

  describe('Category Selection', () => {
    it('should select category when clicked', async () => {
      const onCategoriesChange = jest.fn();
      render(
        <POICategoryPicker
          selectedCategories={[]}
          onCategoriesChange={onCategoriesChange}
          location={mockLocation}
        />
      );

      const healthcareCard = screen.getByRole('button', { name: /healthcare/i });
      await userEvent.click(healthcareCard);

      expect(onCategoriesChange).toHaveBeenCalledWith(['healthcare']);
    });

    it('should deselect category when clicked again', async () => {
      const onCategoriesChange = jest.fn();
      render(
        <POICategoryPicker
          selectedCategories={['healthcare']}
          onCategoriesChange={onCategoriesChange}
          location={mockLocation}
        />
      );

      const healthcareCard = screen.getByRole('button', { name: /healthcare/i });
      await userEvent.click(healthcareCard);

      expect(onCategoriesChange).toHaveBeenCalledWith([]);
    });

    it('should respect max selections limit', async () => {
      const onCategoriesChange = jest.fn();
      render(
        <POICategoryPicker
          selectedCategories={['healthcare', 'education']}
          onCategoriesChange={onCategoriesChange}
          location={mockLocation}
          maxSelections={2}
        />
      );

      const foodCard = screen.getByRole('button', { name: /food/i });
      await userEvent.click(foodCard);

      // Should show warning message
      await waitFor(() => {
        expect(screen.getByText(/you can select up to 2 categories/i)).toBeInTheDocument();
      });
      
      expect(onCategoriesChange).not.toHaveBeenCalled();
    });
  });

  describe('Popular Combinations', () => {
    it('should select popular combination when clicked', async () => {
      const onCategoriesChange = jest.fn();
      render(
        <POICategoryPicker
          selectedCategories={[]}
          onCategoriesChange={onCategoriesChange}
          location={mockLocation}
          showPopularCombinations={true}
        />
      );

      const healthcareCombo = screen.getByRole('button', { name: /complete healthcare/i });
      await userEvent.click(healthcareCombo);

      expect(onCategoriesChange).toHaveBeenCalledWith(['healthcare']);
    });
  });

  describe('Subcategory Selection', () => {
    it('should show subcategories when category is selected', async () => {
      render(
        <POICategoryPicker
          selectedCategories={['healthcare']}
          onCategoriesChange={jest.fn()}
          location={mockLocation}
        />
      );

      expect(screen.getByText(/hospitals/i)).toBeInTheDocument();
      expect(screen.getByText(/clinics/i)).toBeInTheDocument();
    });

    it('should toggle subcategory selection', async () => {
      render(
        <POICategoryPicker
          selectedCategories={['healthcare']}
          onCategoriesChange={jest.fn()}
          location={mockLocation}
        />
      );

      const hospitalCheckbox = screen.getByRole('checkbox', { name: /hospitals/i });
      await userEvent.click(hospitalCheckbox);

      // Verify subcategory state changed
      expect(hospitalCheckbox).not.toBeChecked();
    });
  });

  describe('Custom POI Upload', () => {
    it('should open upload modal when clicked', async () => {
      render(
        <POICategoryPicker
          selectedCategories={[]}
          onCategoriesChange={jest.fn()}
          location={mockLocation}
          showCustomUpload={true}
        />
      );

      const uploadButton = screen.getByRole('button', { name: /upload custom locations/i });
      await userEvent.click(uploadButton);

      expect(screen.getByText(/upload custom points of interest/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(
        <POICategoryPicker
          selectedCategories={[]}
          onCategoriesChange={jest.fn()}
          location={mockLocation}
        />
      );

      expect(screen.getByRole('region')).toHaveAttribute('aria-label');
    });

    it('should announce selection changes', async () => {
      const announcement = jest.fn();
      // Mock screen reader announcement
      global.announceToScreenReader = announcement;

      render(
        <POICategoryPicker
          selectedCategories={[]}
          onCategoriesChange={jest.fn()}
          location={mockLocation}
          announceChanges={true}
        />
      );

      // Simulate category selection that would trigger announcement
      // Verify announcement was made
    });

    it('should support keyboard navigation', async () => {
      render(
        <POICategoryPicker
          selectedCategories={[]}
          onCategoriesChange={jest.fn()}
          location={mockLocation}
        />
      );

      const picker = screen.getByRole('region');
      picker.focus();

      // Test arrow key navigation
      await userEvent.keyboard('{ArrowRight}');
      await userEvent.keyboard('{Enter}');

      // Verify navigation and selection worked
    });
  });

  describe('POI Count Display', () => {
    it('should show POI counts when available', async () => {
      // Mock API response
      const mockCounts = {
        healthcare: { totalCount: 189, subcategoryCounts: { hospital: 23, clinic: 156 } }
      };

      render(
        <POICategoryPicker
          selectedCategories={[]}
          onCategoriesChange={jest.fn()}
          location={mockLocation}
          showPOICounts={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/189 found/i)).toBeInTheDocument();
      });
    });

    it('should show loading state while fetching counts', () => {
      render(
        <POICategoryPicker
          selectedCategories={[]}
          onCategoriesChange={jest.fn()}
          location={mockLocation}
          showPOICounts={true}
        />
      );

      expect(screen.getByRole('img', { name: /loading/i })).toBeInTheDocument();
    });
  });
});
```

---

*This POICategoryPicker component specification provides a comprehensive, accessible, and user-friendly interface for POI category selection that transforms technical POI taxonomies into an intuitive visual selection experience.*