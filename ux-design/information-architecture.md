# Information Architecture & User Flows
## Project 1.2 - SocialMapper Visual Configuration Interface

**Date**: August 10, 2025  
**Design Phase**: Week 6-7  
**Focus**: Complete user journey design from landing to results

---

## Site Map Overview

```
┌─ Landing Page (/)
│  ├─ Value Proposition
│  ├─ Demo Scenarios Preview
│  └─ Get Started CTA
│
├─ Demo Scenarios (/demo)
│  ├─ 5 Pre-built Scenarios
│  ├─ Parameter Customization
│  └─ Bridge to Custom Analysis
│
├─ Analysis Wizard (/analysis)
│  ├─ Step 1: Location Selection
│  ├─ Step 2: Analysis Type & POI
│  ├─ Step 3: Parameters & Travel
│  ├─ Step 4: Demographics & Export
│  └─ Confirmation & Launch
│
├─ Results Dashboard (/results/:jobId)
│  ├─ Real-time Progress Tracking
│  ├─ Interactive Map Visualization
│  ├─ Summary Statistics
│  ├─ Detailed Analytics
│  ├─ Export & Sharing Options
│  └─ Analysis History
│
└─ Support & Resources (/help)
   ├─ Tutorial Library
   ├─ Method Documentation
   ├─ Use Case Examples
   └─ Contact Support
```

---

## User Flow 1: Landing Experience
**Goal**: First impression → Understanding → Demo engagement within 60 seconds

### Flow Steps
```
Landing Page → Value Understanding → Demo Selection → Demo Results → Custom Analysis Decision
```

### Detailed Flow

**1. Landing Page Entry**
- **Hero Section**: "Create accessibility analysis in under 5 minutes"
- **Visual Demo**: Animated preview of analysis process
- **Value Props**: "No GIS experience required • Academic quality results • Export ready"
- **Social Proof**: "Used by 200+ urban planners and community advocates"

**2. Value Proposition Comprehension**
- **Problem Statement**: "Complex CLI tools → Simple visual interface"
- **Before/After**: CLI command vs. 4-step visual wizard
- **Use Cases**: Quick access to relevant persona examples
- **Credibility**: Method transparency and data source citations

**3. Engagement Decision**
- **Primary CTA**: "Try 3-Minute Demo" (leads to demo scenarios)
- **Secondary CTA**: "Create Custom Analysis" (leads to wizard)
- **Learning CTA**: "See How It Works" (leads to tutorial)

**Success Criteria**:
- 70%+ users click primary CTA within 60 seconds
- <10% bounce rate from hero section
- Clear value proposition comprehension in user testing

---

## User Flow 2: Demo-to-Configuration Bridge  
**Goal**: Demo completion → Custom analysis confidence → Wizard entry

### Flow Steps
```
Demo Results → Success Validation → Custom Analysis Invitation → Wizard Entry
```

### Detailed Flow

**1. Demo Results Celebration**
- **Achievement Banner**: "Analysis complete! Here's what you discovered:"
- **Key Insights**: 3 bullet points of main findings
- **Visual Success**: Completed analysis preview with professional styling

**2. Capability Demonstration** 
- **Results Quality**: Professional maps and clear statistics
- **Export Preview**: Show CSV and GeoJSON download options
- **Time Validation**: "Completed in 2:34 - faster than expected!"

**3. Custom Analysis Invitation**
- **Natural Progression**: "Ready to analyze your own location?"
- **Confidence Building**: "You've got the skills - this demo proves it"
- **Easy Entry**: "Start Custom Analysis" button with wizard preview

**4. Transition Smoothing**
- **Progress Saving**: "We'll save your progress in case you need to step away"
- **Parameter Transfer**: "Want to use similar settings from your demo?"
- **Help Availability**: "Get help anytime during your custom analysis"

**Success Criteria**:
- 50%+ demo completers start custom analysis
- <20% abandon custom wizard after starting
- Increased user confidence scores pre/post demo

---

## User Flow 3: Configuration Wizard Flow
**Goal**: Intuitive 4-step process → Confident parameter selection → Analysis launch

