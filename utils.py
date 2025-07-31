# --- Helper Script for AI-Driven Software Engineering Course ---
# Description: This script provides a unified interface for interacting with
#              multiple LLM providers (OpenAI, Anthropic, Hugging Face, Google Gemini)
#              and simplifies common tasks like artifact management.
# -----------------------------------------------------------------

import os
import json
import requests
from PIL import Image
from io import BytesIO
import re
import base64

# --- Dynamic Library Installation ---
try:
    from dotenv import load_dotenv
    from IPython.display import display, Markdown, Code, Image as IPyImage
    from plantuml import PlantUML
except ImportError:
    print("Core dependencies not found. Please install them by running:")
    print("pip install python-dotenv ipython plantuml anthropic")

# --- Model & Provider Configuration ---
RECOMMENDED_MODELS = {
    # Original OpenAI Models
    "gpt-4o":        {"provider": "openai", "vision": True, "overview": "Latest flagship model, fast and intelligent"},
    "gpt-4.1":       {"provider": "openai", "vision": True, "overview": "Advanced reasoning and instruction following"},
    "gpt-4.1-mini":  {"provider": "openai", "vision": True, "overview": "Compact and fast version of gpt-4.1"},
    "gpt-4.1-nano":  {"provider": "openai", "vision": True, "overview": "Highly efficient and lightweight model"},
    "gpt-4.5":       {"provider": "openai", "vision": True, "overview": "Next-gen model with enhanced capabilities"},
    "o3":            {"provider": "openai", "vision": True, "overview": "Specialized model for complex logic"},
    "o4-mini":       {"provider": "openai", "vision": True, "overview": "Miniature version of the o4 model"},
    "codex-mini-latest":    {"provider": "openai", "vision": False, "overview": "Optimized for code generation tasks"},

    # Original Gemini Models
    "gemini-2.5-pro":         {"provider": "gemini", "vision": True, "overview": "High-performance, multimodal model"},
    "gemini-2.5-flash":       {"provider": "gemini", "vision": True, "overview": "Fast and cost-effective for high-frequency tasks"},
    "gemini-2.5-flash-lite":  {"provider": "gemini", "vision": True, "overview": "Extremely lightweight and fast model"},
    "gemini-veo-3":           {"provider": "gemini", "vision": True, "overview": "Advanced model for video understanding"},
    "gemini-deep-think":      {"provider": "gemini", "vision": True, "overview": "Specialized for deep, complex reasoning"},

    # Original Hugging Face Models
    "meta-llama/Llama-3.3-70B-Instruct": {"provider": "huggingface", "vision": False, "overview": "Large-scale Llama 3 model for instruction following"},
    "tokyotech-llm/Llama-3.1-Swallow-8B-Instruct-v0.5": {"provider": "huggingface", "vision": False, "overview": "8B parameter model with strong instruction capabilities"},
    "tokyotech-llm/Llama-3.1-Swallow-70B-Instruct-v0.3": {"provider": "huggingface", "vision": False, "overview": "70B parameter model for advanced tasks"},
    "mistralai/Mistral-7B-Instruct-v0.3": {"provider": "huggingface", "vision": False, "overview": "Popular 7B model known for efficiency and performance"},
    "deepseek-ai/DeepSeek-VL2":         {"provider": "huggingface", "vision": True, "overview": "Strong vision-language model"},
    "deepseek-ai/DeepSeek-VL2-Small":   {"provider": "huggingface", "vision": True, "overview": "Smaller, faster version of DeepSeek-VL2"},
    "deepseek-ai/DeepSeek-VL2-Tiny":    {"provider": "huggingface", "vision": True, "overview": "Lightweight vision-language model for edge devices"},
    "deepseek-ai/DeepSeek-R1":          {"provider": "huggingface", "vision": False, "overview": "Advanced reasoning model from DeepSeek"},
    "deepseek-ai/Janus-Pro-7B":         {"provider": "huggingface", "vision": True, "overview": "Multimodal model with strong reasoning skills"},

    # --- Anthropic Models ---
    "claude-opus-4-20250514":    {"provider": "anthropic", "vision": True, "overview": "Most powerful model for complex, multi-step tasks"},
    "claude-sonnet-4-20250514":  {"provider": "anthropic", "vision": True, "overview": "Balanced model for enterprise workloads"},
    "claude-3-7-sonnet-20250219": {"provider": "anthropic", "vision": True, "overview": "Highly capable Sonnet model for complex tasks"},
    "claude-3-5-haiku-20241022":  {"provider": "anthropic", "vision": True, "overview": "Fastest and most compact model for near-instant responses"},
}


