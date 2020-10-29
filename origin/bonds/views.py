from rest_framework.views import APIView
from rest_framework.response import Response
import requests

from .models import Bond


class HelloWorld(APIView):

    def get(self, request):

        return Response("Hello World!")


class Bonds(APIView):
    """/bonds/ endpoint"""

    def post(self, request):
        """POST method"""

        lei_code = request.data.get("lei")
        if len(lei_code) != 20 or not lei_code.isalnum():
            return Response(status=400, data="LEI code is invalid")

        gleif_response = get_gleif_response(lei_code)

        if gleif_response.status_code != 200:
            return Response(status=500, data="Error obtaining legal name from GLEIF API")

        gleif_response_json = gleif_response.json()
        if len(gleif_response_json) == 0:
            return Response(status=404, data="Could not find entity for the given LEI code")

        legal_name = gleif_response_json[0]["Entity"]["LegalName"]["$"]

        new_bond = Bond(isin=request.data.get("isin"),
                        size=request.data.get("size"),
                        currency=request.data.get("currency"),
                        maturity=request.data.get("maturity"),
                        lei=request.data.get("lei"),
                        legal_name=legal_name)
        new_bond.save()

        return Response("Bond successfully created.")


def get_gleif_response(lei_code):
    """Given a LEI code, returns the response when searching for the LEI code using the GLEIF API"""

    return requests.get("https://leilookup.gleif.org/api/v2/leirecords?lei=" + lei_code)