### Flow Architecture
```
Step 1: Location → Step 2: Analysis Type → Step 3: Travel Parameters → Step 4: Demographics → Confirmation → Launch
```

### Step 1: Location Selection
**Primary Task**: Select analysis location with confidence

**Interface Elements**:
- **Interactive Map**: Click or search to select location
- **Search Bar**: "Enter city, address, or click on map"
- **Popular Locations**: Quick-select from commonly analyzed areas
- **Location Confirmation**: "Analyzing accessibility for [Location Name]"

**Visual Feedback**:
- **Map Preview**: Highlighted bounding box of analysis area
- **Area Estimate**: "~45 square miles will be analyzed"
- **Population Preview**: "Approximately 180,000 residents"

**Validation**:
- **Location Bounds**: Ensure reasonable analysis area size
- **Data Availability**: Confirm census and POI data exists
- **Processing Estimate**: "This analysis will take 3-4 minutes"

### Step 2: Analysis Type & POI Selection
**Primary Task**: Choose what to analyze with visual understanding

**Analysis Categories**:
```
🏥 Healthcare Access        🏫 Education & Culture
   • Hospitals                • Schools
   • Clinics                  • Libraries  
   • Urgent Care             • Museums

🛒 Daily Needs             🚌 Transportation
   • Grocery Stores          • Bus Stops
   • Pharmacies              • Train Stations
   • Banks                   • Bike Shares

🌳 Recreation              🏛️ Public Services
   • Parks                   • Post Offices
   • Gyms                    • Government Offices
   • Community Centers       • Police Stations
```

**Visual Selection Interface**:
- **Category Cards**: Large, visual cards with icons and examples
- **POI Preview**: "~47 libraries found in your area"  
- **Custom POI Option**: "Upload your own locations (CSV/Excel)"
- **Multiple Selection**: "Analyze multiple facility types together"

**Smart Defaults**:
- **Popular Combinations**: "Libraries + Community Centers" for education access
- **Domain Suggestions**: Show relevant analysis types based on location characteristics
- **Recent Selections**: "Other users analyzing [Location] often choose..."

### Step 3: Travel Parameters Configuration  
**Primary Task**: Configure travel settings with visual understanding

**Travel Time Selection**:
- **Visual Slider**: 5-60 minutes with distance indicators
- **Travel Zone Preview**: Live map update showing coverage area
- **Population Impact**: "15 minutes reaches ~85,000 people"
- **Contextual Guidance**: "Most accessibility studies use 15-30 minutes"

**Travel Mode Selection**:
```
🚶 Walking           🚗 Driving
   Pedestrian access    Car-based access
   Up to 30 min        Up to 60 min
   
🚲 Cycling          🚌 Public Transit  
   Bike-friendly routes  Bus/train routes
   Up to 45 min         Schedule-based
```

**Advanced Options** (Collapsible):
- **Time of Day**: "Analyze during peak/off-peak hours"
- **Accessibility**: "Include wheelchair accessible routes only"
- **Traffic**: "Consider real-time traffic conditions"

### Step 4: Demographics & Export Configuration
**Primary Task**: Select demographic analysis and output preferences

**Demographic Variables** (Plain Language):
```
👥 Population Data       💰 Economic Indicators
   • Total Population       • Household Income
   • Age Groups            • Poverty Rates
   • Household Size        • Employment Status

🏠 Housing Characteristics  🎓 Education Levels
   • Homeownership         • Educational Attainment  
   • Housing Age           • School Enrollment
   • Occupancy Status      • Language Spoken
```

**Export Configuration**:
- **Format Selection**: CSV (spreadsheets), GeoJSON (GIS), PDF (reports)
- **Content Options**: "Include isochrone boundaries", "Include demographic details"
- **Sharing Settings**: "Generate shareable link", "Email results when complete"

**Analysis Summary**:
- **Configuration Review**: Clear summary of all selections
- **Time Estimate**: "Your analysis will take approximately 4 minutes"
- **Result Preview**: "You'll get maps, statistics, and exportable data"

### Confirmation & Launch
**Primary Task**: Final validation and analysis initiation

