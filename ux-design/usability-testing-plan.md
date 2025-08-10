# Usability Testing Plan
## Project 1.2 - Visual Configuration Interface Validation

**Date**: August 10, 2025  
**Testing Phase**: Weeks 16-20  
**Success Metric**: Urban planning professor can create meaningful analysis in under 5 minutes without documentation

---

## Executive Summary

This usability testing plan validates the Visual Configuration Interface design through systematic user testing with representative personas. The primary goal is to achieve <5 minute time-to-first-analysis while maintaining 80%+ task completion rates and ensuring accessibility compliance across all user types.

### Key Objectives
1. **Validate time-to-analysis target** of under 5 minutes for first-time users
2. **Confirm task completion rates** of 80%+ across all user personas
3. **Verify accessibility compliance** for screen readers and keyboard navigation
4. **Identify usability barriers** that prevent successful analysis configuration
5. **Measure confidence levels** in parameter selection and result interpretation

---

## Testing Framework

### Research Questions

#### Primary Research Questions
1. **Time Efficiency**: Can users complete their first analysis configuration in under 5 minutes?
2. **Task Success**: What percentage of users successfully submit a valid analysis configuration?
3. **User Confidence**: Do users feel confident in their parameter selections and understand what they're analyzing?
4. **Error Recovery**: How effectively do users recover from validation errors or configuration mistakes?
5. **Accessibility**: Can users with assistive technologies successfully complete the workflow?

#### Secondary Research Questions
1. **Learning Curve**: How does performance improve from first to second analysis attempt?
2. **Feature Discovery**: Do users discover and utilize advanced features (custom POIs, subcategory selection)?
3. **Comparative Preference**: How does the visual interface compare to command-line tools for technical users?
4. **Mobile Usability**: Is the interface usable on tablet devices for field work?

### Testing Methodology

#### Mixed Methods Approach
- **Quantitative Metrics**: Task completion times, error rates, success rates
- **Qualitative Insights**: Think-aloud protocols, post-task interviews
- **Behavioral Observation**: Screen recording and interaction analysis
- **Accessibility Testing**: Automated and manual accessibility validation

#### Testing Phases
1. **Phase 1**: Individual user testing sessions (Weeks 16-17)
2. **Phase 2**: Group comparative testing (Week 18)
3. **Phase 3**: Accessibility-focused testing (Week 19)
4. **Phase 4**: Iteration validation testing (Week 20)

---

## Participant Recruitment

### Target Participants (N=24)

#### Primary Personas (n=16)
- **Urban Planning Professors (n=4)**
  - PhD in Urban Planning or related field
  - Teaching experience with spatial analysis
  - Mixed technical comfort levels
  - Access to students for research projects

- **Community Advocates (n=4)**
  - Work at nonprofits or community organizations
  - Policy advocacy experience
  - Limited technical GIS background
  - Need to create accessible community presentations

- **Policy Researchers (n=4)**
  - Government or think tank employment
  - Policy analysis and briefing experience
  - Some R/Python experience preferred
  - Tight deadline pressures in work

- **City Government Analysts (n=4)**
  - Local government planning departments
  - Some ArcGIS experience
  - Respond to elected official requests
  - Need professional-quality outputs

#### Accessibility Participants (n=8)
- **Screen Reader Users (n=4)**: Experienced JAWS, NVDA, or VoiceOver users
- **Motor Impairment Users (n=2)**: Keyboard-only navigation users
- **Cognitive Accessibility (n=2)**: Users with attention or processing differences

### Recruitment Criteria
- **Minimum Requirements**: Professional experience with spatial concepts, need for accessibility analysis in work
- **Technical Experience**: Mixed levels from novice to intermediate (no GIS experts)
- **Geographic Distribution**: Represent urban, suburban, and rural analysis contexts
- **Compensation**: $75/session + $25 travel reimbursement

---

## Testing Scenarios

### Core Task Scenarios

#### Scenario 1: Healthcare Access Analysis (Dr. Sarah Chen Persona)
**Context**: "You're preparing a lecture on healthcare accessibility for your Urban Planning 301 class. You want to show students how different neighborhoods in Denver have different levels of access to medical care."

