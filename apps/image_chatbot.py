import base64
import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Azure AI Foundry endpoint using the OpenAI v1 / Responses API
client = OpenAI(
    base_url=os.getenv("AZURE_OPENAI_BASE_URL", "https://niai-image-2026.services.ai.azure.com/openai/v1/"),
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)
MODEL = os.environ["CHAT_DEPLOYMENT"]  # your gpt-4o DEPLOYMENT name in Foundry

SYSTEM_PROMPT = "You are a helpful assistant that can describe and analyze images and answer questions."

st.set_page_config(page_title="Image Explainer Chatbot", page_icon="🖼️")
st.title("🖼️ Image Explainer Chatbot")

if "display" not in st.session_state:
    st.session_state.display = []          # [{"role", "text", "image"}]
    st.session_state.last_response_id = None

with st.sidebar:
    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"])
    if uploaded:
        st.image(uploaded)
    if st.button("Clear chat"):
        st.session_state.clear()
        st.rerun()

for m in st.session_state.display:
    with st.chat_message(m["role"]):
        if m.get("image"):
            st.image(m["image"])
        st.write(m["text"])

if prompt := st.chat_input("Ask about the image or anything else..."):
    content = [{"type": "input_text", "text": prompt}]
    img_bytes = None
    if uploaded:
        img_bytes = uploaded.getvalue()
        b64 = base64.b64encode(img_bytes).decode()
        content.append({"type": "input_image", "image_url": f"data:{uploaded.type};base64,{b64}"})

    st.session_state.display.append({"role": "user", "text": prompt, "image": img_bytes})
    with st.chat_message("user"):
        if img_bytes:
            st.image(img_bytes)
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = client.responses.create(
                    model=MODEL,
                    instructions=SYSTEM_PROMPT,
                    input=[{"role": "user", "content": content}],
                    previous_response_id=st.session_state.last_response_id,
                )
                st.session_state.last_response_id = resp.id
                answer = resp.output_text
            except Exception as e:
                answer = f"Error: {e}"
        st.write(answer)
    st.session_state.display.append({"role": "assistant", "text": answer})
