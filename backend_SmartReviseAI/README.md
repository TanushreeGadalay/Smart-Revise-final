# SmartRevise AI — Backend

## Overview

SmartRevise AI backend provides an asynchronous API that generates revision material for a given topic. It uses Flask for API handling, Celery for background task execution, and Redis as the message broker.

The backend allows users to submit a topic and retrieve generated notes, MCQs, and practice questions without blocking the main application.

---

## Technologies Used

* Python
* Flask — REST API framework
* Celery — asynchronous task queue
* Redis — message broker

---

## Setup Instructions

### 1. Activate virtual environment

venv\Scripts\activate

---

### 2. Start Redis server

redis-server

Verify:

redis-cli ping

Expected output:

PONG

---

### 3. Start Celery worker

celery -A tasks worker --loglevel=info --pool=solo

---

### 4. Start Flask backend

python app.py

Server runs at:

http://127.0.0.1:5000

---

## API Endpoints

### POST /generate

Triggers asynchronous revision generation.

Request:

{
"topic": "Binary Search Tree"
}

Response:

{
"task_id": "uuid"
}

---

### GET /result/<task_id>

Fetches task result.

Possible responses:

* PENDING — still processing
* SUCCESS — generated revision content
* FAILURE — task error

---

## Backend Completion Criteria

Backend is complete when:

* Topic triggers Celery async task
* Redis queues task successfully
* Result API returns generated content
* Input validation is enforced
* Documentation is available

---

SmartRevise AI backend is now ready for frontend integration.
