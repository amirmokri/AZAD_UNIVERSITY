"""
Management command to clean up old votes and reset expired cancellation statuses.
Run this daily via cron or task scheduler.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from classes.models import ClassSchedule, ClassCancellationVote


class Command(BaseCommand):
    help = 'Clean up old votes and reset expired cancellation statuses'

    def handle(self, *args, **options):
        # Remove votes older than 24 hours
        time_threshold = timezone.now() - timedelta(hours=24)
        old_votes = ClassCancellationVote.objects.filter(voted_at__lt=time_threshold)
        vote_count = old_votes.count()
        old_votes.delete()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {vote_count} old votes'))
        
        # Reset schedules where 24 hours have passed since report
        schedules_to_reset = ClassSchedule.objects.filter(
            student_reported_not_holding=True,
            not_holding_reported_at__lt=time_threshold
        )
        
        reset_count = 0
        for schedule in schedules_to_reset:
            schedule.student_reported_not_holding = False
            schedule.not_holding_reported_at = None
            schedule.save()
            reset_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Reset {reset_count} schedules to holding status'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Cleanup complete!'))

