"""
children.models

Updated schema for Child welfare records including mandatory full name, DOB,
legal status, caseworker assignment, emergency medical details, photo, and
optional background case history & accommodation details.
"""

from django.db import models


class Child(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    class LegalStatus(models.TextChoices):
        TEMPORARY_CUSTODY = "Temporary Custody", "Temporary Custody"
        PERMANENT_WARD = "Permanent Ward", "Permanent Ward"
        VOLUNTARY_PLACEMENT = "Voluntary Placement", "Voluntary Placement"
        COURT_ORDERED = "Court-Ordered", "Court-Ordered"
        UNDER_INVESTIGATION = "Under Investigation", "Under Investigation"

    class BloodGroup(models.TextChoices):
        UNKNOWN = "Unknown", "Unknown / Not Tested"
        A_POSITIVE = "A+", "A+"
        A_NEGATIVE = "A-", "A-"
        B_POSITIVE = "B+", "B+"
        B_NEGATIVE = "B-", "B-"
        AB_POSITIVE = "AB+", "AB+"
        AB_NEGATIVE = "AB-", "AB-"
        O_POSITIVE = "O+", "O+"
        O_NEGATIVE = "O-", "O-"

    class Language(models.TextChoices):
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

    class SpecialNeedsType(models.TextChoices):
        NONE = "None", "None"
        PHYSICAL = "Physical disability", "Physical disability"
        DEVELOPMENTAL = "Developmental disability", "Developmental disability"
        LEARNING = "Learning disability", "Learning disability"
        MEDICAL = "Medical condition", "Medical condition"
        MULTIPLE = "Multiple special needs", "Multiple special needs"

    class SupportLevel(models.TextChoices):
        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"

    class YesNoChoices(models.TextChoices):
        YES = "Yes", "Yes"
        NO = "No", "No"

    class SchoolAttendanceStatus(models.TextChoices):
        NONE = "None", "None"
        REGULAR = "Regular", "Regular"
        IRREGULAR = "Irregular", "Irregular"
        NOT_ENROLLED = "Not Enrolled", "Not Enrolled"

    # --- MANDATORY / REQUIRED FIELDS ---
    first_name = models.CharField(max_length=100, help_text="First name")
    middle_name = models.CharField(max_length=100, blank=True, default="", help_text="Middle name")
    last_name = models.CharField(max_length=100, blank=True, default="", help_text="Last name")

    date_of_birth = models.DateField(null=True, blank=True, help_text="Date of birth")
    age = models.PositiveSmallIntegerField(help_text="Age in years (0-17)")
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE)

    legal_status = models.CharField(
        max_length=100,
        choices=LegalStatus.choices,
        default=LegalStatus.TEMPORARY_CUSTODY,
        help_text="Legal custody type",
    )

    class CaseworkerRole(models.TextChoices):
        CASEWORKER = "Caseworker", "Caseworker"
        SOCIAL_WORKER = "Social Worker", "Social Worker"
        CARE_COORDINATOR = "Care Coordinator", "Care Coordinator"
        UNASSIGNED = "Unassigned", "Unassigned"

    caseworker_name = models.CharField(
        max_length=150,
        choices=CaseworkerRole.choices,
        default=CaseworkerRole.UNASSIGNED,
        help_text="Primary Social Worker / Caseworker assigned",
    )
    caseworker_contact = models.CharField(
        max_length=150,
        blank=True,
        default="",
        help_text="Caseworker phone or email contact details",
    )

    blood_group = models.CharField(
        max_length=10,
        choices=BloodGroup.choices,
        default=BloodGroup.UNKNOWN,
        help_text="Emergency medical blood group",
    )
    severe_allergies = models.CharField(
        max_length=255,
        blank=True,
        default="None",
        help_text="Known severe allergies (e.g., peanuts, penicillin)",
    )
    photo = models.ImageField(
        upload_to="children_photos/",
        null=True,
        blank=True,
        help_text="Child photograph",
    )

    # --- OPTIONAL FIELDS ---
    place_of_birth = models.CharField(max_length=150, blank=True, default="")
    nationality = models.CharField(max_length=100, blank=True, default="")
    ethnicity = models.CharField(max_length=100, blank=True, default="", help_text="Ethnicity / Cultural background")
    languages_spoken = models.CharField(
        max_length=100,
        choices=Language.choices,
        default=Language.ENGLISH,
        help_text="Primary language spoken by the child",
    )
    school_info = models.CharField(max_length=255, blank=True, default="", help_text="School & grade information")
    medical_history = models.TextField(blank=True, default="", help_text="Detailed medical history & conditions")
    special_needs_details = models.TextField(blank=True, default="", help_text="Special needs & accommodation details")
    dietary_preferences = models.CharField(max_length=255, blank=True, default="", help_text="Dietary preferences & restrictions")
    case_notes = models.TextField(
        blank=True,
        default="",
        help_text="Trauma history, sibling placement notes, or behavioral triggers",
    )

    # --- ML & SYSTEM TRACKING FIELDS ---
    state = models.CharField(max_length=100, default="Texas", db_index=True)
    special_needs = models.CharField(
        max_length=100,
        choices=SpecialNeedsType.choices,
        default=SpecialNeedsType.NONE,
        help_text="Special needs category requirement",
    )
    behavioral_support_level = models.CharField(
        max_length=20,
        choices=SupportLevel.choices,
        default=SupportLevel.LOW,
        help_text="Behavioral support level required",
    )
    mental_health_support_level = models.CharField(
        max_length=20,
        choices=SupportLevel.choices,
        default=SupportLevel.LOW,
        help_text="Mental health support level required",
    )
    medical_needs_level = models.CharField(
        max_length=20,
        choices=SupportLevel.choices,
        default=SupportLevel.LOW,
        help_text="Medical needs level required",
    )
    sibling_group_size = models.PositiveSmallIntegerField(
        default=1,
        help_text="1 means the child has no siblings needing joint placement.",
    )
    needs_sibling_placement = models.CharField(
        max_length=10,
        choices=YesNoChoices.choices,
        default=YesNoChoices.NO,
        help_text="Requires joint sibling placement",
    )
    previous_foster_placements = models.PositiveSmallIntegerField(
        default=0,
        help_text="Number of previous foster care placements",
    )
    trauma_severity_level = models.CharField(
        max_length=20,
        choices=SupportLevel.choices,
        default=SupportLevel.LOW,
        help_text="Trauma severity level",
    )
    school_attendance_status = models.CharField(
        max_length=50,
        choices=SchoolAttendanceStatus.choices,
        default=SchoolAttendanceStatus.NONE,
        help_text="School attendance status",
    )
    sibling_group_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="Identifier grouping siblings together for joint placement.",
    )
    behavioral_notes_score = models.FloatField(
        default=0.5,
        help_text="Synthetic 0.0-1.0 severity index used as an ML feature.",
    )
    education_level = models.CharField(max_length=50, default="Elementary")
    time_in_care_months = models.PositiveIntegerField(
        default=6,
        help_text="How long the child has been in the care system so far.",
    )
    is_placed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["state", "is_placed"]),
        ]

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        name = " ".join(p for p in parts if p).strip()
        return name if name else self.first_name

    def save(self, *args, **kwargs):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            dob = self.date_of_birth
            calc_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if calc_age >= 0:
                self.age = calc_age
        super().save(*args, **kwargs)

    @property
    def has_special_needs(self) -> bool:
        return bool(self.special_needs and str(self.special_needs).strip().lower() not in ("none", "", "false", "0"))

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
            ("Primary Language Spoken", _is_completed(self.languages_spoken)),
            ("Special Needs Category", _is_completed(self.special_needs)),
            ("Behavioral Support Level", _is_completed(self.behavioral_support_level)),
            ("Mental Health Support Level", _is_completed(self.mental_health_support_level)),
            ("Medical Needs Level", _is_completed(self.medical_needs_level)),
            ("Sibling Group Size", self.sibling_group_size is not None),
            ("Sibling Placement Required", _is_completed(self.needs_sibling_placement)),
            ("Previous Foster Placements", self.previous_foster_placements is not None),
            ("Trauma Severity Level", _is_completed(self.trauma_severity_level)),
            ("School Attendance Status", _is_completed(self.school_attendance_status)),
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

    def __str__(self):
        return f"{self.full_name} ({self.age}, {self.state})"
