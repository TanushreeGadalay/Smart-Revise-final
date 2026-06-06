from flask import Flask, request, jsonify
from flask_cors import CORS
import bcrypt
from dotenv import load_dotenv
import os
import time
import requests
from google import genai
import json
load_dotenv()
# print("API KEY:", os.getenv("GEMINI_API_KEY"))
client_ai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

from dotenv import load_dotenv
from ml.logic import generate_content
load_dotenv()

from tasks import generate_revision

import traceback
import sys

try:
    # your existing app startup code
    pass
except Exception as e:
    traceback.print_exc()
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# ------------------------
# Database (In-Memory)
# ------------------------
# Using in-memory storage instead of MongoDB due to disk space limitations
db_users = {}

print("[+] Using in-memory database")

# ------------------------
# Health Check
# ------------------------
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "Backend running",
        "project": "SmartRevise AI",
        "database": "In-Memory",
        "users_count": len(db_users)
    })

# ------------------------
# SIGNUP
# ------------------------
@app.route("/signup", methods=["POST", "OPTIONS"])
def signup():
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body missing"}), 400

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            return jsonify({"error": "All fields required"}), 400

        # Check if user already exists
        if email in db_users:
            return jsonify({"error": "User already exists"}), 400

        # Hash password
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        db_users[email] = {
            "name": name,
            "email": email,
            "password": hashed_pw,
            "progress": {}
        }

        print(f"[+] User registered: {email}")
        return jsonify({"message": "User created successfully"}), 201
    
    except Exception as e:
        print(f"Signup Error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ------------------------
# LOGIN
# ------------------------
@app.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body missing"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        user = db_users.get(email)

        if not user:
            return jsonify({"error": "User not found. Please sign up first."}), 404

        if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            return jsonify({"error": "Invalid password"}), 401

        print(f"[+] User logged in: {email}")
        return jsonify({
            "message": "Login successful",
            "user": {
                "name": user["name"],
                "email": user["email"]
            }
        }), 200
    
    except Exception as e:
        print(f"Login Error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ------------------------
# SMART NOTES
# ------------------------
# File: backend_SmartReviseAI/app.py

@app.route("/smart-notes", methods=["POST"])
def smart_notes():

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body missing"}), 400

    language = data.get("language")
    topic = data.get("topic")

    if not language:
        return jsonify({"error": "Language is required"}), 400

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    content = generate_content(language, topic)

    return jsonify(content)

# ------------------------
# AI ROUTES (Your Existing)
# ------------------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body missing"}), 400

    language = data.get("language")
    topic = data.get("topic", "")

    if isinstance(topic, str) and ":" in topic:
        parts = topic.split(":", 1)
        if len(parts) == 2:
            possible_lang = parts[0].strip()
            possible_topic = parts[1].strip()
            if not language:
                language = possible_lang
                topic = possible_topic
            elif possible_lang.lower() == language.lower():
                topic = possible_topic

    language = language or "General"
    topic = topic.strip()

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    content = generate_content(language, topic)
    return jsonify(content)


@app.route("/result/<task_id>", methods=["GET"])
def get_result(task_id):
    task = generate_revision.AsyncResult(task_id)

    if task.state == "SUCCESS":
        return jsonify(task.result)

    return jsonify({
        "state": task.state
    })

# ------------------------
# Save generated note
@app.route("/save-note", methods=["POST", "OPTIONS"])
def save_note():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body missing"}), 400

    email = data.get("email")
    topic = data.get("topic")
    content = data.get("content")
    timestamp = data.get("timestamp")

    if not email or not topic or not content:
        return jsonify({"error": "Email, topic, and content are required"}), 400

    user = db_users.get(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.setdefault("progress", {})
    user["progress"].setdefault("notes_saved", []).append({
        "topic": topic,
        "content": content,
        "timestamp": timestamp
    })

    return jsonify({"message": "Note saved"}), 201

# ------------------------
# MCQ GENERATION
# ------------------------
@app.route("/generate-mcqs", methods=["POST", "OPTIONS"])
def generate_mcqs_route():

    if request.method == "OPTIONS":
        return "", 200

    try:

        data = request.json

        topic = data.get("topic")

        if not topic:
            return jsonify({"error": "Topic is required"}), 400

        prompt = f"""
Generate exactly 5 beginner-friendly multiple choice questions about {topic}.

IMPORTANT:
- If a question contains code, include the FULL code snippet inside the question text.
- Format code using plain text.
- Each question must have 4 options (A,B,C,D)
- Include the correct answer
- Return ONLY valid JSON

Format:

[
  {{
    "question": "...",
    "options": {{
      "A": "...",
      "B": "...",
      "C": "...",
      "D": "..."
    }},
    "answer": "A"
  }}
]
"""

        def local_mcq_generator(topic_text, count=5):
            # topic_text may be in the form "Language: Topic" — parse it
            lang = None
            subj = topic_text
            try:
                if isinstance(topic_text, str) and ":" in topic_text:
                    parts = topic_text.split(":", 1)
                    lang = parts[0].strip()
                    subj = parts[1].strip()
            except Exception:
                pass

            subj_title = subj.title() if isinstance(subj, str) else str(subj)

            def make_question(i):
                # Vary question phrasing
                templates = [
                    f"What is {subj_title}?",
                    f"Which of the following best describes {subj_title}?",
                    f"How is {subj_title} typically used in {lang if lang else 'programming'}?",
                    f"Which statement about {subj_title} is TRUE?",
                    f"Choose the correct explanation for {subj_title}."
                ]
                return templates[i % len(templates)]

            def make_options(i):
                # Correct explanation
                correct = f"{subj_title} is a core concept used to structure data and behavior in {lang if lang else 'programming'} applications."

                # Common misconception / partial
                partial = f"{subj_title} relates to some aspects of code organization but is not solely responsible for logic flow."

                # False statement
                falsey = f"{subj_title} is a low-level debugging tool used for performance tuning."

                # Unrelated option (sometimes include a short code example when language known)
                if lang and lang.lower() in ("python", "java", "javascript", "c", "c++"):
                    code_example = {
                        "python": f"Example: def example():\n    pass",
                        "java": f"Example: public class Example {{ }}",
                        "javascript": f"Example: function example() {{ }}",
                        "c": f"Example: int main() {{ return 0; }}",
                        "c++": f"Example: #include <iostream>\nint main() {{ return 0; }}"
                    }.get(lang.lower(), "Example code depends on language.")
                    unrelated = f"A usage example: {code_example}"
                else:
                    unrelated = f"{subj_title} is sometimes confused with unrelated topics like UI layout."

                opts = [correct, partial, falsey, unrelated]

                # Rotate options deterministically per question to vary position
                shift = i % 4
                opts_rotated = opts[shift:] + opts[:shift]

                letters = ["A", "B", "C", "D"]
                options_map = {letters[idx]: opts_rotated[idx] for idx in range(4)}

                # Determine which letter holds the correct answer
                correct_letter = letters[opts_rotated.index(correct)]

                return options_map, correct_letter

            mcqs_list = []
            for i in range(count):
                q_text = make_question(i)
                options_map, correct_letter = make_options(i)
                mcqs_list.append({
                    "question": q_text,
                    "options": options_map,
                    "answer": correct_letter
                })

            return mcqs_list

        import time

        response = None
        last_exception = None

        for attempt in range(3):

            try:

                response = client_ai.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )

                break

            except Exception as e:
                last_exception = e
                print("Retrying Gemini...", e)
                traceback.print_exc()

                time.sleep(3)

        if response is None:
            # Gemini unavailable — use local fallback generator
            mcqs_fallback = local_mcq_generator(topic, count=5)
            err_msg = str(last_exception) if last_exception else "No response from Gemini"
            return jsonify({
                "mcqs": mcqs_fallback,
                "fallback": True,
                "note": "Used local fallback because Gemini was unavailable",
                "detail": err_msg
            }), 200

        cleaned_text = response.text.strip()

        cleaned_text = cleaned_text.replace("```json", "")
        cleaned_text = cleaned_text.replace("```", "")

        try:
            mcqs = json.loads(cleaned_text)
        except Exception as e:
            print("Failed to parse Gemini output as JSON:", e)
            traceback.print_exc()
            # Return fallback MCQs along with raw text for debugging
            mcqs_fallback = local_mcq_generator(topic, count=5)
            return jsonify({
                "mcqs": mcqs_fallback,
                "fallback": True,
                "raw_text": cleaned_text,
                "detail": str(e)
            }), 200

        return jsonify({
            "mcqs": mcqs
        })

    except Exception as e:

        print("MCQ ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500
# ------------------------
# PROGRESS TRACKING
# ------------------------
@app.route("/progress", methods=["GET", "OPTIONS"])
def get_progress():
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        email = request.args.get("email")
        
        if not email:
            return jsonify({"error": "Email required"}), 400
        
        user = db_users.get(email)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        progress_data = user.get("progress", {})
        
        # Calculate statistics
        quizzes = progress_data.get("quizzes", [])
        notes_read = progress_data.get("notes_read", [])
        logic_building = progress_data.get("logic_building", [])
        
        quiz_scores = [q.get("score", 0) for q in quizzes]
        avg_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
        
        return jsonify({
            "email": email,
            "name": user["name"],
            "progress": {
                "quizzes": quizzes,
                "notes_read": notes_read,
                "logic_building": logic_building,
                "stats": {
                    "total_quizzes": len(quizzes),
                    "avg_quiz_score": round(avg_score, 2),
                    "notes_completed": len(notes_read),
                    "logic_problems_solved": len(logic_building)
                }
            }
        }), 200
    
    except Exception as e:
        print(f"Progress Error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/progress/quiz", methods=["POST", "OPTIONS"])
def update_quiz_progress():
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        data = request.get_json()
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Email required"}), 400
        
        user = db_users.get(email)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if "progress" not in user:
            user["progress"] = {}
        
        if "quizzes" not in user["progress"]:
            user["progress"]["quizzes"] = []
        
        quiz_result = {
            "topic": data.get("topic"),
            "score": data.get("score"),
            "total": data.get("total", 10),
            "date": data.get("date"),
            "answers": data.get("answers", [])
        }
        
        user["progress"]["quizzes"].append(quiz_result)
        
        print(f"[+] Quiz progress saved for {email}: {quiz_result['topic']}")
        return jsonify({"message": "Quiz progress saved", "quiz": quiz_result}), 201
    
    except Exception as e:
        print(f"Quiz Progress Error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/progress/notes", methods=["POST", "OPTIONS"])
def update_notes_progress():
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        data = request.get_json()
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Email required"}), 400
        
        user = db_users.get(email)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if "progress" not in user:
            user["progress"] = {}
        
        if "notes_read" not in user["progress"]:
            user["progress"]["notes_read"] = []
        
        note_entry = {
            "topic": data.get("topic"),
            "language": data.get("language"),
            "date": data.get("date")
        }
        
        user["progress"]["notes_read"].append(note_entry)
        
        print(f"[+] Notes progress saved for {email}: {note_entry['topic']}")
        return jsonify({"message": "Notes progress saved", "note": note_entry}), 201
    
    except Exception as e:
        print(f"Notes Progress Error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/progress/logic-building", methods=["POST", "OPTIONS"])
def update_logic_building_progress():
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        data = request.get_json()
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Email required"}), 400
        
        user = db_users.get(email)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if "progress" not in user:
            user["progress"] = {}
        
        if "logic_building" not in user["progress"]:
            user["progress"]["logic_building"] = []
        
        logic_entry = {
            "problem": data.get("problem"),
            "language": data.get("language"),
            "status": data.get("status"),  # "solved" or "attempted"
            "date": data.get("date")
        }
        
        user["progress"]["logic_building"].append(logic_entry)
        
        print(f"[+] Logic building progress saved for {email}: {logic_entry['problem']}")
        return jsonify({"message": "Logic building progress saved", "entry": logic_entry}), 201
    
    except Exception as e:
        print(f"Logic Building Progress Error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500



    
# ------------------------
# LOGIC BUILDERS DATA
# ------------------------
logic_builders_data = {
    "elementary": [
        {"id": 1, "title": "Swap Two Numbers", "goal": "Exchange the values of two variables A and B.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read two numbers 👉 A, B", "✅ Step 3: Use a temporary variable 👉 temp = A", "✅ Step 4: Swap values 👉 A = B, 👉 B = temp", "✅ Step 5: Display swapped values of A and B Stop"]},
        {"id": 2, "title": "Find Largest of Three", "goal": "Find the maximum among three given numbers A, B, and C.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read three numbers 👉 A, B, C", "✅ Step 3: Compare numbers 👉 IF A > B AND A > C THEN Max = A", "✅ Step 4: Compare remaining 👉 ELSE IF B > C THEN Max = B, ELSE Max = C", "✅ Step 5: Display Max Stop"]},
        {"id": 3, "title": "Even or Odd", "goal": "Check if a given number N is even or odd.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read number 👉 N", "✅ Step 3: Check divisibility by 2 👉 IF N % 2 == 0 THEN Result = 'Even'", "✅ Step 4: Handle odd case 👉 ELSE Result = 'Odd'", "✅ Step 5: Display Result Stop"]},
        {"id": 4, "title": "Factorial Calculation", "goal": "Calculate the product of all positive integers up to N.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read number 👉 N", "✅ Step 3: Initialize result 👉 fact = 1", "✅ Step 4: Loop from 1 to N 👉 fact = fact * i", "✅ Step 5: Display fact Stop"]},
        {"id": 5, "title": "Fibonacci Series", "goal": "Generate the first N numbers of the Fibonacci sequence.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read count 👉 N", "✅ Step 3: Initialize first two 👉 A = 0, B = 1", "✅ Step 4: Loop N times 👉 Display A, 👉 C = A + B, 👉 A = B, 👉 B = C", "✅ Step 5: Stop"]},
        {"id": 6, "title": "Check Prime Number", "goal": "Determine if a number N is prime (divisible only by 1 and itself).", "logic": ["✅ Step 1: Start", "✅ Step 2: Read number 👉 N", "✅ Step 3: Check factor loop 👉 FOR i from 2 to SQRT(N)", "✅ Step 4: Verify division 👉 IF N % i == 0 THEN Result = 'Not Prime', STOP", "✅ Step 5: Display 'Prime Number' Stop"]},
        {"id": 7, "title": "Reverse a Number", "goal": "Invert the digits of a given integer N.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read number 👉 N", "✅ Step 3: Loop while N > 0 👉 digit = N % 10, 👉 rev = (rev * 10) + digit", "✅ Step 4: Reduce N 👉 N = N / 10", "✅ Step 5: Display rev Stop"]},
        {"id": 8, "title": "Sum of Digits", "goal": "Calculate the sum of individual digits of a number N.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read number 👉 N", "✅ Step 3: Loop while N > 0 👉 sum = sum + (N % 10)", "✅ Step 4: Reduce N 👉 N = N / 10", "✅ Step 5: Display sum Stop"]},
        {"id": 9, "title": "Leap Year Check", "goal": "Determine if a given year Y is a leap year.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read year 👉 Y", "✅ Step 3: Check conditions 👉 IF (Y % 400 == 0) OR (Y % 4 == 0 AND Y % 100 != 0)", "✅ Step 4: Assign result 👉 Result = 'Leap Year', ELSE Result = 'Not Leap Year'", "✅ Step 5: Display Result Stop"]},
        {"id": 10, "title": "Palindrome Number", "goal": "Check if a number reads the same forwards and backwards.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read number 👉 N", "✅ Step 3: Reverse N into R 👉 Use Reverse Logic", "✅ Step 4: Compare 👉 IF N == R THEN Result = 'Palindrome'", "✅ Step 5: Display Result Stop"]}
    ],
    "intermediate": [
        {"id": 1, "title": "Binary Search", "goal": "Find the position of a target element in a sorted array using divide and conquer.", "logic": ["✅ Step 1: Start", "✅ Step 2: Initialize boundaries 👉 Low = 0, 👉 High = Length - 1", "✅ Step 3: Loop while Low <= High", "✅ Step 4: Calculate mid-point 👉 Mid = (Low + High) / 2", "✅ Step 5: Check if found 👉 IF Arr[Mid] == Target THEN RETURN Mid", "✅ Step 6: Adjust search range 👉 ELSE IF Arr[Mid] < Target THEN Low = Mid + 1", "✅ Step 7: Adjust search range 👉 ELSE High = Mid - 1", "✅ Step 8: Return -1 if not in list Stop"]},
        {"id": 2, "title": "Bubble Sort", "goal": "Sort an array by repeatedly swapping adjacent elements until sorted.", "logic": ["✅ Step 1: Start", "✅ Step 2: Outer loop i from 0 to N-1", "✅ Step 3: Inner loop j from 0 to N-i-2", "✅ Step 4: Compare neighbors 👉 IF Arr[j] > Arr[j+1]", "✅ Step 5: Perform Swap 👉 temp = Arr[j], 👉 Arr[j] = Arr[j+1], 👉 Arr[j+1] = temp", "✅ Step 6: Continue inner loop", "✅ Step 7: Continue outer loop Stop"]},
        {"id": 3, "title": "Anagram Check", "goal": "Determine if two strings S1 and S2 contain exact same characters.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read S1, S2", "✅ Step 3: Compare lengths 👉 IF length(S1) != length(S2) THEN Result = False, STOP", "✅ Step 4: Sort S1 characters alphabetically", "✅ Step 5: Sort S2 characters alphabetically", "✅ Step 6: Compare sorted strings 👉 IF Sorted(S1) == Sorted(S2)", "✅ Step 7: Assign Result 👉 Result = True, ELSE Result = False", "✅ Step 8: Display Result Stop"]},
        {"id": 4, "title": "GCD (Euclidean)", "goal": "Find the Greatest Common Divisor of two numbers A and B.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read two numbers 👉 A, B", "✅ Step 3: Repeat until B becomes 0", "✅ Step 4: Store B 👉 temp = B", "✅ Step 5: Update B 👉 B = A % B", "✅ Step 6: Update A 👉 A = temp", "✅ Step 7: Final Result 👉 GCD = A", "✅ Step 8: Display GCD Stop"]},
        {"id": 5, "title": "Armstrong Number", "goal": "Check if sum of digits raised to power of digit-count equals the number.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read N, store as original", "✅ Step 3: Count total digits 👉 P", "✅ Step 4: Initialize sum = 0", "✅ Step 5: Loop while N > 0", "✅ Step 6: Power of digit 👉 d = N % 10, 👉 sum = sum + (d ^ P)", "✅ Step 7: Reduce N 👉 N = N / 10", "✅ Step 8: Compare 👉 IF sum == original THEN Result = True", "✅ Step 9: Display Result Stop"]},
        {"id": 6, "title": "String Palindrome", "goal": "Check if a string reads the same backward as forward.", "logic": ["✅ Step 1: Start", "✅ Step 2: Set pointers 👉 i = 0, 👉 j = Length-1", "✅ Step 3: Loop while i < j", "✅ Step 4: Compare chars 👉 IF S[i] != S[j] THEN Result = False, STOP", "✅ Step 5: Shift pointers 👉 i++, j--", "✅ Step 6: Loop ends 👉 Result = True", "✅ Step 7: Display Result Stop"]},
        {"id": 8, "title": "Remove Duplicates", "goal": "Create a collection of unique elements from a given array.", "logic": ["✅ Step 1: Start", "✅ Step 2: Read Array", "✅ Step 3: Initialize empty Result list and 'Seen' tracker", "✅ Step 4: Loop through each element X in Array", "✅ Step 5: Check if seen 👉 IF X is NOT in Seen THEN", "✅ Step 6: Add unique 👉 ADD X to Result list, 👉 ADD X to Seen tracker", "✅ Step 7: Return final Result Stop"]},
        {"id": 9, "title": "Second Largest", "goal": "Identify the second highest value in an unsorted array.", "logic": ["✅ Step 1: Start", "✅ Step 2: Initialize 👉 Max1 = -Infinity, 👉 Max2 = -Infinity", "✅ Step 3: Loop through each number X", "✅ Step 4: New first max? 👉 IF X > Max1 THEN", "✅ Step 5: Update both 👉 Max2 = Max1, 👉 Max1 = X", "✅ Step 6: New second max? 👉 ELSE IF X > Max2 AND X != Max1 THEN", "✅ Step 7: Update second 👉 Max2 = X", "✅ Step 8: Display Max2 Stop"]}
    ],
    "advanced": [
        {"id": 1, "title": "Quick Sort", "goal": "Efficient sorting using pivot picking and recursive partitioning.", "logic": ["✅ Step 1: Start", "✅ Step 2: Pick a Pivot element (e.g., the last element)", "✅ Step 3: Partition around pivot 👉 Elements < Pivot move to Left", "✅ Step 4: Partition around pivot 👉 Elements > Pivot move to Right", "✅ Step 5: Place Pivot in correct position", "✅ Step 6: First Recursion 👉 Apply QuickSort to Left partition", "✅ Step 7: Second Recursion 👉 Apply QuickSort to Right partition", "✅ Step 8: Stop"]},
        {"id": 3, "title": "Reverse Linked List", "goal": "Invert the direction of all pointers in a singly linked list.", "logic": ["✅ Step 1: Start", "✅ Step 2: Initialize pointers 👉 Prev = NULL, 👉 Curr = HEAD", "✅ Step 3: While Curr node is not NULL", "✅ Step 4: Save next node 👉 NextNode = Curr.Next", "✅ Step 5: Reverse pointer 👉 Curr.Next = Prev", "✅ Step 6: Shift forward 👉 Prev = Curr, 👉 Curr = NextNode", "✅ Step 7: New head found 👉 NewHead = Prev", "✅ Step 8: Display NewHead Stop"]},
        {"id": 6, "title": "Dijkstra's Algorithm", "goal": "Find the shortest path to all nodes in a weighted graph from a source.", "logic": ["✅ Step 1: Start", "✅ Step 2: Initialize distances 👉 dist[source] = 0, ALL others = Infinity", "✅ Step 3: Mark all nodes as Unvisited", "✅ Step 4: While Unvisited nodes exist", "✅ Step 5: Pivot node 👉 Pick node U with smallest dist in Unvisited", "✅ Step 6: Update neighbors 👉 Loop each neighbor V of U", "✅ Step 7: Relaxation 👉 IF dist[U] + edge(U, V) < dist[V] THEN", "✅ Step 8: Update path 👉 dist[V] = dist[U] + edge(U, V)", "✅ Step 9: Mark U as Visited Stop"]},
        {"id": 7, "title": "DFS Traversal", "goal": "Traverse graph by visiting as deep as possible before backtracking.", "logic": ["✅ Step 1: Start", "✅ Step 2: Pick starting node U", "✅ Step 3: Mark node U as Visited", "✅ Step 4: Print node U", "✅ Step 5: Explore neighbors 👉 For each neighbor V of U", "✅ Step 6: Recurse 👉 IF V is NOT Visited THEN Call DFS(V)", "✅ Step 7: All neighbors done 👉 Backtrack to previous node Stop"]},
        {"id": 8, "title": "BFS Traversal", "goal": "Traverse graph level by level from a source node using a queue.", "logic": ["✅ Step 1: Start", "✅ Step 2: Initialize Queue and Visited set", "✅ Step 3: Enqueue Source and Mark as Visited", "✅ Step 4: While Queue is not empty", "✅ Step 5: Pop node 👉 Curr = Dequeue()", "✅ Step 6: Print Curr", "✅ Step 7: Check neighbors 👉 For each neighbor V of Curr", "✅ Step 8: Update queue 👉 IF V is NOT Visited THEN Enqueue V and mark Visited", "✅ Step 9: Stop"]},
        {"id": 10, "title": "N-Queens Logic", "goal": "Place N queens on a board such that no two queens attack each other.", "logic": ["✅ Step 1: Start", "✅ Step 2: Initialize Board with size N", "✅ Step 3: Begin recursion at Row R = 0", "✅ Step 4: Loop columns C from 0 to N-1", "✅ Step 5: Check safety 👉 IF Queen is SAFE at (R, C)", "✅ Step 6: Place Queen 👉 Board[R] = C", "✅ Step 7: Next Queen 👉 IF Solve(R + 1) is TRUE then DONE", "✅ Step 8: Backtrack 👉 IF not solved, REMOVE Queen and try next C", "✅ Step 9: Stop"]}
    ]
}

@app.route("/logic-builders", methods=["GET"])
def get_logic_builders():
    level = request.args.get("level")
    if level:
        return jsonify(logic_builders_data.get(level.lower(), []))
    return jsonify(logic_builders_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)