# Artfolio Analytics

![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-V2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-003B57?style=for-the-badge&logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

An open-source analytics platform for [Artfolio](https://www.artfolio.tech) — track views, visitor trends, referral sources, and device breakdowns for portfolio URLs.

The system architecture is updated in the URL: [Artfolio Analytics System Design](https://whimsical.com/amruth26/artfolio-analytics-system-design-2eZGHwX3Ju32bhnfTZbXv7)

# Production setup

To run production environment, set the environment variable DEBUG to `False`

# Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Getting Started](#getting-started)
- [Production Setup](#production-setup)
- [Contributing](#contributing)
- [License](#license)

# Overview

**Artfolio Analytics** is a platform designed to help users seamlessly track and analyze traffic and engagement on their Artfolio URLs. Our goal is to provide actionable insights and easy integration for artists and creators to understand their audience better.

# Features

- Easy integration with Artfolio URLs
- Real-time analytics dashboard
- User-friendly visualizations
- Secure and scalable backend
- Exportable reports

# System Architecture

The system is designed for scalability and reliability, leveraging modern cloud-native technologies. The architecture includes:

- **Frontend**: React-based dashboard for analytics visualization
- **Backend**: RESTful API built with Python (FastAPI/Django)
- **Database**: PostgreSQL for structured data storage
- **Analytics Engine**: Real-time event processing
- **Authentication**: Secure user management and OAuth integration
- **Deployment**: Dockerized services orchestrated via Kubernetes

For a detailed architecture diagram, visit: [Artfolio Analytics System Design](https://whimsical.com/amruth26/artfolio-analytics-system-design-2eZGHwX3Ju32bhnfTZbXv7)

# Getting Started

1. **Clone the repository:**

   ```bash
   git clone https://github.com/amruth-k99/artfolio-analytics.git
   cd artfolio-analytics
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the development server:**

   ```bash
   export DEBUG=True
   uvicorn src.main:app --reload
   ```

4. **Run the test suite:**
   ```bash
   PYTHONPATH=. pytest
   ```

# Production Setup

To run the production environment, set the environment variable `DEBUG` to `False` and configure your production settings as needed.

# Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements and bug fixes.

# License

This project is licensed under the MIT License.

# Powered by Artfolio.tech

We are proud to say that this is our first open-source project. We are open to collaborations. If you find any issues within our current architecture, feel free to raise a PR or e-mail us at [amruth@artfolio.tech](amruth@artfolio.tech) or [Artfolio Support](support@artfolio.tech).
