# Job-Scraper-with-AI-Insights

This repository contains all of the components of the Job Scraper with AI Insights project. Here are the contents of this README:

1. Chrome Extension
2. Streamlit Dashboard
3. PostgreSQL Database
4. Flask API Backend

## 1. Chrome Extension

The Chrome Extension was created using vanilla HTML, CSS, and JS, alongside additional functions derived from the Chrome Extension `Manifest.json` permissions. The Chrome Extension has been configured to communicate with the Flask back-end via API calls, ensuring scalability and enabling the GenAI functionality.
The Chrome Extension has also been configured to launch the Streamlit dashboard and record the user's obfuscated user ID. 
You can find the Chrome Extension in this link (insert link here), or clone the path `/job-scraper-extension` and configure it using your own OAuth2 credentials from the Google Cloud Platform.

![Chrome Extension Screenshot](https://github.com/brandon-wee/Job-Scraper-with-AI-Insights/blob/main/images/chrome_extension.png)

### Usage:
- To use the Chrome Extension, you must first enable sync in `chrome://settings`
- Navigate to a job listing you would like to save, and press **"Extract Job"**
- Press **"View Saved Jobs"** to launch the Streamlit dashboard with your credentials.

### Technology Stack:
- HTML, CSS, JavaScript, Chrome Extension Manifest.json

---

## 2. Streamlit Dashboard

The Streamlit dashboard was created using Python and communicates with the Flask API and PostgreSQL. The Streamlit Dashboard enables users to browse their saved job listings and gain AI insights in the form of:

- **Resume and Job Skill Matching and Similarity Score**
  - `Gemini-2.0-Flash` was used to match the skills.
  - A linear combination of BERT, TF-IDF, and the percentage of compatible skills was used to determine the Similarity Score.

- **Cover Letter Generation**
  - `Gemini-2.0-Flash`, along with job listing details stored in PostgreSQL, was used to draft a Cover Letter.
  - Cover letters are downloadable as DOCX files for user editing.

- **Occupational Skills Recommendation**
  - Using `Gemini-2.0-Flash`, along with a custom FAISS pipeline, the system recommends skills based on a desired occupation and the user's resume.
  - Implemented **Retrieval Augmented Generation (RAG)** using FAISS vector store and OpenAI embeddings (`text-embedding-3-large`).

The Streamlit Dashboard also includes a **Geospatial Visualizer**, displaying job listing locations with a heatmap option for analyzing office hotspots.

You can launch your dashboard from the extension, or clone the path `/job-scraper-dashboard` and configure it using your own Supabase credentials, hash secrets, and Flask API calls.

![Home Page Screenshot](https://github.com/brandon-wee/Job-Scraper-with-AI-Insights/blob/main/images/dashboard_1.png)
![View Listings Page Screenshot](https://github.com/brandon-wee/Job-Scraper-with-AI-Insights/blob/main/images/dashboard_2.png)
![Resume Analysis Page Screenshot](https://github.com/brandon-wee/Job-Scraper-with-AI-Insights/blob/main/images/dashboard_3.png)
![Geospatial Visualization Page Screenshot](https://github.com/brandon-wee/Job-Scraper-with-AI-Insights/blob/main/images/dashboard_4.png)

### Usage:
- Launch the dashboard by pressing **"View Saved Jobs"** in the Chrome Extension.
- Change your username (optional) on the Home Page.
- View your job listings on the **View Listings Page**.
- Gain AI insights on the **Resume Analysis Page**.
- Visualize office locations on the **Geospatial Visualization Page**.

### Technology Stack:
- Python, Streamlit, Supabase, PostgreSQL, Requests, Streamlit-Options-Menu, Pandas, Leafmap

---

## 3. PostgreSQL Database

The PostgreSQL database stores details related to:
  - Users
  - Companies
  - Jobs
  - Relationships between entities

The PostgreSQL database is deployed on Supabase and designed as a **normalized relational database up to the third normal form (3NF)** to minimize data redundancy while ensuring scalability and performance.

You do not have access to the deployed database, but you can recreate it using the following **ER diagram**.

![Database Schema Screenshot](https://github.com/brandon-wee/Job-Scraper-with-AI-Insights/blob/main/images/database_schema.png)

### Technology Stack:
- SQL, PostgreSQL, Supabase

---

## 4. Flask API Backend

The Flask API Backend, built with Python, serves as the communication bridge between the front-end components (Chrome Extension and Streamlit Dashboard) and the PostgreSQL database. The API is equipped with **GenAI-powered functionalities** to provide AI-driven job insights.

### Features:
- Handles job extraction requests from the Chrome Extension
- Facilitates job listing retrieval for the Streamlit Dashboard
- Processes AI-powered resume and job skill matching
- Generates cover letters using Gemini-2.0-Flash and stored job listing details
- Implements Retrieval Augmented Generation (RAG) for skill recommendations using FAISS and OpenAI embeddings
- Ensures secure authentication and API request handling
- Uses NLTK and scikit-learn to preprocess for TF-IDF calculations

### Technology Stack:
- Python, Flask, PostgreSQL, Gemini-2.0-Flash and Flash-Lite, OpenAI Embeddings, Hugging Face Interactive API, NLTK, scikit-learn, FAISS, TF-IDF

---

## Manual Installation & Setup

### Prerequisites:
1. **Chrome Extension**: Load the unpacked extension from the `/job-scraper-extension` folder.
2. **Streamlit Dashboard**:
   - Install dependencies: `pip install -r requirements.txt`
   - Run Streamlit: `streamlit run app.py`
3. **Flask API**:
   - Install dependencies: `pip install -r requirements.txt`
   - Run Flask server: `gunicorn app:app` or `flask run`
4. **PostgreSQL Database**:
   - Set up a PostgreSQL instance via Supabase or another hosting service.
   - Apply the provided ER schema.

---

## Contact
For any inquiries, reach out via email: [bwee.dev01@gmail.com] or submit an issue on this repository.

Happy job hunting! 🚀