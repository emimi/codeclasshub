"""
CodeCraftHub - Course Tracking REST API

This Flask application provides CRUD operations for courses and stores
course data in a local JSON file named courses.json.

Run with:

    python app.py

The API will be available at:

    http://127.0.0.1:5000
"""

from datetime import datetime, timezone
import json
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS


# Create the Flask application
app = Flask(__name__)
CORS(app)

# Store courses.json in the same directory as this Python file
DATA_FILE = Path(__file__).parent / "courses.json"


# These are the only status values accepted by the API
VALID_STATUSES = {
    "Not Started",
    "In Progress",
    "Completed",
}


class StorageError(Exception):
    """
    Custom exception used when there is a problem reading or writing
    the courses.json file.
    """

    pass


def create_data_file_if_needed():
    """
    Create courses.json automatically if it does not already exist.

    The file starts with an empty JSON list because courses will be
    stored as a list of objects.
    """

    try:
        if not DATA_FILE.exists():
            DATA_FILE.write_text("[]", encoding="utf-8")

    except OSError as error:
        raise StorageError(
            f"Unable to create data file: {error}"
        ) from error


def load_courses():
    """
    Read and return all courses from courses.json.

    Returns:
        list: A list of course dictionaries.

    Raises:
        StorageError: If the file cannot be read or contains invalid JSON.
    """

    create_data_file_if_needed()

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            courses = json.load(file)

    except json.JSONDecodeError as error:
        raise StorageError(
            "The courses.json file contains invalid JSON."
        ) from error

    except OSError as error:
        raise StorageError(
            f"Unable to read courses.json: {error}"
        ) from error

    # Make sure the JSON file contains a list
    if not isinstance(courses, list):
        raise StorageError(
            "The courses.json file must contain a JSON list."
        )

    return courses


def save_courses(courses):
    """
    Save the complete list of courses to courses.json.

    Args:
        courses (list): The list of course dictionaries to save.

    Raises:
        StorageError: If the file cannot be written.
    """

    try:
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(courses, file, indent=4)

    except OSError as error:
        raise StorageError(
            f"Unable to write to courses.json: {error}"
        ) from error


def get_next_course_id(courses):
    """
    Generate the next course ID.

    The first course receives ID 1. After that, the next ID is one
    greater than the highest existing ID.

    This prevents deleted IDs from being reused.
    """

    if not courses:
        return 1

    highest_id = max(course.get("id", 0) for course in courses)
    return highest_id + 1


def get_current_timestamp():
    """
    Return the current UTC time in ISO 8601 format.

    Example:

        2026-09-18T12:30:45.123456Z
    """

    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def validate_course_data(data, require_all_fields=True):
    """
    Validate course data sent by the client.

    Args:
        data (dict): Request JSON data.
        require_all_fields (bool): If True, all required fields must
            be present. This is used when creating a course and with
            PUT requests.

    Returns:
        str or None: An error message if validation fails,
        otherwise None.
    """

    required_fields = [
        "name",
        "description",
        "target_date",
        "status",
    ]

    # Check that all required fields exist
    if require_all_fields:
        missing_fields = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing_fields:
            return (
                "Missing required fields: "
                + ", ".join(missing_fields)
            )

    # Validate fields that were included in the request
    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            return "name is required and must be a non-empty string"

    if "description" in data:
        if (
            not isinstance(data["description"], str)
            or not data["description"].strip()
        ):
            return (
                "description is required and must be "
                "a non-empty string"
            )

    if "target_date" in data:
        target_date = data["target_date"]

        if not isinstance(target_date, str):
            return "target_date must be a string in YYYY-MM-DD format"

        try:
            # strptime verifies that the date is a real calendar date
            datetime.strptime(target_date, "%Y-%m-%d")

        except ValueError:
            return (
                "target_date must use the YYYY-MM-DD format"
            )

    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return (
                "status must be one of: "
                "'Not Started', 'In Progress', or 'Completed'"
            )

    return None


def get_request_json():
    """
    Safely retrieve JSON data from the request body.

    Returns:
        dict: The request JSON object.

    Raises:
        ValueError: If the body is missing or is not a JSON object.
    """

    data = request.get_json(silent=True)

    if data is None:
        raise ValueError(
            "Request body must contain valid JSON."
        )

    if not isinstance(data, dict):
        raise ValueError(
            "Request JSON must be an object."
        )

    return data


def find_course(courses, course_id):
    """
    Find a course by its numeric ID.

    Returns:
        dict or None: The matching course, if found.
    """

    return next(
        (
            course
            for course in courses
            if course.get("id") == course_id
        ),
        None,
    )


