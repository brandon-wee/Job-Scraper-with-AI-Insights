import streamlit as st
from supabase import create_client, Client
import pandas as pd
import os
import requests  # For API call
from dotenv import load_dotenv
import hmac, hashlib
from streamlit_option_menu import option_menu
import base64, json
import time, io
from docx import Document
import leafmap.foliumap as leafmap

# Load environment variables
load_dotenv()

# Supabase Credentials (Replace with your Supabase details)
url: str  = os.environ.get("SUPABASE_URL")
key: str  = os.environ.get("SUPABASE_KEY")

# Initialize Supabase Client
supabase: Client = create_client(url, key)

# Function to fetch job data
def fetch_jobs(hashed_id):
    response = supabase.table("JOB").select("job_title, COMPANY!inner(company_name), job_skills_required, job_experience_level, job_url, job_id, USER_JOB!inner(user_id)").eq("USER_JOB.user_id", hashed_id).execute()
    if response.data:
        df = pd.DataFrame(response.data)
        df.drop(columns=["USER_JOB"], inplace=True)
        df["company_name"] = df["COMPANY"].apply(lambda x: x["company_name"])
        df.drop(columns=["COMPANY"], inplace=True)
        return df  # Convert to DataFrame
    return pd.DataFrame(columns=["job_title", "company_name", "job_skills_required", "job_experience_level", "job_url", "job_id"])  # Empty Table

# Function to delete a job by ID
def delete_job(job_id):
    response = supabase.table("USER_JOB").delete().eq("job_id", job_id).eq("user_id", hashed_id).execute()
    return response

# Function to hash credentials
def hash_id(user_id):
    return hmac.new(os.getenv("HASH_SECRET").encode(), user_id.encode(), hashlib.sha256).hexdigest()

def encode_pdf(pdf_bytes):
    """Encodes PDF bytes into a JSON-serializable Base64 string."""
    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")  # Convert bytes → Base64 → String
    return base64_pdf  # Store in a JSON object

# Function to call API for resume analysis
def process_resume(resume_text, user_id):
    API_URL = "https://API_LINK/get_similarity"  # Replace with actual API URL
    response = requests.post(API_URL, json={"resume_contents": encode_pdf(resume_text), "user_id": user_id})
    
    if response.status_code == 200:
        return response.json()["result"]  # Assumes JSON response with similarity_score, compatible_skills, missing_skills

# Function to call API for cover letter generation
def generate_cover_letter(job_id, resume_bytes):
    API_URL = "https://API_LINK/generate_cover_letter"  # Replace with actual API URL
    response = requests.post(API_URL, json={"job_id": job_id, "resume_contents": encode_pdf(resume_bytes)})

    if response.status_code == 200:
        return response.json()["cover_letter"]

# Function to convert cover letter to DOCX
def convert_to_docx(cover_letter):
    docx_data = io.BytesIO()
    docx = Document()
    docx.add_paragraph(cover_letter)
    docx.save(docx_data)
    docx_data.seek(0)
    return docx_data

# Function to stream cover letter
def stream_text(text):
    for word in text.replace("\n", "\n\n").split(" "):
        yield word + " "
        time.sleep(0.02)

# Function to call API for skills recommendation
def recommend_skills(resume_bytes, occupation):
    API_URL = "https://API_LINK/get_skills_recommendation"  # Replace with your actual API URL
    response = requests.post(API_URL, json={
        "resume_contents": encode_pdf(resume_bytes),
        "job_occupation": occupation
    })
    if response.status_code == 200:
        return response.json().get("skills", ""), response.json().get("context", [])
    else:
        st.error("Failed to retrieve skills recommendations.")
        return []

# Function to fetch job locations
def fetch_job_locations(hashed_id):
    response = supabase.table("JOB").select("COMPANY!inner(company_id, company_name, company_lat, company_long, company_address), USER_JOB!inner(user_id)").eq("USER_JOB.user_id", hashed_id).execute()
    job_listings = fetch_jobs(hashed_id)
    if response.data:
        df = pd.DataFrame(response.data)
        df.drop(columns=["USER_JOB"], inplace=True)
        df["company_id"] = df["COMPANY"].apply(lambda x: x["company_id"])
        df["company_name"] = df["COMPANY"].apply(lambda x: x["company_name"])
        df["company_long"] = df["COMPANY"].apply(lambda x: x["company_long"])
        df["company_lat"] = df["COMPANY"].apply(lambda x: x["company_lat"])
        df["company_address"] = df["COMPANY"].apply(lambda x: x["company_address"])
        df.drop(columns=["COMPANY"], inplace=True)
        
        # Calculate the count of jobs from each company
        job_counts = job_listings["company_name"].value_counts().to_dict()
        df["count"] = df["company_name"].map(job_counts).fillna(0).astype(int)
        
        # Ensure each company_id is only added once
        df = df.drop_duplicates(subset=["company_id"])
        
        return df  # Convert to DataFrame
    return pd.DataFrame(columns=["company_id", "company_name", "company_long", "company_lat", "company_address", "count"])  # Empty Table

