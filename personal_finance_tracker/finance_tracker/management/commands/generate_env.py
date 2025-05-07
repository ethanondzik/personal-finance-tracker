import os
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key

class Command(BaseCommand):
    help = 'Generates an .env file with a random SECRET_KEY'

    def handle(self, *args, **kwargs):
        """
        Generates a .env file with a random SECRET_KEY in the project root directory.
        """
        self.stdout.write("Generating .env file...")

        # Generate a random SECRET_KEY
        secret_key = get_random_secret_key()

        # Placeholder info for database configuration when using postgres
        database_info = (
            "\nDB_NAME=personal_finance_tracker\n"
            "DB_USER=ethan\n"
            "DB_PASSWORD=Test1234$\n"
            "DB_HOST=localhost\n"
            "DB_PORT=5432")

        # Create the .env content
        env_content = f"SECRET_KEY={secret_key}" + database_info

        # Determine project root directory (two levels up from management/commands)
        commands_dir = os.path.dirname(os.path.abspath(__file__))
        management_dir = os.path.dirname(commands_dir)
        app_dir = os.path.dirname(management_dir)
        django_project_dir = os.path.dirname(app_dir)
        project_root = os.path.dirname(django_project_dir)

        # Write to .env file in the project root
        env_file_path = os.path.join(project_root, ".env")
        with open(env_file_path, "w") as env_file:
            env_file.write(env_content.strip())

        self.stdout.write(self.style.SUCCESS(f".env file generated at: {env_file_path}"))
        self.stdout.write("Please update the .env file with your database credentials if necessary.")