@app.route("/api/courses", methods=["POST"])
@app.route("/api/courses/", methods=["POST"])
def create_course():
    """
    Create a new course.

    POST /api/courses

    Expected JSON body:

    {
        "name": "REST API Fundamentals",
        "description": "Learn REST API concepts.",
        "target_date": "2026-12-31",
        "status": "Not Started"
    }
    """

    try:
        data = get_request_json()

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    validation_error = validate_course_data(data)

    if validation_error:
        return jsonify({"error": validation_error}), 400

    try:
        courses = load_courses()

        new_course = {
            "id": get_next_course_id(courses),
            "name": data["name"].strip(),
            "description": data["description"].strip(),
            "target_date": data["target_date"],
            "status": data["status"],
            "created_at": get_current_timestamp(),
        }

        courses.append(new_course)
        save_courses(courses)

    except StorageError as error:
        return jsonify({"error": str(error)}), 500

    return jsonify(new_course), 201


@app.route("/api/courses", methods=["GET"])
@app.route("/api/courses/", methods=["GET"])
def get_courses():
    """
    Return all courses.

    GET /api/courses
    """

    try:
        courses = load_courses()

    except StorageError as error:
        return jsonify({"error": str(error)}), 500

    return jsonify(courses), 200


@app.route("/api/courses/<int:course_id>", methods=["GET"])
@app.route("/api/courses/<int:course_id>/", methods=["GET"])
def get_course(course_id):
    """
    Return one course by ID.

    GET /api/courses/1
    """

    try:
        courses = load_courses()

    except StorageError as error:
        return jsonify({"error": str(error)}), 500

    course = find_course(courses, course_id)

    if course is None:
        return jsonify({
            "error": f"Course with ID {course_id} was not found."
        }), 404

    return jsonify(course), 200


@app.route("/api/courses/<int:course_id>", methods=["PUT"])
@app.route("/api/courses/<int:course_id>/", methods=["PUT"])
def update_course(course_id):
    """
    Replace an existing course.

    PUT /api/courses/1

    PUT requires all editable course fields:

    {
        "name": "Updated Course Name",
        "description": "Updated description.",
        "target_date": "2027-01-15",
        "status": "In Progress"
    }

    The ID and created_at values cannot be changed.
    """

    try:
        data = get_request_json()

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    validation_error = validate_course_data(
        data,
        require_all_fields=True,
    )

    if validation_error:
        return jsonify({"error": validation_error}), 400

    try:
        courses = load_courses()

    except StorageError as error:
        return jsonify({"error": str(error)}), 500

    course = find_course(courses, course_id)

    if course is None:
        return jsonify({
            "error": f"Course with ID {course_id} was not found."
        }), 404

    # Update only the editable fields.
    # The ID and created_at timestamp remain unchanged.
    course["name"] = data["name"].strip()
    course["description"] = data["description"].strip()
    course["target_date"] = data["target_date"]
    course["status"] = data["status"]

    try:
        save_courses(courses)

    except StorageError as error:
        return jsonify({"error": str(error)}), 500

    return jsonify(course), 200


@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
@app.route("/api/courses/<int:course_id>/", methods=["DELETE"])
def delete_course(course_id):
    """
    Delete a course by ID.

    DELETE /api/courses/1
    """

    try:
        courses = load_courses()

    except StorageError as error:
        return jsonify({"error": str(error)}), 500

    course = find_course(courses, course_id)

    if course is None:
        return jsonify({
            "error": f"Course with ID {course_id} was not found."
        }), 404

    # Create a new list without the course being deleted
    updated_courses = [
        existing_course
        for existing_course in courses
        if existing_course.get("id") != course_id
    ]

    try:
        save_courses(updated_courses)

    except StorageError as error:
        return jsonify({"error": str(error)}), 500

    return jsonify({
        "message": f"Course with ID {course_id} was deleted."
    }), 200


@app.errorhandler(404)
def handle_not_found(error):
    """
    Handle unknown URLs with a JSON response instead of Flask's
    default HTML error page.
    """

    return jsonify({
        "error": "The requested endpoint was not found."
    }), 404


@app.errorhandler(405)
def handle_method_not_allowed(error):
    """
    Handle HTTP methods that are not supported by an endpoint.
    """

    return jsonify({
        "error": "The HTTP method is not allowed for this endpoint."
    }), 405


@app.errorhandler(500)
def handle_internal_server_error(error):
    """
    Handle unexpected server errors.
    """

    return jsonify({
        "error": "An unexpected internal server error occurred."
    }), 500


if __name__ == "__main__":
    # Create courses.json before starting the server.
    # This ensures the file exists even before the first API request.
    try:
        create_data_file_if_needed()
    except StorageError as error:
        print(f"Startup error: {error}")
        raise SystemExit(1)

    # debug=True is useful while learning and developing.
    # Turn it off in production.
    app.run(debug=True)