# Function to download CSV file
def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href

# Streamlit App Configuration
st.set_page_config(page_title="Job Listings Dashboard", page_icon="📌", layout="wide")

query_params = st.query_params
user_id = query_params.get("user_id")

# Sidebar Navigation
# Sidebar Design
# Sidebar Design
# Remove radio bullets by using selectbox
with st.sidebar:
    page = option_menu(
        menu_title="🔗 Navigation Menu",
        options=["Home", "View Listings", "Resume Analysis", "Geospatial Visualization"],
        icons=["house", "list-task", "file-earmark-text", "globe2"],
        default_index=0,
        menu_icon="🔗"
    )

st.sidebar.markdown("---")  # Horizontal separator
st.sidebar.write("💡 **New:** You can now access the **Resume Analysis** tab to gain **AI insights** on where you can improve!")



# ---------------- JOB LISTINGS PAGE ----------------
st.session_state["user_id"] = user_id
hashed_id = hash_id(user_id)
if not user_id:
    st.title("🔒 Job Listings Dashboard")
    st.write("Please launch this dashboard from the Chrome extension to view your job listings.")
    st.write("If you have already done so, please refresh the page.")

# ---------------- HOME PAGE ----------------
elif page == "Home":
    # 🔥 Stylish Header
    st.markdown(
        """
        <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .title {
            font-size: 40px;
            font-weight: bold;
            text-align: center;
            color: #f8f9fa;
            animation: fadeIn 1s ease-in-out;
        }
        .subtitle {
            font-size: 22px;
            text-align: center;
            color: #adb5bd;
            margin-bottom: 20px;
            font-style: italic;
            animation: fadeIn 1.2s ease-in-out;
        }
        .welcome {
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            color: #ffffff;
            animation: fadeIn 1.4s ease-in-out;
        }
        </style>
        <h1 class="title">Job Scraper and AI Insights Dashboard</h1>
        <h4 class="subtitle">Where all your career dreams become a reality!*</h4>
        """,
        unsafe_allow_html=True
    )

    # Fetch Username
    if user_id:
        hashed_id = hash_id(user_id)
        user_data = supabase.table("USER").select("user_name").eq("user_id", hashed_id).execute()
        if user_data.data:
            username = user_data.data[0]["user_name"]
        else:
            username = f"User {user_id}"
    else:
        username = "Guest"

    # 🏆 Animated Welcome Message
    st.markdown(f"<h3 class='welcome'>Welcome, {username}! 🎉</h3>", unsafe_allow_html=True)
    st.write("🔍 This dashboard allows you to **track job listings, analyze your resume, and gain AI-powered insights!**")
    st.write("📊 Use the sidebar to **navigate between different sections and unlock valuable career insights.**")

    # 💡 Feature Highlights Section
    st.markdown("---")
    st.subheader("✨ Why You'll Love This Dashboard")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("✅ **AI-Powered Resume Matching**")
        st.markdown("✅ **Find Missing Skills & Improve**")

    with col2:
        st.markdown("🌎 **Visualize Job Locations**")
        st.markdown("📊 **Organize and Keep Track of Your Job Listings**")

    with col3:
        st.markdown("⚡ **Lightning Fast Job Scraping**")
        st.markdown("📝 **Auto-Generate Cover Letters**")

    st.markdown("---")
    st.subheader("📩 Need Help or Want to Support Us?")
    st.write("📧 **For inquiries:** Reach out at [bwee.support@gmail.com](mailto:bwee.support@gmail.com)")
    st.write("☕ **Love this tool?** Buy me a coffee to keep this project alive!")
    
    st.markdown("---")
    st.subheader("Account Configuration")
    st.write("Update your account details below:")
    new_username = st.text_input("Enter your new username:")
    print(hashed_id, new_username)
    if st.button("Update Username"):
        print(hashed_id, new_username)
        if new_username:
            response = supabase.table("USER").update({"user_name": new_username}).eq("user_id", hashed_id).execute()
            print(response)
            if response:
                st.success("Username updated successfully!")
                st.rerun()


    st.markdown("---")
    st.caption("*May not apply to all users. Please consult your career advisor for more information.")

