from dotenv import load_dotenv
import streamlit as st
import os
import io
import base64
from PIL import Image
# from pdf2image import convert_from_path
import pdf2image
import google.generativeai as genai
import re
import plotly.graph_objects as go

# Load environment variables
load_dotenv()

# Configure the Google API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input, pdf_content[0], prompt])
    return response.text

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        try:
            # Convert PDF to images using poppler-utils installed via apt-get
            images = pdf2image.convert_from_bytes(uploaded_file.read())  # Removed poppler_path
            first_page = images[0]
            img_byte_arr = io.BytesIO()
            first_page.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()

            # Prepare the image for processing
            pdf_parts = [
                {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(img_byte_arr).decode()
                }
            ]
            return pdf_parts
        except pdf2image.exceptions.PDFInfoNotInstalledError as e:
            st.error(f"PDFInfoNotInstalledError: {e}")
            raise e
        except Exception as e:
            st.error(f"An error occurred: {e}")
            raise e
    else:
        raise FileNotFoundError("No file uploaded")

st.set_page_config(page_title="Your Resume Expert", layout="wide", initial_sidebar_state="expanded")

# Sidebar setup
logo='logo.png'
st.sidebar.image(logo, width=150, clamp=True)
st.sidebar.header(":blue[_Resume Analyser_]", divider="blue")
st.sidebar.subheader("Upload Your Resume and Job Description")
input_text = st.sidebar.text_area("Job Description:", key="input")
uploaded_file = st.sidebar.file_uploader("Upload your resume (PDF)...", type=["pdf"])

if uploaded_file is not None:
    st.sidebar.success("PDF Uploaded Successfully")

# Buttons in sidebar
submit1 = st.sidebar.button("How is my Resume")
submit2 = st.sidebar.button("Help Me Improve My Resume")
submit3 = st.sidebar.button("ATS Score")

input_prompt1 = """
Extract the technical skills, soft skills and important information only from the resume. 
Ensure to categorize each piece of information explicitly stated in the resume in form of table and tells overall how the resume according to the given job description.
"""

input_prompt2 = """
Analyze the resume against the provided job description and Identify the keywords and skills mentioned in the job description that are missing in the resume. 
Prioritize these based on their relevance to the job and show them in table. Provide suggestions for incorporating these keywords into the resume effectively, 
with emphasis on achievements and quantifiable results, also tell some ways to improve resume in points.
"""

input_prompt3 = """
You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality, 
your task is to evaluate the resume against the provided job description. give me the percentage of match if the resume matches
the job description. First the output should come as percentage and then keywords missing and last final thoughts.
"""

def display_response(response, title):
    st.subheader(title)
    st.write(response)

def extract_percentage(response):
    # Use regex to find percentage in the response text
    match = re.search(r'(\d+)%', response)
    if match:
        return int(match.group(1))
    else:
        return None

def show_gauge_chart(percentage):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percentage,
        title={'text': "Match Percentage"},
        gauge={'axis': {'range': [0, 100]},
               'bar': {'color': "green"},
               'steps': [{'range': [0, 50], 'color': "red"},
                         {'range': [50, 75], 'color': "yellow"},
                         {'range': [75, 100], 'color': "green"}]}))
    
    fig.update_layout(
        width=400,  # Set the width
        height=300,  # Set the height
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=False)

# def custom_spinner(size=50):
#     spinner_html = f"""
#     <div style='text-align: center; padding: 10px; justify-content: center;'>
#         <div class="loader" style="border-top: {size}px solid #3498db; border-right: {size}px solid transparent; border-radius: 50%; width: {size}px; height: {size}px; animation: spin 1s linear infinite;"></div>
#     </div>
#     <style>
#         @keyframes spin {{
#             0% {{ transform: rotate(0deg); }}
#             100% {{ transform: rotate(360deg); }}
#         }}
#     </style>
#     """
#     st.markdown(spinner_html, unsafe_allow_html=True)

if submit1:
    if uploaded_file is not None:
        with st.spinner('Analysing.....'):
            try:
                pdf_content = input_pdf_setup(uploaded_file)
                response = get_gemini_response(input_prompt1, pdf_content, input_text)
                st.success('Analysing complete!')
                display_response(response, "Resume Analysis")
            except FileNotFoundError:
                st.error("Please upload the resume")
            except Exception as e:
                st.error(f"An error occurred while Analysing the PDF: {e}")
    else:
        st.error("Please upload the resume")

if submit2:
    if uploaded_file is not None:
        with st.spinner('Analysing.....'):
            try:
                pdf_content = input_pdf_setup(uploaded_file)
                response = get_gemini_response(input_prompt2, pdf_content, input_text)
                st.success('Analysing complete!')
                display_response(response, "Suggested Skills to Strengthen Your Resume")
            except FileNotFoundError:
                st.error("Please upload the resume")
            except Exception as e:
                st.error(f"An error occurred while Analysing the PDF: {e}")
    else:
        st.error("Please upload the resume")

if submit3:
    if uploaded_file is not None:
        with st.spinner('Analysing.....'):
            try:
                pdf_content = input_pdf_setup(uploaded_file)
                response = get_gemini_response(input_prompt3, pdf_content, input_text)
                # Extract percentage match from response
                match_percentage = extract_percentage(response)
                if match_percentage is not None:
                    st.subheader("Here is your Resume Score")
                    st.metric(label="Match Percentage", value=f"{match_percentage}%")
                    show_gauge_chart(match_percentage)
                st.success('Analysing complete!')
                display_response(response, "Resume & Job Description Matching")
            except FileNotFoundError:
                st.error("Please upload the resume")
            except Exception as e:
                st.error(f"An error occurred while Analysing the PDF: {e}")
    else:
        st.error("Please upload the resume")

footer = """
<div style='text-align: center; padding: 10px; bottom:0;'>
   <p>© 2024 <a href="https://github.com/JrG-One/" target="_blank" style='text-decoration: none; color: inherit;'> Jr.G-One</a></p>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
