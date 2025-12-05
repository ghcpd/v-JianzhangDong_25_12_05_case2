FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
# Default environment variables (should be set securely in real deployments)
ENV FLASK_APP=inputs.py
CMD ["/bin/bash","-lc","python -u test_runner.py input.py secure"]
