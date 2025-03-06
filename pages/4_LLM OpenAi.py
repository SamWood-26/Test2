import streamlit as st
import openai
import textwrap
from IPython.display import display, Markdown

st.title("Large Language Model (LLM) Interaction Page (OpenAI)")

if "species" not in st.session_state:
    st.session_state.species = None
if "tissue" not in st.session_state:
    st.session_state.tissue = None
if "marker_genes" not in st.session_state:
    st.session_state.marker_genes = ""
if "api_key" not in st.session_state:
    st.session_state.api_key = ""


api_key = st.session_state.api_key

if api_key:
    openai.api_key = api_key  
else:
    st.warning("Please enter an API key to use the chatbot.")
    st.stop()  

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_input = st.chat_input("Ask me about cell types, marker genes, or tissues...")

if user_input:
    # Store user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Automatically include session state variables in the prompt
    species = st.session_state.species or "unspecified species"
    tissue = st.session_state.tissue or "unspecified tissue"
    marker_genes = st.session_state.marker_genes or "none provided"

    context = f"""
    Species: {species}
    Tissue: {tissue}
    Marker Genes: {marker_genes}
    """

    # Construct full prompt
    full_prompt = f"""
    You are an expert in cell type annotation. The user is working with the following biological context:

    {context}

    Based on this information, answer their question as accurately as possible.
    
    User: {user_input}
    """

    try:
        # Call OpenAI API with the stored API key
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in cell biology and annotation."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        # Extract response
        response_text = response['choices'][0]['message']['content'].strip()

        # Display and store response
        with st.chat_message("assistant"):
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})

    except Exception as e:
        st.error(f"An error occurred: {e}")

#https://www.celltypist.org/ #https://www.youtube.com/watch?v=eZDmDn6Iq9Y 
#https://www.nature.com/articles/s41592-024-02201-0 - GPT better 
#https://www.biorxiv.org/content/10.1101/2024.09.16.613342v3.abstract - linear better than GPT 
#https://youtu.be/eMlx5fFNoYc?feature=shared

#old

# import streamlit as st
# import openai
# import textwrap
# from IPython.display import display, Markdown

# st.title("Large Language Model (LLM) Interaction Page (OpenAI)")

# # Input for OpenAI API key
# api_key = st.text_input("Enter your OpenAI API key", type="password", placeholder="sk-...")
# if api_key:
#     openai.api_key = api_key
# else:
#     st.warning("Enter an API key to use this feature.")

# mode = st.radio("Select Input Mode", ["Form-based Input", "Custom Prompt"], index=0)


# # Inputs for tissue context and marker genes
# if mode == "Form-based Input":
#     tissue_context = st.text_input(
#         "Enter tissue context",
#         placeholder="Example: 'liver' or for multiple, separate with 'or' (e.g., 'liver or heart')"
#     )
#     marker_genes = st.text_area(
#         "Enter marker genes",
#         placeholder="Enter marker genes separated by commas (e.g., Gpx2, Rps12, Rpl12)."
#     )

#     # Input for options
#     num_options = st.number_input("How many options?", min_value=2, max_value=10, value=4)
#     options = []
#     for i in range(num_options):
#         option = st.text_input(f"Option {chr(65 + i)}:", key=f"option_{i}")
#         options.append(option)

#     # Generate cell type annotation
#     if st.button("Generate Cell Type Annotation"):
#         if not api_key:
#             st.error("An API key is required to use this feature.")
#         elif tissue_context and marker_genes and all(options):
#             options_text = '\n'.join([f"{chr(65 + i)}) {option}" for i, option in enumerate(options)])
#             prompt = f"""You are an annotator of cell types. You will be given a list of marker genes and tissue context, and you need to determine the most likely cell types among the possible options. Choose the correct option from the given choices by responding with only one letter: A, B, C, etc.
#             Question: The tissue context is {tissue_context} and the marker genes are {marker_genes}. What is the most likely cell type among the following options?
#             {options_text}
#             Answer:"""

#             try:
#                 # Call OpenAI API
#                 response = openai.ChatCompletion.create(
#                     model="gpt-4",
#                     messages=[
#                         {"role": "system", "content": "You are annotator of cell types. Choose the most likely cell type."},
#                         {"role": "user", "content": prompt}
#                     ],
#                     max_tokens=1,
#                     temperature=0.0
#                 )

#                 # Extract and map the response
#                 response_text = response['choices'][0]['message']['content'].strip()
#                 answer_letter = response_text[-1]
#                 answer_index = ord(answer_letter.upper()) - ord('A')
#                 answer_name = options[answer_index] if 0 <= answer_index < len(options) else "Unknown"

#                 st.markdown(f"**Most Likely Cell Type:** {answer_name}")

#             except Exception as e:
#                 st.error(f"An error occurred: {e}")
#         else:
#             st.error("Please provide all required inputs and ensure all options are filled.")

# elif mode == "Custom Prompt":
#     custom_prompt = st.text_area("Enter your full prompt", placeholder="Type your prompt here...")
    
#     if st.button("Generate from Custom Prompt"):
#         if not api_key:
#             st.error("An API key is required to use this feature.")
#         elif custom_prompt:
#             try:
#                 response = openai.ChatCompletion.create(
#                     model="gpt-4",
#                     messages=[{"role": "user", "content": custom_prompt}],
#                     max_tokens=500,
#                     temperature=0.7
#                 )
                
#                 response_text = response['choices'][0]['message']['content'].strip()
#                 st.markdown(f"**Model Response:** {response_text}")
#             except Exception as e:
#                 st.error(f"An error occurred: {e}")
#         else:
#             st.error("Please provide a valid prompt.")