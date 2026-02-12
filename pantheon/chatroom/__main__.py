import fire
from dotenv import load_dotenv

# Load .env file with override=False to NOT override existing environment variables
# This allows command-line args (like --auto-start-nats) to take precedence
load_dotenv(override=False)

# Now safe to import other modules
from .start import start_services


if __name__ == "__main__":
    fire.Fire(start_services)
