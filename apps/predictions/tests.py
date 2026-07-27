"""
apps.predictions.tests

Unit tests for the Smart Matching Recommendations engine (ml/inference/matching.py)
and the role-gated AJAX endpoint (predictions:matching).
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Profile
from apps.children.models import Child
from apps.families.models import FosterFamily
from ml.inference.matching import find_suitable_matches_for_child, find_suitable_matches_for_family


class SmartMatchingTestCase(TestCase):

    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_superuser(username="admin_match", password="password123")
        self.caseworker_user = User.objects.create_user(username="caseworker_match", password="password123")
        self.caseworker_user.profile.role = Profile.Role.CASEWORKER
        self.caseworker_user.profile.save()

        self.viewer_user = User.objects.create_user(username="viewer_match", password="password123")
        self.viewer_user.profile.role = Profile.Role.VIEWER
        self.viewer_user.profile.save()

        # Create test children
        self.child_normal = Child.objects.create(
            first_name="Alice",
            age=8,
            gender="F",
            state="Texas",
            special_needs=False,
            sibling_group_size=1,
            behavioral_notes_score=0.2,
            education_level="Elementary",
            time_in_care_months=4,
        )
        self.child_special = Child.objects.create(
            first_name="Bob",
            age=12,
            gender="M",
            state="Texas",
            special_needs=True,
            sibling_group_size=1,
            behavioral_notes_score=0.4,
            education_level="Middle School",
            time_in_care_months=12,
        )


        # Create test families
        self.family_suitable = FosterFamily.objects.create(
            family_name="SmithFamily",
            state="Texas",
            capacity=3,
            current_occupancy=0,
            experience_years=6,
            accepts_special_needs=True,
            accepts_sibling_groups=True,
            is_active=True,
        )
        self.family_full = FosterFamily.objects.create(
            family_name="FullFamily",
            state="Texas",
            capacity=2,
            current_occupancy=2,  # FULL!
            experience_years=5,
            accepts_special_needs=True,
            accepts_sibling_groups=True,
            is_active=True,
        )
        self.family_no_special = FosterFamily.objects.create(
            family_name="NoSpecialFamily",
            state="Texas",
            capacity=3,
            current_occupancy=0,
            experience_years=4,
            accepts_special_needs=False,  # NO SPECIAL NEEDS
            accepts_sibling_groups=True,
            is_active=True,
        )

    def test_find_suitable_matches_for_child_filters_unsuitable_families(self):
        """Full families and special needs mismatches must be filtered out."""
        matches = find_suitable_matches_for_child(self.child_special)
        family_ids = [m["id"] for m in matches]

        # Suitable family should be included
        self.assertIn(self.family_suitable.id, family_ids)

        # Full family must be excluded
        self.assertNotIn(self.family_full.id, family_ids)

        # Family that doesn't accept special needs must be excluded for Bob (special_needs=True)
        self.assertNotIn(self.family_no_special.id, family_ids)

    def test_find_suitable_matches_for_family(self):
        """Family with no capacity returns empty matches."""
        matches = find_suitable_matches_for_family(self.family_full)
        self.assertEqual(len(matches), 0)

    def test_matching_endpoint_permission_gating(self):
        """Viewers get 403 Forbidden; Admin and Caseworker get 200 JSON response."""
        # Viewer -> 403
        self.client.login(username="viewer_match", password="password123")
        res_viewer = self.client.get(reverse("predictions:matching"), {"child_id": self.child_normal.id})
        self.assertEqual(res_viewer.status_code, 403)

        # Caseworker -> 200 JSON
        self.client.login(username="caseworker_match", password="password123")
        res_cw = self.client.get(reverse("predictions:matching"), {"child_id": self.child_normal.id})
        self.assertEqual(res_cw.status_code, 200)
        json_data = res_cw.json()
        self.assertEqual(json_data["mode"], "child")
        self.assertGreaterEqual(len(json_data["matches"]), 1)

        # Admin -> 200 JSON
        self.client.login(username="admin_match", password="password123")
        res_admin = self.client.get(reverse("predictions:matching"), {"child_id": self.child_normal.id})
        self.assertEqual(res_admin.status_code, 200)
