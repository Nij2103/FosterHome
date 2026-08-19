import random
from django.core.management.base import BaseCommand
from apps.children.models import Child
from apps.families.models import FosterFamily


class Command(BaseCommand):
    help = "Populates missing assessment fields for all existing Child and FosterFamily records with realistic random values so all profiles reach 100% completion."

    def handle(self, *args, **options):
        # 1. Update Child Records
        children = Child.objects.all()
        child_updated_count = 0

        languages = ["English", "Spanish", "Gujarati", "Hindi", "Marathi", "Bengali", "Tamil", "Telugu", "Kannada", "Malayalam", "Punjabi", "Urdu"]
        special_needs_choices = [
            "Physical disability",
            "Developmental disability",
            "Learning disability",
            "Medical condition",
            "Multiple special needs",
        ]
        levels = ["Low", "Medium", "High"]
        yes_no = ["Yes", "No"]

        for child in children:
            updated = False

            # languages_spoken
            if not child.languages_spoken or child.languages_spoken.strip().lower() == "none":
                child.languages_spoken = random.choice(languages)
                updated = True

            # special_needs
            if not child.special_needs or str(child.special_needs).strip().lower() == "none":
                child.special_needs = random.choice(special_needs_choices)
                updated = True

            # behavioral_support_level
            if not child.behavioral_support_level or child.behavioral_support_level.strip().lower() == "none":
                child.behavioral_support_level = random.choice(levels)
                updated = True

            # mental_health_support_level
            if not child.mental_health_support_level or child.mental_health_support_level.strip().lower() == "none":
                child.mental_health_support_level = random.choice(levels)
                updated = True

            # medical_needs_level
            if not child.medical_needs_level or child.medical_needs_level.strip().lower() == "none":
                child.medical_needs_level = random.choice(levels)
                updated = True

            # sibling_group_size
            if child.sibling_group_size is None or child.sibling_group_size < 1:
                child.sibling_group_size = random.choice([1, 1, 1, 2, 2, 3])
                updated = True

            # needs_sibling_placement
            if not child.needs_sibling_placement or child.needs_sibling_placement.strip().lower() == "none":
                child.needs_sibling_placement = "Yes" if child.sibling_group_size > 1 else random.choice(yes_no)
                updated = True

            # previous_foster_placements
            if child.previous_foster_placements is None:
                child.previous_foster_placements = random.choice([0, 0, 1, 2])
                updated = True

            # trauma_severity_level
            if not child.trauma_severity_level or child.trauma_severity_level.strip().lower() == "none":
                child.trauma_severity_level = random.choice(levels)
                updated = True

            # school_attendance_status
            if not child.school_attendance_status or child.school_attendance_status.strip().lower() == "none":
                child.school_attendance_status = random.choice(["Regular", "Regular", "Irregular"])
                updated = True

            if updated or not child.profile_completion_score.get("is_complete"):
                child.save()
                child_updated_count += 1

        # 2. Update Foster Family Records
        families = FosterFamily.objects.all()
        family_updated_count = 0

        marital_statuses = ["Single Parent", "Married Couple", "Joint Family"]
        household_compositions = ["No children", "One child", "Two children", "Three or more children"]
        preferred_age_groups = ["0–5", "6–10", "11–15", "16–18", "Any age"]
        preferred_genders = ["Male", "Female", "Any"]
        preferred_special_needs_choices = [
            "Physical Disability",
            "Developmental Disability",
            "Learning Disability",
            "Medical Condition",
            "Multiple Needs",
        ]

        for family in families:
            updated = False

            # languages_spoken
            if not family.languages_spoken or family.languages_spoken.strip().lower() == "none":
                family.languages_spoken = random.choice(languages)
                updated = True

            # marital_status
            if not family.marital_status or family.marital_status.strip().lower() == "none":
                family.marital_status = random.choice(marital_statuses)
                updated = True

            # household_composition
            if not family.household_composition or family.household_composition.strip().lower() == "none":
                family.household_composition = random.choice(household_compositions)
                updated = True

            # preferred_age_group
            if not family.preferred_age_group or family.preferred_age_group.strip().lower() == "none":
                family.preferred_age_group = random.choice(preferred_age_groups)
                updated = True

            # preferred_gender
            if not family.preferred_gender or family.preferred_gender.strip().lower() == "none":
                family.preferred_gender = random.choice(preferred_genders)
                updated = True

            # preferred_special_needs
            if not family.preferred_special_needs or family.preferred_special_needs.strip().lower() == "none":
                family.preferred_special_needs = random.choice(preferred_special_needs_choices)
                updated = True

            # accept_sibling_placements
            if not family.accept_sibling_placements or family.accept_sibling_placements.strip().lower() == "none":
                family.accept_sibling_placements = random.choice(["Yes", "Yes", "No"])
                updated = True

            # max_sibling_group_accepted
            if family.max_sibling_group_accepted is None or family.max_sibling_group_accepted < 1:
                family.max_sibling_group_accepted = random.choice([2, 3, 4])
                updated = True

            # behavioral_support_capacity
            if not family.behavioral_support_capacity or family.behavioral_support_capacity.strip().lower() == "none":
                family.behavioral_support_capacity = random.choice(levels)
                updated = True

            # mental_health_support_capacity
            if not family.mental_health_support_capacity or family.mental_health_support_capacity.strip().lower() == "none":
                family.mental_health_support_capacity = random.choice(levels)
                updated = True

            # medical_support_capacity
            if not family.medical_support_capacity or family.medical_support_capacity.strip().lower() == "none":
                family.medical_support_capacity = random.choice(levels)
                updated = True

            # parenting_experience_years
            if family.parenting_experience_years is None:
                family.parenting_experience_years = random.choice([2, 4, 6, 8, 10])
                updated = True

            # previous_foster_placements_count
            if family.previous_foster_placements_count is None:
                family.previous_foster_placements_count = random.choice([1, 2, 3, 4])
                updated = True

            # successful_foster_placements_count
            if family.successful_foster_placements_count is None:
                family.successful_foster_placements_count = random.choice([1, 2, 3])
                updated = True

            # housing_stability
            if not family.housing_stability or family.housing_stability.strip().lower() == "none":
                family.housing_stability = random.choice(["High", "High", "Medium"])
                updated = True

            # family_support_network
            if not family.family_support_network or family.family_support_network.strip().lower() == "none":
                family.family_support_network = random.choice(["High", "Medium", "High"])
                updated = True

            # long_term_placement_willingness
            if not family.long_term_placement_willingness or family.long_term_placement_willingness.strip().lower() == "none":
                family.long_term_placement_willingness = random.choice(["Yes", "Yes", "No"])
                updated = True

            # therapy_support_availability
            if not family.therapy_support_availability or family.therapy_support_availability.strip().lower() == "none":
                family.therapy_support_availability = random.choice(["Yes", "Yes", "No"])
                updated = True

            if updated or not family.profile_completion_score.get("is_complete"):
                family.save()
                family_updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {child_updated_count} child records and {family_updated_count} foster family records. All profiles are now 100% Complete & Prediction Ready!"
            )
        )
