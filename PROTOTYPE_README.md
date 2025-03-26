
# Steps to install and run the financial tracking functional prototype

1. Put functional_prototype.zip file in desired location

2. Unzip the file: `unzip functional_prototype.zip`
Note: This will take a few seconds

3. Navigate into the unzipped directory and setup a python virtual environment
```bash
cd functional_prototype

python3 -m venv .venv

source .venv/bin/activate
```

4. Install packages into virtual environment with pip
`pip install -r requirements.txt`

5. Generate a secret key and put it into a .env file
`echo "SECRET_KEY=$(python3 generate_secret_key.py)" > personal_finance_tracker/personal_finance_tracker/.env`

6. Configure Database
```bash
python3 personal_finance_tracker/manage.py migrate
```

7. Start the server
```bash
python3 personal_finance_tracker/manage.py runserver
```

8. Navigate to the url: http://localhost:8000/
From here you can register an account, login, and begin adding transactions

