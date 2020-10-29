from rest_framework.views import APIView
from rest_framework.response import Response
import requests


class HelloWorld(APIView):

    def get(self, request):

        return Response("Hello World!")


def get_legal_name(lei):
    """Returns the legal name for the given lei code. If the lei code is invalid or an entity cannot be found for the
       lei code, then None is returned."""

    gleif_response = requests.get("https://leilookup.gleif.org/api/v2/leirecords?lei=" + lei)
    if gleif_response.status_code == 200:
        # If given lei code is valid

        gleif_response_json = gleif_response.json()
        if len(gleif_response_json) != 0:
            # If an entity is found for the given lei code

            return gleif_response_json[0]["Entity"]["LegalName"]["$"]

    return None
