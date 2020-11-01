from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from django.test import TestCase
from datetime import datetime

from .views import get_gleif_response
from .models import Bond


class GetGleifResponseTest(TestCase):

    def test_correct_legal_name_found(self):

        # Find legal name for Apple's LEI code
        gleif_response_apple = get_gleif_response("HWUPKR0MPOU8FGXBT394")
        gleif_response_apple_json = gleif_response_apple.json()
        self.assertEqual(gleif_response_apple_json[0]["Entity"]["LegalName"]["$"], "APPLE INC.")

        # Find legal name for John Lewis' LEI code
        gleif_response_john_lewis = get_gleif_response("213800JSUFNZLZLCVJ25")
        gleif_response_john_lewis_json = gleif_response_john_lewis.json()
        self.assertEqual(gleif_response_john_lewis_json[0]["Entity"]["LegalName"]["$"], "JOHN LEWIS PLC")

        # Find legal name for Oracle's LEI code
        gleif_response_oracle = get_gleif_response("549300FL0LHI0TEZ8V48")
        gleif_response_oracle_json = gleif_response_oracle.json()
        self.assertEqual(gleif_response_oracle_json[0]["Entity"]["LegalName"]["$"], "ORACLE SYSTEMS CORPORATION")


class BondsAPITest(APITestCase):

    # Helper method to create a user
    def create_user(self, username, password):

        self.client.post(path='/register/', data={"username": username, "password": password})

    # Helper method to login as a user
    def login_user(self, username, password):

        login_response = self.client.post(path="/api-token-auth/", data={"username": username, "password": password})
        token = login_response.data.get("token")
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)

    def setUp(self):

        self.client = APIClient()

        # Create and login a test_user_1
        self.create_user("test_user_1", "djy6T6W8ki$")
        self.login_user("test_user_1", "djy6T6W8ki$")

    def test_status_400_returned_when_lei_code_is_invalid(self):

        bond_with_hyphen_in_lei_code = {
            "isin": "FR0000131104",
            "size": 100000000,
            "currency": "EUR",
            "maturity": "2025-02-28",
            "lei": "R0MUWSFPU8MPRO8K5P_3"
        }

        bond_with_lei_code_that_is_too_long = {
            "isin": "FR0000131104",
            "size": 100000000,
            "currency": "EUR",
            "maturity": "2025-02-28",
            "lei": "R0MUWSFPU8MPRO8K5P836"
        }

        response = self.client.post(path="/bonds/", data=bond_with_hyphen_in_lei_code)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, "LEI code is invalid")

        response = self.client.post(path="/bonds/", data=bond_with_lei_code_that_is_too_long)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, "LEI code is invalid")

    def test_status_404_returned_when_entity_doesnt_exist_for_lei_code(self):

        bond_with_non_existing_lei_code = {
            "isin": "FR0000131104",
            "size": 100000000,
            "currency": "EUR",
            "maturity": "2025-02-28",
            "lei": "99999999999999999999"
        }

        response = self.client.post(path="/bonds/", data=bond_with_non_existing_lei_code)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, "Could not find entity for the given LEI code")

    def test_bond_created_successfully_for_lei_code_that_is_valid_and_exists(self):

        bond_with_correct_details = {
            "isin": "FR0000131104",
            "size": 100000000,
            "currency": "EUR",
            "maturity": "2025-02-28",
            "lei": "R0MUWSFPU8MPRO8K5P83"
        }

        response = self.client.post(path="/bonds/", data=bond_with_correct_details)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Bond successfully created.")

        created_bond = Bond.objects.all().last()
        maturity_date = datetime.strptime(bond_with_correct_details["maturity"], "%Y-%m-%d").date()

        self.assertEqual(created_bond.isin, bond_with_correct_details["isin"])
        self.assertEqual(created_bond.size, bond_with_correct_details["size"])
        self.assertEqual(created_bond.currency, bond_with_correct_details["currency"])
        self.assertEqual(created_bond.maturity, maturity_date)
        self.assertEqual(created_bond.lei, bond_with_correct_details["lei"])
        self.assertEqual(created_bond.legal_name, "BNP PARIBAS")
        self.assertEqual(created_bond.user.username, "test_user_1")

    def test_no_bonds_returned_for_user_with_no_bonds(self):

        response = self.client.get(path="/bonds/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_users_bonds_are_returned(self):

        bond_1 = {
            "isin": "FR0000131104",
            "size": 100000000,
            "currency": "EUR",
            "maturity": "2025-02-28",
            "lei": "R0MUWSFPU8MPRO8K5P83"
        }

        bond_2 = {
            "isin": "GB0003HVGHA3",
            "size": 245678,
            "currency": "GBP",
            "maturity": "2022-06-06",
            "lei": "F32G12M10LW6RUUWKX69"
        }

        # Create first bond, then check it is returned correctly from the GET request
        self.client.post(path="/bonds/", data=bond_1)
        response = self.client.get(path="/bonds/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["isin"], bond_1["isin"])

        # Create the second bond, then check both bonds are returned correctly from the GET request
        self.client.post(path="/bonds/", data=bond_2)
        response = self.client.get(path="/bonds/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["isin"], bond_1["isin"])
        self.assertEqual(response.data[1]["isin"], bond_2["isin"])

    def test_only_the_requesting_users_bonds_are_returned(self):

        test_user_1_bond = {
            "isin": "FR0000131104",
            "size": 100000000,
            "currency": "EUR",
            "maturity": "2025-02-28",
            "lei": "R0MUWSFPU8MPRO8K5P83"
        }

        test_user_2_bond = {
            "isin": "GB0003HVGHA3",
            "size": 245678,
            "currency": "GBP",
            "maturity": "2022-06-06",
            "lei": "F32G12M10LW6RUUWKX69"
        }

        # Create bond for test_user_1
        self.client.post(path="/bonds/", data=test_user_1_bond)

        # Create user test_user_2 and login
        self.create_user("test_user_2", "dY6G4FmAkyuS")
        self.login_user("test_user_2", "dY6G4FmAkyuS")

        # Send GET request, and check no bonds are returned
        get_response = self.client.get(path="/bonds/")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data, [])

        # Create bond for test_user_2, and check it is the only bond returned by a GET request
        self.client.post(path="/bonds/", data=test_user_2_bond)
        get_response = self.client.get(path="/bonds/")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(get_response.data), 1)
        self.assertEqual(get_response.data[0]["isin"], "GB0003HVGHA3")

        # Log back into test_user_1, and check test_user_1_bond is the only bond returned
        self.login_user("test_user_1", "djy6T6W8ki$")
        get_response = self.client.get(path="/bonds/")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(get_response.data), 1)
        self.assertEqual(get_response.data[0]["isin"], "FR0000131104")


