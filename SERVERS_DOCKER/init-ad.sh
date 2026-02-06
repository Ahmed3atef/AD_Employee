#!/bin/bash
# Active Directory Initialization Script
# This script creates OUs and sample users

# Wait for AD to be ready
echo "Waiting for Active Directory to initialize..."
sleep 60

# Set variables
DOMAIN="eissa.local"
BASE_DN="DC=eissa,DC=local"
ADMIN_PASS="Admin@123456"

# Create the main "New" OU
echo "Creating New OU..."
samba-tool ou create "OU=New,$BASE_DN" 2>/dev/null || echo "New OU may already exist"

# Create sub-OUs under "New"
OUS=(
    "Accountant"
    "Administrative Affairs"
    "Camera"
    "Exhibit"
    "HR"
    "IT"
    "Audit"
    "Out Work"
    "Projects"
    "Sales"
    "Supplies"
    "Secretarial"
)

for ou in "${OUS[@]}"; do
    echo "Creating OU: $ou"
    samba-tool ou create "OU=$ou,OU=New,$BASE_DN" 2>/dev/null || echo "OU $ou may already exist"
done

# Create sample users
echo "Creating sample users..."

# User 1: Mohamed Khaled (Projects)
samba-tool user create mohamed.khaled "User@123456" \
    --given-name="mohamed" \
    --surname="khaled" \
    --mail-address="mohamed.khaled@eissa.local" \
    --telephone-number="110030" \
    --userou="OU=Projects,OU=New" 2>/dev/null || echo "User mohamed.khaled may already exist"

# User 2: Ahmed Hassan (IT)
samba-tool user create ahmed.hassan "User@123456" \
    --given-name="ahmed" \
    --surname="hassan" \
    --mail-address="ahmed.hassan@eissa.local" \
    --telephone-number="110031" \
    --userou="OU=IT,OU=New" 2>/dev/null || echo "User ahmed.hassan may already exist"

# User 3: Sara Ali (HR)
samba-tool user create sara.ali "User@123456" \
    --given-name="sara" \
    --surname="ali" \
    --mail-address="sara.ali@eissa.local" \
    --telephone-number="110032" \
    --userou="OU=HR,OU=New" 2>/dev/null || echo "User sara.ali may already exist"

# User 4: Fatima Ahmed (Accountant)
samba-tool user create fatima.ahmed "User@123456" \
    --given-name="fatima" \
    --surname="ahmed" \
    --mail-address="fatima.ahmed@eissa.local" \
    --telephone-number="110033" \
    --userou="OU=Accountant,OU=New" 2>/dev/null || echo "User fatima.ahmed may already exist"

# User 5: Omar Mahmoud (Sales)
samba-tool user create omar.mahmoud "User@123456" \
    --given-name="omar" \
    --surname="mahmoud" \
    --mail-address="omar.mahmoud@eissa.local" \
    --telephone-number="110034" \
    --userou="OU=Sales,OU=New" 2>/dev/null || echo "User omar.mahmoud may already exist"

echo "Active Directory initialization completed!"
echo ""
echo "=== AD Server Information ==="
echo "Domain: eissa.local"
echo "Base DN: DC=eissa,DC=local"
echo "LDAP Port: 389"
echo "LDAPS Port: 636"
echo "Administrator@eissa.local Password: Admin@123456"
echo "Sample User Password: User@123456"
echo ""
echo "=== Sample Users Created ==="
echo "1. mohamed.khaled@eissa.local (OU=Projects)"
echo "2. ahmed.hassan@eissa.local (OU=IT)"
echo "3. sara.ali@eissa.local (OU=HR)"
echo "4. fatima.ahmed@eissa.local (OU=Accountant)"
echo "5. omar.mahmoud@eissa.local (OU=Sales)"