**Pre-launch Checklist**:
- **Parameter Summary**: Visual confirmation of all selections
- **Data Sources**: Transparency about census and POI data used
- **Methodology Note**: "Analysis uses network distance, not straight-line"
- **Contact Info**: Optional email for completion notification

**Launch Interface**:
- **Prominent Start Button**: "Start My Analysis"
- **Progress Promise**: "We'll show live progress and you can cancel anytime"
- **Next Steps**: "You'll be redirected to watch your analysis in real-time"

**Success Criteria**:
- 80%+ completion rate from step 1 to launch
- <3 average validation errors per session  
- <30 second average time per step

---

## User Flow 4: Results & Export Flow
**Goal**: Analysis completion → Result comprehension → Actionable export

### Flow Steps
```
Progress Tracking → Results Preview → Insight Discovery → Export Selection → Action Planning
```

### Detailed Flow

**1. Real-time Progress Tracking**
- **Progress Visualization**: Animated progress bar with current step
- **Time Updates**: "3:42 remaining • Analyzing transportation networks"
- **Cancel Option**: Prominent cancel button with confirmation dialog
- **Background Option**: "Continue in another tab - we'll email when done"

**2. Results Preview & Initial Insights**
- **Success Celebration**: "Analysis complete! Here's what we found:"
- **Key Statistics**: Large, prominent numbers with context
  - "67% of residents can reach a library within 15 minutes"
  - "23 libraries serve your analysis area"
  - "~180,000 people live in your study area"

**3. Interactive Map Exploration**
- **Layered Visualization**: Toggle between isochrones, POI locations, demographics
- **Accessibility Zones**: Color-coded areas showing travel time to nearest POI
- **POI Details**: Click POI markers for address and service information
- **Demographic Overlay**: Census data visualization with accessibility context

**4. Detailed Analytics Dashboard**
- **Summary Statistics**: Professional tables with key metrics
- **Demographic Breakdown**: Population served by income, age, housing status
- **Accessibility Gaps**: Areas and populations with limited access
- **Comparative Context**: How results compare to similar areas

**5. Export & Sharing Interface**
- **Format Selection**: 
  - **PDF Report**: Executive summary with maps and key findings
  - **CSV Data**: Raw statistics for further analysis
  - **GeoJSON**: Geographic boundaries for GIS software
  - **Web Map**: Shareable interactive map
- **Customization Options**: Include/exclude specific data layers
- **Sharing Tools**: Generate public link, email to collaborators

**Success Criteria**:
- Users understand key findings within 30 seconds of results
- 60%+ users export results in at least one format
- Clear comprehension of accessibility gaps and coverage

---

## User Flow 5: Error Recovery Flows
**Goal**: Error occurrence → Clear understanding → Successful resolution

### Common Error Scenarios

**1. Location Data Unavailable**
```
Error Detection → Clear Explanation → Alternative Suggestions → Resolution
```
- **Error Message**: "We don't have enough data for this rural area"
- **Explanation**: "Census and POI data is limited for areas with <1,000 people"
- **Alternatives**: "Try a nearby city" with suggestions
- **Escalation**: "Contact support for custom data options"

**2. Analysis Timeout/Failure**
```
Error Detection → Status Communication → Recovery Options → Prevention
```
- **Error Message**: "Your analysis took longer than expected"
- **Explanation**: "Large analysis areas sometimes need more processing time" 
- **Recovery**: "Try a smaller area" or "We'll email when complete"
- **Prevention**: Better upfront area size validation

**3. Invalid Parameter Combinations**  
```
Real-time Validation → Clear Feedback → Guided Correction → Success
```
- **Validation**: "60-minute walking distance is unrealistic for most people"
- **Suggestion**: "Try 30 minutes or switch to driving mode"
- **Guidance**: "Most walking accessibility studies use 15-30 minutes"
- **Learning**: Contextual help explains parameter relationships

**4. Export/Download Failures**
```
Download Attempt → Failure Detection → Alternative Options → Resolution
```
- **Error Message**: "Download failed - file may be too large"
- **Alternatives**: "Try smaller file format" or "Simplified export"
- **Backup**: "Email download link" or "Try again in 5 minutes"
- **Support**: "Contact us if downloads continue failing"

