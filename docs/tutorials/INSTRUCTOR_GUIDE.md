# SocialMapper Instructor Guide

## Teaching Accessibility Analysis with Python

This guide provides comprehensive support for instructors teaching spatial accessibility analysis using SocialMapper. Whether you're running a workshop, teaching a course, or leading a training session, this guide will help you deliver effective instruction.

---

## 📚 Tutorial Teaching Notes

### Tutorial 01: Getting Started (30-45 minutes)

#### Key Teaching Points:
- **Emphasize the workflow:** Location → Isochrone → POIs → Demographics → Visualization
- **Start with visual examples:** Show what an isochrone looks like before coding
- **Explain coordinate systems:** Latitude/longitude vs. addresses
- **Census data basics:** What are block groups and why they matter

#### Time Breakdown:
- Introduction & setup check (5 min)
- Concept explanation with visuals (10 min)
- Live coding demonstration (10 min)
- Student practice (10 min)
- Q&A and troubleshooting (10 min)

#### Common Student Questions:
1. **"Why coordinates instead of addresses?"**
   - Geocoding services have rate limits
   - Coordinates are more reliable
   - Addresses can be ambiguous

2. **"What exactly is an isochrone?"**
   - Area reachable within specific time
   - Accounts for actual road/path networks
   - Different from simple radius circles

3. **"Why is it slow the first time?"**
   - Building local caches
   - Downloading map data
   - Subsequent runs are faster

#### Discussion Prompts:
- How would isochrones differ in urban vs. rural areas?
- What factors affect travel time besides distance?
- How might this tool support equity analysis?

#### Assessment Ideas:
- **Quick Check:** Create a 10-minute walking isochrone for their campus/office
- **Analysis:** Compare population reached by walk vs. drive
- **Interpretation:** Explain what the demographic data reveals

#### Modifications:
- **Easier:** Provide pre-set coordinates, reduce travel time to 5 minutes
- **Harder:** Add multiple travel modes, analyze 3+ demographics
- **Advanced:** Calculate accessibility ratios, create custom metrics

---

### Tutorial 02: Travel Modes (30-40 minutes)

#### Key Teaching Points:
- **Mode impacts on accessibility:** Walking ≠ Driving in coverage
- **Infrastructure dependency:** Sidewalks, bike lanes, roads
- **Equity implications:** Not everyone has car access
- **Real-world applications:** Transit planning, walkability scores

#### Time Breakdown:
- Review isochrone concept (3 min)
- Explain travel modes (7 min)
- Demonstrate mode comparison (10 min)
- Student exploration (10 min)
- Group discussion (10 min)

#### Common Student Questions:
1. **"How accurate are the travel times?"**
   - Based on OpenStreetMap data
   - Typical speeds, not real-time traffic
   - Good for relative comparisons

2. **"Can I add custom modes like scooters?"**
   - Currently supports walk, bike, drive
   - Can approximate with bike + adjusted time
   - Custom modes in development

3. **"Why is bike sometimes larger than walk but smaller than drive?"**
   - Bike can use paths cars cannot
   - Faster than walking
   - Network topology matters

#### Discussion Prompts:
- Which populations rely most on walking/biking?
- How do travel modes affect access to essential services?
- What urban design features improve multi-modal access?

#### Assessment Ideas:
- **Comparison:** Calculate area ratios between modes
- **Analysis:** Identify locations with large mode disparities
- **Application:** Recommend infrastructure improvements

#### Modifications:
- **Easier:** Focus on two modes only, use 5-minute intervals
- **Harder:** Add demographic analysis per mode, calculate equity metrics
- **Advanced:** Create accessibility index combining all modes

---

### Tutorial 03: Census Demographics (45-60 minutes)

#### Key Teaching Points:
- **Census geography hierarchy:** Blocks < Block Groups < Tracts < Counties
- **Variable selection:** Population, income, age, race, housing
- **API usage:** Rate limits, caching, error handling
- **Data interpretation:** Margins of error, suppression, estimates

#### Time Breakdown:
- Census geography overview (10 min)
- API setup and keys (5 min)
- Variable exploration (10 min)
- Data retrieval demo (10 min)
- Analysis practice (15 min)
- Interpretation discussion (10 min)

#### Common Student Questions:
1. **"What's the difference between blocks and block groups?"**
   - Blocks: Smallest, limited data
   - Block groups: 600-3000 people, rich data
   - Trade-off: Granularity vs. privacy