# ---------------- VIEW LISTINGS PAGE ----------------
elif page == "View Listings":
    st.title("Job Listings Dashboard")
    st.caption("View and manage your scraped job listings from LinkedIn!")

    st.markdown("---")

    col1, col2, col3 = st.columns([0.8, 1, 8])
    with col1:
        if st.button("🔄 Refresh Listings"):
            st.rerun()

    # Fetch jobs from Supabase
    job_data = fetch_jobs(hashed_id)

    # Rename columns for proper capitalization
    job_data.rename(columns={
        "job_title": "Position",
        "company_name": "Company",
        "job_skills_required": "Technical Requirements",
        "job_experience_level": "Experience",
        "job_url": "URL",
        "job_id": "Job ID"
    }, inplace=True)

    with col2:
        csv = job_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📂 Download Listings (CSV)",
            data=csv,
            file_name=f'{user_id}_job_listings.csv',
            mime='text/csv',
        )

    with col3:
        excel = job_data.to_excel("output.xlsx", index=False)
        with open("output.xlsx", "rb") as file:
            excel = file.read()
            st.download_button(
                label="📂 Download Listings (Excel)",
                data=excel,
                file_name=f'{user_id}_job_listings.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

    if not job_data.empty:
        # Add Headers
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns([2, 1, 5, 4, 1, 1.5])
        with header_col1:
            st.subheader("Position")
        with header_col2:
            st.subheader("Company")
        with header_col3:
            st.subheader("Technical Requirements")
        with header_col4:
            st.subheader("Experience")
        with header_col5:
            st.subheader("Job URL")
        with header_col6:
            st.subheader("Actions")

        st.markdown("---")
        # Display job listings
        for index, row in job_data.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 5, 4, 1, 1.5])

            with col1:
                st.write(f"**{row['Position']}**")

            with col2:
                st.write(row['Company'])

            with col3:
                st.write(row['Technical Requirements'])

            with col4:
                st.write(row['Experience'])

            with col5:
                job_url = row["URL"]
                st.markdown(f"[🔗 View Job]({job_url})", unsafe_allow_html=True)

            with col6:
                job_id = row["Job ID"]
                if st.button("❌", key=job_id):
                    delete_job(job_id)
                    st.warning(f"Deleted job: {row['Position']}")
                    st.rerun()
            st.markdown("---")
    else:
        st.info("No job listings available!")


