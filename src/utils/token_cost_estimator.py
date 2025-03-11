import tiktoken

# Model Pricing Dictionary
MODEL_PRICING = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},  # GPT-4o pricing per 1K tokens
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
}

def get_model_price(model):
    """Returns the input and output price per 1K tokens for the given model."""
    return MODEL_PRICING.get(model, {"input": 0.06, "output": 0.06})  # Default price if model not found

def chatgpt_encoding_count(text, model="gpt-3.5-turbo"):
    """Encodes text using the correct tokenizer and returns token count."""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def calculate_cost(model, prompts, response):
    """Calculates the cost based on the number of tokens and model pricing."""
    enc = tiktoken.encoding_for_model(model)
    
    input_price, output_price = get_model_price(model)["input"], get_model_price(model)["output"]
    
    if isinstance(prompts, list):
        input_tokens = chatgpt_encoding_count("".join(prompt["content"] for prompt in prompts), model)
    else:
        input_tokens = chatgpt_encoding_count(prompts, model)
    
    output_tokens = len(enc.encode(response))

    total_cost = (input_tokens / 1000) * input_price + (output_tokens / 1000) * output_price

    return input_tokens, output_tokens, total_cost