**Task**: Create an analysis showing healthcare accessibility in Denver, Colorado with a 15-minute travel time.

**Success Criteria**:
- Selects Denver as location
- Chooses healthcare POI category
- Sets reasonable travel parameters
- Completes analysis submission
- Understands what results will show

**Expected Completion Time**: 3-4 minutes

#### Scenario 2: Grocery Access Advocacy (Maria Rodriguez Persona)
**Context**: "You're preparing for a city council meeting next week about food deserts in your community. You need to create maps and data showing which neighborhoods lack access to affordable groceries."

**Task**: Analyze grocery store access in a city you're familiar with, focusing on areas where people might struggle to reach supermarkets.

**Success Criteria**:
- Selects relevant location
- Chooses appropriate food/grocery POI categories
- Considers transportation mode (likely driving or transit)
- Includes demographic variables
- Plans to export results for presentation

**Expected Completion Time**: 4-5 minutes

#### Scenario 3: Policy Comparison (David Park Persona)
**Context**: "Your commissioner needs to compare public transit accessibility between three cities for a transportation funding proposal. She needs the analysis by tomorrow morning."

**Task**: Set up an analysis for comparing bus stop accessibility across different cities.

**Success Criteria**:
- Understands how to configure transit analysis
- Considers appropriate travel parameters
- Plans for comparative analysis
- Selects professional export formats

**Expected Completion Time**: 3-4 minutes

#### Scenario 4: Public Service Response (Jennifer Kim Persona)
**Context**: "A council member received a complaint that the new neighborhood lacks access to parks for families. You need to analyze park accessibility to respond to this citizen concern."

**Task**: Create an analysis showing park and playground access for families with children.

**Success Criteria**:
- Selects appropriate recreation POI categories
- Considers family-appropriate travel modes (walking/driving)
- Includes relevant demographic variables (age groups)
- Prepares professional city government response

**Expected Completion Time**: 4-5 minutes

### Advanced Feature Scenarios

#### Scenario 5: Custom POI Analysis
**Task**: Upload custom library locations from a CSV file and analyze accessibility.

**Success Criteria**:
- Successfully uploads custom POI file
- Validates POI data accuracy
- Completes analysis with custom locations

#### Scenario 6: Complex Multi-Category Analysis
**Task**: Analyze access to "daily essentials" including grocery stores, pharmacies, and transit stops.

**Success Criteria**:
- Selects multiple POI categories
- Understands subcategory options
- Configures appropriate parameters for multiple POI types

---

## Testing Procedures

### Session Structure (75 minutes)

#### Pre-Session Setup (5 minutes)
- Technical setup and screen recording
- Participant consent and compensation
- Brief demographic questionnaire
- Accessibility accommodations setup

#### Introduction (5 minutes)
- Welcome and study overview
- Think-aloud protocol explanation
- Emphasize testing the interface, not the participant
- Permission to ask questions and take breaks

#### Main Testing (45 minutes)
- **Scenario 1** (15 minutes): Primary persona task
- **Break** (3 minutes): Quick stretch and questions
- **Scenario 2** (12 minutes): Secondary task or advanced feature
- **Scenario 3** (15 minutes): Challenging or comparative task

#### Post-Task Interview (15 minutes)
- Task completion retrospective
- System Usability Scale (SUS) questionnaire
- Confidence and satisfaction ratings
- Improvement suggestions

#### Wrap-up (5 minutes)
- Additional questions or comments
- Compensation and next steps
- Thank you and contact information

### Think-Aloud Protocol Guidelines

#### For Participants
- "Please talk out loud about what you're thinking as you work through this"
- "If something is confusing or unclear, let me know what you expected"
- "There are no wrong answers - we want to understand how you naturally approach this"

#### For Facilitators
- **Neutral Probing**: "What are you thinking about right now?"
- **Clarification**: "Can you tell me more about that?"
- **Process Focus**: "What would you expect to happen if you clicked that?"
- **Avoid Leading**: Don't suggest solutions or correct approaches

