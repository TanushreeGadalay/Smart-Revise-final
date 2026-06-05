import re
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["smartrevise"]
dataset = db["python_library"]


def count_bullet_points(text):
    return sum(
        1
        for line in text.splitlines()
        if line.strip().startswith(('-', '*')) or re.match(r'^\s*\d+\.', line)
    )


def build_additional_bullets(language, topic, missing):
    normalized_topic = topic.strip().rstrip("?")
    base = normalized_topic.title()
    points = [
        f"- {base} is a fundamental concept every {language} learner should understand.",
        f"- It is commonly used in real-world {language} applications.",
        f"- Knowing {normalized_topic} helps you write cleaner and more reliable code.",
        f"- You should practice {normalized_topic} with small examples first.",
        f"- Understanding {normalized_topic} makes debugging easier.",
        f"- This topic often appears in interviews and exams.",
        f"- Pay attention to common pitfalls when working with {normalized_topic}.",
        f"- Use {normalized_topic} together with related concepts to build larger programs.",
        f"- Always test your {language} code for edge cases when using {normalized_topic}.",
        f"- Try different examples to see how {normalized_topic} behaves in {language}.",
        f"- Learn one or two best practices for {normalized_topic} in {language}.",
        f"- Combine {normalized_topic} with other programming ideas for better results."
    ]
    return "\n".join(points[:missing])


def ensure_minimum_bullets(notes, language, topic, minimum=10):
    count = count_bullet_points(notes)
    if count >= minimum:
        return notes

    missing = minimum - count
    additional = build_additional_bullets(language, topic, missing)
    if "Key points:" in notes:
        return f"{notes}\n{additional}"
    return f"{notes}\n\nAdditional key points:\n{additional}"


def generate_content(language, topic):
    result = dataset.find_one({
        "content": {"$regex": topic, "$options": "i"}
    })

    if result and result.get("content"):
        notes = result["content"]
        notes = ensure_minimum_bullets(notes, language, topic)
        mcqs = [
            f"What is {topic} in {language}?",
            f"Explain {topic} with example."
        ]
        practice_questions = [
            f"Write a program related to {topic}",
            f"Explain real use of {topic}"
        ]
    else:
        notes, mcqs, practice_questions = generate_fallback(language, topic)

    return {
        "language": language,
        "topic": topic,
        "notes": notes,
        "mcqs": mcqs,
        "practice_questions": practice_questions
    }


