"""
Elasticsearch document classes for indexing and searching.

This module defines Elasticsearch documents for:
- Course: For searching courses by name, code, description
- Teacher: For searching teachers by name, email, specialization

These documents enable fast and flexible search functionality.
"""

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Course, Teacher


@registry.register_document
class CourseDocument(Document):
    """Elasticsearch document for Course model."""
    
    faculty = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'faculty_name': fields.TextField(),
        'faculty_code': fields.TextField(),
    })
    
    class Index:
        # Name of the Elasticsearch index
        name = 'courses'
        # See Elasticsearch Indices API reference for available settings
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'persian_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'persian_stop']
                    }
                },
                'filter': {
                    'persian_stop': {
                        'type': 'stop',
                        'stopwords': '_persian_'
                    }
                }
            }
        }

    class Django:
        model = Course  # The model associated with this Document
        
        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'id',
            'course_code',
            'course_name',
            'credit_hours',
            'description',
            'is_active',
        ]
        
        # To enable automatic updates from model
        related_models = ['Faculty']
        
    def get_queryset(self):
        """Override to only index active courses."""
        return super().get_queryset().select_related('faculty')
    
    def get_instances_from_related(self, related_instance):
        """If related_models is set, define how to retrieve the Course instance(s) from the related model."""
        if isinstance(related_instance, Faculty):
            return related_instance.courses.all()


@registry.register_document
class TeacherDocument(Document):
    """Elasticsearch document for Teacher model."""
    
    class Index:
        # Name of the Elasticsearch index
        name = 'teachers'
        # See Elasticsearch Indices API reference for available settings
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'persian_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'persian_stop']
                    }
                },
                'filter': {
                    'persian_stop': {
                        'type': 'stop',
                        'stopwords': '_persian_'
                    }
                }
            }
        }

    class Django:
        model = Teacher  # The model associated with this Document
        
        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'id',
            'full_name',
            'email',
            'phone_number',
            'specialization',
            'is_active',
        ]
    
    def get_queryset(self):
        """Override to only index active teachers."""
        return super().get_queryset().filter(is_active=True)

