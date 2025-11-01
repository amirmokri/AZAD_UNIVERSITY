from django.db import migrations


def cleanup_vote_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    app_label = 'classes'
    model_names = ['classcancellationvote', 'classconfirmationvote']

    for model_name in model_names:
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model_name)
        except ContentType.DoesNotExist:
            ct = None

        if ct:
            Permission.objects.filter(content_type=ct).delete()
            ct.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('classes', '0020_ad_facultyadminprofile_adtracking_and_more'),
        ('contenttypes', '__first__'),
        ('auth', '__first__'),
    ]

    operations = [
        migrations.RunPython(cleanup_vote_permissions, migrations.RunPython.noop),
    ]


