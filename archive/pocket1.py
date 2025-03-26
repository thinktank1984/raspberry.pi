import logging
from pocket import Pocket, PocketException

logging.basicConfig(level=logging.DEBUG)

p = Pocket(
    consumer_key='114205-4f640a16a3fd75d1b69798d',
    access_token='0c67ad2b-95d3-a656-d9bd-eb08b7'
)

# Fetch a list of articles with all required parameters
try:
    # Adding state parameter which is often required
    response = p.get(state='all', count=10)
    print(response)
except PocketException as e:
    print(f"Pocket API Error: {str(e)}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")