# Version 0.3.0-alpha

## Streamlit App Integration
- **Added Streamlit Web App**: Introduced a new Streamlit-based web application (`Home.py`) for SocialMapper, providing an interactive and user-friendly interface for community mapping workflows.
- **Enhanced User Experience**: The Streamlit app allows users to configure, run, and visualize community mapping analyses directly from the browser, streamlining the workflow for both technical and non-technical users.

## New Progress Tracking Functionality
- **Integrated stqdm for Progress Tracking**: Added the `stqdm` library to provide real-time progress bars and feedback during long-running analyses, such as census data fetching and POI processing.
- **Improved User Feedback**: Progress tracking is now visible both in the command-line interface and within the Streamlit app, making it easier to monitor the status of data processing tasks.

## Block Group Fetching: State to County Transition
- **Refactored Block Group Fetching**: Changed the logic for fetching census block groups from a state-based approach to a county-based approach, significantly improving performance and accuracy.
- **County-Based Selection**: Users can now select and analyze block groups at the county level, enabling more granular and relevant community analyses.
- **Optimized Data Handling**: The new approach reduces unnecessary data fetching and processing, resulting in faster and more efficient analyses.

---

These enhancements mark a major step forward in the usability, performance, and flexibility of the SocialMapper project. The addition of the Streamlit app, improved progress tracking, and the shift to county-based block group selection collectively provide a more robust and user-friendly experience for all users. 