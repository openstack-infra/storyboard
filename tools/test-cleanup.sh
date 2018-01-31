#!/bin/bash -xe

# Remove any lingering storyboard_test_db_% databases.

# The 'show databases' output looks like:
#
# +---------------------------------------------------------+
# | Database (storyboard_test_db_%)                         |
# +---------------------------------------------------------+
# | storyboard_test_db_03033b25_dd78_40c0_9b93_c1af5e3dc983 |
# | storyboard_test_db_0393fbbc_133d_46b3_8af1_e3b5aa40eb0f |
# | storyboard_test_db_07ec9cd9_7f30_4424_802a_a54e2d56bd41 |
# | storyboard_test_db_09442795_dfdf_4839_8572_f4e53bc152d9 |
# +---------------------------------------------------------+
#
# Build the list of databases, removing the table heading.
DATABASES=$(mysql -u root -e "show databases like 'storyboard_test_db_%';" |
                   grep storyboard_test_db | grep -v Database | cut -f1 -d\| )

for db in $DATABASES; do
    mysql -u root -e "drop database $db;"
done
