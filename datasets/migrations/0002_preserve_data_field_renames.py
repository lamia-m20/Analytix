from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0001_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='dataset',
            name='datasets_da_owner_i_4ddb22_idx',
        ),
        migrations.RenameField(
            model_name='dataset',
            old_name='owner',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='dataset',
            old_name='name',
            new_name='title',
        ),
        migrations.RenameField(
            model_name='dataset',
            old_name='original_file',
            new_name='file',
        ),
        migrations.RenameField(
            model_name='datasetsheet',
            old_name='sheet_index',
            new_name='index',
        ),
        migrations.RenameField(
            model_name='datasetsheet',
            old_name='rows_count',
            new_name='row_count',
        ),
        migrations.RenameField(
            model_name='datasetsheet',
            old_name='columns_count',
            new_name='column_count',
        ),
        migrations.RenameField(
            model_name='datasetsheet',
            old_name='is_selected',
            new_name='is_active',
        ),
        migrations.RenameField(
            model_name='datasetcolumn',
            old_name='column_index',
            new_name='position',
        ),
        migrations.RenameField(
            model_name='datasetcolumn',
            old_name='detected_type',
            new_name='data_type',
        ),
        migrations.RenameField(
            model_name='datasetcolumn',
            old_name='missing_values_count',
            new_name='null_count',
        ),
        migrations.RenameField(
            model_name='datasetcolumn',
            old_name='unique_values_count',
            new_name='unique_count',
        ),
    ]
