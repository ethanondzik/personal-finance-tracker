import os
from django.core.management.utils import get_random_secret_key


def generate_env_file():
    """
    Generates a .env file with a random SECRET_KEY.
    """
    print("Generating .env file...")

    # Generate a random SECRET_KEY
    secret_key = get_random_secret_key()

    #placeholder info for database configuration when using postgres
    database_info = ( 
        "\nDB_NAME=personal_finance_tracker\n"
        "DB_USER=test_admin\n"
        "DB_PASSWORD=your_password\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432")
    

    # Create the .env content
    env_content = f"SECRET_KEY={secret_key}" + database_info

    # Write to .env file
    env_file_path = os.path.join(os.getcwd(), ".env")
    with open(env_file_path, "w") as env_file:
        env_file.write(env_content.strip())

    print(f".env file generated at: {env_file_path}")
    print("Please update the .env file with your database credentials if necessary.")


if __name__ == "__main__":
    generate_env_file()
    
    