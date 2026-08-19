"""
apps.accounts.tests

Unit tests for the Foster Care Placement Predictor Role System.
Verifies:
1. Self-registration strictly creates VIEWER accounts (privilege escalation prevention).
2. `can_edit` template filter correctly gates Admin/Caseworker vs Viewer/Anonymous.
3. Mutation endpoints enforce 403 Forbidden when accessed directly by Viewers.
4. Viewer accounts retain access to Prediction creation.
5. Admin and Caseworker accounts have full access to mutation endpoints.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Profile
from apps.accounts.templatetags.role_tags import can_edit, is_viewer
from apps.children.models import Child
from apps.families.models import FosterFamily


class RoleSystemTestCase(TestCase):

    def setUp(self):
        # Create users for each role
        self.admin_user = User.objects.create_superuser(username="admin_test", password="password123")
        self.caseworker_user = User.objects.create_user(username="caseworker_test", password="password123")
        self.caseworker_user.profile.role = Profile.Role.CASEWORKER
        self.caseworker_user.profile.save()

        self.viewer_user = User.objects.create_user(username="viewer_test", password="password123")
        # Ensure viewer_user is viewer role
        self.viewer_user.profile.role = Profile.Role.VIEWER
        self.viewer_user.profile.save()

        # Seed sample child and family for mutation tests
        self.child = Child.objects.create(
            first_name="TestChild",
            age=10,
            gender="M",
            state="Texas",
            special_needs=False,
            sibling_group_size=1,
            behavioral_notes_score=0.5,
            education_level="Elementary",
            time_in_care_months=6,
        )

        self.family = FosterFamily.objects.create(
            family_name="TestFamily",
            state="Texas",
            capacity=3,
            current_occupancy=0,
            experience_years=5,
            accepts_special_needs=True,
            accepts_sibling_groups=True,
            home_type="single_family",
        )

    def test_self_registration_creates_viewer_role(self):
        """Self-registration must strictly assign Profile.Role.VIEWER."""
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new_registered_user",
                "email": "newuser@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirects after successful registration
        new_user = User.objects.get(username="new_registered_user")
        self.assertEqual(new_user.profile.role, Profile.Role.VIEWER)
        self.assertTrue(new_user.profile.is_viewer)
        self.assertFalse(new_user.profile.is_admin)
        self.assertFalse(new_user.profile.is_caseworker)

    def test_can_edit_template_filter(self):
        """can_edit filter must be True for Admin/Caseworker/Superuser, False for Viewer/Anonymous."""
        self.assertTrue(can_edit(self.admin_user))
        self.assertTrue(can_edit(self.caseworker_user))
        self.assertFalse(can_edit(self.viewer_user))
        self.assertFalse(can_edit(None))
        self.assertTrue(is_viewer(self.viewer_user))
        self.assertFalse(is_viewer(self.admin_user))

    def test_viewer_blocked_from_restricted_mutation_urls(self):
        """Viewers attempting restricted mutation access receive HTTP 403 Forbidden."""
        self.client.login(username="viewer_test", password="password123")

        # Create Placement (Restricted to Admin & Caseworker)
        res1 = self.client.post(reverse("placements:create"), {"child": self.child.id, "family": self.family.id})
        self.assertEqual(res1.status_code, 403)

    def test_viewer_can_add_child_and_family(self):
        """Viewers can access Child and Foster Family creation forms."""
        self.client.login(username="viewer_test", password="password123")
        res_child = self.client.get(reverse("children:create"))
        self.assertEqual(res_child.status_code, 200)

        res_family = self.client.get(reverse("families:create"))
        self.assertEqual(res_family.status_code, 200)

    def test_viewer_can_access_prediction_creation(self):
        """Viewers must retain permission to request predictions."""
        self.client.login(username="viewer_test", password="password123")
        response = self.client.get(reverse("predictions:create"))
        self.assertEqual(response.status_code, 200)

    def test_admin_and_caseworker_can_access_mutation_views(self):
        """Admin and Caseworker can access creation forms."""
        # Caseworker
        self.client.login(username="caseworker_test", password="password123")
        res_cw = self.client.get(reverse("children:create"))
        self.assertEqual(res_cw.status_code, 200)

        # Admin
        self.client.login(username="admin_test", password="password123")
        res_admin = self.client.get(reverse("children:create"))
        self.assertEqual(res_admin.status_code, 200)