### Data Collection Methods

#### Quantitative Metrics
- **Task Completion Time**: Stopwatch timing from start to successful submission
- **Task Success Rate**: Binary success/failure per task
- **Error Count**: Number of validation errors or incorrect attempts
- **Click/Interaction Count**: Efficiency of navigation paths
- **Abandonment Points**: Where users give up or get stuck

#### Qualitative Observations
- **Confusion Points**: Where users pause, hesitate, or express uncertainty
- **Discovery Patterns**: How users find and use features
- **Mental Models**: What users expect vs. what actually happens
- **Emotional Responses**: Frustration, confidence, satisfaction expressions
- **Recovery Strategies**: How users resolve problems or errors

#### Screen Recording Analysis
- **Navigation Patterns**: Common paths through the interface
- **Interaction Hotspots**: Most and least used interface elements
- **Error Sequences**: What leads to validation errors or failures
- **Time Distribution**: How long users spend in each step

---

## Success Metrics & Benchmarks

### Primary Success Metrics

#### Time-to-Analysis (Target: <5 minutes)
- **Excellent**: <3 minutes (40% of users)
- **Good**: 3-5 minutes (50% of users)
- **Acceptable**: 5-7 minutes (10% of users)
- **Needs Improvement**: >7 minutes (0% tolerance)

#### Task Completion Rate (Target: 80%+)
- **Excellent**: 90%+ completion rate
- **Good**: 80-89% completion rate
- **Acceptable**: 70-79% completion rate
- **Needs Improvement**: <70% completion rate

#### Error Rate (Target: <3 errors per session)
- **Excellent**: <1 validation error on average
- **Good**: 1-2 validation errors on average
- **Acceptable**: 2-3 validation errors on average
- **Needs Improvement**: >3 validation errors on average

#### System Usability Scale (Target: >80)
- **Excellent**: SUS score 85-100
- **Good**: SUS score 80-84
- **Acceptable**: SUS score 70-79
- **Needs Improvement**: SUS score <70

### Secondary Success Metrics

#### User Confidence (Target: 4.0/5.0)
Rating scale for "How confident are you that your analysis will provide useful results?"
- **1**: Not at all confident
- **2**: Slightly confident
- **3**: Moderately confident
- **4**: Very confident
- **5**: Extremely confident

#### Parameter Understanding (Target: 80% accurate)
Post-task question: "In your own words, what analysis did you just set up?"
- **Excellent**: >90% accurate description
- **Good**: 80-90% accurate description
- **Acceptable**: 70-79% accurate description
- **Needs Improvement**: <70% accurate description

#### Feature Discovery (Target: 60% discover advanced features)
Track usage of:
- Subcategory selection
- Advanced travel options
- Custom POI upload
- Popular location shortcuts
- Export format selection

### Accessibility Metrics

#### Screen Reader Compatibility (Target: 100% task completion)
- All tasks completable with screen reader
- Logical reading order maintained
- Form labels and buttons properly announced
- Error messages clearly communicated

#### Keyboard Navigation (Target: 100% functionality)
- All functionality available via keyboard
- Logical tab order maintained
- Focus indicators clearly visible
- No keyboard traps

#### Cognitive Accessibility (Target: 80% task completion)
- Clear error messages help users recover
- Progress indicators reduce anxiety
- Help text available when needed
- Interface doesn't overwhelm users

---

## Testing Environment & Tools

### Technical Setup

#### Testing Lab Configuration
- **Hardware**: 24" monitor (1920x1080), standard keyboard/mouse
- **Software**: Latest Chrome/Firefox, screen recording software
- **Assistive Technology**: NVDA screen reader, Dragon speech recognition
- **Mobile Testing**: iPad Pro 12.9" with Safari

#### Recording & Analysis Tools
- **Screen Recording**: OBS Studio for session capture
- **Analytics**: Hotjar or FullStory for interaction heatmaps
- **Survey Platform**: Typeform for questionnaires
- **Analysis**: Dovetail for qualitative data synthesis