# --- Environment and API Client Setup ---

def load_environment():
    """Loads environment variables from a .env file in the project root."""
    path = os.getcwd()
    while path != os.path.dirname(path):
        if os.path.exists(os.path.join(path, '.env')) or os.path.exists(os.path.join(path, '.git')):
            project_root = path
            break
        path = os.path.dirname(path)
    else:
        project_root = os.getcwd()

    dotenv_path = os.path.join(project_root, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("Warning: .env file not found. API keys may not be loaded.")


def setup_llm_client(model_name="gpt-4o"):
    """Initializes and returns the API client for the specified model provider."""
    load_environment()
    if model_name not in RECOMMENDED_MODELS:
        print(f"ERROR: Model '{model_name}' is not in the list of recommended models.")
        return None, None, None
    config = RECOMMENDED_MODELS[model_name]
    api_provider = config["provider"]
    client = None
    try:
        if api_provider == "openai":
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key: raise ValueError("OPENAI_API_KEY not found in .env file.")
            client = OpenAI(api_key=api_key)
        elif api_provider == "anthropic":
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key: raise ValueError("ANTHROPIC_API_KEY not found in .env file.")
            client = Anthropic(api_key=api_key)
        elif api_provider == "huggingface":
            from huggingface_hub import InferenceClient
            api_key = os.getenv("HUGGINGFACE_API_KEY")
            if not api_key: raise ValueError("HUGGINGFACE_API_KEY not found in .env file.")
            client = InferenceClient(model=model_name, token=api_key)
        elif api_provider == "gemini":
            import google.generativeai as genai
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key: raise ValueError("GOOGLE_API_KEY not found in .env file.")
            genai.configure(api_key=api_key)
            client = genai.GenerativeModel(model_name)
    except ImportError:
        print(f"ERROR: The required library for '{api_provider}' is not installed.")
        return None, None, None
    except ValueError as e:
        print(f"ERROR: {e}")
        return None, None, None
    print(f"✅ LLM Client configured: Using '{api_provider}' with model '{model_name}'")
    return client, model_name, api_provider

# --- Core Interaction Functions ---

def get_completion(prompt, client, model_name, api_provider, temperature=0.7):
    """Gets a text completion from the specified LLM."""
    if not client: return "API client not initialized."
    try:
        if api_provider == "openai":
            response = client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}], temperature=temperature)
            return response.choices[0].message.content
        elif api_provider == "anthropic":
            response = client.messages.create(
                model=model_name,
                max_tokens=4096,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        elif api_provider == "huggingface":
            response = client.chat_completion(messages=[{"role": "user", "content": prompt}], temperature=max(0.1, temperature), max_tokens=4096)
            return response.choices[0].message.content
        elif api_provider == "gemini":
            response = client.generate_content(prompt)
            return response.text
    except Exception as e:
        return f"An API error occurred: {e}"

def get_vision_completion(prompt, image_url, client, model_name, api_provider):
    """Gets a vision-enhanced completion from the specified LLM."""
    if not client: return "API client not initialized."
    if not RECOMMENDED_MODELS.get(model_name, {}).get("vision"):
        return f"Error: Model '{model_name}' does not support vision."
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))

        if api_provider == "openai":
            response = client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_url}}]}], max_tokens=4096)
            return response.choices[0].message.content
        elif api_provider == "anthropic":
            buffered = BytesIO()
            image_format = img.format if img.format else "JPEG"
            img.save(buffered, format=image_format)
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            media_type = f"image/{image_format.lower()}"

            response = client.messages.create(
                model=model_name,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_base64}},
                        {"type": "text", "text": prompt}
                    ],
                }],
            )
            return response.content[0].text
        elif api_provider == "gemini":
            response = client.generate_content([prompt, img])
            return response.text
        elif api_provider == "huggingface":
            response = client.image_to_text(image=img, prompt=prompt)
            return response
    except Exception as e:
        return f"An API error occurred during vision completion: {e}"

