"""Interactive Q&A dialogue system for generating prompts."""
from typing import Tuple
from pydantic import BaseModel
from openai import OpenAI
from ..config.settings import get_model, get_openai_key

class TouchfsPrompts(BaseModel):
    filesystem_prompt: str
    content_prompt: str

def run_qa_dialogue() -> Tuple[str, str]:
    """Run an interactive Q&A dialogue to generate filesystem and content prompts.
    
    Returns:
        Tuple[str, str]: (filesystem_generation_prompt, content_generation_prompt)
    """
    # Ask 5 specific questions
    questions = [
        "What is the main purpose of this filesystem? (e.g. project workspace, documentation, data storage)",
        "What types of files do you need? (e.g. code files, documents, images)",
        "How should the files be organized? (e.g. by type, by feature, by date)",
        "What kind of content should be generated for these files?",
        "Are there any specific requirements or constraints? (e.g. file formats, naming conventions)"
    ]
    
    answers = []
    for question in questions:
        print(f"\n{question}")
        answer = input("> ")
        answers.append({"role": "user", "content": f"Q: {question}\nA: {answer}"})
    
    # Generate prompts from answers
    client = OpenAI(api_key=get_openai_key())
    completion = client.beta.chat.completions.parse(
        model=get_model(),
        messages=[{
            "role": "system", 
            "content": """Based on the user's answers to the questions about their filesystem needs, generate two prompts:
            1. filesystem_prompt: A prompt that will generate the desired directory structure
            2. content_prompt: A prompt that will generate appropriate content for the files
            
            Keep the prompts clear, specific and focused on the user's requirements.
            """
        }, *answers],
        response_format=TouchfsPrompts,
    )
    
    prompts = completion.choices[0].message.parsed
    return prompts.filesystem_prompt, prompts.content_prompt
