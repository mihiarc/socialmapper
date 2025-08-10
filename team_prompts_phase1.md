# SocialMapper Phase 1 Team Role Prompts

## 1. Senior Frontend Lead (6 months, $75K)

**Primary Mission**: Architect and deliver a complete React-based web interface that transforms SocialMapper from CLI-only to a visual platform accessible to non-technical users within 5 minutes.

**Key Deliverables**:
- Production-ready React/TypeScript web application with responsive design
- Integration with existing FastAPI backend (/api/v1 endpoints) 
- Interactive map visualization using Leaflet/MapBox for POI and isochrone display
- Form-based configuration interface replacing CLI parameters
- Real-time analysis progress tracking and result visualization dashboards

**Technical Context**: SocialMapper backend provides FastAPI REST APIs with job management, result storage, and comprehensive analysis capabilities. Current client uses SocialMapperBuilder pattern with Result<T,Error> types. No existing frontend - complete greenfield development required.

**Success Criteria**: Deploy working demo supporting 3 core analysis types (standard POI analysis, nearby POI discovery, census demographic overlays) with <5 minute user onboarding time and 95%+ uptime.

**Critical Dependencies**: Backend API stability from Senior Backend Engineer; UX wireframes and design system from UX/UI Designer; hosting infrastructure from DevOps Engineer.

**Risk Areas**: Integration complexity with existing pipeline orchestrator; handling large GeoJSON result sets in browser; ensuring responsive performance with complex geographic visualizations.

---

## 2. Frontend Developer (6 months, $60K) 

**Primary Mission**: Implement responsive UI components and integrate visualization features under Senior Frontend Lead guidance, focusing on user experience optimization and cross-device compatibility.

**Key Deliverables**:
- Reusable React component library aligned with design system
- Mobile-responsive analysis configuration forms with validation
- Interactive data visualization components (charts, tables, geographic overlays)
- Client-side result export functionality (CSV, GeoJSON, PDF reports)
- Comprehensive unit and integration test coverage (>80%)

**Technical Context**: Work within established React/TypeScript architecture. Implement components consuming SocialMapper Result types and API response formats. Focus on Leaflet map integrations and data visualization libraries (D3.js, Chart.js).

**Success Criteria**: Deliver all UI components on schedule with documented APIs, pass accessibility standards (WCAG 2.1 AA), and maintain component test coverage above 80%.

**Critical Dependencies**: Component specifications and design assets from UX/UI Designer; API integration patterns from Senior Frontend Lead; performance requirements validation from DevOps Engineer.

**Risk Areas**: Cross-browser compatibility issues; performance bottlenecks with large datasets; mobile responsiveness challenges for complex geographic interfaces.

---

## 3. Senior Backend Engineer (3 months, $45K)

**Primary Mission**: Enhance existing FastAPI infrastructure to support high-concurrency web usage patterns and implement robust job queuing for the hosted demo platform.

**Key Deliverables**:
- Optimized API endpoints with request/response caching and database connection pooling
- Background job processing system using Celery/Redis for long-running analyses  
- Enhanced error handling and validation for web client integration
- API rate limiting and user session management
- Performance monitoring and logging infrastructure

**Technical Context**: Extend existing FastAPI server (api_server/main.py) with job_manager and result_storage services. Current architecture uses PipelineOrchestrator with SocialMapperClient/Builder patterns. Backend handles census data, POI discovery, and isochrone generation.

**Success Criteria**: Support 50+ concurrent users with <3 second API response times, implement job queuing with progress tracking, and achieve 99.5% API uptime during demo period.

**Critical Dependencies**: Infrastructure provisioning from DevOps Engineer; frontend integration requirements from Senior Frontend Lead; performance specifications from technical requirements.

**Risk Areas**: Database query optimization under load; job queue management complexity; API backward compatibility during enhancements.

---

## 4. DevOps Engineer (4 months, $60K)

**Primary Mission**: Design and deploy production-ready hosting infrastructure supporting the public demo platform with automated deployment, monitoring, and scaling capabilities.

**Key Deliverables**:
- Docker containerization for both frontend and backend services
- AWS/GCP deployment with auto-scaling, load balancing, and CDN integration
- CI/CD pipeline with automated testing, security scanning, and blue-green deployments
- Comprehensive monitoring stack (metrics, logging, alerting) with Prometheus/Grafana
- Infrastructure-as-code using Terraform with disaster recovery procedures

**Technical Context**: Deploy React SPA with FastAPI backend, Redis job queue, and PostgreSQL database. Handle geographic data processing workloads and file storage for analysis results. Must support demo traffic spikes and ensure data security.

**Success Criteria**: Achieve 99.9% platform uptime, <2 second global page load times, automated deployments with <5 minute rollback capability, and infrastructure costs under $2K/month.

**Critical Dependencies**: Application architecture decisions from Senior Backend Engineer; deployment requirements from Senior Frontend Lead; security and compliance requirements from project specifications.

**Risk Areas**: Infrastructure cost overruns; scaling challenges during traffic spikes; data backup and recovery complexity; security vulnerabilities in public-facing deployment.

---

## 5. UX/UI Designer (4 months, $50K)

**Primary Mission**: Create an intuitive design system and user experience that enables non-technical users to configure complex geographic analyses through visual interfaces rather than command-line parameters.

**Key Deliverables**:
- Complete design system with React component specifications and style guide
- User journey mapping and wireframes for 3 core analysis workflows
- Interactive prototypes demonstrating <5 minute user onboarding experience
- Accessibility-compliant designs meeting WCAG 2.1 AA standards
- User testing reports with iteration recommendations based on usability feedback

**Technical Context**: Design for SocialMapper's complex geographic analysis capabilities including POI discovery, census demographic overlays, and isochrone generation. Must simplify CLI parameters (travel_time, poi_categories, census_variables) into intuitive form interfaces.

**Success Criteria**: Achieve <5 minute time-to-first-analysis in user testing, 90%+ user satisfaction scores, and successful conversion of 3 major analysis types from CLI to visual interface.

**Critical Dependencies**: Technical constraints and capabilities from Senior Frontend Lead; user research data and personas from project stakeholders; development timeline coordination with Frontend Developer.

**Risk Areas**: Oversimplifying complex geographic concepts; accessibility compliance gaps; user testing delays impacting development timelines; design-development handoff communication issues.

---

## 6. Technical Writer (3 months, $30K)

**Primary Mission**: Create comprehensive documentation ecosystem that accelerates developer adoption and provides clear guidance for both API consumers and web platform users.

**Key Deliverables**:
- Interactive API documentation with code examples and integration tutorials
- User guide for web platform covering all analysis types with step-by-step workflows
- Developer onboarding documentation including local setup and contribution guidelines  
- Video tutorials demonstrating key platform features and use cases
- Community forum setup with FAQ, troubleshooting guides, and example galleries

**Technical Context**: Document existing SocialMapperClient/Builder APIs, new web platform features, and FastAPI endpoints. Content must bridge technical implementation details with user-friendly explanations for geographic analysis concepts.

**Success Criteria**: Reduce average developer onboarding time to <30 minutes, achieve documentation satisfaction scores >4.5/5, and create content supporting 1000+ monthly active community forum users.

**Critical Dependencies**: Feature specifications from Senior Frontend Lead; API documentation from Senior Backend Engineer; user feedback and personas from UX/UI Designer.

**Risk Areas**: Technical accuracy gaps during rapid development cycles; content maintenance overhead as features evolve; community engagement and moderation scalability.