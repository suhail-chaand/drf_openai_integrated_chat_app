import os
import openai
import subprocess
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

training_dataframe = pd.read_csv("davinci_training_data.csv")

prepared_data = training_dataframe.loc[:, ['sub_prompt', 'response_text']]
prepared_data.rename(columns={'sub_prompt': 'prompt', 'response_text': 'completion'}, inplace=True)
prepared_data.to_csv('davinci_training_file.csv')

subprocess.run('openai tools fine_tunes.prepare_data -f davinci_training_file.csv --quiet'.split())

subprocess.run('openai api fine_tunes.create -t davinci_training_file_prepared.jsonl '
               '-m davinci --suffix "davinci-superhero-describer"'.split())
