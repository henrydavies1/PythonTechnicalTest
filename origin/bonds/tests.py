from rest_framework.test import APISimpleTestCase, APITestCase
from django.test import TestCase
from datetime import datetime

from .views import get_gleif_response
from .models import Bond


class HelloWorld(APISimpleTestCase):

    def test_root(self):

        resp = self.client.get("/")
        assert resp.status_code == 200


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
