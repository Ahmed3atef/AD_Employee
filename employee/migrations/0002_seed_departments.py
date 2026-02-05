from django.db import migrations


def add_departments(apps, schema_editor):
    Department = apps.get_model('employee', 'Department')

    departments = [
        "Accountant",
        "Administrative Affairs",
        "Camera",
        "Exhibit",
        "HR",
        "IT",
        "Audit",
        "Out Work",
        "Projects",
        "Sales",
        "Supplies",
        "Secretarial",
    ]

    for name in departments:
        Department.objects.get_or_create(name=name)


def remove_departments(apps, schema_editor):
    Department = apps.get_model('employee', 'Department')

    departments = [
        "Accountant",
        "Administrative Affairs",
        "Camera",
        "Exhibit",
        "HR",
        "IT",
        "Audit",
        "Out Work",
        "Projects",
        "Sales",
        "Supplies",
        "Secretarial",
    ]

    Department.objects.filter(name__in=departments).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_departments, remove_departments),
    ]
