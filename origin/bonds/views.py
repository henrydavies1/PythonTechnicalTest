from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, permission_classes
from django.contrib.auth.models import User
import requests

from .models import Bond


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
                        legal_name=legal_name,
                        user=request.user)
        new_bond.save()

        return Response("Bond successfully created.")


def get_gleif_response(lei_code):
    """Given a LEI code, returns the response when searching for the LEI code using the GLEIF API"""

    return requests.get("https://leilookup.gleif.org/api/v2/leirecords?lei=" + lei_code)


@authentication_classes([])
@permission_classes([])
class Register(APIView):
    """/register/ endpoint to register new users"""

    def post(self, request):
        """POST method"""

        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(status=400, data={"username": "required", "password": "required"})

        if User.objects.filter(username=username):
            return Response(status=409, data="Username already exists, please provide another.")

        new_user = User.objects.create_user(username=username,
                                            password=password)
        new_user.save()

        return Response(status=200, data="User created successfully")
