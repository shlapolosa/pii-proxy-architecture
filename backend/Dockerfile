FROM ghcr.io/berriai/litellm:main-latest

RUN pip install presidio-analyzer presidio-anonymizer spacy
RUN python -m spacy download en_core_web_lg

COPY pii_detection_service.py custom_recognizers.py presidio_config.py \
     notification_handler.py error_handler.py litellm_pii_hook.py /app/