2. **"Why are some values missing or zero?"**
   - Privacy protection for small populations
   - Data suppression rules
   - Sampling limitations

3. **"How current is the census data?"**
   - American Community Survey: 5-year estimates
   - Decennial census: Every 10 years
   - Trade-offs in recency vs. reliability

#### Discussion Prompts:
- What biases might exist in census data?
- How do we handle missing or suppressed data?
- What additional data sources could complement census data?

#### Assessment Ideas:
- **Data Retrieval:** Get 5 specific variables for an area
- **Analysis:** Calculate demographic profiles for isochrones
- **Comparison:** Compare demographics inside/outside service areas

#### Modifications:
- **Easier:** Provide variable codes, limit to 3 demographics
- **Harder:** Add margin of error analysis, time series comparison
- **Advanced:** Integrate with other data sources, statistical modeling

---

### Tutorial 04: Custom POIs (30-40 minutes)

#### Key Teaching Points:
- **Data preparation:** CSV format, required columns, cleaning
- **Batch processing:** Efficiency, error handling, progress tracking
- **Use cases:** Store locations, community resources, hazards
- **Quality control:** Geocoding accuracy, duplicate handling

#### Time Breakdown:
- CSV format explanation (5 min)
- Data preparation demo (10 min)
- Batch processing code (10 min)
- Student practice with own data (10 min)
- Results comparison (5 min)

#### Common Student Questions:
1. **"What CSV columns are required?"**
   - Minimum: name, latitude, longitude
   - Optional: category, description, metadata
   - Flexible schema for custom fields

2. **"How many POIs can I process?"**
   - Technically unlimited
   - Performance considerations after 100+
   - Use sampling for large datasets

3. **"Can I use addresses instead of coordinates?"**
   - Yes, with geocoding step
   - Additional processing time
   - Potential geocoding failures

#### Discussion Prompts:
- What POIs are most relevant for your research?
- How do we validate POI data quality?
- What metadata should we track for POIs?

#### Assessment Ideas:
- **Data Prep:** Create CSV with 10 local POIs
- **Analysis:** Compare accessibility of different POI types
- **Visualization:** Map POI clusters and gaps

#### Modifications:
- **Easier:** Provide sample CSV, process 5 POIs
- **Harder:** Add category analysis, overlap detection
- **Advanced:** Implement POI prioritization algorithms

---

### Tutorial 05: Combining Analysis (45-60 minutes)

#### Key Teaching Points:
- **Workflow design:** Sequential vs. parallel processing
- **Data integration:** Joining spatial and tabular data
- **Composite metrics:** Creating meaningful indicators
- **Reproducibility:** Documenting analysis steps

#### Time Breakdown:
- Workflow patterns overview (10 min)
- Integration techniques (10 min)
- Metric development (10 min)
- Combined analysis demo (15 min)
- Student implementation (10 min)
- Review and discussion (5 min)

#### Common Student Questions:
1. **"How do I know which analyses to combine?"**
   - Start with research questions
   - Consider data relationships
   - Build incrementally

2. **"What's the best way to structure complex workflows?"**
   - Modular functions
   - Clear data flow
   - Error handling at each step

3. **"How do I handle different data scales?"**
   - Normalization techniques
   - Aggregation strategies
   - Weighting schemes

#### Discussion Prompts:
- What makes a good accessibility metric?
- How do we validate composite indicators?
- What are the trade-offs in complexity vs. interpretability?

#### Assessment Ideas:
- **Design:** Create workflow diagram for analysis
- **Implementation:** Build 3-step analysis pipeline
- **Evaluation:** Compare different metric formulations

#### Modifications:
- **Easier:** Provide workflow template, 2 components only
- **Harder:** Add statistical validation, sensitivity analysis
- **Advanced:** Create reusable analysis modules

---

### Tutorial 06: Multi-Location Analysis (45-60 minutes)

#### Key Teaching Points:
- **Batch processing patterns:** Loops, parallel processing, error handling
- **Comparison matrices:** Systematic evaluation methods
- **Overlap analysis:** Service area interactions
- **Gap identification:** Finding underserved areas

#### Time Breakdown:
- Multi-location concepts (10 min)
- Batch processing patterns (10 min)
- Comparison techniques (10 min)
- Overlap analysis demo (10 min)
- Practice with 3 locations (15 min)
- Results interpretation (5 min)

#### Common Student Questions:
1. **"How many locations can I analyze simultaneously?"**
   - Depends on travel time and area
   - 10-20 for interactive analysis
   - 100+ with batch processing