### Remote Testing Capabilities
- **Video Conferencing**: Zoom with screen sharing
- **Remote Screen Recording**: User consent for local recording
- **Prototype Access**: Password-protected staging environment
- **Accessibility Testing**: RemoteVR for assistive technology sessions

---

## Data Analysis Plan

### Quantitative Analysis

#### Statistical Methods
- **Descriptive Statistics**: Mean, median, mode for completion times
- **Comparative Analysis**: ANOVA between persona groups
- **Correlation Analysis**: Relationship between experience and performance
- **Regression Analysis**: Predictors of task success

#### Reporting Metrics
- **Completion Time Distribution**: Histogram of task completion times
- **Success Rate by Persona**: Comparison across user types
- **Error Pattern Analysis**: Most common failure points
- **Feature Usage Analytics**: Adoption rates of advanced features

### Qualitative Analysis

#### Thematic Analysis
- **Usability Issues**: Common pain points and confusion areas
- **Mental Model Gaps**: Where interface doesn't match expectations
- **Positive Feedback**: What works well and builds confidence
- **Improvement Suggestions**: User-proposed enhancements

#### Journey Mapping
- **Emotional Journey**: Confidence and frustration throughout tasks
- **Interaction Patterns**: Common navigation paths and shortcuts
- **Decision Points**: Where users pause to consider options
- **Recovery Paths**: How users resolve errors and confusion

### Accessibility Analysis

#### Compliance Assessment
- **WCAG 2.1 AA Validation**: Automated and manual testing results
- **Assistive Technology Compatibility**: Screen reader effectiveness
- **Keyboard Navigation Efficiency**: Task completion with keyboard only
- **Cognitive Load Assessment**: Mental effort required for task completion

---

## Iteration & Validation Plan

### Design Iteration Process

#### High Priority Issues (Week 17)
Issues that prevent >20% of users from completing tasks:
- **Critical Navigation Problems**: Users can't find essential features
- **Blocking Validation Errors**: Error messages don't help users recover
- **Accessibility Barriers**: Screen reader users can't complete tasks
- **Performance Issues**: Interface too slow for practical use

#### Medium Priority Issues (Week 18)
Issues that slow down or frustrate users but don't prevent completion:
- **Efficiency Improvements**: Reduce clicks or steps for common tasks
- **Clarity Enhancements**: Better labels, descriptions, or examples
- **Feature Discoverability**: Make useful features more findable
- **Visual Design Polish**: Improve visual hierarchy and feedback

#### Low Priority Issues (Week 19)
Issues that affect satisfaction but not core functionality:
- **Nice-to-Have Features**: User-requested enhancements
- **Visual Refinements**: Color, spacing, icon improvements
- **Advanced User Features**: Power user shortcuts and customization
- **Mobile Optimization**: Touch-friendly improvements

### Validation Testing (Week 20)

#### Rapid Iteration Validation
- **A/B Testing**: Compare original vs. improved versions
- **Focused Sessions**: 30-minute tests on specific improvements
- **Metrics Tracking**: Measure improvement in key success metrics
- **User Feedback**: Collect satisfaction ratings on changes

#### Success Validation Criteria
- **Time Improvement**: 15% reduction in average completion time
- **Error Reduction**: 25% fewer validation errors
- **Satisfaction Increase**: 10+ point increase in SUS scores
- **Accessibility Enhancement**: 100% task completion for assistive technology users

---

## Risk Mitigation

### Potential Testing Challenges

#### Participant Recruitment Issues
- **Risk**: Difficulty finding representative users
- **Mitigation**: Partner with professional organizations, offer competitive compensation
- **Backup Plan**: Expand recruitment network, extend timeline if needed

#### Technical Problems
- **Risk**: Prototype instability during testing
- **Mitigation**: Extensive pre-testing, backup systems ready
- **Backup Plan**: Screen sharing alternatives, paper prototype fallback

