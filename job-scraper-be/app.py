from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models import JobDetailsExtractLLM, ResumeSkillsSimilarity, change_username,CoverLetterLLM
from skills_recommendation import get_skills_recommendation

app = Flask(__name__)
CORS(app)

job_extrator = JobDetailsExtractLLM()
similarity_checker = ResumeSkillsSimilarity()
cover_letter_generator = CoverLetterLLM()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save', methods=['POST', 'GET'])
def save():
    try:
        contents = request.get_json()
        message = contents['message']
        user_id = contents['userId']

        result = job_extrator.save_job_details(message, user_id)
        return jsonify(result)
    
    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/get_similarity', methods=['POST', 'GET'])
def get_similarity():
    try:
        contents = request.get_json()
        resume_contents = contents['resume_contents']
        user_id = contents['user_id']

        result = similarity_checker.get_similarity(resume_contents, user_id)
        return jsonify({"result": result})
    
    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "error": str(e), "similarity": 0, "resume_skills": ""})

@app.route('/add_user', methods=['POST', 'GET'])
def add_user():
    try:
        contents = request.get_json()
        user_id = contents['user_id']

        result = job_extrator.add_user(user_id)
        return jsonify(result)
    
    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/change_username', methods=['POST', 'GET'])
def change_username():
    try:
        contents = request.get_json()
        user_id = contents['user_id']
        new_username = contents['new_username']

        result = change_username(user_id, new_username)
        return jsonify(result)
    
    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/generate_cover_letter', methods=['POST', 'GET'])
def generate_cover_letter():
    try:
        contents = request.get_json()
        job_id = contents['job_id']
        resume_contents = contents['resume_contents']

        result = cover_letter_generator.generate_cover_letter(job_id, resume_contents)
        return jsonify({"cover_letter": result})
    
    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_skills_recommendation', methods=['POST', 'GET'])
def get_skills_recommendation_route():
    try:
        contents = request.get_json()
        job_occupation = contents['job_occupation']
        resume_contents = contents['resume_contents']
        
        result, context = get_skills_recommendation(job_occupation, resume_contents)
        return jsonify({"skills": result, "context": context})
    
    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "error": str(e)})