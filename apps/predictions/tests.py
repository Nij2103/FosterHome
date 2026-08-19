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

    def test_viewer_must_create_family_before_predicting(self):
        """Viewer without created families has 0 family options; only viewer-created families appear."""
        self.client.login(username="viewer_match", password="password123")
        res_get = self.client.get(reverse("predictions:create"))
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.context["user_family_count"], 0)
        self.assertTrue(res_get.context["is_viewer"])

        # Create a family as viewer_user
        viewer_family = FosterFamily.objects.create(
            family_name="ViewerFamily",
            primary_applicant_name="John Viewer",
            state="Texas",
            capacity=2,
            is_active=True,
            created_by=self.viewer_user,
        )

        res_get2 = self.client.get(reverse("predictions:create"))
        self.assertEqual(res_get2.status_code, 200)
        self.assertEqual(res_get2.context["user_family_count"], 1)

        # Form choices for family should only include viewer_family
        form_choices = list(res_get2.context["form"].fields["family"].queryset)
        self.assertIn(viewer_family, form_choices)
        self.assertNotIn(self.family_suitable, form_choices)

    def test_prediction_blocked_when_profiles_incomplete(self):
        """Predictions must be blocked when child or family profile is under 100% complete."""
        self.client.login(username="caseworker_match", password="password123")

        # Post prediction request with incomplete child and family profiles
        response = self.client.post(
            reverse("predictions:create"),
            {"child": self.child_normal.pk, "family": self.family_suitable.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profile must reach 100% completion before running predictions")

    def test_prediction_successful_when_profiles_100_percent_complete(self):
        """Prediction executes successfully when child & family profiles have 100% completion."""
        self.client.login(username="caseworker_match", password="password123")

        # Make child 100% complete
        self.child_normal.languages_spoken = "English"
        self.child_normal.special_needs = "Physical disability"
        self.child_normal.behavioral_support_level = "Low"
        self.child_normal.mental_health_support_level = "Low"
        self.child_normal.medical_needs_level = "Low"
        self.child_normal.sibling_group_size = 1
        self.child_normal.needs_sibling_placement = "No"
        self.child_normal.previous_foster_placements = 0
        self.child_normal.trauma_severity_level = "Low"
        self.child_normal.school_attendance_status = "Regular"
        self.child_normal.save()

        # Make family 100% complete
        self.family_suitable.languages_spoken = "English"
        self.family_suitable.marital_status = "Married Couple"
        self.family_suitable.household_composition = "One child"
        self.family_suitable.preferred_age_group = "6–10"
        self.family_suitable.preferred_gender = "Female"
        self.family_suitable.preferred_special_needs = "Physical Disability"
        self.family_suitable.accept_sibling_placements = "Yes"
        self.family_suitable.max_sibling_group_accepted = 2
        self.family_suitable.behavioral_support_capacity = "Medium"
        self.family_suitable.mental_health_support_capacity = "Medium"
        self.family_suitable.medical_support_capacity = "Medium"
        self.family_suitable.parenting_experience_years = 5
        self.family_suitable.previous_foster_placements_count = 2
        self.family_suitable.successful_foster_placements_count = 2
        self.family_suitable.housing_stability = "High"
        self.family_suitable.family_support_network = "High"
        self.family_suitable.long_term_placement_willingness = "Yes"
        self.family_suitable.therapy_support_availability = "Yes"
        self.family_suitable.save()

        response = self.client.post(
            reverse("predictions:create"),
            {"child": self.child_normal.pk, "family": self.family_suitable.pk},
        )
        self.assertEqual(response.status_code, 302)  # Redirect to detail page

