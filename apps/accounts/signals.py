"""
Signal handlers for the accounts app.

WHY A SIGNAL HERE:
Every Django User must have exactly one Profile (it's how we store role).
Rather than remembering to manually create a Profile everywhere a User is
created (registration view, Django admin, management commands, tests), we
hook into User's post_save signal once, here, so it happens automatically
and can never be forgotten. This is the standard, idiomatic use of Django
signals — small, single-purpose, and not overused.
"""

from django.contrib.auth.models import Group, User
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import Profile

# Maps Profile.Role values to the Group name seeded by `manage.py seed_roles`.
ROLE_TO_GROUP_NAME = {
    Profile.Role.ADMIN: "Admin",
    Profile.Role.CASEWORKER: "Case Worker",
    Profile.Role.VIEWER: "Viewer",
}


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        role = Profile.Role.ADMIN if (instance.is_superuser or instance.is_staff) else Profile.Role.VIEWER
        Profile.objects.create(user=instance, role=role)
    else:
        profile, _ = Profile.objects.get_or_create(user=instance)
        if (instance.is_superuser or instance.is_staff) and profile.role != Profile.Role.ADMIN:
            profile.role = Profile.Role.ADMIN
            profile.save()


@receiver(post_save, sender=Profile)
def sync_group_with_role(sender, instance, **kwargs):
    """
    Keep Django's Group membership in sync with Profile.role.

    WHY THIS EXISTS: Profile.role is what templates/UI logic read (fast,
    simple, no extra query pattern). Groups are what Django's permission
    system (`user.has_perm(...)`) actually enforces at the view level. If
    these ever drifted out of sync, a user could see an "Admin" UI while
    actually lacking Admin permissions, or vice-versa - a real security
    bug. This signal makes drift impossible: every save to Profile.role
    immediately updates the user's single role Group membership.

    Safe no-op if `seed_roles` hasn't been run yet in this environment -
    the relevant Group simply won't exist and membership stays unchanged
    until it is.
    """
    target_group_name = ROLE_TO_GROUP_NAME.get(instance.role)
    if not target_group_name:
        return

    user = instance.user
    all_role_group_names = list(ROLE_TO_GROUP_NAME.values())
    stale_groups = Group.objects.filter(name__in=all_role_group_names).exclude(name=target_group_name)
    user.groups.remove(*stale_groups)

    try:
        target_group = Group.objects.get(name=target_group_name)
    except Group.DoesNotExist:
        return
    user.groups.add(target_group)

    if instance.role == Profile.Role.ADMIN and not user.is_staff:
        user.is_staff = True
        user.save(update_fields=["is_staff"])
