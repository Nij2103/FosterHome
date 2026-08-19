"""
apps.families.forms
"""

from django import forms

from apps.families.models import FosterFamily


class FosterFamilyForm(forms.ModelForm):
    TRAINING_CHOICES = [
        ("Trauma-informed care", "Trauma-informed care"),
        ("CPR & First Aid", "CPR & First Aid"),
        ("Child mental health", "Child mental health"),
        ("Special needs care", "Special needs care"),
        ("Medical care training", "Medical care training"),
        ("Behavioral intervention training", "Behavioral intervention training"),
    ]

    special_trainings_list = forms.MultipleChoiceField(
        choices=TRAINING_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Special Training / Certifications",
    )

    class Meta:
        model = FosterFamily
        fields = [
            # Mandatory / Core Info
            "family_name", "primary_applicant_name",
            "phone_number", "email_address", "residential_address",
            "capacity", "languages_spoken",
            "license_status", "background_clearance_status",
            "identity_doc_number", "identity_document",
            # Household & Preferences
            "marital_status", "household_composition",
            "preferred_age_group", "preferred_gender", "preferred_special_needs",
            "accept_sibling_placements", "max_sibling_group_accepted",
            "special_trainings",
            # Family Placement Assessment Section
            "behavioral_support_capacity", "mental_health_support_capacity",
            "medical_support_capacity", "parenting_experience_years",
            "previous_foster_placements_count", "successful_foster_placements_count",
            "housing_stability", "family_support_network",
            "long_term_placement_willingness", "therapy_support_availability",
        ]
        widgets = {
            "family_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Family Name (e.g. Johnson Family)"}),
            "primary_applicant_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Legal Name(s) of Foster Parent(s)"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "9876543210", "maxlength": "15"}),
            "email_address": forms.EmailInput(attrs={"class": "form-control", "placeholder": "family@example.com"}),
            "residential_address": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Street Address, City, State, ZIP"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1, "placeholder": "Max children allowed"}),
            "languages_spoken": forms.Select(attrs={"class": "form-select"}),

            "license_status": forms.Select(attrs={"class": "form-select"}),
            "background_clearance_status": forms.Select(attrs={"class": "form-select"}),
            "identity_doc_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Driver License / Passport / Govt ID Number"}),
            "identity_document": forms.FileInput(attrs={"class": "form-control", "accept": "image/*", "capture": "environment"}),

            "marital_status": forms.Select(attrs={"class": "form-select"}),
            "household_composition": forms.Select(attrs={"class": "form-select"}),
            "preferred_age_group": forms.Select(attrs={"class": "form-select"}),
            "preferred_gender": forms.Select(attrs={"class": "form-select"}),
            "preferred_special_needs": forms.Select(attrs={"class": "form-select"}),
            "accept_sibling_placements": forms.Select(attrs={"class": "form-select"}),
            "max_sibling_group_accepted": forms.NumberInput(attrs={"class": "form-control", "min": 0, "placeholder": "0"}),

            # Assessment Widgets
            "behavioral_support_capacity": forms.Select(attrs={"class": "form-select"}),
            "mental_health_support_capacity": forms.Select(attrs={"class": "form-select"}),
            "medical_support_capacity": forms.Select(attrs={"class": "form-select"}),
            "parenting_experience_years": forms.NumberInput(attrs={"class": "form-control", "min": 0, "placeholder": "0"}),
            "previous_foster_placements_count": forms.NumberInput(attrs={"class": "form-control", "min": 0, "placeholder": "0"}),
            "successful_foster_placements_count": forms.NumberInput(attrs={"class": "form-control", "min": 0, "placeholder": "0"}),
            "housing_stability": forms.Select(attrs={"class": "form-select"}),
            "family_support_network": forms.Select(attrs={"class": "form-select"}),
            "long_term_placement_willingness": forms.Select(attrs={"class": "form-select"}),
            "therapy_support_availability": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate selected checkboxes for edit mode
        if self.instance and self.instance.pk and self.instance.special_trainings:
            selected = [s.strip() for s in self.instance.special_trainings.split(",") if s.strip()]
            self.initial["special_trainings_list"] = selected

        # Optional fields allowed to be blank
        self.fields["email_address"].required = False
        self.fields["identity_doc_number"].required = False
        self.fields["identity_document"].required = False
        self.fields["max_sibling_group_accepted"].required = False
        self.fields["parenting_experience_years"].required = False
        self.fields["previous_foster_placements_count"].required = False
        self.fields["successful_foster_placements_count"].required = False

        dropdown_fields = [
            "languages_spoken",
            "license_status",
            "background_clearance_status",
            "marital_status",
            "household_composition",
            "preferred_age_group",
            "preferred_gender",
            "preferred_special_needs",
            "accept_sibling_placements",
            "behavioral_support_capacity",
            "mental_health_support_capacity",
            "medical_support_capacity",
            "housing_stability",
            "family_support_network",
            "long_term_placement_willingness",
            "therapy_support_availability",
        ]

        for field_name in dropdown_fields:
            if field_name in self.fields:
                field = self.fields[field_name]
                current_choices = list(field.choices)
                if not any(c[0] == "None" for c in current_choices):
                    field.choices = [("None", "None")] + [c for c in current_choices if c[0] not in ("", "None")]
                else:
                    field.choices = [("None", "None")] + [c for c in current_choices if c[0] not in ("", "None")]

                if not self.instance.pk:
                    self.initial[field_name] = "None"

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        if not phone:
            raise forms.ValidationError("Phone number is required.")

        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        elif len(digits) == 11 and digits.startswith("0"):
            digits = digits[1:]

        if len(digits) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit phone number (no more, no less).")

        if digits[0] not in ("6", "7", "8", "9"):
            raise forms.ValidationError("Indian phone number must start with 6, 7, 8, or 9.")

        return f"+91-{digits[:5]}-{digits[5:]}"

    def clean_capacity(self):
        capacity = self.cleaned_data.get("capacity")
        if capacity is not None and capacity < 1:
            raise forms.ValidationError("Home capacity must be at least 1 child.")
        return capacity

    def clean(self):
        cleaned_data = super().clean()
        trainings = cleaned_data.get("special_trainings_list", [])
        cleaned_data["special_trainings"] = ", ".join(trainings)
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        trainings = self.cleaned_data.get("special_trainings_list", [])
        instance.special_trainings = ", ".join(trainings)
        if commit:
            instance.save()
        return instance
