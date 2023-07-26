#!/usr/bin/python
import config

import sys
import psycopg2

try:
    conn = psycopg2.connect(database=config.db_name,
                            user=config.db_user,
                            password=config.db_password,
                            host='postgresql',
                            )

    dumpfile = open("dumpfile.sql", "r")

    conn.set_session(autocommit=True)
    cur = conn.cursor()

    count = 0
    while True:
        count += 1

        line = dumpfile.readline()

        if not line:
            break

        try:
            cur.execute(line)
        except Exception as e:
            print(f"Failed to insert line {count}: {line}: {e}",
                  file=sys.stderr)

            conn.rollback()
            break

    # cur.execute(open("dumpfile.sql", "r").read())

    conn.commit()

    print("Successfully executed migration")

except Exception as e:
    conn.rollback()

    print(f"Something went wrong: {e}", file=sys.stderr)
    sys.exit("Database failure")

finally:
    conn.close()
    dumpfile.close()
