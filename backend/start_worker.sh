#!/bin/bash
celery -A app.core.celery_app worker --beat --loglevel=info