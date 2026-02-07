FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    # For MS SQL Server
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    # For LDAP
    libldap2-dev \
    libsasl2-dev \
    ldap-utils \
    # Build tools
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 18 for SQL Server (corrected method)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project src
COPY . .

RUN mkdir -p /staticfiles /media

# Create Django user
RUN useradd -m -u 1000 django && \
    chown -R django:django /app /staticfiles /media

USER django

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/admin/', timeout=5)" || exit 1

# Command will be overridden by docker-compose
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]