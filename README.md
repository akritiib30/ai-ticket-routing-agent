# 🚀 Resolve IQ

### AI-Powered Intelligent Ticket Routing & Resolution Agent

Resolve IQ is an AI-powered support ticket management system designed to intelligently analyze, classify, prioritize, route, and assist in resolving technical support tickets.

The system combines Machine Learning, knowledge-based retrieval, confidence analysis, escalation logic, and an interactive Streamlit dashboard to create an end-to-end intelligent ticket management experience.

---

## 🎯 Project Overview

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

## ✨ Key Features

### 🤖 AI-Based Ticket Classification
Uses a trained Machine Learning classifier to predict the category of incoming support tickets.

### 🎯 Intelligent Ticket Routing
Automatically maps predicted ticket categories to the appropriate support team.

### 🚨 Priority Estimation
Analyzes ticket content and estimates priority levels:

- 🔴 Urgent
- 🟠 High
- 🟡 Medium
- 🟢 Low

### 🧠 Intelligent Resolution Assistance
Provides resolution recommendations based on the ticket information and retrieved knowledge.

### 🔍 Knowledge-Based Retrieval
Searches the project's ticket knowledge base to find relevant information that can assist with resolving similar issues.

### 📊 Analytics Dashboard
Provides an overview of ticket activity and classification results through an interactive dashboard.

### 📋 Ticket History
Stores submitted tickets and allows users to search and filter historical tickets.

### 🔎 Search & Filtering
History can be filtered using:

- Ticket text
- Category
- Priority

### 👤 User Login / Landing Page
Provides a simple login/landing experience using:

- Name
- Employee/Student ID
- Organization name

No password is required for the current project version.

### 📎 File Attachments
Users can optionally attach files while submitting tickets.

### 📥 CSV Export
Allows ticket information to be exported as CSV data.

### 📄 PDF Reports
Generates downloadable PDF reports containing ticket information and analytics.

### 🌙 Dark / Light Theme
Provides a theme toggle for a more comfortable dashboard experience.

### 👨‍💼 Human Escalation
Low-confidence or sensitive cases can be identified for human review instead of relying completely on automated processing.

### ❓ General / Other Query Handling
Supports queries that do not belong to the main IT ticket categories.

---

## 🧠 Ticket Processing Workflow

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
                         │  & Cleaning         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   AI Classification  │
                         │  Predict Category    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  Priority Estimation │
                         │ Urgent / High /      │
                         │ Medium / Low         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Intelligent        │
                         │   Ticket Routing     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Knowledge Retrieval  │
                         │ Find Relevant        │
                         │ Information          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Resolution        │
                         │   Recommendation     │
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
                  │ Automated      │  │ Human Review / │
                  │ Assistance     │  │ Escalation     │
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


