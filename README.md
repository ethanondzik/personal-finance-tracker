# personal-finance-tracker
A simple personal finance tracking application built with Django and Python.

## Project Overview

This project aims to help users track their income and expenses easily. The exact features and implementation details are still being worked out, but the goal is to provide a straightforward and useful tool for managing personal finances.

Tech Stack
- Backend: Django (Python)
- Database: PostgreSQL (tentative)
- Frontend: TBD

## Installation (Work in Progress)
1. Clone the repository:

`git clone https://github.com/ethanondzik/personal-finance-tracker.git`
`cd personal-finance-tracker`

2. Create and activate a virtual environment:

`python3 -m venv .venv`
`source .venv/bin/activate #for macOS/Linux`
`.venv\Scripts\activate #for Windows`

3. Install dependencies:
`pip install -r requirements.txt`

4. Generate a secret key
From the root directory execute this command:
`echo "SECRET_KEY=$(python3 generate_secret_key.py)" > personal_finance_tracker/personal_finance_tracker/.env`

## Running the server
Navigate to where the manage.py file is (e.g. /home/user/GitHub/personal-finance-tracker/personal_finance_tracker) and run the following command:
`python3 manage.py runserver`

This will run a server that is accessable at http://127.0.0.1:8000/

## Development Status
This project is in the early stages of development. More details will be added as we make progress. 

## Contributors
- Oleksii Zhukov
- Yagna Patel
- Ethan Ondzik
    
    