def clean_llm_output(output_str: str, language: str = 'json') -> str:
    """Cleans markdown code blocks from LLM output."""
    if '```' in output_str:
#        pattern = re.compile(rf'```{language}\n(.*?)\n```', re.DOTALL | re.MULTILINE)
        pattern = re.compile(rf'```{language}\s*([\s\S]*?)\s*```', re.DOTALL | re.MULTILINE)
        match = pattern.search(output_str)
        if match:
            return match.group(1).strip()
        else:
            cleaned = output_str.split('```', 1)[-1]
            cleaned = cleaned.rsplit('```', 1)[0]
            return cleaned.strip().lstrip(language).strip()
    return output_str.strip()

def clean_llm_output_ray(output_str: str, language: str = 'json') -> str:
    """Cleans markdown code blocks from LLM output.

    Extracts only the code from the first code block matching the specified language.
    If no such block is found, returns the original string stripped of whitespace.

    Fix: For 'markdown', returns the entire content between the first and last triple backticks,
    regardless of language, to avoid truncating mixed-language markdown files.
    """
    if '```' in output_str:
        if language == "markdown":
            # For markdown, extract everything between the first and last triple backticks
            parts = output_str.split('```')
            if len(parts) >= 3:
                # Return everything between the first and last code block
                return '```'.join(parts[1:-1]).strip()
            else:
                # Fallback: remove leading/trailing backticks
                return output_str.replace('```', '').strip()
        else:
            # For other languages, extract the first matching code block
            pattern = re.compile(rf'```{language}\s*([\s\S]*?)\s*```', re.DOTALL | re.MULTILINE)
            match = pattern.search(output_str)
            if match:
                return match.group(1).strip()
            else:
                cleaned = output_str.split('```', 1)[-1]
                cleaned = cleaned.rsplit('```', 1)[0]
# --- Artifact Management & Display ---

def _find_project_root():
    """
    Finds the project root by searching upwards for a known directory marker
    (like '.git' or 'artifacts'). This is more reliable than just using os.getcwd().
    """
    path = os.getcwd()
    while path != os.path.dirname(path):
        if any(os.path.exists(os.path.join(path, marker)) for marker in ['.git', 'artifacts', 'README.md']):
            return path
        path = os.path.dirname(path)
    print("Warning: Project root marker not found. Defaulting to current directory.")
    return os.getcwd()


def save_artifact(content, file_path):
    """Saves content to a specified file path, creating directories if needed."""
    try:
        project_root = _find_project_root()
        full_path = os.path.join(project_root, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Successfully saved artifact to: {file_path}")
    except Exception as e:
        print(f"❌ Error saving artifact to {file_path}: {e}")

def load_artifact(file_path):
    """Loads content from a specified file path."""
    try:
        project_root = _find_project_root()
        full_path = os.path.join(project_root, file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: Artifact file not found at {file_path}.")
        return None

def render_plantuml_diagram(puml_code, output_path="artifacts/diagram.png"):
    """Renders PlantUML code and saves it as a PNG image."""
    try:
        pl = PlantUML(url='http://www.plantuml.com/plantuml/img/')
        project_root = _find_project_root()
        full_path = os.path.join(project_root, output_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        # pl.processes(puml_code, outfile=full_path)
        image_bytes = pl.processes(puml_code)
        with open(full_path, "wb") as img_file:
            img_file.write(image_bytes)
        print(f"✅ Diagram rendered and saved to: {output_path}")
        display(IPyImage(url=full_path))
    except Exception as e:
        print(f"❌ Error rendering PlantUML diagram: {e}")