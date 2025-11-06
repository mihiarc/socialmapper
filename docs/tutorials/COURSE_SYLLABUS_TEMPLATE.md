# Course Syllabus: Accessibility Analysis with Python

## GIS 450 / URPL 580: Spatial Accessibility and Equity Analysis

### Course Information

**Term:** Spring 2025 (8 weeks)
**Credits:** 3 credit hours
**Meeting Time:** Tuesdays & Thursdays, 2:00-3:30 PM
**Location:** Computer Lab 205 / Online Option Available
**Prerequisites:** Basic Python programming or instructor consent

**Instructor:** [Your Name]
**Email:** [instructor@university.edu]
**Office Hours:** Mon/Wed 3:00-4:00 PM or by appointment
**Course Website:** [Canvas/Blackboard URL]

---

## Course Description

This hands-on course introduces students to spatial accessibility analysis using Python and the SocialMapper library. Students will learn to measure, analyze, and visualize how communities access essential services, with emphasis on equity implications and policy applications. The course combines technical skills in geospatial analysis with critical thinking about urban planning, public health, and social justice.

## Learning Outcomes

Upon successful completion of this course, students will be able to:

1. **Technical Skills**
   - Create and interpret isochrones for multiple travel modes
   - Integrate census demographic data with spatial analysis
   - Develop custom accessibility metrics and indices
   - Build reproducible analysis workflows in Python

2. **Analytical Skills**
   - Evaluate spatial equity in service provision
   - Identify and quantify accessibility gaps
   - Compare accessibility across different populations
   - Assess policy interventions using spatial analysis

3. **Applied Skills**
   - Conduct real-world accessibility assessments
   - Create publication-quality maps and visualizations
   - Communicate findings to diverse audiences
   - Develop evidence-based policy recommendations

4. **Critical Thinking**
   - Critique assumptions in accessibility modeling
   - Understand limitations of spatial analysis
   - Consider multiple perspectives on equity
   - Evaluate ethical implications of data use

---

## Required Materials

### Software (Free)
- Python 3.11+ with SocialMapper library
- Census API key (free from census.gov)
- GitHub account for code sharing
- Jupyter notebooks or VS Code

### Textbook
- No required textbook
- All materials provided through course website
- Optional: "Python for Geographic Data Analysis" (recommended)

### Hardware Requirements
- Computer with 8GB+ RAM
- Stable internet connection
- Windows, Mac, or Linux OS

---

## Course Schedule

### Week 1: Foundations of Accessibility Analysis
**Learning Objectives:**
- Understand accessibility vs. mobility concepts
- Master basic SocialMapper workflow
- Compare travel mode impacts on access

**Tuesday: Introduction & Setup**
- Course overview and expectations
- What is accessibility analysis?
- Software installation and testing
- **Tutorial 01:** Getting Started (in-class)
- **Reading:** Páez et al. (2012) "Measuring Accessibility"

**Thursday: Travel Modes & Networks**
- Network analysis principles
- Travel mode characteristics
- **Tutorial 02:** Travel Modes (hands-on)
- **Exercise:** Compare modes for your neighborhood

**Assignment 1:** Basic Accessibility Analysis (Due Week 2)
- Analyze grocery store access in assigned area
- Compare walk, bike, drive access
- Create summary report with maps

---

### Week 2: Demographics and Data Integration
**Learning Objectives:**
- Work with census geographic hierarchies
- Integrate demographic and spatial data
- Handle missing and suppressed data

**Tuesday: Census Geography & API**
- Understanding census units
- American Community Survey overview
- **Tutorial 03:** Census Demographics
- **Reading:** Logan et al. (2014) "Interpolating US Census Data"

**Thursday: Custom Data Integration**
- Preparing and validating POI data
- Batch processing techniques
- **Tutorial 04:** Custom POIs
- **Exercise:** Import and analyze custom dataset

**Assignment 2:** Demographic Profile (Due Week 3)
- Create area demographic profile
- Analyze population characteristics
- Compare different geographic scales

---

### Week 3: Advanced Analysis Techniques
**Learning Objectives:**
- Design complex analysis workflows
- Create composite accessibility metrics
- Implement multi-location comparisons

**Tuesday: Combining Analyses**
- Workflow design patterns
- Data integration strategies
- **Tutorial 05:** Combining Analysis
- **Lab:** Build custom workflow

**Thursday: Multi-Location Analysis**
- Batch processing strategies
- Service area overlaps
- **Tutorial 06:** Multi-Location Analysis
- **Exercise:** Site selection problem

