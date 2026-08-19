"""
apps.children.forms
"""

from django import forms

from apps.children.models import Child


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = [
            # Mandatory fields
            "first_name", "middle_name", "last_name",
            "date_of_birth", "age", "gender",
            "legal_status", "caseworker_name", "caseworker_contact",
            "blood_group", "severe_allergies", "photo",
            # Optional fields
            "ethnicity", "languages_spoken", "special_needs",
            "behavioral_support_level", "mental_health_support_level", "medical_needs_level",
            "sibling_group_size", "needs_sibling_placement", "previous_foster_placements",
            "trauma_severity_level", "school_attendance_status",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"}),
            "middle_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Middle Name (Optional)"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name (Optional)"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "age": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 17, "placeholder": "Age"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "legal_status": forms.Select(attrs={"class": "form-select"}),
            "caseworker_name": forms.Select(
                choices=[
                    ("Unassigned", "Unassigned"),
                    ("Caseworker", "Caseworker"),
                    ("Social Worker", "Social Worker"),
                    ("Care Coordinator", "Care Coordinator"),
                ],
                attrs={"class": "form-select"}
            ),
            "caseworker_contact": forms.TextInput(attrs={"class": "form-control", "placeholder": "10-digit Phone Number"}),
            "blood_group": forms.Select(attrs={"class": "form-select"}),
            "severe_allergies": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Peanuts, Penicillin, None"}),
            "photo": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),

            "ethnicity": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ethnic / Cultural background"}),
            "languages_spoken": forms.Select(attrs={"class": "form-select"}),
            "special_needs": forms.Select(attrs={"class": "form-select"}),
            "behavioral_support_level": forms.Select(attrs={"class": "form-select"}),
            "mental_health_support_level": forms.Select(attrs={"class": "form-select"}),
            "medical_needs_level": forms.Select(attrs={"class": "form-select"}),
            "sibling_group_size": forms.NumberInput(attrs={"class": "form-control", "min": 0, "placeholder": "0"}),
            "needs_sibling_placement": forms.Select(attrs={"class": "form-select"}),
            "previous_foster_placements": forms.NumberInput(attrs={"class": "form-control", "min": 0, "placeholder": "0"}),
            "trauma_severity_level": forms.Select(attrs={"class": "form-select"}),
            "school_attendance_status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional fields allowed to be blank
        self.fields["middle_name"].required = False
        self.fields["last_name"].required = False
        self.fields["photo"].required = False
        self.fields["caseworker_contact"].required = False
        self.fields["severe_allergies"].required = False
        self.fields["ethnicity"].required = False
        self.fields["sibling_group_size"].required = False
        self.fields["previous_foster_placements"].required = False

        dropdown_fields = [
            "gender",
            "legal_status",
            "caseworker_name",
            "blood_group",
            "languages_spoken",
            "special_needs",
            "behavioral_support_level",
            "mental_health_support_level",
            "medical_needs_level",
            "needs_sibling_placement",
            "trauma_severity_level",
            "school_attendance_status",
        ]

        for field_name in dropdown_fields:
            if field_name in self.fields:
                field = self.fields[field_name]
                current_choices = list(field.choices)
                # Ensure "None" is at the top of choices
                if not any(c[0] == "None" for c in current_choices):
                    field.choices = [("None", "None")] + [c for c in current_choices if c[0] not in ("", "None")]
                else:
                    field.choices = [("None", "None")] + [c for c in current_choices if c[0] not in ("", "None")]

                # Set default selected value to "None" when registering a new child
                if not self.instance.pk:
                    self.initial[field_name] = "None"

    def clean_gender(self):
        gender = self.cleaned_data.get("gender")
        if gender == "None" or not gender:
            raise forms.ValidationError("Please select a valid Gender / Sex.")
        return gender

    def clean_legal_status(self):
        status = self.cleaned_data.get("legal_status")
        if status == "None" or not status:
            raise forms.ValidationError("Please select a valid Legal Status / Custody Type.")
        return status

    def clean_age(self):
        age = self.cleaned_data.get("age")
        if age is not None:
            if age < 0 or age > 17:
                raise forms.ValidationError(
                    "Invalid Age. Because this is a child identity section, the age must be between 0 and 17."
                )
        return age

    def clean_severe_allergies(self):
        allergies = self.cleaned_data.get("severe_allergies", "").strip()
        return allergies

    def clean_caseworker_contact(self):
        contact = self.cleaned_data.get("caseworker_contact", "").strip()
        if not contact:
            return ""

        if "@" in contact:
            raise forms.ValidationError("Email address is not allowed here. Please enter a valid 10-digit Indian phone number.")

        digits = "".join(c for c in contact if c.isdigit())
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        elif len(digits) == 11 and digits.startswith("0"):
            digits = digits[1:]

        if len(digits) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit phone number (no more, no less).")

        if digits[0] not in ("6", "7", "8", "9"):
            raise forms.ValidationError("Indian phone number must start with 6, 7, 8, or 9.")

        return f"+91-{digits[:5]}-{digits[5:]}"

    def clean(self):
        cleaned_data = super().clean()
        dob = cleaned_data.get("date_of_birth")
        age = cleaned_data.get("age")

        if dob:
            from datetime import date
            today = date.today()
            if dob > today:
                self.add_error("date_of_birth", "Date of birth cannot be in the future.")
                return cleaned_data

            calc_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

            if calc_age < 0 or calc_age > 17:
                self.add_error(
                    "date_of_birth",
                    "Invalid Age. Because this is a child identity section, the age must be between 0 and 17."
                )
            elif age is not None and age != calc_age:
                self.add_error(
                    "date_of_birth",
                    f"Date of birth indicates age {calc_age}, which does not match entered age {age}."
                )
            elif age is None and 0 <= calc_age <= 17:
                cleaned_data["age"] = calc_age
                if "age" in self._errors:
                    del self._errors["age"]
        return cleaned_data
