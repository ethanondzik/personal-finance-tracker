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
Run `python3 manage.py migrate` if running the program for the first time
`python3 manage.py runserver`

This will run a server that is accessable at http://127.0.0.1:8000/

## Make a test user
Running the the python script `populate_sample_user.py` located in the project root directory will populate a user instance with predefined categories and bank accounts.
Email: test.user@example.com
Password: Test1234$

## Development Status
This project is in the early stages of development. More details will be added as we make progress. 

## Contributors
- Oleksii Zhukov
- Yagna Patel
- Ethan Ondzik
    
## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### Third-Party Licenses
This project uses third-party libraries and assets. See [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) for details.