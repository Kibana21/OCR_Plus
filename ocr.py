import dspy
from dotenv import load_dotenv
import os

load_dotenv()

lm = dspy.LM("openai/gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
dspy.configure(lm=lm)



sentence = "it's a charming and often affecting journey."  

classify = dspy.Predict('sentence -> sentiment: bool')  
sentiment=classify(sentence=sentence).sentiment
print(sentiment)