# ---------------- RESUME ANALYSIS PAGE ----------------
elif page == "Resume Analysis":
    st.title("Resume Analysis")
    st.caption("Upload your resume to receive personalized AI insights and recommendations for enhancing your career prospects!")
    st.markdown("---")

    st.subheader("What Can You Do Here?")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("📊 Analyze the **similarity score** of your resume with job listings.")
    
    with col2:
        st.write("💡 Get **skills recommendations** based on your resume and desired occupation.")

    with col3:
        st.write("📝 Generate a **cover letter** tailored to a specific job listing.")

    st.markdown("---")
    # Upload Resume
    uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])

    if uploaded_file:
        st.success("✅ Resume uploaded successfully!")
        st.caption("Make sure your PDF contains text for accurate analysis. The AI will struggle with scanned images.")

        # analysis_type = st.selectbox("Choose an analysis type:", ["Job Resume Similarity Score", "Cover Letter Generation", "Skills Recommendation"])
        st.markdown("---")
        analysis_type = option_menu(
            menu_title=None,
            options=["Job Resume Similarity Score", "Skills Recommendation", "Cover Letter Generation"],
            default_index=0,
            icons=["bar-chart", "lightbulb", "file-earmark-text"],
            menu_icon="toggles",
            orientation="horizontal",
        )
        if analysis_type == "Job Resume Similarity Score":
            if st.button("Upload & Analyze Resume"):
                with st.spinner("Analyzing resume... This may take a few seconds."):
                    # Read resume contents
                    resume_contents = uploaded_file.read()

                    # Call API to process resume
                    result = process_resume(resume_contents, user_id)

                    if result:
                        # Convert API response into a DataFrame
                        analysis_data = pd.DataFrame(result)  

                        # Ensure correct column ordering & sorting by similarity score
                        analysis_data = analysis_data[["position", "company", "similarity_score", "compatible_skills", "missing_skills"]]
                        analysis_data = analysis_data.sort_values(by="similarity_score", ascending=False)

                        # Display Table Headers
                        st.write("Jobs sorted by highest similarity score:")

                        header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([1, 1, 2, 3, 3])
                        with header_col1:
                            st.subheader("Position")
                        with header_col2:
                            st.subheader("Company")
                        with header_col3:
                            tooltip = '''# How is this score calculated?
                
    The similarity score is calculated using:
    - BERT Similarity (Semantic meaning)
    - TF-IDF Similarity (Keyword matching)
    - Skill Compatibility Ratio

    A higher score means a better job fit.
    '''
                            st.subheader("Similarity Score", help=tooltip)
                        
                        with header_col4:
                            st.subheader("Compatible Skills")
                        with header_col5:
                            st.subheader("Missing Skills")

                        # Display each job listing in structured columns
                        for index, row in analysis_data.iterrows():
                            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 3, 3])

                            with col1:
                                st.write(f"**{row['position']}**")

                            with col2:
                                st.write(row['company'])

                            with col3:
                                similarity_score = f"{row['similarity_score']:.2%}"  # Convert to percentage
                                st.write(f"🟢 {similarity_score}")  # Add emoji for visual effect

                            with col4:
                                compatible_skills = row["compatible_skills"] if row["compatible_skills"] else "None"
                                st.write(compatible_skills)

                            with col5:
                                missing_skills = row["missing_skills"] if row["missing_skills"] else "None"
                                st.write(missing_skills)
                            
                            st.markdown("---")

                    else:
                        st.error("❌ Failed to process resume. Please try again.")

        elif analysis_type == "Cover Letter Generation":
            job_options = fetch_jobs(hashed_id)  # Fetch user's job listings
            job_choice = st.selectbox("Select a job listing:", job_options["job_id"] + " - " + job_options["job_title"] + " @ " + job_options["company_name"])

            if st.button("Generate Cover Letter"):
                with st.spinner("Generating cover letter..."):
                    job_id = job_choice.split(" - ")[0]
                    cover_letter = generate_cover_letter(job_id, uploaded_file.read())  # API Call

                    if cover_letter:
                        st.markdown("---")
                        st.subheader("**Generated Cover Letter:**")
                        st.write_stream(stream_text(cover_letter))
                        # Button to Download as DOCX
                        docx_data = convert_to_docx(cover_letter)
                        
                        st.download_button("Download Cover Letter (DOCX)", docx_data, f"{job_id}_cover_letter.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

                    else:
                        st.error("❌ Failed to generate cover letter. Try again.")

        elif analysis_type == "Skills Recommendation":
            occupation = st.text_input("Enter the occupation you're interested in:")

            if st.button("Discover"):
                if uploaded_file and occupation:
                    with st.spinner("Fetching skills recommendations..."):
                        resume_contents = uploaded_file.read()
                        recommended_skills, context = recommend_skills(resume_contents, occupation)

                        if recommended_skills:
                            st.subheader("Here are the skills recommended for you:")
                            st.write_stream(stream_text(recommended_skills))
                            st.subheader("References: " )
                            for c in context:
                                title = c["title"]
                                link = c["link"]
                                st.markdown(f"[{title}]({link})", unsafe_allow_html=True)

                        else:
                            st.info("No specific skills recommendations found.")
                else:
                    st.warning("Please upload your resume and specify an occupation.")

    st.markdown("---")
    st.caption("Insights are generated using Gemini-2.0-Flash. Errors may occur due to the limitations and probabilistic nature of GenAI models.")

elif page == "Geospatial Visualization":
    st.title("Geospatial Visualization")
    st.caption("Visualize the locations of companies of your job listings on an interactive map!")
    st.markdown("---")
    df = fetch_job_locations(hashed_id)
    filepath = "./job_locations.csv"
    df.to_csv(filepath, index=False, sep=",")
    center = [df["company_lat"].mean(), df["company_long"].mean()]
    visualization = option_menu(
            menu_title=None,
            options=["Points", "Heatmap"],
            default_index=0,
            icons=["geo-alt-fill", "pin-map-fill"],
            menu_icon="toggles",
            orientation="horizontal",
        )
    if visualization == "Points":
        m = leafmap.Map(center=center, zoom=4)
        m.add_points_from_xy(
            filepath,
            y="company_lat",
            x="company_long",
            layer_name="Job Locations",
        )
    elif visualization == "Heatmap":
        m = leafmap.Map(center=center, zoom=4)
        m.add_heatmap(
            filepath,
            latitude="company_lat",
            longitude="company_long",
            value="count",
            name="Job Locations Heatmap",
        )
    m.to_streamlit(height=800)