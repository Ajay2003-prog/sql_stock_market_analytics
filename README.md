@"
# SQL Stock Market Analytics

An end-to-end stock market analytics project built using **Python, Pandas, SQL, SQLite and Streamlit**.

The project analyzes historical market data for six major Indian companies and converts raw CSV data into a cleaned analytical database, SQL insights and an interactive business intelligence dashboard.

---

## Project Overview

This project demonstrates a complete data analytics workflow:

**Raw CSV Data → Data Cleaning → Cleaned CSV → SQLite Database → SQL Analysis → Streamlit Dashboard**

The analysis covers historical stock prices, trading activity, moving averages, Buy/Sell/Hold crossover signals, returns, volatility, drawdowns and corporate-action analysis.

---

## Companies Analyzed

The project contains historical market data for:

- Bajaj Auto
- Eicher Motors
- Hero Motocorp
- Infosys
- TCS
- TVS Motors

### Dataset Period

**January 2015 – July 2018**

Each stock dataset contains **889 trading records**, resulting in:

**5,334 total records across six stocks.**

---

## Business Objectives

The project focuses on answering practical analytical questions such as:

- How did each stock perform over the analysis period?
- Which stock generated the strongest historical return?
- Which stock had the lowest and highest volatility?
- What were the largest daily price declines?
- How do 20-day and 50-day moving averages compare?
- When did Buy and Sell crossover signals occur?
- Which stocks showed stronger historical momentum?
- How can unusual price movements be investigated?
- How do corporate actions affect historical return calculations?

---

## Project Workflow

```text
Raw CSV Files
      ↓
Data Cleaning with Pandas
      ↓
Cleaned CSV Files
      ↓
SQLite Database
      ↓
SQL Analysis
      ↓
Business Insights
      ↓
Interactive Streamlit Dashboard