2. **"How do I handle overlapping service areas?"**
   - Union for total coverage
   - Intersection for redundancy
   - Difference for unique areas

3. **"What's the best way to compare locations?"**
   - Standardized metrics
   - Ranking systems
   - Multi-criteria evaluation

#### Discussion Prompts:
- How do we prioritize locations for investment?
- What constitutes "good" coverage?
- How do we balance efficiency and equity?

#### Assessment Ideas:
- **Analysis:** Compare 5 potential sites
- **Optimization:** Find best 3 of 10 locations
- **Report:** Create site selection recommendation

#### Modifications:
- **Easier:** Compare 2 locations, single metric
- **Harder:** Add demographic weighting, cost factors
- **Advanced:** Implement location-allocation algorithms

---

### Tutorial 07: ZIP Code Analysis (45-50 minutes)

#### Key Teaching Points:
- **ZCTA vs. ZIP codes:** Census geography distinctions
- **Scale considerations:** When to use ZCTAs vs. block groups
- **Regional patterns:** Broader spatial analysis
- **Performance trade-offs:** Speed vs. granularity

#### Time Breakdown:
- ZCTA explanation (10 min)
- Data retrieval methods (10 min)
- Regional analysis demo (10 min)
- Performance comparison (5 min)
- Student practice (10 min)
- Discussion (5 min)

#### Common Student Questions:
1. **"What's the difference between ZIP codes and ZCTAs?"**
   - ZIP: Postal delivery routes
   - ZCTA: Census approximation
   - Not always 1:1 mapping

2. **"When should I use ZCTAs instead of block groups?"**
   - Regional analysis
   - Faster processing
   - When precise boundaries less critical

3. **"Can I mix ZCTA and block group analysis?"**
   - Yes, for multi-scale analysis
   - Requires careful aggregation
   - Consider MAUP effects

#### Discussion Prompts:
- How does geographic scale affect results?
- What patterns emerge at regional level?
- When is precision more important than speed?

#### Assessment Ideas:
- **Comparison:** Analyze same area with both geographies
- **Regional:** Create county-wide accessibility profile
- **Performance:** Benchmark different approaches

#### Modifications:
- **Easier:** Single ZCTA analysis, basic demographics
- **Harder:** Multi-county comparison, statistical tests
- **Advanced:** Hierarchical analysis, scale effects

---

### Tutorial 08: Address Geocoding (30-40 minutes)

#### Key Teaching Points:
- **Geocoding services:** Nominatim, Google, Census
- **Address standardization:** Formats, abbreviations, completeness
- **Error handling:** Failed geocoding, ambiguous results
- **Batch strategies:** Rate limits, caching, fallbacks

#### Time Breakdown:
- Geocoding concepts (5 min)
- Service comparison (5 min)
- Address preparation (10 min)
- Geocoding demo (10 min)
- Error handling (5 min)
- Practice (5 min)

#### Common Student Questions:
1. **"Which geocoding service is best?"**
   - Depends on use case
   - Trade-offs: Cost, accuracy, rate limits
   - Nominatim: Free but limited

2. **"How do I handle geocoding failures?"**
   - Manual correction
   - Alternative services
   - Approximate locations

3. **"Can I geocode international addresses?"**
   - Service dependent
   - May need different providers
   - Consider coordinate systems

#### Discussion Prompts:
- What are the privacy implications of geocoding?
- How do we validate geocoding accuracy?
- When are approximate locations acceptable?

#### Assessment Ideas:
- **Geocoding:** Convert 10 addresses successfully
- **Validation:** Verify geocoding accuracy
- **Error handling:** Process dataset with problematic addresses

#### Modifications:
- **Easier:** Provide clean addresses, single provider
- **Harder:** Handle messy data, multiple providers
- **Advanced:** Build geocoding pipeline with fallbacks

---

## 🎯 Workshop Formats

### 1-Hour Introduction Workshop

**Objective:** Give participants hands-on experience with basic accessibility analysis

**Schedule:**
- 0:00-0:05 - Introduction and setup verification
- 0:05-0:15 - Concept overview with examples
- 0:15-0:30 - Tutorial 01 walkthrough
- 0:30-0:45 - Participant practice with own location
- 0:45-0:55 - Sharing results and discussion
- 0:55-1:00 - Resources and next steps

**Materials Needed:**
- Slide deck with isochrone examples
- Coordinate reference sheet
- Troubleshooting guide
- Follow-up resources

**Key Deliverable:** Each participant creates one accessibility map