def generate_fallback(language, topic):
    normalized_topic = topic.strip().rstrip("?")
    lookup = normalized_topic.lower()
    example = ""
    description = ""

    if "loop" in lookup:
        description = (
            f"A loop lets you repeat a block of code until a condition is met. "
            f"In {language}, loops are essential for processing repeated tasks."
        )
    elif "function" in lookup or "method" in lookup:
        description = (
            f"A function is a reusable block of code that performs a specific task. "
            f"In {language}, functions help you organize logic and avoid duplication."
        )
    elif "array" in lookup or "list" in lookup:
        description = (
            f"Arrays (or lists) store multiple values in a single variable. "
            f"In {language}, they are used to group related data together."
        )
    elif "pointer" in lookup:
        description = (
            f"Pointers are variables that hold memory addresses. "
            f"They are commonly used in low-level {language} code to access memory directly."
        )
    elif "class" in lookup or "object" in lookup:
        description = (
            f"Classes and objects are central to object-oriented programming. "
            f"In {language}, they let you model real-world entities and reuse behavior."
        )
    else:
        description = (
            f"{normalized_topic.title()} is an important concept in {language}. "
            f"Understanding it will help you write clearer and more effective code."
        )

    if language == "Python":
        if "loop" in lookup:
            example = "for i in range(5):\n    print(i)"
        elif "function" in lookup or "method" in lookup:
            example = "def add(a, b):\n    return a + b"
        elif "array" in lookup or "list" in lookup:
            example = "arr = [1, 2, 3]\nprint(arr[0])"
        elif "pointer" in lookup:
            example = "# Python does not have explicit pointers like C, but references behave similarly."
        elif "class" in lookup or "object" in lookup:
            example = "class Person:\n    def __init__(self, name):\n        self.name = name"
        else:
            example = "# Example code depends on the specific topic."
    elif language == "JavaScript":
        if "loop" in lookup:
            example = "for (let i = 0; i < 5; i++) {\n    console.log(i);\n}"
        elif "function" in lookup or "method" in lookup:
            example = "function add(a, b) {\n    return a + b;\n}"
        elif "array" in lookup or "list" in lookup:
            example = "const arr = [1, 2, 3];\nconsole.log(arr[0]);"
        elif "pointer" in lookup:
            example = "// JavaScript does not use pointers directly."
        elif "class" in lookup or "object" in lookup:
            example = "class Person {\n    constructor(name) {\n        this.name = name;\n    }\n}"
        else:
            example = "// Example code depends on the specific topic."
    elif language == "Java":
        if "loop" in lookup:
            example = "for (int i = 0; i < 5; i++) {\n    System.out.println(i);\n}"
        elif "function" in lookup or "method" in lookup:
            example = "int add(int a, int b) {\n    return a + b;\n}"
        elif "array" in lookup or "list" in lookup:
            example = "int[] arr = {1, 2, 3};\nSystem.out.println(arr[0]);"
        elif "pointer" in lookup:
            example = "// Java does not have pointers in the same way as C/C++."
        elif "class" in lookup or "object" in lookup:
            example = "public class Person {\n    private String name;\n    public Person(String name) {\n        this.name = name;\n    }\n}"
        else:
            example = "// Example code depends on the specific topic."
    elif language == "C":
        if "loop" in lookup:
            example = "for (int i = 0; i < 5; i++) {\n    printf(\"%d\\n\", i);\n}"
        elif "function" in lookup or "method" in lookup:
            example = "int add(int a, int b) {\n    return a + b;\n}"
        elif "array" in lookup or "list" in lookup:
            example = "int arr[3] = {1, 2, 3};\nprintf(\"%d\", arr[0]);"
        elif "pointer" in lookup:
            example = "int *ptr = &value;"
        elif "class" in lookup or "object" in lookup:
            example = "// C does not have classes, but structs can hold related data."
        else:
            example = "// Example code depends on the specific topic."
    elif language == "C++":
        if "loop" in lookup:
            example = "for (int i = 0; i < 5; i++) {\n    std::cout << i << std::endl;\n}"
        elif "function" in lookup or "method" in lookup:
            example = "int add(int a, int b) {\n    return a + b;\n}"
        elif "array" in lookup or "list" in lookup:
            example = "std::vector<int> arr = {1, 2, 3};\nstd::cout << arr[0];"
        elif "pointer" in lookup:
            example = "int *ptr = &value;"
        elif "class" in lookup or "object" in lookup:
            example = "class Person {\n    std::string name;\n    Person(std::string name) : name(name) {}\n};"
        else:
            example = "// Example code depends on the specific topic."
    else:
        example = "// Example code depends on the specific topic and language."

    is_plural = normalized_topic.lower().endswith("s")
    verb = "are" if is_plural else "is"

    bullet_points = [
        f"{normalized_topic.title()} {verb} a core concept in {language}.",
        f"It helps you solve common programming tasks more efficiently.",
        f"Understanding {normalized_topic} improves your ability to read and write {language} code.",
        f"Many exercises and interview questions use {normalized_topic} as the main topic.",
        f"Knowing how to use {normalized_topic} makes it easier to learn advanced topics later.",
        f"You can apply {normalized_topic} in real-world examples and small projects.",
        f"Practice with examples to build confidence in {language}.",
        f"Be aware of common mistakes when using {normalized_topic}.",
        f"Review related concepts to deepen your understanding of {normalized_topic}.",
        f"Always test your {language} code to ensure {normalized_topic} is working correctly."
    ]

    notes = (
        f"{normalized_topic.title()} in {language}\n\n"
        f"{description}\n\n"
        "Key points:\n"
        + "\n".join(f"{idx + 1}. {point}" for idx, point in enumerate(bullet_points))
        + "\n\n"
        f"Example:\n{example}\n\n"
        "Tips:\n"
        "- Break the problem into smaller steps.\n"
        "- Use comments to explain each line.\n"
        "- Test with sample values.\n"
    )

    mcqs = [
        f"What is {normalized_topic} in {language}?",
        f"How do you use {normalized_topic} in {language}?",
        f"Why is {normalized_topic} important in {language}?"
    ]

    practice_questions = [
        f"Write a short {language} example using {normalized_topic}.",
        f"Explain one real-world application of {normalized_topic} in {language}."
    ]

    return notes, mcqs, practice_questions
