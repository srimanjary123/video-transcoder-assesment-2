# Stage 1: build
FROM python:3.11-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip --no-cache-dir install -r requirements.txt
COPY app.py .
# Stage 2: runtime
FROM python:3.11-slim
# create non-root user
RUN groupadd -r app && useradd -r -g app app
WORKDIR /app
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /app /app
# expose the port your app uses (screenshot shows 8082)
EXPOSE 8082
# healthcheck for docker/ECS local testing
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8082/health/live || exit 1

USER app
CMD ["python", "app.py"]