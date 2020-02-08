#!/usr/bin/env python
from __future__ import print_function

import argparse
import re
import sys

from apt_pkg import version_compare, init_system
from subprocess import check_output, CalledProcessError


class PurgeOldVersions:
    def __init__(self):
        self.args = self.parse_arguments()

        if self.args.dry_run:
            print("Run in dry mode, without actually deleting the packages.")

        if not self.args.repo:
            sys.exit("You must declare a repository with: --repo")

        if not self.args.package_query:
            sys.exit("You must declare a package query with: --package-query")

        print("Remove " + self.args.package_query + " from " + self.args.repo +
              " and keep the last " + str(self.args.retain_how_many) +
              " packages")

    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("--dry-run", dest="dry_run",
                            help="List packages to remove without removing "
                                 "them.", action="store_true")
        parser.add_argument("--repo", dest="repo",
                            help="Which repository should be searched?",
                            type=str)
        parser.add_argument("--package-query", dest="package_query",
                            help="Which packages should be removed?\n"
                                 "e.g.\n"
                                 "  - Single package: ros-indigo-rbdl.\n"
                                 "  - Query: 'Name (%% ros-indigo-*)' "
                                 "to match all ros-indigo packages. See \n"
                                 "https://www.aptly.info/doc/feature/query/",
                            type=str)
        parser.add_argument("-n", "--retain-how-many", dest="retain_how_many",
                            help="How many package versions should be kept?",
                            type=int, default=1)
        return parser.parse_args()

    def get_packages(self):
        init_system()

        packages = []

        try:
            output = check_output(["aptly", "repo", "remove", "-dry-run=true",
                                   self.args.repo, self.args.package_query])
            output = [line for line in output.split("\n") if
                      line.startswith("[-]")]
            output = [line.replace("[-] ", "") for line in output]
            output = [line.replace(" removed", "") for line in output]


            for p in output:
                packages.append(
                    re.sub("[_](\d{1,}[:])?(\d{1,}[.]){1,}(.*)", '', p))
            packages = list(set(packages))
            packages.sort()

        except CalledProcessError as e:
            print(e)

        finally:
            return packages

    def purge(self):
        init_system()

        packages = self.get_packages()
        if not packages:
            sys.exit("No packages to remove.")

        # Initial call to print 0% progress
        i = 0
        l = len(packages)
        printProgressBar(i, l, prefix='Progress:', suffix='Complete', length=50)

        packages_to_remove = []
        for package in packages:
            try:
                output = check_output(["aptly", "repo", "remove",
                                       "-dry-run=true", self.args.repo,
                                       package])
                output = [line for line in output.split("\n") if
                          line.startswith("[-]")]
                output = [line.replace("[-] ", "") for line in output]
                output = [line.replace(" removed", "") for line in output]

                def sort_cmp(name1, name2):
                    version_and_build_1 = name1.split("_")[1]
                    version_and_build_2 = name2.split("_")[1]
                    return version_compare(version_and_build_1,
                                           version_and_build_2)

                output.sort(cmp=sort_cmp)
                should_delete = output[:-self.args.retain_how_many]
                packages_to_remove += should_delete

                i += 1
                printProgressBar(i, l, prefix='Progress:', suffix='Complete',
                                 length=100)

            except CalledProcessError as e:
                print(e)

        print(" ")
        if self.args.dry_run:
            print("\nThis packages would be deleted:")
            for p in packages_to_remove:
                print(p)
        else:
            if packages_to_remove:
                print(check_output(["aptly", "repo", "remove",
                                    self.args.repo] + packages_to_remove))
                print("\nRun 'aptly publish update ...' "
                      "to update the repository.")
            else:
                print("nothing to remove")


# Print iterations progress
def printProgressBar(iteration, total, prefix='', suffix='', decimals=1,
                     length=100, fill='#'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent
                                  complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(
        100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


if __name__ == '__main__':
    purge_old_versions = PurgeOldVersions()
    purge_old_versions.purge()
