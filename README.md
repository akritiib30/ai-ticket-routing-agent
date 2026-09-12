# Resolve IQ

### AI-Powered Intelligent Ticket Routing & Resolution Agent

Resolve IQ is an AI-powered support ticket management system designed to intelligently analyze, classify, prioritize, route, and assist in resolving technical support tickets.

The system combines Machine Learning, knowledge-based retrieval, confidence analysis, escalation logic, and an interactive dashboard to create an end-to-end intelligent ticket management experience.

The system automates the majority of the ticket management workflow, from classification and routing to resolution assistance and escalation.

---

## Project Overview

In traditional IT support systems, tickets often need to be manually reviewed, categorized, prioritized, and assigned to the appropriate team.

Resolve IQ automates much of this process.

A user submits a support ticket, and the system analyzes the ticket to determine:

- What type of issue it represents
- Which team should handle it
- How urgent the issue is
- Whether it can be handled automatically
- Whether human intervention may be required
- What relevant knowledge or resolution information can assist with the issue

The result is a faster, more organized, and more intelligent ticket management workflow.

---

## Key Features

### AI-Based Ticket Classification

Uses a trained Machine Learning classifier to predict the category of incoming support tickets.

### Intelligent Ticket Routing

Automatically maps predicted ticket categories to the appropriate support team.

### Priority Estimation

Analyzes ticket content and estimates priority levels:

- Urgent
- High
- Medium
- Low

### Intelligent Resolution Assistance

Provides resolution recommendations based on ticket information and retrieved knowledge from historical tickets.

### Knowledge-Based Retrieval

Searches the project's ticket knowledge base to find relevant information that can assist with resolving similar issues.

### Confidence Analysis

Evaluates the confidence of the classification and determines whether the ticket can be handled automatically or requires human review.

### Human Escalation

Low-confidence or sensitive cases can be identified for human review instead of relying completely on automated processing.

### Recurring Issue Detection

Identifies potentially recurring issues by comparing incoming tickets with previously submitted tickets.

### Analytics Dashboard

Provides an overview of ticket activity, categories, priorities, and classification results through an interactive dashboard.

### Ticket History

Stores submitted tickets and allows users to search and review historical ticket information.

### Search & Filtering

Historical tickets can be filtered using:

- Ticket text
- Category
- Priority

### User Login / Landing Page

Provides a simple login/landing experience using:

- Name
- Employee/Student ID
- Organization name

No password is required for the current project version.

### File Attachments

Users can optionally attach files while submitting tickets.

### CSV Export

Allows ticket information to be exported as CSV data.

### PDF Reports

Generates downloadable PDF reports containing ticket information and analytics.

### Dark / Light Theme

Provides a theme toggle for a more comfortable dashboard experience.

### General / Other Query Handling

Supports queries that do not belong to the main IT ticket categories.

---

## Ticket Processing Workflow

```text
                         ┌──────────────────────┐
                         │         User         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Login / Landing    │
                         │        Page          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Submit Support     │
                         │       Ticket         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  Text Preprocessing  │
                         │      & Cleaning      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  AI Classification   │
                         │   Predict Category   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  Priority Estimation │
                         │  Urgent / High /     │
                         │  Medium / Low        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Intelligent Ticket   │
                         │       Routing        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Knowledge Retrieval  │
                         │  Find Relevant       │
                         │     Information      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     Resolution       │
                         │    Recommendation    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Confidence Analysis  │
                         └──────────┬───────────┘
                                    │
                           ┌────────┴────────┐
                           │                 │
                         High              Low /
                       Confidence        Sensitive
                           │                 │
                           ▼                 ▼
                  ┌────────────────┐  ┌────────────────┐
                  │   Automated    │  │  Human Review  │
                  │   Assistance   │  │ / Escalation   │
                  └───────┬────────┘  └───────┬────────┘
                          │                   │
                          └─────────┬─────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Ticket History    │
                         │ Search & Filtering   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Analytics       │
                         │   & Export Reports   │
                         └──────────────────────┘
```

---

## Machine Learning

Resolve IQ uses a Machine Learning pipeline for ticket classification.

### Classification Pipeline

```text
Ticket Text
     |
     ▼
Text Preprocessing
     |
     ▼
TF-IDF Vectorization
     |
     ▼
Logistic Regression
     |
     ▼
Predicted Ticket Category
```

