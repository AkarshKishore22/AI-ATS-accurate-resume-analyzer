import streamlit as st
import google.generativeai as genai
import re
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import time
from datetime import datetime
# Load environment variables
load_dotenv()
# Configure Streamlit page settings
st.set_page_config(
    page_title="Smart ATS",
    page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTy0x5TXAZwt1-8S7dMnehqGlTOLIffkE6CQvW2R2C9&s",
    layout="centered",
)
# Configure Gemini AI model with the provided API key
API_KEY = "AIzaSyBsj1V-Z7ojsLVFp3C0Bt2dK_gWU3wJFmI"
genai.configure(api_key=API_KEY)
# Function to get response from Gemini AI
def get_gemini_response(input, max_retries=10):
    retries = 0
    while retries < max_retries:
        try:
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            response = model.generate_content(input)
            time.sleep(0.5)
            return response.text
        except Exception as e:
            print("An error occurred:", e)
            if retries < max_retries - 1:
                retries += 1
                print(f"Retrying attempt {retries}/{max_retries}...")
                time.sleep(2 ** retries)  # Exponential backoff
            else:
                raise RuntimeError("Exceeded maximum retries. Failed to get response.")
# Function to extract the year of bachelor's degree completion from the resume text
def extract_bachelors_completion_year(text):
    # Regular expression pattern to match year
    year_pattern = r'\b(19|20)\d{2}\b'  # Matches years between 1900 and 2099
    # Keywords to identify bachelor's degree completion
    bachelor_keywords = ['bachelor', "bachelor's", 'undergraduate']
    
    # Find matches for bachelor's degree completion year
    matches = re.findall(year_pattern, text, flags=re.IGNORECASE)
    
    # Find keywords indicating bachelor's degree
    bachelor_found = any(keyword in text.lower() for keyword in bachelor_keywords)
    
    if matches:
        # Take the last matched year (assuming it's the most recent completion year)
        completion_year = matches[-1]
        return completion_year, bachelor_found
    else:
        return None, bachelor_found
# Function to extract text from uploaded PDF file
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text
# Prompt Template
input_prompt = """
Hey Act Like a skilled or very experienced ATS (Application Tracking System)
with a deep understanding of the tech field, software engineering, data science, data analyst
and big data engineering. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide the
best assistance for improving the resumes. Assign the percentage Matching based on JD ,
the matched skills, the unmatched skills, calculate the total experience of the person after the completion of their bachelors degree till present,
for experience matched or not with answer "Yes" or "No"
if he holds a masters degree or not with answer as "Yes" or "No" and the missing keywords with high accuracy.
Sort it according to the JD match in descending order.
resume:{text}
description:{jd}
I want the response in one single string having the structure
{{"JD Match":"%","Matched Skills":[],"Unmatched Skills":[],"MissingKeywords":[],"Masters Degree":"","Total Experience after graduation":"","Experience matched or not": "","Profile Summary":""}}
"""
## Streamlit app
st.title("Resume Matcher ATS")
st.markdown("Tessolve Semicondutors(https://www.tessolve.com)")
jd = st.text_area("Paste the Job Description")
uploaded_files = st.file_uploader("Upload Your Resumes", type="pdf", accept_multiple_files=True, help="Please upload PDFs")
submit = st.button("Submit")
if submit:
    for uploaded_file in uploaded_files:
        text = input_pdf_text(uploaded_file)
    # Extract completion year of bachelor's degree
        bachelors_completion_year, bachelor_found = extract_bachelors_completion_year(text)
        if bachelors_completion_year:
           # st.write(f"Bachelor's degree completion year: {bachelors_completion_year}")
        # Calculate total experience since bachelor's degree completion
            current_year = datetime.now().year
            total_experience = current_year - int(bachelors_completion_year)
            #st.write(f"Total experience after completion of bachelor's degree: {total_experience} years")
        else:
            st.write("Unable to determine bachelor's degree completion year from the resume.")
            response = get_gemini_response(input_prompt.format(text=text, jd=jd))
    if uploaded_files:
        results = []
        for uploaded_file in uploaded_files:
            # st.write(f"Analyzing {uploaded_file.name}...")
            text = input_pdf_text(uploaded_file)
            response = get_gemini_response(input_prompt.format(text=text, jd=jd))
            # st.subheader(f"Response for {uploaded_file.name}:")
            try:
                parsed_response = json.loads(response)
                results.append({"file_name": uploaded_file.name, "response": parsed_response})
            except json.JSONDecodeError as e:
                st.error(f"Error decoding JSON: {e}")
        results_sorted = []
        for result in results:
            try:
                jd_match = result["response"].get("JD Match", "0%")  # Default to "0%" if "JD Match" key is missing
                jd_match_value = float(jd_match.strip("%"))  # Convert to float
                results_sorted.append((result, jd_match_value))
            except ValueError as e:
                st.warning(f"Error parsing JD match for {result['file_name']}: {e}")
        # Sort results based on JD match values
        results_sorted.sort(key=lambda x: -x[1])
        # Display sorted results
        for result, _ in results_sorted:
            st.subheader(f"Response for {result['file_name']}:")
            for key, value in result['response'].items():
                st.write(f"**{key}:** {value}")