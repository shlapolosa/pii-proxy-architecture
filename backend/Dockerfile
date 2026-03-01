# NOTE: main-latest tracks the latest dev build. Pin to a specific tag
# (e.g. main-v1.67.2.dev1) if you need reproducible builds.
FROM ghcr.io/berriai/litellm:main-latest

WORKDIR /app

RUN pip install presidio-analyzer presidio-anonymizer spacy
RUN python -m spacy download en_core_web_lg

COPY pii_detection_service.py custom_recognizers.py presidio_config.py \
     notification_handler.py error_handler.py litellm_pii_hook.py /app/
