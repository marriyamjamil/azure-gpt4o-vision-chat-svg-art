import base64
import os
import re

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("AZURE_OPENAI_BASE_URL", "https://niai-image-2026.services.ai.azure.com/openai/v1/"),
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)
MODEL = os.environ["CHAT_DEPLOYMENT"]  # gpt-4o deployment name

INSTRUCTIONS = (
    "You are an illustrator that draws images as SVG code. Reply with ONE complete SVG only: "
    'start with <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"> and end with </svg>. '
    "No markdown, no explanation, no scripts, no external images or fonts. "
    "Use gradients, shapes, and paths to make it detailed and attractive. "
    "If a current SVG is provided, modify it according to the request."
)


def extract_svg(text: str) -> str | None:
    m = re.search(r"<svg.*?</svg>", text, re.DOTALL | re.IGNORECASE)
    if not m:
        return None
    svg = m.group(0)
    if re.search(r"<script|onload=|onclick=", svg, re.IGNORECASE):  # basic safety
        return None
    return svg


def show_svg(svg: str, width: int = 512):
    b64 = base64.b64encode(svg.encode()).decode()
    st.markdown(
        f'<img src="data:image/svg+xml;base64,{b64}" width="{width}"/>',
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="GPT-4o Image Maker", page_icon="🎨")
st.title("🎨 GPT-4o Image Maker (SVG)")

if "svg" not in st.session_state:
    st.session_state.svg = None

prompt = st.text_area(
    "Describe the image (or how to change the current one)",
    placeholder="A red fox sitting on a hill at sunset, flat illustration style",
)
c1, c2 = st.columns(2)
generate = c1.button("Generate / Update", type="primary")
if c2.button("Start over"):
    st.session_state.svg = None
    st.rerun()

if generate and prompt.strip():
    user_text = prompt
    if st.session_state.svg:
        user_text = f"Current SVG:\n{st.session_state.svg}\n\nRequest: {prompt}"
    with st.spinner("Drawing..."):
        try:
            resp = client.responses.create(model=MODEL, instructions=INSTRUCTIONS, input=user_text)
            svg = extract_svg(resp.output_text)
            if svg:
                st.session_state.svg = svg
            else:
                st.error("The model did not return a valid SVG. Try again or rephrase.")
        except Exception as e:
            st.error(f"Error: {e}")


if st.session_state.svg:
    show_svg(st.session_state.svg)

    st.download_button(
        "Download SVG",
        st.session_state.svg,
        "image.svg",
        "image/svg+xml"
    )

    try:
        import cairosvg

        png = cairosvg.svg2png(
            bytestring=st.session_state.svg.encode(),
            output_width=1024
        )

        # Save PNG beside svg.py
        folder = os.path.dirname(os.path.abspath(__file__))
        png_path = os.path.join(folder, "image.png")

        with open(png_path, "wb") as f:
            f.write(png)

        st.success(f"PNG saved to: {png_path}")

        st.download_button(
            "Download PNG",
            png,
            "image.png",
            "image/png"
        )

    except Exception as e:
        st.warning(f"PNG export failed: {e}")