The classifier is trained on a dataset of technical support tickets covering multiple IT support categories.

The system also uses rule-based intent detection for commonly identifiable issues before falling back to the Machine Learning classifier.

---

## Ticket Categories

The system supports an enterprise-oriented ticket taxonomy including:

- Infrastructure
- Application & Software
- Security Operations
- Database & Storage
- Network & Connectivity
- Account & Access
- Hardware & Peripherals
- Email & Collaboration
- General / Other

These categories are mapped to the appropriate support teams for routing.

---

## Confidence-Based Decision Making

Resolve IQ uses classification confidence to determine the level of automation.

| Confidence | Decision |
|------------|----------|
| High | Automated assistance |
| Medium | Recommendation with human review |
| Low | Escalation to human support |

Sensitive categories can also be routed for human intervention even when the classification confidence is high.

This approach helps maintain a balance between automation and operational safety.

---

## Knowledge Retrieval

The system maintains a historical ticket knowledge base that can be used to identify similar previously resolved issues.

The retrieved historical information can provide:

- Similar ticket descriptions
- Previous resolutions
- Relevant issue categories
- Supporting information for troubleshooting

This allows the system to reuse existing organizational knowledge instead of treating every ticket as a completely new problem.

---

## Priority Estimation

Ticket priority is estimated based on the content and context of the ticket.

The system supports four priority levels:

| Priority | Description |
|----------|-------------|
| Urgent | Immediate attention required |
| High | Significant impact or sensitive issue |
| Medium | Normal support requirement |
| Low | Minor or non-critical issue |

Priority estimation helps support teams focus on tickets that require faster attention.

---

## Human-in-the-Loop Architecture

Resolve IQ does not attempt to automate every type of IT operation.

The system is designed to escalate cases that are:

- Low confidence
- Security-sensitive
- Access-sensitive
- Database-related
- Potentially high-risk
- Outside the system's safe automation boundaries

This ensures that automation supports human IT teams rather than replacing human oversight for critical operations.

---

## Technology Stack

### Backend

- Python
- Flask
- SQLite

### Machine Learning

- Scikit-learn
- TF-IDF
- Logistic Regression

### Data Processing

- Pandas
- NumPy

### Frontend

- Streamlit
- HTML/CSS/JavaScript

### Reporting

- CSV Export
- PDF Report Generation

---

## Project Structure

```text
resolve-iq/
│
├── agent/
│   ├── classification/
│   ├── retrieval/
│   ├── routing/
│   ├── resolution/
│   ├── escalation/
│   └── remediation/
│
├── data/
│   └── tickets.csv
│
├── models/
│   └── trained ML models
│
├── templates/
│   └── frontend templates
│
├── static/
│   └── CSS / JavaScript / assets
│
├── app.py
├── flask_app.py
├── pipeline.py
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd resolve-iq
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment.

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

For the Streamlit application:

```bash
streamlit run app.py
```

For the Flask application:

```bash
python flask_app.py
```

Open the URL displayed in the terminal to access the application.

---

## Future Scope

- **Semantic RAG:** Integrate embeddings and vector databases for more accurate retrieval of similar historical tickets and solutions.
- **LLM-Powered Resolution:** Generate contextual troubleshooting steps using retrieved knowledge and ticket information.
- **Agentic Automation:** Introduce specialized AI agents for diagnosis, resolution, escalation, and supervision.
- **Automated Remediation:** Integrate with enterprise IT tools to safely execute approved fixes with human-in-the-loop controls.
- **Continuous Learning:** Learn from resolved tickets and technician feedback to improve classification and recommendations.
- **Predictive Support:** Detect recurring patterns and potential IT incidents before they become major issues.
- **Enterprise Integration:** Connect with platforms such as ServiceNow, Jira, Microsoft Teams, Slack, and monitoring systems.
- **Multilingual Support:** Enable ticket handling in multiple Indian and international languages.

---

## Project Vision

Resolve IQ aims to evolve from an intelligent ticket management system into an autonomous IT support platform capable of understanding incidents, retrieving organizational knowledge, diagnosing issues, recommending solutions, performing safe automated remediation, and escalating complex cases to human experts.

---

## Disclaimer

Resolve IQ is an academic/project implementation and is intended for demonstration and development purposes. Automated recommendations should be reviewed by qualified IT personnel before being applied to production systems.