**Midterm Project Assigned:** Community Resource Assessment
- Select study area and resources
- Design analysis methodology
- Due Week 5

---

### Week 4: Geographic Scales and Special Cases
**Learning Objectives:**
- Understand MAUP and scale effects
- Implement geocoding pipelines
- Handle different geographic units

**Tuesday: Scale and Aggregation**
- ZIP codes vs. census blocks
- Modifiable Areal Unit Problem
- **Tutorial 07:** ZIP Code Analysis
- **Reading:** Openshaw (1984) "The MAUP"

**Thursday: Address Geocoding**
- Geocoding services comparison
- Error handling strategies
- **Tutorial 08:** Address Geocoding
- **Lab:** Build geocoding pipeline

**Assignment 3:** Scale Comparison (Due Week 5)
- Analyze same area at multiple scales
- Document scale effects
- Recommend appropriate scale

---

### Week 5: Equity Analysis Framework
**Learning Objectives:**
- Develop equity metrics
- Analyze disparate access
- Create equity indices

**Tuesday: Measuring Equity**
- Equity vs. equality concepts
- Vulnerability indicators
- **Tutorial 09:** Equity Analysis
- **Discussion:** What makes access equitable?

**Thursday: Transit Equity Case Study**
- Transportation justice framework
- Transit desert identification
- **Tutorial 10:** Transit Desert Analysis
- **Guest Speaker:** Local transit planner

**Midterm Project Due**
- Present findings (10 minutes)
- Peer review and feedback
- Submit written report

---

### Week 6: Applied Case Studies
**Learning Objectives:**
- Apply methods to real problems
- Evaluate policy interventions
- Communicate to stakeholders

**Tuesday: Public Health Applications**
- Healthcare accessibility
- Food environment analysis
- **Tutorial 11:** Healthcare Deserts
- **Case Study:** COVID-19 vaccine access

**Thursday: Environmental Justice**
- Environmental burden analysis
- Cumulative impact assessment
- **Lab:** Environmental justice indicators
- **Reading:** Bullard (2008) "Environmental Justice"

**Assignment 4:** Policy Brief (Due Week 7)
- Identify accessibility problem
- Propose intervention
- Evaluate expected impact

---

### Week 7: Comparative and Advanced Methods
**Learning Objectives:**
- Compare cities/regions
- Implement advanced metrics
- Optimize facility locations

**Tuesday: Comparative Analysis**
- Cross-city comparisons
- Standardization methods
- **Tutorial 12:** Comparative Urban Analysis
- **Exercise:** Compare 3 cities

**Thursday: Advanced Techniques**
- Location-allocation models
- Optimization approaches
- Machine learning integration
- **Lab:** Custom metric development

**Final Project Assigned:** Comprehensive Accessibility Study
- Original research question
- Multiple data sources
- Policy recommendations
- Due Week 8

---

### Week 8: Research Methods and Presentations
**Learning Objectives:**
- Ensure reproducible research
- Present complex analyses
- Critique accessibility studies

**Tuesday: Reproducible Research**
- Documentation standards
- Version control with Git
- **Tutorial 13:** Reproducible Workflows
- **Workshop:** Creating research packages

**Thursday: Final Presentations**
- Student presentations (7 minutes each)
- Peer feedback and discussion
- Course wrap-up and reflection

**Final Project Due:** Friday, 5:00 PM
- Written report (15-20 pages)
- Code repository
- Presentation slides

---

## Assessment and Grading

### Grade Distribution

| Component | Percentage | Description |
|-----------|------------|-------------|
| Assignments (4) | 40% | Weekly assignments (10% each) |
| Midterm Project | 20% | Community resource assessment |
| Final Project | 25% | Comprehensive accessibility study |
| Participation | 10% | Class discussion, peer review |
| Exercises | 5% | Tutorial completion and exercises |

### Grading Scale

| Grade | Percentage | Grade Points |
|-------|------------|--------------|
| A | 93-100% | 4.0 |
| A- | 90-92% | 3.7 |
| B+ | 87-89% | 3.3 |
| B | 83-86% | 3.0 |
| B- | 80-82% | 2.7 |
| C+ | 77-79% | 2.3 |
| C | 73-76% | 2.0 |
| C- | 70-72% | 1.7 |
| D | 60-69% | 1.0 |
| F | <60% | 0.0 |

### Assignment Rubrics

