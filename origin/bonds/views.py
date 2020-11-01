from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, permission_classes
from django.contrib.auth.models import User
import requests
from datetime import datetime

from .models import Bond


class Bonds(APIView):
    """/bonds/ endpoint"""

    def get(self, request):
        """GET method"""

        query_set = Bond.objects.filter(user=request.user)

        isin_term = request.query_params.get("isin")
        size_term = request.query_params.get("size")
        currency_term = request.query_params.get("currency")
        maturity_term = request.query_params.get("maturity")
        lei_term = request.query_params.get("lei")
        legal_name_term = request.query_params.get("legal_name")

        # Apply filtering for each given search term
        if isin_term:
            query_set = query_set.filter(isin=isin_term.replace('\n', ''))
        if size_term:

            # Convert the size term from a string to an integer before filtering
            try:
                size_term_as_integer = int(size_term.replace('\n', ''))
                query_set = query_set.filter(size=size_term_as_integer)
            except ValueError:
                return Response(status=400, data="An integer must be provided for search term 'size'.")

        if currency_term:
            query_set = query_set.filter(currency=currency_term.replace('\n', ''))
        if maturity_term:

            # Convert the date term from a string to a date object before filtering
            try:
                maturity_term_as_date = datetime.strptime(maturity_term.replace('\n', ''), "%Y-%m-%d").date()
                query_set = query_set.filter(maturity=maturity_term_as_date)
            except ValueError:
                return Response(status=400, data="Dates must be given in the following format: YYYY-mm-dd. For "
                                                 "example: 2023-06-07")

        if lei_term:
            query_set = query_set.filter(lei=lei_term.replace('\n', ''))
        if legal_name_term:
            query_set = query_set.filter(legal_name=legal_name_term.replace('\n', ''))

        return_data = []
        for bond in query_set:
            bond_dict = {
                "isin": bond.isin,
                "size": bond.size,
                "currency": bond.currency,
                "maturity": bond.maturity,
                "lei": bond.lei,
                "legal_name": bond.legal_name
            }
            return_data.append(bond_dict)

        return Response(status=200, data=return_data)

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
