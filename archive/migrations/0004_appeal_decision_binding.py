from django.db import migrations, models
import django.db.models.deletion

def bind_appeals(apps,schema_editor):
    Appeal=apps.get_model('archive','Appeal')
    Decision=apps.get_model('archive','Decision')
    for appeal in Appeal.objects.all():
        source=Decision.objects.filter(submission_id=appeal.submission_id,created_at__lte=appeal.created_at).order_by('-created_at','-id').first()
        if not source:
            raise RuntimeError('An existing appeal has no prior decision. Operator reconciliation is required.')
        if Appeal.objects.filter(decision_id=source.id).exists():
            raise RuntimeError('Multiple existing appeals refer to one decision. Operator reconciliation is required.')
        appeal.decision_id=source.id
        appeal.save(update_fields=['decision'])

class Migration(migrations.Migration):
    dependencies=[('archive','0003_decision_conflicts')]
    operations=[
        migrations.AddField(model_name='appeal',name='decision',field=models.OneToOneField(null=True,on_delete=django.db.models.deletion.PROTECT,to='archive.decision')),
        migrations.RunPython(bind_appeals,migrations.RunPython.noop),
        migrations.AlterField(model_name='appeal',name='decision',field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,to='archive.decision')),
    ]
