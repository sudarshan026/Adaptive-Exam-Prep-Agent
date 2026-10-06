from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_syllabus_pdf(filename, title, content_lines):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, title)

    # Content
    c.setFont("Helvetica", 12)
    y_position = height - 100

    for line in content_lines:
        if line.isupper() and len(line) < 50:
            c.setFont("Helvetica-Bold", 14)
            y_position -= 10
            c.drawString(72, y_position, line)
            c.setFont("Helvetica", 12)
        else:
            c.drawString(72, y_position, line)
        
        y_position -= 20
        
        if y_position < 72:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 72

    c.save()

# Example 1: Data Structures and Algorithms
dsa_content = [
    "DATA STRUCTURES AND ALGORITHMS",
    "Module 1. Introduction to Algorithms",
    "Module 2. Arrays and Linked Lists",
    "Module 3. Stacks and Queues",
    "Module 4. Trees and Graphs",
    "Module 5. Sorting and Searching",
    "",
    "DATABASE MANAGEMENT SYSTEMS",
    "Module 1. Relational Data Model",
    "Module 2. SQL and Normalization",
    "Module 3. Transaction Management",
    "Module 4. Concurrency Control",
    "",
    "OPERATING SYSTEMS",
    "Module 1. Process Management",
    "Module 2. Memory Management",
    "Module 3. File Systems",
    "Module 4. Deadlocks"
]
create_syllabus_pdf("demo_cs_syllabus.pdf", "Computer Science Semester 4 Syllabus", dsa_content)

# Example 2: Machine Learning
ml_content = [
    "MACHINE LEARNING FOUNDATIONS",
    "Module 1. Linear Algebra and Calculus",
    "Module 2. Probability and Statistics",
    "Module 3. Python for Data Science",
    "",
    "SUPERVISED LEARNING",
    "Module 1. Linear Regression",
    "Module 2. Logistic Regression",
    "Module 3. Decision Trees and Random Forests",
    "Module 4. Support Vector Machines",
    "",
    "UNSUPERVISED LEARNING",
    "Module 1. K-Means Clustering",
    "Module 2. Principal Component Analysis",
    "Module 3. Neural Networks Basics"
]
create_syllabus_pdf("demo_ml_syllabus.pdf", "Introduction to Machine Learning Syllabus", ml_content)

print("Demo syllabus PDFs created successfully.")
