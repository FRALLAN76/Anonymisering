A Docker-based solution for anonymizing emails and documents containing personally identifiable information (PII), specifically designed for municipal data requests and GDPR compliance.

## Overview

This tool uses Microsoft Presidio to automatically detect and anonymize sensitive information in emails including:
- Names and personal identifiers
- Email addresses and phone numbers
- Social Security Numbers
- Addresses and locations
- Custom municipal-specific patterns

## Features

- **Automated PII Detection**: Uses advanced NLP to identify sensitive information
- **Batch Processing**: Handle multiple email files simultaneously  
- **Multiple Formats**: Supports .eml, .msg, and .txt files
- **Audit Trail**: Generates detailed reports of what was anonymized
- **Docker-based**: Easy deployment and consistent environment
- **Municipal-ready**: Designed for government transparency requirements

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Email files to anonymize
