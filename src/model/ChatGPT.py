from src.model.AbstractRepair import AbstractRepair
from src.utils.token_cost_estimator import calculate_cost
from src.utils.logger import logger
from openai import OpenAI
from dotenv import load_dotenv
import os
import re

load_dotenv()
# api_key = os.getenv("LAB_API_KEY")
# api_key = os.getenv("PERSONAL_API_KEY")
api_key = os.getenv("API_KEY")
client = OpenAI(api_key=api_key)

class ChatGPT(AbstractRepair):
    def __init__(self, model="gpt-3.5-turbo", temperature=0.7, top_p=0.95, top_k=50, frequency_penalty=0.0, presence_penalty=-0.5):
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty

    def load_model(self, input):
        '''
        Load the model and generate the completions
        '''
        ret = None
        while ret is None:
            try:
                ret = client.chat.completions.create(
                    messages=input,
                    model=self.model,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    # top_k=self.top_k,
                    frequency_penalty=self.frequency_penalty,
                    presence_penalty=self.presence_penalty,
                )
            except Exception as e:
                print(e)
                return None
        return ret

    def generate_patch(self, sample_size: int, messages: list) -> str:
        '''
        Generate a patch for the given buggy code

        Return: List of results, including:
            - input_tokens: The input tokens
            - output_tokens: The output tokens
            - total_cost: The total cost
            - patch: The generated patch
        '''
        results = []
        for index in range(sample_size):
            result = {
                'input_tokens': None,
                'output_tokens': None,
                'total_cost': None,
                'patch': None,
                'response': None
            }
            # Generate the patch
            response = self.load_model(messages).choices[0].message.content
            patch = self.decode_patch(response)
            # Calculate the cost
            input_tokens, output_tokens, total_cost = calculate_cost(self.model, messages, response)
            # Update the result
            result['input_tokens'] = input_tokens
            result['output_tokens'] = output_tokens
            result['total_cost'] = total_cost
            result['patch'] = patch
            result['response'] = response
            logger.info(f"Generated patch {index + 1}/{sample_size}, with the input tokens {input_tokens}, output tokens {output_tokens} and cost {total_cost}")
            # Append the result
            results.append(result)
        
        return results

    def decode_patch(self, patch: str) -> str:
        '''
        Decode the patch from the response

        Return:
            - patch: Decoded patch
        '''
        # Regular expression to capture code between triple backticks with 'java'
        code_blocks = re.findall(r'```java\s*(.*?)\s*```', patch, re.DOTALL)
        if not code_blocks:
            return None
        else:
            return max(code_blocks, key=len)