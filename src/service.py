#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: service.py
Author: Cornelius Davis
Date: 2026-09-13
Description: 
"""
import uuid
import os
from datetime import datetime, timedelta, timezone
from enum import Enum

import psycopg2 # postgres driver
from psycopg2.extras import RealDictCursor # Allows me to get results as dictionaries instead of tuples

UTC = timezone.utc

# This mirrors the request states in the db. Helps to avoid invalid transactions.
class RequestState(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    EXPIRED = "EXPIRED"
    
# any business/policy rule failure (caps, reserves, grant rules, state machine rules).
class PolicyViolation(Exception):
    """Raised when a request violates a policy."""
    pass

# When two things try to update the same request at once and conflict.
class ConcurrencyError(Exception):
    """Raised when concurrency/versioning checks fail."""
    pass

#Establish connection to db.
def get_conn():
     """Open a new Postgres connection."""
     return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        cursor_factory=RealDictCursor,
    )

def create_request(
    department_id: str, # The ID of the department making the request.
    requester_id: str, # The ID of the user making the request.
    category: str, # The category of the request.
    amount_cents: int, # The amount requested in cents.
    grant_id: int | None = None, # Optional grant ID associated with the request.
    desired_date: datetime | None = None, # Optional desired date for the request.
    justification: str | None = None, # Optional justification for the request.
) -> str:
    """
    Create a new spend request in SUBMITTED state in the database.
    
    For MVP I will skip the DRAFT state.
    Assign a 14 day expiration date to the request.

    Returns:
        str: The ID of the newly created request.
    """
    request_id = str(uuid.uuid4())
    expires_at = datetime.now(UTC) + timedelta(days=14)

    return request_id