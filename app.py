from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, render_template, request
from database import save_resume_analysis
import os
import pdfplumber
import re
import sqlite3

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def extract_text_from_pdf(pdf_path):
    text = ""
    

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text
skills_db = [
    "python",
    "java",
    "c",
    "html",
    "css",
    "javascript",
    "flask",
    "mysql",
    "sqlite",
    "machine learning",
    "data structures",
    "dbms",
    "operating systems",
    "computer networks",
    "git",
    "github",
    "docker",
    "aws",
    "kubernetes",
    "react"
]
def extract_email(text):

    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

    match = re.search(pattern, text)

    if match:
        return match.group()

    return "Not Found"

def extract_phone(text):

    pattern = r"\+?\d[\d\s-]{8,15}"

    match = re.search(pattern, text)

    if match:
        return match.group()

    return "Not Found"

def extract_name(text):

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if line:
            return line

    return "Not Found"

def extract_skills(text):

    text = text.lower()

    found_skills = []

    for skill in skills_db:

        if skill.lower() in text:
            found_skills.append(skill.title())

    return found_skills


def calculate_resume_score(text):

    text = text.lower()

    score = 0

    suggestions = []

    # Education
    if "education" in text:
        score += 20
    else:
        suggestions.append("Add Education Section")

    # Skills
    if "skills" in text:
        score += 20
    else:
        suggestions.append("Add Skills Section")

    # Projects
    if "project" in text:
        score += 20
    else:
        suggestions.append("Add Projects Section")

    # Certifications
    if "certification" in text or "certifications" in text:
        score += 20
    else:
        suggestions.append("Add Certifications Section")

    # Internship / Experience
    if "internship" in text or "experience" in text:
        score += 20
    else:
        suggestions.append("Add Internship or Experience Section")

    return score, suggestions


def calculate_job_match(resume_text, job_description):
    
    job_description = request.form["job_description"]

    documents = [resume_text, job_description]

    tfidf = TfidfVectorizer()

    tfidf_matrix = tfidf.fit_transform(documents)

    similarity = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:2]
    )

    match_score = round(similarity[0][0] * 100,2)

    return match_score

def get_missing_skills(resume_text, job_description):

    resume_text = resume_text.lower()
    job_description = job_description.lower()

    missing_skills = []

    for skill in skills_db:

        if skill in job_description and skill not in resume_text:
            missing_skills.append(skill.title())
        
    print("Job Description:", job_description)
    print("Missing Skills:", missing_skills)
      
    return missing_skills

def generate_recommendations(
        resume_text,
        score,
        missing_skills):

    recommendations = []

    resume_text = resume_text.lower()

    # Resume Score Based Suggestions

    if score < 60:
        recommendations.append(
            "Your resume needs significant improvement. Add more technical content."
        )

    elif score < 80:
        recommendations.append(
            "Improve your resume by adding projects and certifications."
        )

    # Internship Check

    if "internship" not in resume_text and "experience" not in resume_text:
        recommendations.append(
            "Add Internship or Work Experience section."
        )

    # GitHub Check

    if "github" not in resume_text:
        recommendations.append(
            "Add GitHub profile link."
        )

    # LinkedIn Check

    if "linkedin" not in resume_text:
        recommendations.append(
            "Add LinkedIn profile link."
        )

    # Project Check

    if "project" not in resume_text:
        recommendations.append(
            "Include academic or personal projects."
        )

    # Missing Skills Suggestions

    for skill in missing_skills:

        recommendations.append(
            f"Consider learning {skill} to better match the job requirements."
        )

    return recommendations

def skill_gap_analysis(
        resume_skills,
        missing_skills):

    total_required = len(resume_skills) + len(missing_skills)

    if total_required == 0:
        return 0

    gap_percentage = (
        len(missing_skills) /
        total_required
    ) * 100

    return round(gap_percentage, 2)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "resume" not in request.files:
        return "No file selected"
    
    job_description = request.form.get("job_description", "")

    file = request.files["resume"]

    if file.filename == "":
        return "Please select a file"

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    resume_text = extract_text_from_pdf(filepath)

    name = extract_name(resume_text)

    email = extract_email(resume_text)

    phone = extract_phone(resume_text)

    skills = extract_skills(resume_text)
    
    score, suggestions = calculate_resume_score(resume_text)

    match_score = calculate_job_match(resume_text,job_description)
    
    missing_skills = get_missing_skills(resume_text,job_description)
    
    ai_recommendations = generate_recommendations(resume_text, score, missing_skills)
    
    skill_gap = skill_gap_analysis(skills, missing_skills)
    
    save_resume_analysis(name, email, phone, score, match_score)
    
    return render_template(
        "success.html",
        filename=file.filename,
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        score=score,
        suggestions=suggestions,
        missing_skills=missing_skills,
        ai_recommendations=ai_recommendations,
        skill_gap=skill_gap,
        match_score=match_score,
        resume_text=resume_text
)

@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("resumes.db")

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM resume_analysis
    ORDER BY id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        data=data
    )

if __name__ == "__main__":
    app.run(debug=True)