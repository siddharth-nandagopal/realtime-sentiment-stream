config = {
    "openai": {
        "api_key": "API_KEY",
        "model_name": "gpt-4o-mini",
        "role": "system",
        "context": """
                        You're a machine learning model with a task of classifying comments into POSITIVE, NEGATIVE, NEUTRAL.
                        You are to respond with one word from the option specified above, do not add anything else.
                        Here is the comment:                       
                  """
    },
    "kafka": {
        "bootstrap.servers": "kafka01:29192,kafka02:29292,kafka03:29392"
    },
    "schema-registry": {
        "url": "localhost:8081"
    }
}