**Technical Implementation (40%)**
- Code correctness and efficiency
- Appropriate method selection
- Error handling and validation

**Analysis Quality (30%)**
- Depth of analysis
- Statistical rigor
- Interpretation accuracy

**Communication (20%)**
- Clear writing and visualization
- Appropriate for audience
- Professional presentation

**Innovation (10%)**
- Creative approaches
- Extended analysis
- Novel insights

---

## Course Policies

### Attendance Policy
- Attendance expected but not mandatory
- Recordings available for online students
- Notify instructor of planned absences

### Late Work Policy
- 10% penalty per day late
- Maximum 3 days late accepted
- One "grace day" per student per term

### Collaboration Policy
- Collaboration encouraged on exercises
- Individual work required on assignments
- Cite all sources and collaborators

### Academic Integrity
- Original work required
- Proper citation mandatory
- Plagiarism results in course failure

### Accommodation Statement
Students with documented disabilities who may need accommodations should make an appointment with the instructor as soon as possible. Students should also contact Disability Services to verify their eligibility for reasonable accommodations.

---

## Resources and Support

### Technical Support
- Office hours for debugging help
- Peer tutoring available
- Stack Overflow and GitHub Issues

### Writing Support
- University Writing Center
- Report templates provided
- Peer review sessions

### Mental Health Resources
- Counseling Center: [phone]
- 24/7 Crisis Line: [phone]
- Wellness workshops available

### Additional Resources
- GIS Lab: Open M-F 9am-9pm
- Census Data Portal: data.census.gov
- OpenStreetMap: openstreetmap.org
- Course Discord/Slack channel

---

## Weekly Discussion Topics

### Week 1: What is Accessible?
- How do we define accessibility?
- Who decides what's "essential"?

### Week 2: Whose Data?
- Census undercount issues
- Privacy vs. analysis needs

### Week 3: The Right Scale
- Neighborhood vs. city planning
- Individual vs. aggregate needs

### Week 4: Technical Barriers
- Digital divide impacts
- Open source vs. proprietary

### Week 5: Defining Equity
- Equality vs. equity
- Historical context matters

### Week 6: Policy Impact
- From analysis to action
- Unintended consequences

### Week 7: Comparing Cities
- Context and comparability
- Best practices transfer

### Week 8: Future Directions
- Emerging technologies
- Career paths

---

## Final Project Guidelines

### Project Components

1. **Research Question** (10%)
   - Clear, focused question
   - Theoretical grounding
   - Policy relevance

2. **Literature Review** (15%)
   - Minimum 10 sources
   - Synthesis of findings
   - Identified gaps

3. **Methodology** (25%)
   - Detailed methods
   - Justification of choices
   - Limitations acknowledged

4. **Analysis** (25%)
   - Comprehensive analysis
   - Multiple perspectives
   - Robust validation

5. **Results** (15%)
   - Clear presentation
   - Quality visualizations
   - Interpretation

6. **Recommendations** (10%)
   - Evidence-based
   - Feasible proposals
   - Stakeholder consideration

### Project Ideas by Discipline

**Urban Planning**
- Transit network redesign evaluation
- Affordable housing location assessment
- Green space equity analysis

**Public Health**
- Vaccine site optimization
- Food desert intervention
- Mental health service gaps

**Social Work**
- Social service accessibility
- Homeless service coverage
- Youth program access

**Environmental Studies**
- Environmental justice screening
- Climate vulnerability and access
- Green infrastructure equity

**Public Policy**
- Policy intervention simulation
- Budget allocation optimization
- Service consolidation impacts

---

## Professional Development

### Career Applications
- Urban planning consultancies
- Public health departments
- Transportation agencies
- Non-profit advocacy
- Academic research
- Government policy analysis

### Skills Portfolio
By course end, students will have:
- GitHub repository of analyses
- Portfolio of visualizations
- Policy brief samples
- Technical documentation
- Presentation materials

### Networking Opportunities
- Guest speaker contacts
- Alumni connections
- Conference presentation options
- Internship possibilities

---

## Course Evaluation

### Student Feedback Methods
- Mid-term evaluation (Week 4)
- Final course evaluation
- Weekly check-ins
- Open office hours

### Continuous Improvement
- Student suggestions welcomed
- Iterative content updates
- Community partner input
- Industry trend integration

---

*This syllabus is subject to change. Students will be notified of any modifications via course website and email.*

**Last Updated:** January 2025
**Version:** 1.0
**Contact:** [instructor@university.edu]