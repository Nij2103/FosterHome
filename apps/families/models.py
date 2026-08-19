"""
families.models

Updated schema for Foster Family records including mandatory primary applicant names,
contact information, home capacity, occupants, license status, background clearances,
assigned licensing worker, identity document (Aadhaar/ID), and optional preferences.
"""

from django.conf import settings
from django.db import models


class FosterFamily(models.Model):
    class HomeType(models.TextChoices):
        URBAN = "urban", "Urban"
        SUBURBAN = "suburban", "Suburban"
        RURAL = "rural", "Rural"

    class LicenseStatus(models.TextChoices):
        ACTIVE = "Active", "Active"
        PENDING = "Pending", "Pending"
        SUSPENDED = "Suspended", "Suspended"
        EXPIRED = "Expired", "Expired"

    class ClearanceStatus(models.TextChoices):
        CLEARED = "Cleared / Verified", "Cleared / Verified"
        PENDING = "Pending Review", "Pending Review"
        INCOMPLETE = "Incomplete", "Incomplete"

    class Language(models.TextChoices):
        NONE = "None", "None"
        ENGLISH = "English", "English"
        HINDI = "Hindi", "Hindi"
        GUJARATI = "Gujarati", "Gujarati"
        MARATHI = "Marathi", "Marathi"
        BENGALI = "Bengali", "Bengali"
        TAMIL = "Tamil", "Tamil"
        TELUGU = "Telugu", "Telugu"
        KANNADA = "Kannada", "Kannada"
        MALAYALAM = "Malayalam", "Malayalam"
        PUNJABI = "Punjabi", "Punjabi"
        URDU = "Urdu", "Urdu"
        OTHER = "Other", "Other"

    class MaritalStatusChoices(models.TextChoices):
        NONE = "None", "None"
        SINGLE_PARENT = "Single Parent", "Single Parent"
        MARRIED_COUPLE = "Married Couple", "Married Couple"
        JOINT_FAMILY = "Joint Family", "Joint Family"
        OTHER = "Other", "Other"

    class HouseholdCompositionChoices(models.TextChoices):
        NONE = "None", "None"
        NO_CHILDREN = "No children", "No children"
        ONE_CHILD = "One child", "One child"
        TWO_CHILDREN = "Two children", "Two children"
        THREE_OR_MORE = "Three or more children", "Three or more children"

    class PreferredAgeGroupChoices(models.TextChoices):
        NONE = "None", "None"
        AGE_0_5 = "0–5", "0–5"
        AGE_6_10 = "6–10", "6–10"
        AGE_11_15 = "11–15", "11–15"
        AGE_16_18 = "16–18", "16–18"
        ANY_AGE = "Any age", "Any age"

    class PreferredGenderChoices(models.TextChoices):
        NONE = "None", "None"
        MALE = "Male", "Male"
        FEMALE = "Female", "Female"
        ANY = "Any", "Any"

    class YesNoNoneChoices(models.TextChoices):
        NONE = "None", "None"
        YES = "Yes", "Yes"
        NO = "No", "No"

    class CapacityLevelChoices(models.TextChoices):
        NONE = "None", "None"
        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"

    class PreferredSpecialNeedsChoices(models.TextChoices):
        NONE = "None", "None"
        PHYSICAL = "Physical Disability", "Physical Disability"
        DEVELOPMENTAL = "Developmental Disability", "Developmental Disability"
        LEARNING = "Learning Disability", "Learning Disability"
        MEDICAL = "Medical Condition", "Medical Condition"
        MULTIPLE = "Multiple Needs", "Multiple Needs"

    # --- MANDATORY / REQUIRED FIELDS ---
    family_name = models.CharField(
        max_length=150,
        help_text="Family identifier (e.g. Johnson Family)",
    )
    primary_applicant_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Full legal name(s) of the primary foster parent(s)",
    )
    phone_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Primary phone number",
    )
    email_address = models.EmailField(
        blank=True,
        default="",
        help_text="Contact email address",
    )
    residential_address = models.TextField(
        blank=True,
        default="",
        help_text="Full residential street address",
    )
    capacity = models.PositiveSmallIntegerField(
        default=2,
        help_text="Legal limit of foster children this home is licensed to host at once.",
    )
    current_occupants = models.TextField(
        blank=True,
        default="",
        help_text="Full names of all permanent household residents for background clearance.",
    )

    license_status = models.CharField(
        max_length=50,
        choices=LicenseStatus.choices,
        default=LicenseStatus.ACTIVE,
        help_text="Current foster licensing status",
    )
    licensing_agency = models.CharField(
        max_length=150,
        blank=True,
        default="",
        help_text="Licensing agency name",
    )
    license_expiration = models.DateField(
        null=True,
        blank=True,
        help_text="Expiration date of foster care license",
    )

    background_clearance_status = models.CharField(
        max_length=50,
        choices=ClearanceStatus.choices,
        default=ClearanceStatus.CLEARED,
        help_text="Status of criminal background check, fingerprinting & abuse registry checks",
    )
    licensing_worker_name = models.CharField(
        max_length=150,
        blank=True,
        default="",
        help_text="Assigned agency case manager overseeing this foster home",
    )
    identity_doc_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Official ID document number (Driver License / Passport / Govt ID)",
    )
    identity_document = models.ImageField(
        upload_to="identity_documents/",
        null=True,
        blank=True,
        help_text="Official Identity Document photograph / scan",
    )

    languages_spoken = models.CharField(
        max_length=100,
        choices=Language.choices,
        default=Language.NONE,
        help_text="Primary language spoken in the home",
    )

    # --- STRUCTURED PREFERENCES & PROFILE FIELDS ---
    marital_status = models.CharField(
        max_length=50,
        choices=MaritalStatusChoices.choices,
        default=MaritalStatusChoices.NONE,
        help_text="Marital status",
    )
    household_composition = models.CharField(
        max_length=50,
        choices=HouseholdCompositionChoices.choices,
        default=HouseholdCompositionChoices.NONE,
        help_text="Household composition",
    )
    preferred_age_group = models.CharField(
        max_length=50,
        choices=PreferredAgeGroupChoices.choices,
        default=PreferredAgeGroupChoices.NONE,
        help_text="Preferred child age group",
    )
    preferred_gender = models.CharField(
        max_length=50,
        choices=PreferredGenderChoices.choices,
        default=PreferredGenderChoices.NONE,
        help_text="Preferred child gender",
    )
    preferred_special_needs = models.CharField(
        max_length=50,
        choices=PreferredSpecialNeedsChoices.choices,
        default=PreferredSpecialNeedsChoices.NONE,
        help_text="Preferred special needs category",
    )
    accept_sibling_placements = models.CharField(
        max_length=10,
        choices=YesNoNoneChoices.choices,
        default=YesNoNoneChoices.NONE,
        help_text="Willingness to accept sibling placements",
    )
    max_sibling_group_accepted = models.PositiveSmallIntegerField(
        default=0,
        help_text="Maximum sibling group size accepted",
    )
    special_trainings = models.TextField(
        blank=True,
        default="",
        help_text="Special training & certifications (stored as comma-separated values)",
    )
    references_info = models.TextField(
        blank=True,
        default="",
        help_text="Personal and professional references submitted during home study",
    )

    # --- FAMILY PLACEMENT ASSESSMENT FIELDS ---
    behavioral_support_capacity = models.CharField(
        max_length=20,
        choices=CapacityLevelChoices.choices,
        default=CapacityLevelChoices.NONE,
        help_text="Behavioral support capacity",
    )
    mental_health_support_capacity = models.CharField(
        max_length=20,
        choices=CapacityLevelChoices.choices,
        default=CapacityLevelChoices.NONE,
        help_text="Mental health support capacity",
    )
    medical_support_capacity = models.CharField(
        max_length=20,
        choices=CapacityLevelChoices.choices,
        default=CapacityLevelChoices.NONE,
        help_text="Medical support capacity",
    )
    parenting_experience_years = models.PositiveSmallIntegerField(
        default=0,
        help_text="Parenting experience in years",
    )
    previous_foster_placements_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="Number of previous foster placements hosted",
    )
    successful_foster_placements_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="Number of successful foster placements",
    )
    housing_stability = models.CharField(
        max_length=20,
        choices=CapacityLevelChoices.choices,
        default=CapacityLevelChoices.NONE,
        help_text="Housing stability rating",
    )
    family_support_network = models.CharField(
        max_length=20,
        choices=CapacityLevelChoices.choices,
        default=CapacityLevelChoices.NONE,
        help_text="Family support network rating",
    )
    long_term_placement_willingness = models.CharField(
        max_length=10,
        choices=YesNoNoneChoices.choices,
        default=YesNoNoneChoices.NONE,
        help_text="Long-term placement willingness",
    )
    therapy_support_availability = models.CharField(
        max_length=10,
        choices=YesNoNoneChoices.choices,
        default=YesNoNoneChoices.NONE,
        help_text="Therapy / counseling support availability",
    )

    # --- ML & SYSTEM ATTRIBUTES ---
    state = models.CharField(max_length=100, default="Texas", db_index=True)
    current_occupancy = models.PositiveSmallIntegerField(default=0)
    experience_years = models.PositiveSmallIntegerField(
        default=3,
        help_text="Years this family has been an active foster placement.",
    )
    accepts_special_needs = models.BooleanField(default=False)
    accepts_sibling_groups = models.BooleanField(default=False)
    home_type = models.CharField(
        max_length=20,
        choices=HomeType.choices,
        default=HomeType.SUBURBAN,
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Inactive families are excluded from new placement recommendations.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="families_created",
        help_text="User who registered/added this foster family record",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Foster families"
        indexes = [
            models.Index(fields=["state", "is_active"]),
        ]

    def __str__(self):
        return f"{self.family_name} ({self.primary_applicant_name})"

    @property
    def available_slots(self):
        return max(self.capacity - self.current_occupancy, 0)

    @property
    def profile_completion_score(self) -> dict:
        def _is_completed(val) -> bool:
            if val is None:
                return False
            s_val = str(val).strip()
            if not s_val or s_val.lower() == "none":
                return False
            return True

        checks = [
            ("Languages Spoken", _is_completed(self.languages_spoken)),
            ("Marital Status", _is_completed(self.marital_status)),
            ("Household Composition", _is_completed(self.household_composition)),
            ("Preferred Child Age Group", _is_completed(self.preferred_age_group)),
            ("Preferred Gender", _is_completed(self.preferred_gender)),
            ("Preferred Special Needs Category", _is_completed(self.preferred_special_needs)),
            ("Accept Sibling Placements", _is_completed(self.accept_sibling_placements)),
            ("Max Sibling Group Accepted", self.max_sibling_group_accepted is not None),
            ("Behavioral Support Capacity", _is_completed(self.behavioral_support_capacity)),
            ("Mental Health Support Capacity", _is_completed(self.mental_health_support_capacity)),
            ("Medical Support Capacity", _is_completed(self.medical_support_capacity)),
            ("Parenting Experience", self.parenting_experience_years is not None),
            ("Previous Foster Placements", self.previous_foster_placements_count is not None),
            ("Successful Foster Placements", self.successful_foster_placements_count is not None),
            ("Housing Stability", _is_completed(self.housing_stability)),
            ("Family Support Network", _is_completed(self.family_support_network)),
            ("Long-Term Placement Willingness", _is_completed(self.long_term_placement_willingness)),
            ("Therapy Support Availability", _is_completed(self.therapy_support_availability)),
        ]

        completed = sum(1 for name, val in checks if val)
        total = len(checks)
        pct = int(round((completed / total) * 100))
        is_complete = (pct == 100)

        if is_complete:
            badge_class = "bg-success"
            bar_class = "bg-success"
            status_label = "Complete"
        else:
            badge_class = "bg-warning text-dark"
            bar_class = "bg-warning"
            status_label = "Incomplete"

        missing = [name for name, val in checks if not val]

        return {
            "percentage": pct,
            "completed_count": completed,
            "total_count": total,
            "badge_class": badge_class,
            "bar_class": bar_class,
            "status_label": status_label,
            "is_complete": is_complete,
            "missing_fields": missing,
        }