---

### 3-Hour Hands-On Workshop

**Objective:** Build competency in accessibility analysis and demographic integration

**Schedule:**
- 0:00-0:15 - Introduction and software setup
- 0:15-0:45 - Tutorial 01: Complete workflow
- 0:45-1:15 - Tutorial 02-03: Modes and demographics
- 1:15-1:30 - Break
- 1:30-2:00 - Tutorial 04-05: Custom data and combining
- 2:00-2:30 - Independent project work
- 2:30-2:50 - Presentations and peer review
- 2:50-3:00 - Wrap-up and resources

**Materials Needed:**
- Complete tutorial set
- Sample datasets
- Project templates
- Peer review forms

**Key Deliverable:** Custom analysis of participant's area of interest

---

### Full-Day Intensive

**Objective:** Comprehensive training for research applications

**Schedule:**
- 09:00-09:30 - Setup and introductions
- 09:30-10:30 - Tutorials 01-02: Fundamentals
- 10:30-10:45 - Break
- 10:45-12:00 - Tutorials 03-05: Data integration
- 12:00-13:00 - Lunch
- 13:00-14:30 - Tutorials 06-08: Advanced techniques
- 14:30-14:45 - Break
- 14:45-16:00 - Project development
- 16:00-16:45 - Presentations
- 16:45-17:00 - Next steps and resources

**Materials Needed:**
- All tutorials and solutions
- Research paper examples
- Project rubric
- Certificate of completion

**Key Deliverable:** Research-quality analysis with documentation

---

### Multi-Week Course (8 Weeks)

**Objective:** Deep expertise in accessibility analysis for academic credit

**Weekly Structure:**
- **Week 1:** Introduction and Tutorial 01-02
- **Week 2:** Demographics and Tutorial 03-04
- **Week 3:** Integration and Tutorial 05-06
- **Week 4:** Advanced features and Tutorial 07-08
- **Week 5:** Equity analysis (Tutorial 09-10)
- **Week 6:** Case studies (Tutorial 11-12)
- **Week 7:** Research methods (Tutorial 13)
- **Week 8:** Final project presentations

**Assessment Components:**
- Weekly exercises (40%)
- Midterm project (25%)
- Final project (35%)

---

## 🛠️ Classroom Management

### Pre-Workshop Checklist

#### 2 Weeks Before:
- [ ] Send installation instructions
- [ ] Share Census API key signup link
- [ ] Provide system requirements
- [ ] Create shared folder for materials

#### 1 Week Before:
- [ ] Send reminder with agenda
- [ ] Share test script for setup verification
- [ ] Provide backup plan for technical issues
- [ ] Prepare example datasets

#### 1 Day Before:
- [ ] Test all code examples
- [ ] Prepare troubleshooting guide
- [ ] Set up backup environments
- [ ] Print handouts if needed

#### Day of Workshop:
- [ ] Arrive 30 minutes early
- [ ] Test projector/screen sharing
- [ ] Verify internet connectivity
- [ ] Set up help signal system

### Common Technical Issues

#### Installation Problems:
**Issue:** "Import error: No module named socialmapper"
**Solution:**
```bash
# Verify installation
uv pip list | grep socialmapper
# Reinstall if needed
uv pip install --upgrade socialmapper
```

#### API Key Issues:
**Issue:** "Census API key not found"
**Solution:**
```python
# Set temporarily in notebook
import os
os.environ['CENSUS_API_KEY'] = 'your-key-here'
```

#### Performance Problems:
**Issue:** "Code is running very slowly"
**Solutions:**
- Reduce travel time (5 minutes for testing)
- Limit census blocks (first 20)
- Use pre-cached data
- Check internet connection

#### Geocoding Failures:
**Issue:** "Could not geocode address"
**Solutions:**
- Use coordinates instead
- Provide coordinate lookup tool
- Have backup coordinate list

### Managing Different Skill Levels

#### For Beginners:
- Pair with more experienced participants
- Provide extra scaffolding code
- Use smaller datasets
- Focus on running, not writing code

#### For Advanced Users:
- Suggest extensions to exercises
- Provide optimization challenges
- Encourage peer mentoring
- Share advanced resources

#### Mixed Groups:
- Use breakout rooms/groups by level
- Provide differentiated exercises
- Encourage collaboration
- Have TAs for different levels

### Online vs. In-Person

#### Online Workshops:
**Advantages:**
- Screen sharing for debugging
- Breakout rooms for group work
- Recording for review
- Chat for questions

