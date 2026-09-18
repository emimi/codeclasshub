# CodeCraftHub

CodeCraftHub is a beginner-friendly learning platform API built with Python and Flask.

It allows developers to track courses they want to learn. Course data is stored in a simple JSON file instead of a database, making the project easy to understand while learning the basics of REST APIs.

## Project Overview

CodeCraftHub provides a REST API for managing learning courses.

Each course includes:

- A unique, automatically generated ID
- A course name
- A course description
- A target completion date
- A learning status
- An automatically generated creation timestamp

The API supports all basic CRUD operations:

- **Create** a course
- **Read** courses
- **Update** a course
- **Delete** a course

This project does not include authentication or user management.

---

## Features

- Built with Python and Flask
- RESTful API endpoints
- Create, read, update, and delete courses
- Data stored in `courses.json`
- No database required
- Automatically creates `courses.json` if it does not exist
- Automatically generates course IDs
- Automatically records the course creation timestamp
- Validates required fields
- Validates target dates using `YYYY-MM-DD` format
- Restricts course statuses to:
  - `Not Started`
  - `In Progress`
  - `Completed`
- Returns JSON responses
- Provides helpful error messages
- Includes file read and write error handling

---

## Technologies Used

- Python 3
- Flask
- JSON
- curl for API testing

---

## Requirements

Before installing the project, make sure you have:

- Python 3.8 or newer
- pip, Python's package installer
- A terminal or command prompt
- curl, usually included with macOS and Linux

You can check whether Python is installed:

```bash
python --version