### Error Prevention Strategies
- **Progressive Validation**: Check parameters as users configure
- **Smart Defaults**: Reduce probability of invalid combinations  
- **Capacity Indicators**: Show system load and expected processing times
- **Graceful Degradation**: Partial results when full analysis fails

---

## Navigation Architecture

### Primary Navigation
```
🏠 Home          📊 Demo          ⚡ Analysis          📈 Results          ❓ Help
   Landing         Scenarios        Wizard              Dashboard          Support
```

### Contextual Navigation
- **Breadcrumbs**: Show progress through wizard steps
- **Step Navigation**: Jump between wizard steps (with validation)
- **Quick Actions**: Save progress, get help, start over
- **Exit Options**: Clear exit paths from any workflow

### Mobile Navigation Considerations
- **Bottom Tab Bar**: Primary navigation accessible by thumb
- **Collapsible Sections**: Reduce cognitive load on small screens
- **Touch-Friendly**: Minimum 44px touch targets
- **Offline Support**: Basic functionality without network connection

---

## Content Strategy

### Progressive Disclosure Principles
1. **Essential First**: Most important information prominently displayed
2. **Details on Demand**: Advanced options available but not prominent
3. **Context Sensitive**: Show relevant information based on current task
4. **Learning Integration**: Educational content embedded contextually

### Plain Language Guidelines
- **Technical Terms**: Always accompanied by plain-language explanation
- **User Goals**: Frame content around what users want to accomplish
- **Actionable Language**: Use verbs that clearly indicate what happens next
- **Confidence Building**: Positive, reassuring tone throughout

### Accessibility Content Requirements
- **Alt Text**: Descriptive text for all maps and visualizations
- **Heading Structure**: Logical hierarchy for screen readers
- **Form Labels**: Clear, descriptive labels for all form elements
- **Error Messages**: Specific, actionable guidance for problem resolution

---

## Success Metrics by Flow

### Landing Experience
- **Engagement Rate**: 70%+ click primary CTA within 60 seconds
- **Comprehension**: 80%+ correctly identify tool purpose in testing
- **Conversion**: 40%+ proceed to demo or wizard from landing

### Demo-to-Configuration Bridge
- **Completion Rate**: 60%+ complete at least one demo scenario
- **Progression**: 50%+ attempt custom analysis after demo
- **Confidence**: Increased self-reported confidence in spatial analysis

### Configuration Wizard  
- **Completion Rate**: 80%+ complete all wizard steps
- **Error Rate**: <3 validation errors per session average
- **Time Efficiency**: <5 minutes average from start to launch

### Results & Export
- **Comprehension**: 90%+ correctly interpret key findings
- **Action Rate**: 60%+ export results in at least one format
- **Satisfaction**: 80%+ report results meet their needs

### Error Recovery
- **Recovery Rate**: 70%+ successfully resolve encountered errors  
- **Understanding**: 80%+ report error messages were helpful
- **Prevention**: <10% error rate after first successful analysis

---

## Technical Integration Requirements

### API Integration Points
- **Location Search**: Integrate with geocoding service for location selection
- **POI Discovery**: Real-time POI counts for selected areas
- **Analysis Submission**: Seamless wizard-to-API parameter translation
- **Progress Tracking**: Real-time job status updates via Server-Sent Events
- **Results Retrieval**: Efficient loading of analysis results and visualizations

### State Management
- **Wizard Progress**: Persistent state across browser sessions
- **User Preferences**: Remember common parameter selections
- **Analysis History**: Track previous analyses for easy repeat/modification
- **Error States**: Graceful error handling with recovery options

### Performance Considerations
- **Map Loading**: Progressive enhancement for slow connections
- **Large Results**: Pagination and lazy loading for extensive demographic data
- **Mobile Optimization**: Efficient rendering on resource-constrained devices
- **Offline Capability**: Basic functionality available without network

---

*This information architecture provides the foundation for implementing an intuitive, accessible visual configuration interface that serves users from first discovery through successful analysis completion.*