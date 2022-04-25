from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

# Code of your application, which uses environment variables (e.g. from `os.environ` or
# `os.getenv`) as if they came from the actual environment.
import os
assert os.getenv('SECRET') == "FALSE"

name = 'steve'
print(f'hello {name}')
print('foobar')
