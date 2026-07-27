"""
Management command: generate_synthetic_data

Bridges the framework-independent ml/data/synthetic_generator.py into the
database — mirrors the same pattern used for scrape_reports (Step 6): the
ml/ package stays pure Python/pandas/numpy, and only this command touches
Django models.

Run with:
    python manage.py generate_synthetic_data
    python manage.py generate_synthetic_data --children 500 --families 120
    python manage.py generate_synthetic_data --clear   # wipe existing synthetic rows first

By default this is NOT destructive — re-running adds more rows. Pass
--clear to wipe Child/FosterFamily/Placement first (useful for a clean
demo dataset before EDA/ML work).
"""

import numpy as np
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.children.models import Child
from apps.families.models import FosterFamily
from apps.placements.models import Placement
from ml.data.synthetic_generator import (
    RANDOM_SEED,
    generate_children,
    generate_foster_families,
    generate_placements,
)


class Command(BaseCommand):
    help = "Generate synthetic Child, FosterFamily, and Placement records for development/EDA/ML."

    def add_arguments(self, parser):
        parser.add_argument("--children", type=int, default=300, help="Number of Child records to generate.")
        parser.add_argument("--families", type=int, default=80, help="Number of FosterFamily records to generate.")
        parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for reproducibility.")
        parser.add_argument("--clear", action="store_true", help="Delete existing Child/FosterFamily/Placement rows first.")

    def handle(self, *args, **options):
        n_children = options["children"]
        n_families = options["families"]
        rng = np.random.default_rng(options["seed"])

        if options["clear"]:
            self.stdout.write("Clearing existing Placement/Child/FosterFamily rows...")
            Placement.objects.all().delete()
            Child.objects.all().delete()
            FosterFamily.objects.all().delete()

        self.stdout.write(f"Generating {n_children} synthetic children and {n_families} foster families...")
        children_df = generate_children(n_children, rng)
        families_df = generate_foster_families(n_families, rng)
        placements_df = generate_placements(children_df, families_df, rng)

        with transaction.atomic():
            # bulk_create returns objects with .pk populated (SQLite +
            # modern Django supports RETURNING for this) in the SAME
            # ORDER as the input list, which is what lets us map the
            # DataFrame's positional index back to real primary keys below.
            child_objects = Child.objects.bulk_create([
                Child(**row) for row in children_df.to_dict("records")
            ])
            family_objects = FosterFamily.objects.bulk_create([
                FosterFamily(**row) for row in families_df.to_dict("records")
            ])

            # children_df.index / families_df.index are the positional
            # DataFrame indices generate_placements() referenced —
            # reindex-map them to the newly created objects, in order.
            child_by_index = dict(zip(children_df.index, child_objects))
            family_by_index = dict(zip(families_df.index, family_objects))

            placement_objects = []
            placed_child_pks = set()
            occupancy_updates = {}  # family.pk -> count of newly-added occupants

            for row in placements_df.to_dict("records"):
                child_obj = child_by_index[row["child_index"]]
                family_obj = family_by_index[row["family_index"]]
                placement_objects.append(Placement(
                    child=child_obj,
                    family=family_obj,
                    status=row["status"],
                ))
                if row["status"] in ("active", "completed"):
                    placed_child_pks.add(child_obj.pk)
                    occupancy_updates[family_obj.pk] = occupancy_updates.get(family_obj.pk, 0) + 1

            Placement.objects.bulk_create(placement_objects)

            # Reflect placement outcomes back onto Child.is_placed and
            # FosterFamily.current_occupancy so the two tables stay
            # consistent with the Placement rows we just created.
            if placed_child_pks:
                Child.objects.filter(pk__in=placed_child_pks).update(is_placed=True)

            for family_pk, count in occupancy_updates.items():
                FosterFamily.objects.filter(pk=family_pk).update(current_occupancy=count)

        self.stdout.write(self.style.SUCCESS(
            f"Created {len(child_objects)} children, {len(family_objects)} families, "
            f"{len(placement_objects)} placements."
        ))