#### Accessibility Barriers
- **Risk**: Interface not accessible to assistive technology users
- **Mitigation**: Early accessibility testing, AT expert consultation
- **Backup Plan**: Alternative interface modes, dedicated accessibility sessions

#### Time Constraints
- **Risk**: Testing timeline too aggressive for proper iteration
- **Mitigation**: Prioritize critical issues, parallel development streams
- **Backup Plan**: Focus on highest-impact improvements, defer nice-to-haves

### Quality Assurance

#### Data Validation
- **Inter-rater Reliability**: Multiple analysts review qualitative data
- **Quantitative Verification**: Double-check timing and error calculations
- **Participant Validation**: Follow-up to confirm interpretation accuracy
- **Bias Mitigation**: Diverse facilitator team, structured protocols

#### Ethical Considerations
- **Informed Consent**: Clear explanation of recording and data use
- **Compensation Fairness**: Appropriate payment for time invested
- **Data Privacy**: Secure storage and limited access to recordings
- **Accessibility Rights**: Ensure equal opportunity to participate

---

## Reporting & Recommendations

### Testing Report Structure

#### Executive Summary (2 pages)
- Key findings and recommendations
- Success metric achievement
- Critical usability issues identified
- Next steps and timeline

#### Methodology & Participants (3 pages)
- Testing approach and rationale
- Participant demographics and characteristics
- Session procedures and data collection
- Analysis methods and validation

#### Quantitative Results (4 pages)
- Task completion time analysis
- Success rate by persona and task
- Error pattern identification
- System Usability Scale results
- Statistical significance testing

#### Qualitative Insights (6 pages)
- Thematic analysis of user feedback
- Mental model and expectation gaps
- Positive feedback and success patterns
- User journey emotional mapping
- Feature discovery and usage patterns

#### Accessibility Assessment (3 pages)
- WCAG 2.1 AA compliance status
- Assistive technology compatibility
- Keyboard navigation effectiveness
- Cognitive accessibility evaluation

#### Design Recommendations (4 pages)
- High priority improvement recommendations
- Medium priority enhancement suggestions
- Low priority nice-to-have features
- Implementation timeline and resources

#### Appendices (10 pages)
- Raw data summaries
- Session recordings index
- Participant quotes and feedback
- Detailed task scenarios
- Survey instruments used

### Stakeholder Presentation (30 minutes)

#### Slide Deck Structure
1. **Testing Overview** (3 minutes): Goals, methodology, participants
2. **Key Results** (10 minutes): Time metrics, success rates, major findings
3. **Critical Issues** (8 minutes): Must-fix problems with user examples
4. **Recommendations** (7 minutes): Prioritized improvement roadmap
5. **Q&A** (7 minutes): Stakeholder questions and discussion

#### Success Story Highlights
- Users completing analysis faster than expected
- Positive confidence and satisfaction feedback
- Successful accessibility for all user types
- Clear preference over existing tools

#### Challenge Documentation
- Specific areas where users struggled
- Error patterns and recovery difficulties
- Feature confusion or discovery issues
- Accessibility barriers identified

---

## Success Criteria Summary

### Must-Achieve Targets
- ✅ **<5 minutes** average time-to-first-analysis
- ✅ **80%+** task completion rate across all personas
- ✅ **<3 errors** per session on average
- ✅ **80+ SUS score** system usability rating
- ✅ **100%** accessibility compliance for assistive technology

### Stretch Goals
- 🎯 **<3 minutes** for 40% of users
- 🎯 **90%+** task completion rate
- 🎯 **<1 error** per session average
- 🎯 **85+ SUS score** system usability rating
- 🎯 **4.0/5.0** user confidence in parameter selection

### Validation Requirements
- Representative testing across all four personas
- Both novice and intermediate technical skill levels
- Urban, suburban, and rural analysis contexts
- Screen reader and keyboard-only accessibility validation
- Mobile/tablet usability confirmation

---

*This comprehensive usability testing plan provides the framework for validating that the Visual Configuration Interface successfully transforms complex CLI parameters into an intuitive, accessible experience that meets our <5 minute time-to-analysis goal while maintaining professional analytical rigor.*