import json
import string
import random

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Organization, PrincipalInvestigator, CostUnit


User = get_user_model()


class BaseTestCase(TestCase):
    def create_user(self, email='test@test.io', password='foo-bar',
                    is_staff=True):
        user = User.objects.create_user(email=email, password=password,
                                        is_staff=is_staff)
        user.save()
        return user

    def login(self, email='test@test.io', password='foo-bar'):
        self.client.login(email=email, password=password)

    def _get_random_name(self, len=10):
        return ''.join(random.SystemRandom().choice(
            string.ascii_lowercase + string.digits
        ) for _ in range(len))


class BaseAPITestCase(APITestCase):
    def create_user(self, email='test@test.io', password='foo-bar',
                    is_staff=True):
        user = User.objects.create_user(email=email, password=password,
                                        is_staff=is_staff)
        user.save()
        return user

    def login(self, email='test@test.io', password='foo-bar'):
        self.client.login(email=email, password=password)


# Models

class OrganizationTest(TestCase):
    def setUp(self):
        self.organization = Organization(name='Apple')

    def test_organization_name(self):
        self.assertTrue(isinstance(self.organization, Organization))
        self.assertEqual(self.organization.__str__(), self.organization.name)


class PrincipalInvestigatorTest(TestCase):
    def setUp(self):
        self.org = Organization(name='Apple')
        self.pi = PrincipalInvestigator(name='Tim Cook', organization=self.org)

    def test_pi_name(self):
        self.assertTrue(isinstance(self.org, Organization))
        self.assertTrue(isinstance(self.pi, PrincipalInvestigator))
        self.assertEqual(
            self.pi.__str__(),
            '%s (%s)' % (self.pi.name, self.org.name)
        )


class CostUnitTest(TestCase):
    def setUp(self):
        self.org = Organization(name='Apple')
        self.pi = PrincipalInvestigator(name='Tim Cook', organization=self.org)
        self.cost_unit = CostUnit(name='K', pi=self.pi)

    def test_cost_unit_name(self):
        self.assertTrue(isinstance(self.org, Organization))
        self.assertTrue(isinstance(self.pi, PrincipalInvestigator))
        self.assertTrue(isinstance(self.cost_unit, CostUnit))
        self.assertEqual(
            self.cost_unit.__str__(),
            '%s (%s: %s)' % (
                self.cost_unit.name, self.pi.organization.name, self.pi.name
            )
        )


# Views

class IndexViewTest(TestCase):
    def setUp(self):
        User.objects.create_user(email='foo@bar.io', password='foo-foo')

    def test_get(self):
        self.client.login(email='foo@bar.io', password='foo-foo')
        response = self.client.get(reverse('index'), follow=True)
        self.assertEqual(response.status_code, 200)


class NavigationTreeTest(TestCase):
    def setUp(self):
        User.objects.create_user(
            email='admin@bar.io', password='foo-foo', is_staff=True,
        )

        User.objects.create_user(
            email='user@bar.io', password='foo-foo', is_staff=False,
        )

    def test_navigation_tree_admin(self):
        self.client.login(email='admin@bar.io', password='foo-foo')
        response = self.client.get(reverse('get_navigation_tree'))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(
            len(json.loads(str(response.content, 'utf-8'))['children']), 2,
        )

    def test_navigation_tree_user(self):
        self.client.login(email='user@bar.io', password='foo-foo')
        response = self.client.get(reverse('get_navigation_tree'))
        tabs = [
            t['text']
            for t in json.loads(str(response.content, 'utf-8'))['children']
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(tabs, ['Requests', 'Libraries & Samples'])