**Challenges:**
- Harder to spot confusion
- Technical issues compound
- Less peer interaction
- Attention management

**Best Practices:**
- Regular check-ins (every 15 min)
- Use polls for understanding
- Encourage cameras on
- Have a TA monitor chat
- Shorter segments (10-15 min)
- More breaks

#### In-Person Workshops:
**Advantages:**
- Direct observation
- Peer learning
- Immediate help
- Better engagement

**Challenges:**
- Varied hardware
- Installation issues
- Space requirements
- Projection visibility

**Best Practices:**
- Roam while teaching
- Use sticky notes for help
- Encourage pair programming
- Live code together
- Print key references

---

## 📊 Assessment Tools

### Knowledge Check Questions

#### Tutorial 01 Check:
1. What is an isochrone? Draw and label one.
2. List three types of POIs you might search for.
3. What is a census block group?
4. Describe the basic workflow steps.

#### Tutorial 03 Check:
1. What's the hierarchy of census geographies?
2. Name 5 demographic variables available.
3. Why might data be suppressed?
4. How do you interpret margin of error?

#### Tutorial 05 Check:
1. Draw a workflow diagram for your analysis.
2. What makes a good composite metric?
3. How do you handle missing data?
4. Describe aggregation strategies.

### Practical Assignments

#### Assignment 1: Basic Analysis (Tutorial 01-02)
**Task:** Analyze accessibility to grocery stores
**Requirements:**
- Use 3 travel times (5, 10, 15 min)
- Compare walk and drive modes
- Include population analysis
- Create visualization

**Grading Rubric:**
- Correct implementation (40%)
- Complete analysis (30%)
- Visualization quality (20%)
- Interpretation (10%)

#### Assignment 2: Custom Analysis (Tutorial 04-05)
**Task:** Analyze self-selected POIs
**Requirements:**
- Minimum 5 POIs
- Integrate demographics
- Create composite metric
- Write methodology

**Grading Rubric:**
- Data preparation (25%)
- Analysis design (25%)
- Implementation (25%)
- Documentation (25%)

#### Assignment 3: Research Project (All tutorials)
**Task:** Complete accessibility study
**Requirements:**
- Research question
- Literature review
- Methodology
- Results and discussion
- Limitations

**Grading Rubric:**
- Research design (20%)
- Technical implementation (30%)
- Analysis quality (25%)
- Writing and presentation (25%)

### Project Ideas by Discipline

#### Urban Planning:
- Transit stop accessibility audit
- Bike infrastructure gap analysis
- Community center site selection
- Food desert identification

#### Public Health:
- Healthcare provider accessibility
- Pharmacy desert analysis
- Emergency service coverage
- Mental health service gaps

#### Social Sciences:
- Educational opportunity analysis
- Social service accessibility
- Recreation access equity
- Community resource mapping

#### Environmental Studies:
- Green space accessibility
- Environmental hazard exposure
- Climate vulnerability mapping
- Sustainable transportation analysis

---

## 📝 Teaching Resources

### Slide Templates

#### Lecture 1: Introduction to Accessibility
1. What is accessibility analysis?
2. Isochrones vs. buffers
3. Network analysis principles
4. Real-world applications
5. SocialMapper overview

#### Lecture 2: Census Geography
1. Geographic hierarchy
2. Block groups explained
3. Data availability
4. Privacy and suppression
5. Margins of error

#### Lecture 3: Equity Analysis
1. Defining equity metrics
2. Demographic considerations
3. Composite indicators
4. Interpretation challenges
5. Policy applications

### Handouts

#### Quick Reference Card:
- Common functions
- Parameter options
- Coordinate finder
- Troubleshooting tips
- Resources

#### Exercise Sheets:
- Guided exercises
- Challenge problems
- Solution hints
- Extension ideas

### Additional Materials

#### Sample Datasets:
- City POI lists
- Coordinate references
- Demographic profiles
- Analysis examples

#### Code Templates:
- Basic analysis
- Batch processing
- Custom metrics
- Visualization

---

## 🎓 Instructor Support

### Getting Help
- GitHub Discussions for questions
- Issue tracker for problems
- Community forum
- Office hours (monthly)

### Contributing
- Share teaching materials
- Submit exercise ideas
- Report issues
- Suggest improvements

### Professional Development
- Instructor workshops
- Conference presentations
- Publication opportunities
- Certification program

---

*Thank you for teaching with SocialMapper! Your work helps build more equitable communities through data-driven analysis.* 🗺️📚