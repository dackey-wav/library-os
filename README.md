# SmartLib DB Project

## Getting Started Guide

1. Clone Repository

2. Copy paths templates from .env.example to .env and fill in correct data

3. You can easily connect to a remote DB via the CLI.\
   For Windows, use the following commands:
   - ***./db-connect.ps1 owner***
   - ***./db-connect.ps1 user***
   - (if don't specify a user, it will connect to the owner by default)

   For Linux, use the following commands:
   - ***./db-connect.sh owner***
   - ***./db-connect.sh user***
   - (if don't specify a user, it will connect to the owner by default)

4. ***coming soon...***

## Project structure
```
DB_project/
├─ alembic/              # migrations
├─ app/
│  ├─ models.py          # ORM-models
|  └─ db.py
├─scripts/
|  └─ dataset.py         # dataset import script
├─ static/
|  └─ covers/            # local images for book covers
├─ .env.example
├─ db-connect.ps1        # commands for connecting to DB (Windows)
├─ db-connect.ps1        # commands for connecting to DB (Linux)
├─ requirements.txt
└─ README.md
```
