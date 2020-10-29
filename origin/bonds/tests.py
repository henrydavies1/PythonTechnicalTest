from rest_framework.test import APISimpleTestCase
from django.test import TestCase

from .views import get_legal_name


class HelloWorld(APISimpleTestCase):

    def test_root(self):

        resp = self.client.get("/")
        assert resp.status_code == 200


class GetLegalNameTestCase(TestCase):

    def test_correct_legal_name_returned(self):

        self.assertEqual(get_legal_name("HWUPKR0MPOU8FGXBT394"), "APPLE INC.")
        self.assertEqual(get_legal_name("213800JSUFNZLZLCVJ25"), "JOHN LEWIS PLC")
        self.assertEqual(get_legal_name("549300FL0LHI0TEZ8V48"), "ORACLE SYSTEMS CORPORATION")

    def test_none_returned_if_an_entity_is_not_found_for_the_lei_code(self):

        self.assertEqual(get_legal_name("HWUPKR0MPOU8FGXBT39"), None)
        self.assertEqual(get_legal_name("HWUPKR0MPOU8FGXBT3944"), None)
        self.assertEqual(get_legal_name("99999999999999999999"), None)
