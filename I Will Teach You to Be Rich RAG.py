# -*- coding: utf-8 -*-
"""I_Will_Teach_You_To_Be_Rich_RAG

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1NVx_AClKqeU1-UolR1IP2niaUznzhpZc

### What is RAG anyway?


Retrieval-Augmented Generation (RAG) is a technique primarily used in GenAI applications to improve the quality and accuracy of generated text by LLMs by combining two key processes: retrieval and generation.

### Breaking It Down:
#### Retrieval:

- Before generating a response, the system first looks up relevant information from a large database or knowledge base. This is like searching through a library or the internet to find the most useful facts, articles, or data related to the question or topic.

#### Generation:

- Once the relevant information is retrieved, the system then uses it to help generate a response. This is where the model, like GPT, creates new text (answers, explanations, etc.) based on the retrieved information.

#### Install relevant libraries
"""

! pip install langchain langchain-community openai tiktoken pinecone-client langchain_pinecone unstructured pdfminer==20191125 pdfminer.six==20221105 pillow_heif unstructured_inference youtube-transcript-api pytube sentence-transformers

from langchain.document_loaders import UnstructuredPDFLoader, OnlinePDFLoader, WebBaseLoader, YoutubeLoader, DirectoryLoader, TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sklearn.metrics.pairwise import cosine_similarity
from langchain_pinecone import PineconeVectorStore
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from google.colab import userdata
from pinecone import Pinecone
from openai import OpenAI
import numpy as np
import tiktoken
import os

pinecone_api_key = userdata.get("PINECONE_API_KEY")
os.environ['PINECONE_API_KEY'] = pinecone_api_key

openai_api_key = userdata.get("OPENAI_API_KEY")
os.environ['OPENAI_API_KEY'] = openai_api_key

"""# Initialize the OpenAI client"""

embeddings = OpenAIEmbeddings()
embed_model = "text-embedding-3-small"
openai_client = OpenAI()

"""# Load in a PDF and get its text"""

!pip install tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

loader = PyPDFLoader("/content/drive/MyDrive/I_Will_Teach_You_to_Be_Rich_2nd_Edition.pdf") # Insert the path to a PDF here
data = loader.load()

print(data)

# Get the encoding once to avoid calling it repeatedly
encoding = tiktoken.get_encoding("cl100k_base")

def length_function(text):
    return len(encoding.encode(text)) # Count the number of tokens

text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=100,
        length_function=length_function, # Use the custom length function
        separators=["\n\n", "\n", " ", ""]
    )

texts = text_splitter.split_documents(data)

# Provide a default title if it doesn't exist
vectorstore_from_texts = PineconeVectorStore.from_texts(
    [
        f"Source: {t.metadata.get('source', '')}, Title: {t.metadata.get('title', 'Unknown')} \n\nContent: {t.page_content}"
        for t in texts
    ],
    embeddings,
    index_name=index_name, # Make sure these variables are defined in your environment
    namespace=namespace  # Make sure these variables are defined in your environment
)

# After this, all the code is the same from the Perform RAG section of this notebook
# Since the data from the PDF is now stored in Pinecone, you can perform RAG over it the same way as the YouTube video

texts

"""# Initialize Pinecone"""

vectorstore = PineconeVectorStore(index_name="chatbot-ai", embedding=embeddings)

index_name = "chatbot-ai"

namespace = "i-will-teach-you-to-be-rich"

"""# Insert data into Pinecone

Documentation: https://docs.pinecone.io/integrations/langchain#key-concepts
"""

for document in texts:
    print("\n\n\n\n----")

    print(document.metadata, document.page_content)

    print('\n\n\n\n----')

vectorstore_from_texts = PineconeVectorStore.from_texts(
    [
        f"Source: {t.metadata.get('source', '')}, Title: {t.metadata.get('title', '')} \n\nContent: {t.page_content}"
        for t in texts
    ],
    embeddings,
    index_name=index_name,
    namespace=namespace
)

"""# Perform RAG"""

from pinecone import Pinecone

# Initialize Pinecone
pc = Pinecone(api_key=userdata.get("PINECONE_API_KEY"),)

# Connect to your Pinecone index
pinecone_index = pc.Index("chatbot-ai")

query = "How do I start investing?"

raw_query_embedding = openai_client.embeddings.create(
    input=[query],
    model="text-embedding-3-small"
)

query_embedding = raw_query_embedding.data[0].embedding

query_embedding

top_matches = pinecone_index.query(vector=query_embedding, top_k=10, include_metadata=True, namespace=namespace)

top_matches

# Get the list of retrieved texts
contexts = [item['metadata']['text'] for item in top_matches['matches']]

contexts

augmented_query = "<CONTEXT>\n" + "\n\n-------\n\n".join(contexts[ : 10]) + "\n-------\n</CONTEXT>\n\n\n\nMY QUESTION:\n" + query

print(augmented_query)

# Modify the prompt below as need to improve the response quality

primer = f"""
You are an expert financial advisor and personal assistant with in-depth knowledge of the principles from the book "I Will Teach You to Be Rich" by Ramit Sethi. Your task is to answer any questions I have about the content related to this book or a provided YouTube video.

Please ensure your responses are:

1. **Informative:** Provide detailed and accurate information based on the book's principles and content.
2. **Actionable:** Offer clear, actionable steps or advice that I can easily follow.
3. **Supportive and Encouraging:** Maintain a positive and motivational tone, encouraging smart financial decisions.
4. **Concise:** Keep your responses clear and to the point, avoiding unnecessary jargon.

If the question is about a specific aspect of personal finance, tailor your response to be relevant to that topic, drawing on examples or strategies from the book where possible.

Example topics include budgeting, saving, investing, or managing debt.
"""

res = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": primer},
        {"role": "user", "content": augmented_query}
    ]
)

openai_answer = res.choices[0].message.content

print(openai_answer)

"""# Putting it all together"""

def perform_rag(query):
    # Create an embedding for the query using OpenAI's model
    raw_query_embedding = openai_client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )

    query_embedding = raw_query_embedding.data[0].embedding

    # Query Pinecone to find the top matches in the stored embeddings
    top_matches = pinecone_index.query(vector=query_embedding, top_k=10, include_metadata=True, namespace=namespace)

    # Extract the relevant text from the top matches
    contexts = [item['metadata']['text'] for item in top_matches['matches']]

    # Combine the retrieved texts into a single context to augment the query
    augmented_query = "<CONTEXT>\n" + "\n\n-------\n\n".join(contexts[:10]) + "\n-------\n</CONTEXT>\n\n\n\nMY QUESTION:\n" + query

    # Modify the system prompt to be specific to financial advice based on "I Will Teach You to Be Rich"
    system_prompt = f"""
    You are an expert financial advisor and personal assistant with deep knowledge of the book "I Will Teach You to Be Rich" by Ramit Sethi.
    Answer any financial questions I have based only on the context you have been provided.
    Your responses should be:

    1. **Informative:** Provide detailed and accurate advice grounded in the principles from "I Will Teach You to Be Rich".
    2. **Actionable:** Offer clear, actionable steps or advice that I can easily follow.
    3. **Supportive and Encouraging:** Maintain a positive and motivational tone, encouraging smart financial decisions.
    4. **Concise:** Keep your responses clear and to the point, avoiding unnecessary jargon.

    Always refer to the concepts in the book where applicable, and help the user apply these concepts to their personal financial situation.
    """

    # Generate the response using the augmented query and the modified system prompt
    res = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": augmented_query}
        ]
    )

    return res.choices[0].message.content

perform_rag("How can I start investing?")