class RegisterTest(APITestCase):

    def test_user_not_registered_if_username_not_provided(self):

        user_details_no_username_field = {
            "password": "hyT65DhfnE"
        }

        user_details_blank_username_field = {
            "username": "",
            "password": "hyT65DhfnE"
        }

        register_response = self.client.post(path='/register/', data=user_details_no_username_field)
        self.assertEqual(register_response.status_code, 400)
        self.assertEqual(register_response.data, {"username": "required", "password": "required"})

        register_response = self.client.post(path='/register/', data=user_details_blank_username_field)
        self.assertEqual(register_response.status_code, 400)
        self.assertEqual(register_response.data, {"username": "required", "password": "required"})

    def test_user_not_registered_if_password_not_provided(self):

        user_details_no_password_field = {
            "username": "test_user"
        }

        user_details_blank_password_field = {
            "username": "test_user",
            "password": ""
        }

        register_response = self.client.post(path='/register/', data=user_details_no_password_field)
        self.assertEqual(register_response.status_code, 400)
        self.assertEqual(register_response.data, {"username": "required", "password": "required"})

        register_response = self.client.post(path='/register/', data=user_details_blank_password_field)
        self.assertEqual(register_response.status_code, 400)
        self.assertEqual(register_response.data, {"username": "required", "password": "required"})

    def test_user_with_valid_credentials_is_registered(self):

        user_details_valid = {
            "username": "test_user",
            "password": "hyT65DhfnE"
        }

        register_response = self.client.post(path='/register/', data=user_details_valid)
        self.assertEqual(register_response.status_code, 200)
        self.assertEqual(register_response.data, "User created successfully")

        created_user = User.objects.all().last()
        self.assertEqual(created_user.username, "test_user")

    def test_user_cannot_register_with_an_existing_username(self):

        user_details_valid = {
            "username": "test_user",
            "password": "hyT65DhfnE"
        }

        self.client.post(path='/register/', data=user_details_valid)
        register_response = self.client.post(path='/register/', data=user_details_valid)
        self.assertEqual(register_response.status_code, 409)
        self.assertEqual(register_response.data, "Username already exists, please provide another.")
