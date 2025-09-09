## Pull WealthX Data in Batches

### Objective

Create a project using python to pull WealthX data into a local mongo database. (mongo db is already setup and running)

- WealthX has ~420k records.
- The project needs to pull data in batches of a certain size that ensure completion of pull in 10 days and the pull can happend 3 to 4 times a day.
- The project should be able to resume from the last successful pull in case of failure.
