"""
apps.core.views
"""

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render

from apps.children.models import Child
from apps.core.models import ContactMessage
from apps.families.models import FosterFamily
from apps.placements.models import Placement
from apps.predictions.models import Prediction


def landing(request):
    total_children = Child.objects.count()
    total_families = FosterFamily.objects.count()
    total_placements = Placement.objects.count()
    total_predictions = Prediction.objects.count()

    context = {
        "total_children": total_children,
        "total_families": total_families,
        "total_placements": total_placements,
        "total_predictions": total_predictions,
    }
    return render(request, "core/landing.html", context)


def about(request):
    return render(request, "core/about.html")


def contact(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        organization = request.POST.get("organization", "").strip()
        subject = request.POST.get("subject", "").strip() or "other"
        message_text = request.POST.get("message", "").strip()

        if first_name and email and message_text:
            ContactMessage.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                organization=organization,
                subject=subject,
                message=message_text,
            )
            messages.success(
                request,
                f"Thank you, {first_name}! Your message has been saved and sent to our admin team. We will get back to you shortly."
            )
            return redirect("core:contact")
        else:
            messages.error(request, "Please fill in all required fields before submitting your message.")

    return render(request, "core/contact.html")
