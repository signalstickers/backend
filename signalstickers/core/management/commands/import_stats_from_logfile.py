import csv
from datetime import datetime
import re
import sys

from core.models import Pack, SiteStat
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Import stats from Apache logfile for all packs."

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=open)

    def handle(self, *_, **options):

        print(
            """
                #################
                #### WARNING ####
                #################

This command will DELETE AND REPLACE ALL EXISTING STATS
ON THE APPLICATION. Use it WITH CAUTION.

"""
        )

        reply = str(
            input("Are you sure you want to continue? Type 'yes replace all': ")
        )
        if reply != "yes replace all":
            print("Aborting.")
            sys.exit()
        print("You can still abort during initial parsing with Ctrl+C.\n")

        nb_lines_imported = 0
        packs_stats = {}
        site_stats = {}

        logreader = csv.reader(options["input_file"], delimiter="|")
        for line in logreader:
            if not line:
                continue

            if not line[1].startswith("POST /ping"):
                continue

            visit_date = datetime.fromtimestamp(int(line[0]))
            visit_date = visit_date.strftime("%Y_%m")

            try:
                # Packs
                pack_id = re.match(
                    "https://signalstickers.org/pack/([a-z0-9]{32})", line[2]
                ).group(1)

                if pack_id not in packs_stats:
                    packs_stats[pack_id] = {}

                if visit_date in packs_stats[pack_id]:
                    packs_stats[pack_id][visit_date] += 1
                else:
                    packs_stats[pack_id][visit_date] = 1

            except AttributeError:
                # Visits
                if visit_date in site_stats:
                    site_stats[visit_date] += 1
                else:
                    site_stats[visit_date] = 1

            nb_lines_imported += 1
            if nb_lines_imported % 10000 == 0:
                self.stdout.write(f"\rParsed: {nb_lines_imported} ", ending="")

        print("\n\n##### It is now too late to abort. #####")

        # Save pack stats
        for pack_id, stats in packs_stats.items():
            try:
                Pack.objects.filter(pack_id=pack_id).update(stats=stats)
            except Pack.DoesNotExist:
                continue

        # Save global visit stats
        for month, visits in site_stats.items():
            month_visit = SiteStat.objects.get_or_create(month=month)[0]
            month_visit.visits = visits
            month_visit.save()

        self.stdout.write(f"\nAll done! Imported: {nb_lines_imported} stats items.")
