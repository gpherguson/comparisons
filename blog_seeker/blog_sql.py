#!/usr/bin/env python

from sqlalchemy import create_engine

engine = create_engine('postgres://postgres:password@localhost', echo=True)

