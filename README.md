# Data Analyst AI

Data Analyst AI is a Python-based application that automatically profiles datasets, generates insights, recommends visualizations, and creates downloadable reports.

Built with:

* Python
* Streamlit
* Pandas
* Plotly
* OpenPyXL

---

# Project Overview

The objective of this project is to automate the first stage of data analysis.

Users can upload CSV or Excel files and instantly receive:

* Dataset profiling
* Data quality analysis
* Automatic insights
* Statistical summaries
* Visualization recommendations
* Downloadable reports

---

# Application Preview

## Dataset Upload & Profiling

![Application Overview](Images/Image 1.png)

The application loads CSV and Excel files and automatically generates a complete dataset profile.

---

## Dataset Structure Analysis

![Cardinality Analysis](Images/Image 2.png)

The profiler identifies:

* Missing values
* Duplicate records
* Cardinality
* Numerical variables
* Categorical variables
* Potential unique identifiers

---

## Category Analysis

![Top Categories](Images/Image 3.png)

Automatic category distribution analysis helps users quickly understand the composition of the dataset.

---

## Data Preview

![Dataset Preview](Images/Image 4.png)

The application displays the dataset structure and provides an initial overview of the data.

---

## Data Types & Statistics

![Statistics](Images/Image 5.png)

Automatic generation of:

* Data types
* Descriptive statistics
* Numerical summaries

---

## Intelligent Visualization

![Visualization](Images/Image 6.png)

The application recommends visualizations based on the dataset structure and allows dynamic selection of categories and metrics.

---

# Features

## Data Upload

* CSV support
* Excel (.xlsx) support

## Dataset Profiling

* Row count
* Column count
* Missing values
* Missing value percentage
* Duplicate detection
* Memory usage
* Cardinality analysis
* Top categories
* Potential primary keys

## Automatic Insights

The application automatically generates insights about:

* Dataset size
* Data quality
* Variable distribution
* Potential unique identifiers

## Intelligent Visualization

Supported charts:

* Line Charts
* Bar Charts
* Histograms

Chart recommendations are generated automatically according to the uploaded dataset.

## Report Export

Users can export a report containing:

* Dataset summary
* Profiling information
* Generated insights

---

# Technologies

* Python
* Streamlit
* Pandas
* Plotly
* OpenPyXL

---

# Project Structure

```text
data-analyst-ai/

├── app.py
├── requirements.txt
├── README.md
├── .gitignore

├── Images/

└── src/
    ├── __init__.py
    ├── analysis.py
    ├── charts.py
    └── profiler.py
```

---

# Installation

```bash
git clone https://github.com/Duh1995/Data-Analyst-AI.git
```

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

---

# Roadmap

## Part 1 - Automated Data Profiling & Visualization

Completed:

* Dataset profiling
* Automatic insights
* Intelligent visualizations
* Report export

## Part 2 - AI Integration

Planned:

* Natural language queries
* AI-generated insights
* Executive summaries
* OpenAI integration

---

# Learning Objectives

This project was created to improve practical skills in:

* Data Analytics
* Python Development
* Data Visualization
* Software Architecture
* AI Applications for Analytics

---

# Author

Duarte Silva
