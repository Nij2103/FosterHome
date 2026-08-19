"""
Management command: seed_roles

WHY A MANAGEMENT COMMAND (not a data migration):
Data migrations that create Groups/Permissions are a common Django
anti-pattern — permissions objects are created by Django itself *after*
migrations run (via a post_migrate signal), so a data migration that tries
to assign them can run before they exist, causing flaky failures depending
on app load order. A management command that's run explicitly, once, after
`migrate`, sidesteps this entirely and is the documented-safe approach.

Run with: python manage.py seed_roles
Safe to re-run — uses get_or_create throughout.
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.models import Placement
from apps.predictions.models import Prediction
        # --- Case Worker: full CRUD on operational data ---
        caseworker_group, _ = Group.objects.get_or_create(name="Case Worker")
        caseworker_perms = []
        for model in [Child, FosterFamily, Placement, Prediction]:
            caseworker_perms += self._perms_for(model, ["add", "change", "view", "delete"])
        caseworker_group.permissions.set(caseworker_perms)

        # --- Viewer: read-only everywhere, no create/edit/delete ---
        viewer_group, _ = Group.objects.get_or_create(name="Viewer")
        viewer_perms = []
        for model in [Child, FosterFamily, Placement, Prediction]:
            viewer_perms += self._perms_for(model, ["view"])
        viewer_group.permissions.set(viewer_perms)

        # --- Admin: gets Django's is_superuser flag instead of a permission
        #     list (superusers implicitly pass every has_perm() check) ---
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        # Still attach the full permission set explicitly too, so
        # user.groups.filter(name="Admin") checks in templates/mixins work
        # even for an Admin-role user who isn't flagged is_superuser.
        admin_perms = []
        for model in [Child, FosterFamily, Placement, Prediction, Report, ReportStatistic]:
            admin_perms += self._perms_for(model, ["add", "change", "view", "delete"])
        admin_group.permissions.set(admin_perms)

        self.stdout.write(self.style.SUCCESS(
            "Roles seeded: Admin, Case Worker, Viewer (safe to re-run)."
        ))

    @staticmethod
    def _perms_for(model, actions):
        ct = ContentType.objects.get_for_model(model)
        codenames = [f"{action}_{model._meta.model_name}" for action in actions]
        return list(Permission.objects.filter(content_type=ct, codename__in=codenames))
