import requests
import os
import streamlit as st

st.title("SynthoLogic API Debugger")

# Fetch Token
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    st.error("Token NOT found in Secrets! Please add HF_TOKEN in Settings.")
else:
    st.success(f"Token found: {HF_TOKEN[:5]}... (starts with)")
    
    # Text Input for Prompt
    prompt = st.text_input("Enter a test prompt", value="A simple red car")
    
    if st.button("Test Image Generation"):
        st.write("Sending request to Text-to-Image Model...")
        
        # We will test the Stability AI model as well just in case FLUX is busy
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        try:
            with st.spinner("Calling API..."):
                response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
            
            # 1. Print status code
            st.write(f"Response Status Code: {response.status_code}")
            
            # 2. Try parsing as JSON to see if there's an error message
            try:
                response_json = response.json()
                st.write("Response is JSON (Likely Error):")
                st.code(response_json)
                if response.status_code == 401:
                    st.error("Authentication Error: The token is invalid or does not have Read access.")
                elif response.status_code == 503:
                    st.info("Model is Loading: The API is active but the model is warming up. Wait 1-2 minutes and try again.")
                elif response.status_code == 429:
                    st.warning("Rate Limited: Hugging Face free tier is busy. Try again later.")

            except ValueError:
                # If it's not JSON, assume it's image bytes
                st.write("Response is not JSON. Likely Image Bytes (Success!)")
                if response.status_code == 200 and len(response.content) > 1000:
                    st.success("Successfully generated image bytes!")
                    st.image(response.content)
                else:
                    st.error(f"Received data but status is {response.status_code} or data is too small.")
                    
        except Exception as e:
            st.error(f"Request failed: {e}")