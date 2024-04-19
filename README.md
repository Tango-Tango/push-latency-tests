# Prerequisites

To run the tests, you will need Python installed. They have only been tested with Python 3.11, but
should run on any recent Python version.

# Running the tests

## Using Poetry

1. [Install poetry](https://python-poetry.org/docs/#installation).
2. Run `poetry run app <TARGET_IP_OR_HOSTNAME> --outfile <FILENAME>`.

## Without poetry

1. Optionally [create a virtual environment](https://virtualenv.pypa.io/en/latest/user_guide.html).
2. Install requirements with `python -m pip install -r requirements.txt`.
3. Run `PYTHONPATH=. python -m push_latency_tests.main <TARGET_IP_OR_HOSTNAME> --outfile <FILENAME>`.